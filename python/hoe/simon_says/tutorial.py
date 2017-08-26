from shared import *
from buttons import *
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
# Repeat this, but for a sequence of 3 buttons and a sequence of 4 buttons


class MultiLevelTutorial(af.CollaborationManager, af.Effect):
    def __init__(self, on_finished):
        self.station_id = np.random.randint(N_STATIONS)
        players = self.get_players()
        self.idx = 0
        self.pattern_lengths = (2, 3, 4)
        self.step = SimonSaysTutorial(self.station_id, 2, self.next_step, players, set())
        self.on_finished = on_finished

    def get_players(self):
        players = set(range(N_STATIONS))
        players.remove(self.station_id)
        return players

    def compute_state(self, now, state, osc):
        return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        self.step.next_frame(pixels, now, state, osc)

    def next_step(self, winners, losers):
        logger.info('Finished tutorial with %s steps', self.pattern_lengths[self.idx])
        self.idx += 1
        if self.idx >= len(self.pattern_lengths):
            logger.info('Finished with the tutorial')
            self.on_finished()
        else:
            pattern_length = self.pattern_lengths[self.idx]
            if not winners:
                winner = self.get_players()
                losers = set()
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


class SetPattern(object):
    """A set of steps that defines a pattern

    In this case, the pattern is picked for the user and they just
    have to go along.
    """
    def __init__(self, station_id, pattern_length, on_finished):
        self.station_id = station_id
        self.pattern_length = pattern_length
        self.on_finished = on_finished
        self.step = TurnOnOnlyMyButtonAndWaitForPress(self, self.station_id)
        self.render = None
        self.pattern = []

    def compute_state(self, now, state, osc):
        return self.step.compute_state(now, state, osc)

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
    def __init__(self, winners, losers, pattern, on_finished):
        self.pattern = pattern
        self.followers = [PlayAndFollowPattern(s, pattern, self.next_step) for s in winners]
        self.out = [ColorStation(s, WRONG_COLOR) for s in losers]
        self.on_finished = on_finished
        self.finished_count = 0
        self.winners = set()
        self.losers = set()

    def start(self, now):
        for follower in self.followers:
            follower.start(now)

    def compute_state(self, now, state, osc):
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
        self.station_id = station_id
        self.pattern = pattern
        self.on_finished = on_finished
        self.pattern_idx = -1
        self.finished = False
        self.next_step(correct=True)
        self.render = False
        self.deadline = None

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
            self.on_finished(self.station_id, correct=False)
        else:
            return self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        if not self.render:
            return
        self.render.next_frame(pixels, now, state, osc)

    def next_step(self, correct):
        assert self.finished == False
        self.render = None
        if not correct:
            self.finished = True
            self.render = ColorStation(self.station_id, WRONG_COLOR)
            self.on_finished(self.station_id, correct=False)
            return
        self.pattern_idx += 1
        if self.pattern_idx >= len(self.pattern):
            self.finished = True
            logger.debug('Stations %s is finished', self.station_id)
            self.render = ColorStation(self.station_id, RIGHT_COLOR)
            self.on_finished(self.station_id, correct=True)
            return
        self.step = TurnOnMyButtonAndWaitForPressFollower(
            self, self.station_id, self.pattern[self.pattern_idx], flash=False)


# #
# # this turned into an ugly mess quick.
# #
# class TurnOnOnlyMyButtonAndWaitForPress(object):
#     def __init__(
#             self, parent, station_id, button=None, last_button=None, flash=True, on_finished=None):
#         self.parent = parent
#         self.station_id = station_id
#         self.button = self.get_button(button, last_button)
#         self.set_buttons = False
#         self.flash = flash
#         self.on_finished = on_finished or self.parent.next_step

#     def get_button(self, button, last_button):
#         return button if button is not None else get_random_game_button(excluding=last_button)

#     def compute_state(self, now, state, osc):
#         if not self.set_buttons:
#             self._only_turn_on_my_button()
#             self.set_buttons = True
#         pressed_buttons = osc.buttons[self.station_id]
#         if self.button in pressed_buttons:
#             self._on_correct_button_press(now)
#         other_buttons = pressed_buttons - set([self.button])
#         if other_buttons:
#             self._on_wrong_button_press(now, other_buttons)

#     def _on_correct_button_press(self, now):
#         self._turn_off_button()
#         if self.flash:
#             self.parent.render = Flash(
#                 self.parent, BUTTON_COLORS[self.button], self.on_finished, now)
#         else:
#             self.on_finished()

#     def _on_wrong_button_press(self, now, wrong_buttons):
#         pass

#     def _only_turn_on_my_button(self):
#         logger.debug('Setting buttons')
#         for i, s in enumerate(STATE.stations):
#             s.set_button_values([0, 0, 0, 0, 0])
#             if i == self.station_id:
#                 s.buttons[self.button] = 1

#     def _turn_off_button(self):
#         STATE.stations[self.station_id].buttons[self.button] = 0


# class TurnOnMyButtonAndWaitForPress(TurnOnOnlyMyButtonAndWaitForPress):
#     def _only_turn_on_my_button(self):
#         logger.debug('Setting buttons for my section (%s - %s)', self.station_id, self.button)
#         station = STATE.stations[self.station_id]
#         station.set_button_values([0, 0, 0, 0, 0])
#         station.buttons[self.button] = 1


# class TurnOnMyButtonAndWaitForPressFollower(TurnOnMyButtonAndWaitForPress):
#     def _on_correct_button_press(self, now):
#         def callback():
#             self.parent.next_step(correct=True)
#         self._turn_off_button()
#         print 'Parent:', self.parent
#         self.parent.render = FlashStation(
#             self.parent, self.station_id, RIGHT_COLOR, callback, now)

#     def _on_wrong_button_press(self, now, wrong_buttons):
#         def callback():
#             self.parent.next_step(correct=False)
#         self._turn_off_button()
#         self.parent.render = FlashStation(
#             self.parent, self.station_id, WRONG_COLOR, callback, now)
