"""Thread-safe bounded channels for schema-validated message envelopes."""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from numbers import Real

from .contracts import BackpressurePolicy, ChannelDefinition, ChannelState
from .events import MessageEnvelope, MessageSchema

_CANCEL_POLL_SECONDS = 0.05


class ChannelError(RuntimeError):
    """Base class for deterministic channel operation failures."""


class ChannelClosedError(ChannelError):
    """Raised when sending after close or when close interrupts a blocked send."""


class ChannelFullError(ChannelError):
    """Raised when a REJECT channel cannot accept a message immediately."""


class ChannelCancelledError(ChannelError):
    """Raised when a caller's cancellation event is set before an operation commits."""


class ChannelTimeoutError(ChannelError, TimeoutError):
    """Raised when a blocking send or receive reaches its finite timeout."""


@dataclass(frozen=True, slots=True)
class SendReceipt:
    accepted: bool = True
    dropped_message_id: str | None = None


class BoundedChannel:
    """A FIFO, fixed-capacity message channel; messages never grant authority."""

    def __init__(self, definition: ChannelDefinition, schema: MessageSchema) -> None:
        if not isinstance(definition, ChannelDefinition):
            raise TypeError("definition must be a ChannelDefinition")
        if not isinstance(schema, MessageSchema):
            raise TypeError("schema must be a MessageSchema")
        if definition.message_type != schema.message_type:
            raise ValueError("channel message_type must match its MessageSchema")
        self.definition = definition
        self.schema = schema
        self._items: deque[MessageEnvelope] = deque()
        self._condition = threading.Condition()
        self._state = ChannelState.OPEN

    @property
    def state(self) -> ChannelState:
        with self._condition:
            return self._state

    @property
    def size(self) -> int:
        with self._condition:
            return len(self._items)

    def send(
        self,
        message: MessageEnvelope,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> SendReceipt:
        deadline = _deadline(timeout)
        if not isinstance(message, MessageEnvelope):
            raise TypeError("message must be a MessageEnvelope")
        # Snapshot through the wire contract so the caller cannot mutate a
        # queued payload while this sender waits for capacity.
        queued_message = MessageEnvelope.from_json(message.to_json())
        self.schema.validate(queued_message)
        _validate_cancel_event(cancel_event)

        with self._condition:
            while True:
                _check_cancelled(cancel_event)
                if self._state is ChannelState.CLOSED:
                    raise ChannelClosedError("cannot send to a closed channel")
                if len(self._items) < self.definition.capacity:
                    self._items.append(queued_message)
                    self._condition.notify_all()
                    return SendReceipt()

                policy = self.definition.backpressure
                if policy is BackpressurePolicy.REJECT:
                    raise ChannelFullError("channel is full; message was rejected")
                if policy is BackpressurePolicy.DROP_OLDEST:
                    dropped = self._items.popleft()
                    self._items.append(queued_message)
                    self._condition.notify_all()
                    return SendReceipt(dropped_message_id=dropped.message_id)

                wait_seconds = _wait_duration(deadline, cancel_event)
                self._condition.wait(wait_seconds)

    def receive(
        self,
        *,
        timeout: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> MessageEnvelope | None:
        deadline = _deadline(timeout)
        _validate_cancel_event(cancel_event)
        with self._condition:
            while True:
                _check_cancelled(cancel_event)
                if self._items:
                    message = self._items.popleft()
                    self._condition.notify_all()
                    return message
                if self._state is ChannelState.CLOSED:
                    return None
                wait_seconds = _wait_duration(deadline, cancel_event)
                self._condition.wait(wait_seconds)

    def close(self) -> bool:
        """Close once, wake all waiters, and permit queued items to be drained."""
        with self._condition:
            if self._state is ChannelState.CLOSED:
                return False
            self._state = ChannelState.CLOSED
            self._condition.notify_all()
            return True


def _deadline(timeout: float | None) -> float | None:
    if timeout is None:
        return None
    if isinstance(timeout, bool) or not isinstance(timeout, Real):
        raise ValueError("timeout must be a finite non-negative number")
    try:
        timeout_value = float(timeout)
    except (OverflowError, ValueError) as exc:
        raise ValueError("timeout must be a finite non-negative number") from exc
    if not math.isfinite(timeout_value) or timeout_value < 0:
        raise ValueError("timeout must be a finite non-negative number")
    deadline = time.monotonic() + timeout_value
    if not math.isfinite(deadline):
        raise ValueError("timeout deadline exceeds the supported range")
    return deadline


def _validate_cancel_event(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and not isinstance(cancel_event, threading.Event):
        raise TypeError("cancel_event must be a threading.Event")


def _check_cancelled(cancel_event: threading.Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise ChannelCancelledError("channel operation was cancelled")


def _wait_duration(deadline: float | None, cancel_event: threading.Event | None) -> float | None:
    remaining = None if deadline is None else deadline - time.monotonic()
    if remaining is not None and remaining <= 0:
        raise ChannelTimeoutError("channel operation timed out")
    if cancel_event is None:
        return remaining
    return _CANCEL_POLL_SECONDS if remaining is None else min(remaining, _CANCEL_POLL_SECONDS)
