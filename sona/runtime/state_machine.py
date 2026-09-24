"""Generic finite-state-machine definitions and atomic transition validation."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass

_SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_MAX_STATES = 4_096
_MAX_TRANSITIONS = 65_536


class InvalidStateTransition(ValueError):
    """Raised when an event has no transition from the current state."""


@dataclass(frozen=True, slots=True)
class StateTransition:
    from_state: str
    event: str
    to_state: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("from_state", self.from_state),
            ("event", self.event),
            ("to_state", self.to_state),
        ):
            if not isinstance(value, str) or not _SAFE_NAME.fullmatch(value):
                raise ValueError(f"{field_name} must be a safe identifier")


@dataclass(frozen=True, slots=True)
class StateMachineDefinition:
    states: tuple[str, ...]
    initial_state: str
    transitions: tuple[StateTransition, ...]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.states, tuple) or not self.states:
            raise ValueError("states must be a non-empty tuple")
        if len(self.states) > _MAX_STATES:
            raise ValueError("state count cannot exceed 4096")
        if any(
            not isinstance(state, str) or not _SAFE_NAME.fullmatch(state)
            for state in self.states
        ):
            raise ValueError("states must contain safe identifiers")
        if len(set(self.states)) != len(self.states):
            raise ValueError("state names must be unique")
        if self.initial_state not in self.states:
            raise ValueError("initial_state must be declared")
        if not isinstance(self.transitions, tuple) or any(
            not isinstance(item, StateTransition) for item in self.transitions
        ):
            raise ValueError("transitions must be a tuple of StateTransition records")
        if len(self.transitions) > _MAX_TRANSITIONS:
            raise ValueError("transition count cannot exceed 65536")
        keys: set[tuple[str, str]] = set()
        for transition in self.transitions:
            if transition.from_state not in self.states or transition.to_state not in self.states:
                raise ValueError("transition references an undeclared state")
            key = (transition.from_state, transition.event)
            if key in keys:
                raise ValueError("transition event is ambiguous for its source state")
            keys.add(key)
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version != 1
        ):
            raise ValueError("state machine definition requires schema_version 1")


@dataclass(frozen=True, slots=True)
class StateMachineSnapshot:
    state: str
    sequence: int
    last_event: str | None


class StateMachine:
    """Thread-safe FSM; invalid transition attempts leave state unchanged."""

    def __init__(self, definition: StateMachineDefinition) -> None:
        if not isinstance(definition, StateMachineDefinition):
            raise TypeError("definition must be a StateMachineDefinition")
        self.definition = definition
        self._transitions = {
            (item.from_state, item.event): item.to_state for item in definition.transitions
        }
        self._state = definition.initial_state
        self._sequence = 0
        self._last_event: str | None = None
        self._lock = threading.Lock()

    def snapshot(self) -> StateMachineSnapshot:
        with self._lock:
            return StateMachineSnapshot(self._state, self._sequence, self._last_event)

    def can_trigger(self, event: str) -> bool:
        if not isinstance(event, str):
            return False
        with self._lock:
            return (self._state, event) in self._transitions

    def trigger(self, event: str) -> StateMachineSnapshot:
        if not isinstance(event, str) or not _SAFE_NAME.fullmatch(event):
            raise ValueError("event must be a safe identifier")
        with self._lock:
            target_state = self._transitions.get((self._state, event))
            if target_state is None:
                raise InvalidStateTransition(
                    f"event {event} is not valid from state {self._state}"
                )
            self._state = target_state
            self._sequence += 1
            self._last_event = event
            return StateMachineSnapshot(self._state, self._sequence, self._last_event)
