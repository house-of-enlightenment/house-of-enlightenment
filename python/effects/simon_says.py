import logging

from hoe import animation_framework as af
from hoe.state import STATE


# different modes for the game
DEFINE_PATTERN = 'define-pattern'
DEFINE_PATTERN_WAIT = 'define-pattern-wait'
COPY_PATTERN = 'copy-pattern'
COPY_PATTERN_WAIT = 'copy-pattern-wait'
WON = 'won'


logger = logging.getLogger(__name__)


class BasicSimonSays(af.Effect, af.CollaborationManager):
    def __init__(self):
        self.mode = DEFINE_PATTERN_WAIT
        self.success = False

    def _set_mode(self, val):
        logger.debug('Setting mode to %s', val)
        self._mode = val

    def _get_mode(self):
        return self._mode

    mode = property(_get_mode, _set_mode)

    def scene_starting(self, now, osc):
        for s in STATE.stations:
            s.buttons._buttons = [1, 1, 0, 1, 1]

    def compute_state(self, now, state, osc):
        if self.mode == DEFINE_PATTERN_WAIT:
            # We wait for the first button press
            # when that happens, the person who pressed the button
            # becomes "simon" and they get to define a pattern
            for i, station in enumerate(osc.stations):
                # ignore the middle button
                first = next((b for b in station.button_presses if b != 2), None)
                if first is not None:
                    self.simon = i
                    self.define_pattern = DefinePattern(self, i, first)
                    self.mode = DEFINE_PATTERN
                    return
        elif self.mode == DEFINE_PATTERN:
            self.define_pattern.compute_state(now, state, osc)
        elif self.mode == COPY_PATTERN_WAIT:
            # We wait for the first button press
            # when that happens, the person who pressed the button
            # is the one to try to copy simon
            for i, station in enumerate(osc.stations):
                if i == self.simon:
                    continue
                # ignore the middle button
                first = next((b for b in station.button_presses if b != 2), None)
                if first == self.target_pattern[0]:
                    self.copy_pattern = CopyPattern(self, i, self.target_pattern)
                    self.mode = COPY_PATTERN
                    return
        elif self.mode == COPY_PATTERN:
            self.copy_pattern.compute_state(now, state, osc)

    def pattern_defined(self, pattern):
        assert len(pattern) >= 2
        self.target_pattern = pattern
        self.mode = COPY_PATTERN_WAIT

    def pattern_copied(self):
        for s in STATE.stations:
            s.set_button_values([0, 0, 0, 0, 0])
        self.mode = WON

    def pattern_failed(self):
        self.define_pattern.finish()
        self.mode = COPY_PATTERN_WAIT

    def next_frame(self, pixels, now, state, osc):
        if self.mode == WON:
            pixels[:] = 255


class CopyPattern(object):
    def __init__(self, parent, station_id, target_pattern):
        self.parent = parent
        self.station_id = station_id
        self.target_pattern = target_pattern
        self.idx = 1 # not 0, we've already matched the first by time we are here
        self._start()

    def _start(self):
        for i, s in enumerate(STATE.stations):
            if i == self.station_id:
                s.set_button_values([1, 1, 0, 1, 1])
            else:
                s.set_button_values([0, 0, 0, 0, 0])
        return self

    def compute_state(self, now, state, osc):
        my_buttons = osc.stations[self.station_id].button_presses
        if not my_buttons:
            return
        # TOD: how likely is it that people would mash buttons
        #      and we'd get two hits at the same time?
        expected = self.target_pattern[self.idx]
        if expected in my_buttons:
            logger.debug('Success. Pressed the right button')
            self.advance()
        else:
            logger.debug('Failed. Pressed %s, expected %s', my_buttons, expected)
            self.fail()

    def advance(self):
        self.idx += 1
        if self.idx >= len(self.target_pattern):
            self.parent.pattern_copied()

    def fail(self):
        self.parent.pattern_failed()


class DefinePattern(object):
    def __init__(self, parent, station_id, first_button):
        self.parent = parent
        self.station_id = station_id
        self.pattern = [first_button]
        self._start()

    def _start(self):
        for i, s in enumerate(STATE.stations):
            if i == self.station_id:
                # TODO: shouldn't turn on the middle button until
                # the pattern is at least two long
                s.set_button_values([1, 1, 1, 1, 1])
            else:
                s.set_button_values([0, 0, 0, 0, 0])
        return self

    def compute_state(self, now, state, osc):
        my_buttons = osc.stations[self.station_id].button_presses
        if len(self.pattern) > 2 and 2 in my_buttons:
            self.finish()
            self.parent.pattern_defined(self.pattern)
        else:
            first = next((b for b in my_buttons if b != 2), None)
            if first is not None:
                logger.debug('Adding button %s to pattern', first)
                self.pattern.append(first)

    def finish(self):
        for i, s in enumerate(STATE.stations):
            if i == self.station_id:
                s.set_button_values([0, 0, 0, 0, 0])
            else:
                s.set_button_values([1, 1, 0, 1, 1])


SCENES = [
    af.Scene('basic-simon-says', tags=[], collaboration_manager=BasicSimonSays())
]
