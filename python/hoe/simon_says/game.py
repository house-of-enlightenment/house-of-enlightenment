"""A copy-cat game where one player defines a sequence and the other players
need to copy it. If you miss you're out and we continue playing until only
one player is left.
"""
# This code is largely a copy of the tutorial code.
# There is so much overlap, but just enough differences
# that copy/paste and edit seems to be the way to go.
import logging

import numpy as np

from shared import *
from buttons import *


MIN_PATTERN_LENGTH = 2
MAX_PATTERN_LENGTH = 10


logger = logging.getLogger(__name__)


class SimonSaysGame(af.CollaborationManager, af.Effect):
    def __init__(self, on_finished):
        self.station_id = np.random.randint(N_STATIONS)
        players = set(range(N_STATIONS))
        players.remove(self.station_id)
        self.step = SimonSaysRound(self.station_id, self.next_step, players, set())
        self.on_finished = on_finished

    def compute_state(self, now, state, osc):
        return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        self.step.next_frame(pixels, now, state, osc)

    def next_step(self, winners, losers):
        logger.info('Finished round')
        if len(winners) == 1:
            winner = winners.pop()
            logger.info('Congats! %s won', winner)
            self.on_finished(winner)
        elif len(winners) == 0:
            logger.info('That sucks. Nobody won')
            self.on_finished(None)
        else:
            self.step = SimonSaysRound(self.station_id, self.next_step, winners, losers)


class SimonSaysRound(af.CollaborationManager, af.Effect):
    def __init__(self, simon_station_id, on_finished, winners, losers):
        self.simon_station_id = simon_station_id
        self.step = SetPattern(simon_station_id, self.pattern_defined)
        self.render = self.step
        self.on_finished = on_finished
        self.winners = winners
        self.losers = losers
        self.now = None

    def compute_state(self, now, state, osc):
        self.now = now
        if not self.step:
            return
        return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if not self.render:
            return
        self.render.next_frame(pixels, now, state, osc)

    def finished(self, winners, losers):
        self.step = None
        self.render = None
        self.on_finished(winners, losers)

    def pattern_defined(self, pattern):
        self.step = MultiStation(self.winners, self.losers, pattern, self.finished)
        self.render = self.step
        self.step.start(self.now)


class  NoopHandler(object):
    def _on_correct_button_press(self, now, button):
        pass

    def _on_wrong_button_press(self, now, other_buttons):
        pass



class SetPattern(object):
    """A set of steps that defines a pattern

    In this case, the pattern is picked for the user and they just
    have to go along.
    """
    def __init__(self, station_id, on_finished):
        self.station_id = station_id
        self.on_finished = on_finished
        self.step = TurnOnButtonsAndWaitForPress(self, self.station_id, GAME_BUTTONS)
        self.ignore = [
            TurnOnButtonsAndWaitForPress(self, s, [])
            for s in range(N_STATIONS) if s != station_id]
        self.render = None
        self.pattern = []

    def compute_state(self, now, state, osc):
        for ign in self.ignore:
            ign.compute_state(now, state, osc)
        return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if self.render:
            self.render.next_frame(pixels, now, state, osc)

    def _turn_off_button(self, button):
        STATE.stations[self.station_id].buttons[button] = 0

    def _on_correct_button_press(self, now, button):
        self._turn_off_button(button)
        if button == ENTER_BUTTON:
            STATE.stations[self.station_id].set_button_values([0, 0, 0, 0, 0])
            self.on_finished(self.pattern)
        else:
            def callback():
                self.next_step(button)
            self.render = Flash(self, BUTTON_COLORS[button], callback, now)

    def _on_wrong_button_press(self, now, other_buttons):
        # I don't care about these presses
        pass

    def next_step(self, last_button):
        self.render = None
        self.pattern.append(last_button)
        if len(self.pattern) < MIN_PATTERN_LENGTH:
            buttons = GAME_BUTTONS
        elif len(self.pattern) >= MAX_PATTERN_LENGTH:
            buttons = [ENTER_BUTTON]
        else:
            buttons = ALL_BUTTONS
        valid_buttons = exclude(buttons, last_button)
        self.step = TurnOnButtonsAndWaitForPress(self, self.station_id, valid_buttons)


class MultiStation(object):
    # doesn't actually render anything, just passes the work along.
    def __init__(self, winners, losers, pattern, on_finished):
        self.pattern = pattern
        self.followers = [PlayAndFollowPattern(s, pattern, self.next_step) for s in winners]
        self.out = [ColorStation(s, WRONG_COLOR) for s in losers]
        self.on_finished = on_finished
        self.finished_count = 0
        self.winners = set()
        self.losers = set()
        self.started = False

    def start(self, now):
        self.started = True
        for follower in self.followers:
            follower.start(now)

    def compute_state(self, now, state, osc):
        assert self.started
        points = {}
        for follower in self.followers:
            pt = follower.compute_state(now, state, osc)
            if pt:
                points.update(pt)
        return points

    def next_frame(self, pixels, now, state, osc):
        for follower in self.followers:
            follower.next_frame(pixels, now, state, osc)
        for out in self.out:
            out.next_frame(pixels, now, state, osc)

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
        print pattern
        self.station_id = station_id
        self.pattern = pattern
        self.on_finished = on_finished
        self.pattern_idx = 0
        self.finished = False
        self.render = False
        self.deadline = None
        self.setup_next_button()

    def start(self, now):
        self.deadline = now + len(self.pattern) * 10

    def compute_state(self, now, state, osc):
        if self.finished:
            return
        if now >= self.deadline:
            self.finished = True
            logger.debug('Station %s failed because they took too long', self.station_id)
            # flashing the color is dumb here; we move onto the next
            # step and lose the color
            STATE.stations[self.station_id].set_button_values([0, 0, 0, 0, 0])
            self.on_finished(self.station_id, correct=False)
        else:
            return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if not self.render:
            return
        self.render.next_frame(pixels, now, state, osc)

    def _turn_off_button(self, button):
        STATE.stations[self.station_id].buttons[button] = 0

    def _on_correct_button_press(self, now, button):
        self._turn_off_button(button)
        self.next_step(now, True)
        logger.info('Station %s got a point', self.station_id)
        return {self.station_id: 1}

    def _on_wrong_button_press(self, now, other_buttons):
        self.finished = True
        self.render = ColorStation(self.station_id, WRONG_COLOR)
        STATE.stations[self.station_id].set_button_values([0, 0, 0, 0, 0])
        self.on_finished(self.station_id, correct=False)

    def next_step(self, now, correct):
        assert self.finished == False
        self.pattern_idx += 1
        if self.pattern_idx >= len(self.pattern):
            self.finished = True
            logger.debug('Stations %s is finished', self.station_id)
            self.render = ColorStation(self.station_id, RIGHT_COLOR)
            STATE.stations[self.station_id].set_button_values([0, 0, 0, 0, 0])
            self.on_finished(self.station_id, correct=True)
            return
        self.render = FlashStation(self, self.station_id, RIGHT_COLOR, self.setup_next_button, now)

    def setup_next_button(self):
        # callbacks from a render have to do this
        self.render = None
        right_button = self.pattern[self.pattern_idx]
        print 'the right button is:', right_button
        self.step = TurnOnButtonsAndWaitForPress(
            self, self.station_id, GAME_BUTTONS, [right_button])
