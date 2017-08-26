import functools
import logging

import numpy as np

from hoe import animation_framework as af
from hoe import stations
from hoe.state import STATE


logger = logging.getLogger(__name__)


N_STATIONS = 6
N_BUTTONS = 5
BUTTON_COLORS = stations.BUTTON_COLORS

# want to use GREEN / RED, but don't want to match
# the colors that flash when a pattern is being set
RIGHT_COLOR = (34, 139, 34) # forest green
WRONG_COLOR = (176, 28, 46) # stop sign red

ENTER_BUTTON = 2
GAME_BUTTONS = [0, 1, 3, 4]
ALL_BUTTONS = [0, 1, 2, 3, 4]


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


def exclude(base, excluding):
    if isinstance(excluding, (list, tuple)):
        exclude = set(excluding)
    else:
        exclude = set([excluding])
    return set(base)  - exclude
