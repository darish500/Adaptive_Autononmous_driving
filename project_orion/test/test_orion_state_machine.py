"""Unit tests for the pure-Python ORION state machine logic.

These tests import orion_state_machine directly and do not require
ROS 2 to be running.
"""

from project_orion.orion_state_machine import (
    OrionStateMachine,
    OFF,
    BOOTING,
    MISSION,
    EMERGENCY,
    RECOVERY,
)


def test_starts_in_off():
    machine = OrionStateMachine()
    assert machine.current_state == OFF


def test_legal_transition_succeeds():
    machine = OrionStateMachine()
    accepted, reason = machine.transition(BOOTING)
    assert accepted is True
    assert machine.current_state == BOOTING


def test_illegal_transition_is_rejected_and_state_unchanged():
    machine = OrionStateMachine()
    accepted, reason = machine.transition(MISSION)
    assert accepted is False
    assert machine.current_state == OFF


def test_same_state_request_is_rejected():
    machine = OrionStateMachine()
    accepted, reason = machine.transition(OFF)
    assert accepted is False
    assert machine.current_state == OFF


def test_unknown_state_is_rejected():
    machine = OrionStateMachine()
    accepted, reason = machine.transition(99)
    assert accepted is False
    assert machine.current_state == OFF


def test_emergency_reachable_from_mission():
    machine = OrionStateMachine()
    machine.transition(BOOTING)
    machine.current_state = MISSION  # force state for this isolated check
    accepted, reason = machine.transition(EMERGENCY)
    assert accepted is True
    assert machine.current_state == EMERGENCY


def test_emergency_cannot_skip_directly_to_mission():
    machine = OrionStateMachine()
    machine.current_state = EMERGENCY  # force state for this isolated check
    accepted, reason = machine.transition(MISSION)
    assert accepted is False
    assert machine.current_state == EMERGENCY


def test_emergency_can_reach_recovery():
    machine = OrionStateMachine()
    machine.current_state = EMERGENCY
    accepted, reason = machine.transition(RECOVERY)
    assert accepted is True
    assert machine.current_state == RECOVERY