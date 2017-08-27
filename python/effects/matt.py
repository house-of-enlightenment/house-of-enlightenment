from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.collaboration import CollaborationManager
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from hoe.fountain_models import FountainScene
from random import choice
from random import randint
from random import getrandbits
from itertools import product
from math import ceil
from shared import SolidBackground
from generic_effects import NoOpCollaborationManager
from generic_effects import FrameRotator
from generic_effects import FunctionFrameRotator
import examples
import numpy as np
import debugging_effects
import hoe.osc_utils
from random import randint


class Noise(Effect):
    """Always return a singular color. Can be bound top/bottom and
    left-right (wrap-around not supported yet)"""

    def __init__(self, color=(255, 0, 255), start_col=0, end_col=None, start_row=2, end_row=None):
        Effect.__init__(self)
        self.color = color
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))
        end_row = end_row or STATE.layout.rows
        end_col = end_col or STATE.layout.columns
        self.shape = (end_row-start_row, end_col-start_col, 3)
        self.range = 10
        self.min = 0
        self.i = 0
        print "Created with color", self.color

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        # print pixels
        pixels[self.slice] = np.random.random_integers(low=self.min, high=self.range, size=self.shape)
        self.i += 1
        if self.i % 2 == 0:
            self.min += 1
            self.range += 10
        # pixels[0] = (randint(0, 255),randint(0, 255),randint(0, 255))
        # pixels[self.slice] =(randint(0, 255),randint(0, 255),randint(0, 255))


SCENES = [
    FountainScene("smash", tags=[Scene.TAG_WIP], background_effects=[Noise()]),
]
