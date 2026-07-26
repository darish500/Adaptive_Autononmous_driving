#state_machine_code 

OFF = 0
BOOTING = 1
INITIALIZING = 2
READY = 3
MISSION = 4
EMERGENCY = 5   
RECOVERY = 6
SHUTDOWN = 7

STATE_NAMES = {
    OFF: "OFF",
    BOOTING:"BOOTING",
    INITIALIZING:"INITIALIZING",
    READY:"READY",
    MISSION:"MISSION",
    EMERGENCY:"EMERGENCY",
    RECOVERY:"RECOVERY",
    SHUTDOWN:"SHUTDOWN",
}

LEGAL_TRANSITIONS ={
    OFF: {BOOTING},
    BOOTING:{INITIALIZING, EMERGENCY},
    INITIALIZING: {READY, EMERGENCY},
    READY: {MISSION, SHUTDOWN , EMERGENCY},
    MISSION: {READY , EMERGENCY , RECOVERY},
    EMERGENCY: {RECOVERY, SHUTDOWN},
    RECOVERY: {READY, SHUTDOWN, EMERGENCY },
    SHUTDOWN: {OFF},    
}

class OrionStateMachine:
    """Responsible for the tracking of the current orion state and validating the transistion"""
    def __init__(self):
        self.current_state = OFF

    def can_transition(self, requested_state:int) -> bool:
        """Returns True if it is moving from the current state to the requested state is legal, otherwise returns False"""
        legal_targets = LEGAL_TRANSITIONS.get(self.current_state, set())
        return requested_state in legal_targets

    def transition(self, requested_state: int):
        """Attempt to move to a requested state.

        Returns a (accepted: bool, reason: str) tuple.
        """
        if requested_state not in STATE_NAMES:
            return False, f"Requested state {requested_state} is not a valid state."

        if requested_state == self.current_state:
            return False, (
                f"Already in state {STATE_NAMES[requested_state]}; "
                "no transition needed."
            )

        if not self.can_transition(requested_state):
            legal = ', '.join(
                STATE_NAMES[s] for s in LEGAL_TRANSITIONS[self.current_state]
            )
            return False, (
                f"Illegal transition: {STATE_NAMES[self.current_state]} -> "
                f"{STATE_NAMES[requested_state]}. "
                f"Legal transitions from {STATE_NAMES[self.current_state]} "
                f"are: {legal}."
            )

        old_state = self.current_state
        self.current_state = requested_state
        return True, (
            f"Transition {STATE_NAMES[old_state]} -> "
            f"{STATE_NAMES[requested_state]} successful."
        )

    