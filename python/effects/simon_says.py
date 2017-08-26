import functools
import logging


import numpy as np

from hoe import animation_framework as af
from hoe import stations
from hoe.state import STATE


# different modes for the game
DEFINE_PATTERN = 'define-pattern'
DEFINE_PATTERN_WAIT = 'define-pattern-wait'
COPY_PATTERN = 'copy-pattern'
COPY_PATTERN_WAIT = 'copy-pattern-wait'
WON = 'won'


logger = logging.getLogger(__name__)

N_STATIONS = 6
N_BUTTONS = 5
BUTTON_COLORS = stations.BUTTON_COLORS


# want to use GREEN / RED, but don't want to match
# the colors that flash when a pattern is being set
RIGHT_COLOR = (34, 139, 34) # forest green
WRONG_COLOR = (176, 28, 46) # stop sign red


class BasicSimonSays(af.Effect, af.CollaborationManager):
    def __init__(self):
        self.mode = DEFINE_PATTERN_WAIT
        self.success = False
        self._flash = None

    def _set_mode(self, val):
        logger.debug('Setting mode to %s', val)
        self._mode = val

    def _get_mode(self):
        return self._mode

    mode = property(_get_mode, _set_mode)

    def flash(self, color, now, duration=0.35):
        assert self._flash is None
        until = now + .35
        self._flash = (until, color)

    def scene_starting(self, now, osc):
        for s in STATE.stations:
            s.buttons._buttons = [1, 1, 0, 1, 1]

    def compute_state(self, now, state, osc):
        if self._flash:
            return
        if self.mode == DEFINE_PATTERN_WAIT:
            # We wait for the first button press
            # when that happens, the person who pressed the button
            # becomes "simon" and they get to define a pattern
            for s_id, buttons in osc.buttons.items():
                # ignore the middle button
                first = next((b for b in buttons if b != 2), None)
                if first is not None:
                    self.simon = s_id
                    self.define_pattern = DefinePattern(self, s_id, first)
                    self.flash(BUTTON_COLORS[first], now)
                    self.mode = DEFINE_PATTERN
                    return
        elif self.mode == DEFINE_PATTERN:
            self.define_pattern.compute_state(now, state, osc)
        elif self.mode == COPY_PATTERN_WAIT:
            # We wait for the first button press
            # when that happens, the person who pressed the button
            # is the one to try to copy simon
            for s_id, buttons in osc.buttons.items():
                if s_id == self.simon:
                    continue
                # ignore the middle button
                first = next((b for b in buttons if b != 2), None)
                if first == self.target_pattern[0]:
                    self.copy_pattern = CopyPattern(self, s_id, self.target_pattern)
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
        if self._flash:
            until, color = self._flash
            if now <= until:
                pixels[:2,] = color
            else:
                self._flash = None
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
        my_buttons = osc.buttons[self.station_id]
        if not my_buttons:
            return
        # TODO: how likely is it that people would mash buttons
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
        my_buttons = osc.buttons[self.station_id]
        if len(self.pattern) > 2 and 2 in my_buttons:
            self.finish()
            self.parent.pattern_defined(self.pattern)
        else:
            first = next((b for b in my_buttons if b != 2), None)
            if first is not None:
                logger.debug('Adding button %s to pattern', first)
                self.parent.flash(BUTTON_COLORS[first], now)
                self.pattern.append(first)

    def finish(self):
        for i, s in enumerate(STATE.stations):
            if i == self.station_id:
                s.set_button_values([0, 0, 0, 0, 0])
            else:
                s.set_button_values([1, 1, 0, 1, 1])


# We need a tutorial to introduce everybody to the game.
#
# First round:
# One button flashes.
#    When pressed, the ring flashes that color
# Another button flashes (at the same station)
#    When pressed, the ring flashes
# The center button flashes.
# Now, the first button flashes on all of the other stations
# After being pressed, the second one flashes.
#
# Second round, same thing, but with three buttons.
#
# Third round, the leader gets two options instead of being forced


ENTER_BUTTON = 2
GAME_BUTTONS = [0, 1, 3, 4]


class Flash(object):
    def __init__(self, parent, color, on_finish, now, duration=0.35):
        self.parent = parent
        self.color = color
        self.on_finish = on_finish
        self.until = now + duration
        self.finished = False

    def next_frame(self, pixels, now, state, osc):
        if now >= self.until:
            assert self.finished == False
            self.on_finish()
            self.finished = True
        else:
            self.draw(pixels)

    def draw(self, pixels):
        pixels[:2,] = self.color


class FlashStation(Flash):
    def __init__(self, parent, section_id, color, on_finish, now, duration=0.35):
        self.section_id = section_id
        Flash.__init__(self, parent, color, on_finish, now, duration)

    def draw(self, pixels):
        section = STATE.layout.STATIONS[self.section_id]
        pixels[:2, section.left:section.right] = self.color


class ColorStation(object):
    def __init__(self, station_id, color):
        self.station_id = station_id
        self.color = color

    def next_frame(self, pixels, now, state, osc):
        section = STATE.layout.STATIONS[self.station_id]
        pixels[:2, section.left:section.right] = self.color


def get_random_game_button(excluding=None):
    if excluding is None:
        exclude = set()
    elif isinstance(excluding, (list, tuple)):
        exclude = set(excluding)
    else:
        exclude = set([excluding])
    game_buttons = set(GAME_BUTTONS) - exclude
    return np.random.choice(list(game_buttons))


class MultiLevelTutorial(af.CollaborationManager, af.Effect):
    def __init__(self):
        self.station_id = np.random.randint(N_STATIONS)
        players = set(range(N_STATIONS))
        players.remove(self.station_id)
        self.idx = 0
        self.pattern_lengths = (2, 3, 4)
        self.step = SimonSaysTutorial(self.station_id, 2, self.next_step, players, set())

    def compute_state(self, now, state, osc):
        self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        self.step.next_frame(pixels, now, state, osc)

    def next_step(self, winners, losers):
        logger.info('Finished tutorial with %s steps', self.pattern_lengths[self.idx])
        self.idx += 1
        pattern_length = self.pattern_lengths[self.idx]
        self.step = SimonSaysTutorial(
            self.station_id, pattern_length, self.next_step, winners, losers)


# I just realized that this game is basically an annoying state-machine
# but its probably not worth the effort to incorporate a FSM library
# ... I'll just write my own poor variant
class SimonSaysTutorial(af.CollaborationManager, af.Effect):
    def __init__(self, simon_station_id, pattern_length, on_finished, winners, losers):
        self.simon_station_id = simon_station_id
        self.step = SetPattern(simon_station_id, pattern_length, self.pattern_defined)
        self.render = self.step
        self.on_finished = on_finished
        self.winners = winners
        self.losers = losers

    def compute_state(self, now, state, osc):
        if not self.step:
            return
        self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if not self.render:
            return
        self.render.next_frame(pixels, now, state, osc)

    def finished(self, winners, losers):
        self.step = None
        self.render = None
        self.on_finished(winners, losers)

    def pattern_defined(self, pattern):
        self.step = MultiStation(self.winners, pattern, self.finished)
        self.render = self.step


class SetPattern(object):
    """A set of steps that defines a pattern"""
    def __init__(self, station_id, pattern_length, on_finished):
        self.station_id = station_id
        self.pattern_length = pattern_length
        self.on_finished = on_finished
        self.step = TurnOnOnlyMyButtonAndWaitForPress(self, self.station_id)
        self.render = None
        self.pattern = []

    def compute_state(self, now, state, osc):
        self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if self.render:
            self.render.next_frame(pixels, now, state, osc)

    def next_step(self):
        self.render = None
        self.pattern.append(self.step.button)
        if len(self.pattern) < self.pattern_length:
            self.step = TurnOnOnlyMyButtonAndWaitForPress(
                self, self.station_id, last_button=self.step.button)
        elif len(self.pattern) == self.pattern_length:
            def callback():
                self.on_finished(self.pattern)
            # when the pattern length isn't defined, Simon has to hit enter
            # to indicate that she's done
            self.step = TurnOnOnlyMyButtonAndWaitForPress(
                self, self.station_id, button=ENTER_BUTTON, flash=False,
                on_finished=callback
            )
        else:
            raise Exception('We should never get here')


class MultiStation(object):
    # doesn't actually render anything, just passes the work along.
    def __init__(self, stations, pattern, on_finished):
        self.pattern = pattern
        self.followers = [
            PlayAndFollowPattern(s, pattern, self.next_step) for s in stations]
        self.on_finished = on_finished
        self.finished_count = 0
        self.winners = set()
        self.losers = set()

    def compute_state(self, now, state, osc):
        for follower in self.followers:
            follower.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        for follower in self.followers:
            follower.next_frame(pixels, now, state, osc)

    def next_step(self, station_id, correct):
        logger.info('Station %s got %s', station_id, 'right' if correct else 'wrong')
        if correct:
            self.winners.add(station_id)
        else:
            self.losers.add(station_id)
        self.finished_count += 1
        if self.finished_count == len(self.followers):
            self.on_finished(self.winners, self.losers)


class PlayAndFollowPattern(object):
    def __init__(self, station_id, pattern, on_finished):
        self.station_id = station_id
        self.pattern = pattern
        self.on_finished = on_finished
        self.pattern_idx = -1
        self.next_step(correct=True)
        self.render = False

    def compute_state(self, now, state, osc):
        self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if not self.render:
            return
        self.render.next_frame(pixels, now, state, osc)

    def next_step(self, correct):
        logger.debug('Removing the render')
        self.render = None
        if not correct:
            print "You fucked up"
            self.render = ColorStation(self.station_id, WRONG_COLOR)
            self.on_finished(self.station_id, correct=False)
            return
        self.pattern_idx += 1
        if self.pattern_idx >= len(self.pattern):
            logger.debug('Stations %s is finished', self.station_id)
            self.render = ColorStation(self.station_id, RIGHT_COLOR)
            self.on_finished(self.station_id, correct=True)
            return
        self.step = TurnOnMyButtonAndWaitForPressFollower(
            self, self.station_id, self.pattern[self.pattern_idx], flash=False)


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
            self._on_correct_button_press(now)
        other_buttons = pressed_buttons - set([self.button])
        if other_buttons:
            self._on_wrong_button_press(now, other_buttons)

    def _on_correct_button_press(self, now):
        self._turn_off_button()
        if self.flash:
            self.parent.render = Flash(
                self.parent, BUTTON_COLORS[self.button], self.on_finished, now)
        else:
            self.on_finished()

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


SCENES = [
    af.Scene('basic-simon-says', tags=[], collaboration_manager=BasicSimonSays()),
    af.Scene('simon-says-tutorial', tags=[], collaboration_manager=MultiLevelTutorial())
]
