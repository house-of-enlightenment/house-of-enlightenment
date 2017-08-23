import random
import itertools

import numpy as np

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from hoe import color_utils
from hoe.state import STATE

from generic_effects import NoOpCollaborationManager
from shared import SolidBackground


light_blue = (52, 152, 219)
blue = (41, 128, 185)
dark_blue=(0, 81, 134)


class Ripple(Effect):
    def __init__(self, color=dark_blue, start_row=0, end_row=None, start_col=0, end_col=None):
        Effect.__init__(self)
        self.color = color
        # a grid of the row/columns of all 0's
        self.previous_ripple_state = np.zeros((STATE.layout.rows, STATE.layout.columns), int)
        self.ripple_state = np.zeros((STATE.layout.rows, STATE.layout.columns), int)
        self.ripple_state[2, 16] = 50
        self.damping = .8

    def value_to_color(self, value):
        if value > 0:
            return (30, 30, 30)
        elif value < 0:
            return (255, 255, 255)
        else:
            return blue

    def start_ripple(self):
        idx = tuple(np.random.randint(0, s) for s in self.ripple_state.shape)
        self.ripple_state[idx] = np.random.randint(-50, 50)

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.start_ripple()
        self.ripple_state[1:-1, 1:-1] = (
            self.previous_ripple_state[:-2, 1:-1] +
            self.previous_ripple_state[2:, 1:-1] +
            self.previous_ripple_state[1:-1, :-2] +
            self.previous_ripple_state[1:-1, 2:]) / 4 - self.ripple_state[1:-1, 1:-1]
        # numpy doesn't like multiplying ints and floats so tell it to be unsafe
        np.multiply(self.ripple_state, self.damping, out=self.ripple_state, casting='unsafe')
        pixels[:] = self.get_pixels()
        self.swap_buffers()

    def get_pixels(self):
        shape = (STATE.layout.rows * STATE.layout.columns, 3)
        np_value_to_color = np.vectorize(self.value_to_color)
        print '---'
        print 'max', np.max(self.ripple_state)
        print 'min', np.min(self.ripple_state)
        v = np.array(np_value_to_color(self.ripple_state))
        v = np.moveaxis(v, 0, 2)
        return v.reshape(shape)

    def swap_buffers(self):
        self.previous_ripple_state, self.ripple_state = \
            self.ripple_state, self.previous_ripple_state


SCENES = [
    Scene(
        "ripple",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=dark_blue), Ripple()])
]
