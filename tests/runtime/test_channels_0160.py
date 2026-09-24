"""Tests for bounded channel lifecycle and backpressure behavior."""

from __future__ import annotations

import threading

import pytest

from sona.runtime import (
    BackpressurePolicy,
    BoundedChannel,
    ChannelCancelledError,
    ChannelClosedError,
    ChannelDefinition,
    ChannelFullError,
    ChannelState,
    ChannelTimeoutError,
    MessageEnvelope,
    MessageField,
    MessageSchema,
)


def _schema() -> MessageSchema:
    return MessageSchema(
        "BuildResult",
        1,
        (MessageField("artifact", "string"),),
    )


def _message(artifact: str) -> MessageEnvelope:
    return MessageEnvelope("BuildResult", {"artifact": artifact})


def _channel(capacity: int = 2, policy: BackpressurePolicy = BackpressurePolicy.BLOCK):
    definition = ChannelDefinition("build-results", "BuildResult", capacity, policy)
    return BoundedChannel(definition, _schema())


def test_channel_fifo_is_bounded_and_close_drains_before_end_of_stream():
    channel = _channel(capacity=2)
    first, second = _message("one"), _message("two")
    assert channel.send(first).accepted
    assert channel.send(second).accepted
    assert channel.size == 2

    assert channel.close()
    assert channel.close() is False
    assert channel.state is ChannelState.CLOSED
    with pytest.raises(ChannelClosedError):
        channel.send(_message("three"))
    assert channel.receive() == first
    assert channel.receive() == second
    assert channel.receive() is None
    assert channel.size == 0


def test_reject_backpressure_reports_full_without_losing_queued_message():
    channel = _channel(capacity=1, policy=BackpressurePolicy.REJECT)
    first = _message("keep")
    channel.send(first)
    with pytest.raises(ChannelFullError):
        channel.send(_message("reject"))
    assert channel.receive() == first


def test_drop_oldest_backpressure_reports_exact_discarded_message():
    channel = _channel(capacity=1, policy=BackpressurePolicy.DROP_OLDEST)
    first, second = _message("old"), _message("new")
    channel.send(first)
    result = channel.send(second)
    assert result.dropped_message_id == first.message_id
    assert channel.size == 1
    assert channel.receive() == second


def test_blocking_sender_resumes_when_receiver_frees_capacity():
    channel = _channel(capacity=1)
    channel.send(_message("initial"))
    with pytest.raises(ChannelTimeoutError):
        channel.send(_message("timed-out"), timeout=0.001)
    assert channel.size == 1
    started, finished = threading.Event(), threading.Event()
    outcomes: list[object] = []

    def sender() -> None:
        started.set()
        try:
            outcomes.append(channel.send(_message("next"), timeout=2))
        except Exception as exc:  # surfaced in the owning test thread
            outcomes.append(exc)
        finally:
            finished.set()

    thread = threading.Thread(target=sender)
    thread.start()
    assert started.wait(1)
    assert not finished.wait(0.05)
    assert channel.receive().payload == {"artifact": "initial"}
    assert finished.wait(1)
    thread.join(1)
    assert len(outcomes) == 1 and not isinstance(outcomes[0], BaseException)
    assert channel.receive().payload == {"artifact": "next"}


def test_waiting_receive_supports_timeout_cancellation_and_close_wakeup():
    channel = _channel()
    with pytest.raises(ChannelTimeoutError):
        channel.receive(timeout=0.001)

    cancel_event = threading.Event()
    queued = _message("preserve-on-cancel")
    channel.send(queued)
    cancel_event.set()
    with pytest.raises(ChannelCancelledError):
        channel.receive(cancel_event=cancel_event)
    assert channel.size == 1
    assert channel.receive() == queued

    cancel_event.clear()
    started, finished = threading.Event(), threading.Event()
    outcomes: list[object] = []

    def receiver() -> None:
        started.set()
        try:
            outcomes.append(channel.receive(cancel_event=cancel_event))
        except Exception as exc:  # surfaced in the owning test thread
            outcomes.append(exc)
        finally:
            finished.set()

    thread = threading.Thread(target=receiver)
    thread.start()
    assert started.wait(1)
    cancel_event.set()
    assert finished.wait(1)
    thread.join(1)
    assert len(outcomes) == 1 and isinstance(outcomes[0], ChannelCancelledError)

    waiting_channel = _channel()
    close_started = threading.Event()
    close_outcomes: list[object] = []

    def closed_receiver() -> None:
        close_started.set()
        close_outcomes.append(waiting_channel.receive())

    close_thread = threading.Thread(target=closed_receiver)
    close_thread.start()
    assert close_started.wait(1)
    waiting_channel.close()
    close_thread.join(1)
    assert not close_thread.is_alive()
    assert close_outcomes == [None]


def test_blocked_send_is_cancelled_and_schema_mismatch_is_rejected():
    channel = _channel(capacity=1)
    channel.send(_message("initial"))
    with pytest.raises(ValueError, match="message type does not match schema"):
        channel.send(MessageEnvelope("Other", {}))

    cancel_event = threading.Event()
    started, finished = threading.Event(), threading.Event()
    outcomes: list[object] = []

    def sender() -> None:
        started.set()
        try:
            channel.send(_message("cancel"), cancel_event=cancel_event)
        except Exception as exc:  # surfaced in the owning test thread
            outcomes.append(exc)
        finally:
            finished.set()

    thread = threading.Thread(target=sender)
    thread.start()
    assert started.wait(1)
    cancel_event.set()
    assert finished.wait(1)
    thread.join(1)
    assert len(outcomes) == 1 and isinstance(outcomes[0], ChannelCancelledError)
    assert channel.size == 1


def test_close_interrupts_a_blocked_sender_without_enqueuing_its_message():
    channel = _channel(capacity=1)
    channel.send(_message("initial"))
    started = threading.Event()
    outcomes: list[object] = []

    def sender() -> None:
        started.set()
        try:
            channel.send(_message("after-close"))
        except Exception as exc:  # surfaced in the owning test thread
            outcomes.append(exc)

    thread = threading.Thread(target=sender)
    thread.start()
    assert started.wait(1)
    channel.close()
    thread.join(1)
    assert not thread.is_alive()
    assert len(outcomes) == 1 and isinstance(outcomes[0], ChannelClosedError)
    assert channel.size == 1


def test_channel_definition_rejects_invalid_bounds_and_backpressure_types():
    with pytest.raises(ValueError, match="between 1 and 65536"):
        ChannelDefinition("huge", "BuildResult", 65_537)
    with pytest.raises(ValueError, match="must be an integer"):
        ChannelDefinition("fraction", "BuildResult", 1.5)
    with pytest.raises(ValueError, match="BackpressurePolicy"):
        ChannelDefinition("bad-policy", "BuildResult", 1, "drop_oldest")
    with pytest.raises(ValueError, match="finite non-negative number"):
        _channel().receive(timeout=float("inf"))
