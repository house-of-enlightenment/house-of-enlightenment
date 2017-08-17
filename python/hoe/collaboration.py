from hoe.state import STATE


class CollaborationManager(object):
    def compute_state(self, t, collaboration_state, osc_data):
        raise NotImplementedError("All feedback effects must implement compute_state")
        # TODO: use abc


class ButtonToggleResponderManager(CollaborationManager):
    """Each button press sends a toggle command back to the controller.

        Currently useful for testing, but not much else.

       TODO: Store the button state and send explicit on/off commands
    """

    def compute_state(self, t, collaboration_state, osc_data):
        # type: (float, {}, StoredOSCData) -> None
        for s, station in enumerate(osc_data.stations):
            for b_id, val in station.button_presses.items():
                STATE.buttons[s][b_id] = StationButtons.BUTTON_TOGGLE


class NoOpCollaborationManager(CollaborationManager):
    """A no-op collaboration manager for when you need a placeholder in your scene"""

    def compute_state(self, t, collaboration_state, osc_data):
        pass
