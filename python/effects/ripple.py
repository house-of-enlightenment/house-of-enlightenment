from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from generic_effects import NoOpCollaborationManager
from shared import SolidBackground
from hoe.pixels import Pixels
from hoe.state import STATE

import random
import itertools
import numpy as np

light_blue = (52, 152, 219)
blue = (41, 128, 185)
dark_blue=(0, 81, 134)


class Ripple(Effect):
    def __init__(self, color=dark_blue, start_row=0, end_row=None, start_col=0, end_col=None):
        Effect.__init__(self)
        self.color = color
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))

        # a grid of the row/columns of all 0's
        self.ripple_state = np.zeros((STATE.layout.rows, STATE.layout.columns), np.int)
        self.ripple_state[2, 16] = 100

    def value_to_color(self, value):
        if (value > 0):
            return (30, 30, 30)
        elif (value < 0):
            return (255, 255, 255)
        else:
            return blue

    def next_frame(self, pixels, t, collaboration_state, osc_data):

        inner_pixels = []
        above = []
        below = []
        left = []
        right = []

        # add a ripple
        # if (random.random() < 0.1) :
        #     row = random.randint(0, STATE.layout.rows)
        #     column = random.randint(0, STATE.layout.columns)
        #     print("adding ripple!", row, column)
        #     self.ripple_state[row, column] = 1

        print("HEH", self.ripple_state[2, 16])

        for r, c in itertools.product(range(STATE.layout.rows), range(STATE.layout.columns)):
            if r == 0 or r == STATE.layout.rows - 1:
                continue
            if c == 0 or c == STATE.layout.columns - 1:
                continue
            me = self.ripple_state[r, c]
            above_me = self.ripple_state[r + 1, c]
            below_me = self.ripple_state[r - 1, c]
            left_of_me = self.ripple_state[r, c - 1]
            right_of_me = self.ripple_state[r, c + 1]
            inner_pixels.append(me)
            above.append(above_me)
            below.append(below_me)
            left.append(left_of_me)
            right.append(right_of_me)

            if (r == 2 and c==16):
                print("ME", me)
                print("above_me", above_me)
                print("below_me", below_me)


        self.ripple_state = (self.ripple_state[above] + self.ripple_state[below] + self.ripple_state[left] + self.ripple_state[right]) / 2 - self.ripple_state[inner_pixels]

        # function that will map over a numpy array
        np_value_to_color = np.vectorize(self.value_to_color)

        pixels = np_value_to_color(self.ripple_state)


SCENES = [
    Scene(
        "ripple",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=dark_blue), Ripple()])
]
