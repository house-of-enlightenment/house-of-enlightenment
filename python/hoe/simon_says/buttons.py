import logging

from hoe.state import STATE

from shared import *


logger = logging.getLogger(__name__)


class TurnOnButtonsAndWaitForPress(object):
    def __init__(self, parent, station_id, lit_buttons, right_buttons=None):
        print station_id, lit_buttons
        self.parent = parent
        self.station_id = station_id
        self.lit_buttons = set(lit_buttons)
        self.right_buttons = set(right_buttons or lit_buttons)
        self.need_to_set_buttons = True

    def compute_state(self, now, state, osc):
        if self.need_to_set_buttons:
            self._only_turn_on_my_buttons()
            self.need_to_set_buttons = False
        pressed_buttons = osc.buttons[self.station_id]
        allowed_pressed_buttons = pressed_buttons & self.right_buttons
        if allowed_pressed_buttons:
            button = allowed_pressed_buttons.pop()
            # if you pressed a right and wrong button, we'll give you
            # the benefit of the doubt
            return self._on_correct_button_press(now, button)
        other_buttons = pressed_buttons - self.right_buttons
        if other_buttons:
            self._on_wrong_button_press(now,other_buttons)

    def _only_turn_on_my_buttons(self):
        logger.debug(
            'Setting buttons for my section (%s - %s)', self.station_id, self.lit_buttons)
        station = STATE.stations[self.station_id]
        station.set_button_values([0, 0, 0, 0, 0])
        for b in self.lit_buttons:
            station.buttons[b] = 1

    def _on_correct_button_press(self, now, button):
        return self.parent._on_correct_button_press(now, button)

    def _on_wrong_button_press(self, now, other_buttons):
        return self.parent._on_wrong_button_press(now, other_buttons)

#
# this turned into an ugly mess quick.
#
class TurnOnOnlyMyButtonAndWaitForPress(object):
    def __init__(
            self, parent, station_id, button=None, last_button=None, flash=True, on_finished=None):
        self.parent = parent
        self.station_id = station_id
        self.button = self.get_button(button, last_button)
        self.set_buttons = False
        self.flash = flash
        self.on_finished = on_finished or self.parent.next_step

    def get_button(self, button, last_button):
        return button if button is not None else get_random_game_button(excluding=last_button)

    def compute_state(self, now, state, osc):
        if not self.set_buttons:
            self._only_turn_on_my_button()
            self.set_buttons = True
        pressed_buttons = osc.buttons[self.station_id]
        if self.button in pressed_buttons:
            return self._on_correct_button_press(now)
        other_buttons = pressed_buttons - set([self.button])
        if other_buttons:
            return self._on_wrong_button_press(now, other_buttons)

    def _on_correct_button_press(self, now):
        self._turn_off_button()
        if self.flash:
            self.parent.render = Flash(
                self.parent, BUTTON_COLORS[self.button], self.on_finished, now)
        else:
            self.on_finished()
        print "we got a point"
        return {self.station_id: 1}

    def _on_wrong_button_press(self, now, wrong_buttons):
        pass

    def _only_turn_on_my_button(self):
        logger.debug('Setting buttons')
        for i, s in enumerate(STATE.stations):
            s.set_button_values([0, 0, 0, 0, 0])
            if i == self.station_id:
                s.buttons[self.button] = 1

    def _turn_off_button(self):
        STATE.stations[self.station_id].buttons[self.button] = 0


class TurnOnMyButtonAndWaitForPress(TurnOnOnlyMyButtonAndWaitForPress):
    def _only_turn_on_my_button(self):
        logger.debug('Setting buttons for my section (%s - %s)', self.station_id, self.button)
        station = STATE.stations[self.station_id]
        station.set_button_values([0, 0, 0, 0, 0])
        station.buttons[self.button] = 1


class TurnOnMyButtonAndWaitForPressFollower(TurnOnMyButtonAndWaitForPress):
    def _on_correct_button_press(self, now):
        def callback():
            self.parent.next_step(correct=True)
        self._turn_off_button()
        print 'Parent:', self.parent
        self.parent.render = FlashStation(
            self.parent, self.station_id, RIGHT_COLOR, callback, now)

    def _on_wrong_button_press(self, now, wrong_buttons):
        def callback():
            self.parent.next_step(correct=False)
        self._turn_off_button()
        self.parent.render = FlashStation(
            self.parent, self.station_id, WRONG_COLOR, callback, now)

