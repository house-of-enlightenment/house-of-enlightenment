import functools
import logging


import numpy as np

from hoe import animation_framework as af
from hoe import stations
from hoe.state import STATE
from hoe.simon_says import tutorial
from hoe.simon_says import game


logger = logging.getLogger(__name__)


N_STATIONS = 6
N_BUTTONS = 5
BUTTON_COLORS = stations.BUTTON_COLORS


# want to use GREEN / RED, but don't want to match
# the colors that flash when a pattern is being set
RIGHT_COLOR = (34, 139, 34) # forest green
WRONG_COLOR = (176, 28, 46) # stop sign red




class SimonSays(af.Effect, af.CollaborationManager):
    def __init__(self):
        self.step = MultiLevelTutorial(on_finished=self.start_game)

    def start_game(self):
        self.step = BasicSimonSays()

    def compute_state(self, now, state, osc):
        self.step.compute_state(now, state, osc)

    def next_frame(self, pixels, now, state, osc):
        self.step.next_frame(pixels, now, state, osc)


def echo(*args):
    print args


SCENES = [
#    af.Scene('basic-simon-says', tags=[], collaboration_manager=BasicSimonSays()),
#    af.Scene('simon-says-tutorial', tags=[], collaboration_manager=MultiLevelTutorial())
    af.Scene('simon-says', tags=[], collaboration_manager=game.SimonSaysGame(echo))
]
