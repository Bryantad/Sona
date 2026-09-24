"""Tests for generic finite-state-machine contract validation."""

from __future__ import annotations

import pytest

from sona.runtime import (
    InvalidStateTransition,
    StateMachine,
    StateMachineDefinition,
    StateTransition,
)


def _definition() -> StateMachineDefinition:
    return StateMachineDefinition(
        states=("closed", "opening", "open"),
        initial_state="closed",
        transitions=(
            StateTransition("closed", "open_requested", "opening"),
            StateTransition("opening", "opened", "open"),
            StateTransition("opening", "open_failed", "closed"),
            StateTransition("open", "close_requested", "closed"),
        ),
    )


def test_machine_accepts_defined_transitions_and_increments_sequence():
    machine = StateMachine(_definition())
    assert machine.can_trigger("open_requested")
    first = machine.trigger("open_requested")
    assert (first.state, first.sequence, first.last_event) == (
        "opening",
        1,
        "open_requested",
    )
    second = machine.trigger("opened")
    assert (second.state, second.sequence) == ("open", 2)
    assert machine.trigger("close_requested").state == "closed"


def test_undefined_transition_fails_without_mutating_machine_state():
    machine = StateMachine(_definition())
    before = machine.snapshot()
    assert not machine.can_trigger("opened")
    with pytest.raises(InvalidStateTransition, match="not valid from state closed"):
        machine.trigger("opened")
    assert machine.snapshot() == before


def test_definition_rejects_duplicate_or_undeclared_transitions():
    with pytest.raises(ValueError, match="state names must be unique"):
        StateMachineDefinition(("idle", "idle"), "idle", ())
    with pytest.raises(ValueError, match="initial_state must be declared"):
        StateMachineDefinition(("idle",), "missing", ())
    with pytest.raises(ValueError, match="undeclared state"):
        StateMachineDefinition(
            ("idle",), "idle", (StateTransition("idle", "start", "running"),)
        )
    with pytest.raises(ValueError, match="ambiguous"):
        StateMachineDefinition(
            ("idle", "running", "stopped"),
            "idle",
            (
                StateTransition("idle", "start", "running"),
                StateTransition("idle", "start", "stopped"),
            ),
        )


def test_machine_rejects_malformed_events_and_definitions():
    machine = StateMachine(_definition())
    with pytest.raises(ValueError, match="safe identifier"):
        machine.trigger("bad event")
    with pytest.raises(ValueError, match="non-empty tuple"):
        StateMachineDefinition((), "idle", ())
    with pytest.raises(ValueError, match="schema_version 1"):
        StateMachineDefinition(("idle",), "idle", (), schema_version=2)
    with pytest.raises(ValueError, match="state count cannot exceed"):
        StateMachineDefinition(tuple(f"state-{index}" for index in range(4097)), "state-0", ())
