from hoe.stations import StationButtons
from hoe.state import STATE


class CollaborationManager(object):
    def compute_state(self, t, collaboration_state, osc_data):
        raise NotImplementedError("All feedback effects must implement compute_state")


class ButtonToggleResponderManager(CollaborationManager):
    """Each button press sends a toggle command back to the controller.

        Currently useful for testing, but not much else.

       TODO: Store the button state and send explicit on/off commands
    """

    def compute_state(self, t, collaboration_state, osc_data):
        # type: (float, {}, StoredOSCData) -> None
        for s, station in enumerate(osc_data.stations):
            for b_id, val in station.button_presses.items():
                # pylint: disable=unsubscriptable-object
                STATE.stations[s].buttons[b_id] = StationButtons.BUTTON_TOGGLE


class NoOpCollaborationManager(CollaborationManager):
    """A no-op collaboration manager for when you need a placeholder in your scene"""

    def compute_state(self, t, collaboration_state, osc_data):
        pass


class PassThru(object):
    """A collab manager where all of the responsibility for setting the
    state belongs to the effects.
    """
    def compute_state(self, t, collaboration_state, osc_date):
        return collaboration_state
