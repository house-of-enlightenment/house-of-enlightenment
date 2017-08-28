import random
import itertools

import numpy as np

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
import hoe.fountain_models as fm
from hoe import color_utils
from hoe.state import STATE

from generic_effects import NoOpCollaborationManager
from shared import SolidBackground

light_blue = (52, 152, 219)
blue = (41, 128, 185)
dark_blue = (0, 81, 134)


# https://web.archive.org/web/20080731165022/http://freespace.virgin.net:80/hugo.elias/graphics/x_water.htm
class Ripple(Effect):
    def __init__(self,
                 color=blue,
                 dark_color=(0, 0, 0),
                 light_color=(255, 255, 255),
                 start_row=0,
                 end_row=None,
                 start_col=0,
                 end_col=None):
        Effect.__init__(self)
        self.color = color
        self.light_color = light_color
        self.dark_color = dark_color
        # a grid of the row/columns of all 0's
        self.previous_ripple_state = np.zeros((STATE.layout.rows, STATE.layout.columns), int)
        self.ripple_state = np.zeros((STATE.layout.rows, STATE.layout.columns), int)
        # self.ripple_state[2, 16] = 50
        self.damping = 0.8
        self.frameCount = 0

    def value_to_color(self, value):

        if value > 0:
            return self.dark_color
        elif value < 0:
            return self.light_color
        else:
            return self.color

    def start_ripple(self):
        idx = tuple(np.random.randint(0, s) for s in self.ripple_state.shape)

        self.ripple_state[idx] = np.random.randint(0, 500)

    def next_frame(self, pixels, t, collaboration_state, osc_data):

        # render every 2 frames so the ripples are slower
        self.frameCount += 1
        if (self.frameCount % 2 == 0):
            pixels[:, :] = self.get_pixels()
            return

        # only generate a ripple every couple frames
        if (random.random() < 0.12):
            self.start_ripple()

        # calculate a pixel values based on it's neighbors
        self.ripple_state[1:-1, 1:-1] = (
            self.previous_ripple_state[:-2, 1:-1] + self.previous_ripple_state[2:, 1:-1] +
            self.previous_ripple_state[1:-1, :-2] + self.previous_ripple_state[1:-1, 2:]
        ) * 0.5 - self.ripple_state[1:-1, 1:-1]

        # damping
        # numpy doesn't like multiplying ints and floats so tell it to be unsafe
        np.multiply(self.ripple_state, self.damping, out=self.ripple_state, casting='unsafe')

        pixels[:, :] = self.get_pixels()
        self.swap_buffers()

    def get_pixels(self):
        shape = (STATE.layout.rows * STATE.layout.columns, 3)
        np_value_to_color = np.vectorize(self.value_to_color)
        # print '---'
        # print 'max', np.max(self.ripple_state)
        # print 'min', np.min(self.ripple_state)
        v = np.array(np_value_to_color(self.ripple_state))
        # moveaxis is because v starts off as a (3, 216, 66) array
        # and we actually want (216, 66, 3)
        v = np.moveaxis(v, 0, 2)
        return v

    def swap_buffers(self):
        self.previous_ripple_state, self.ripple_state = \
            self.ripple_state, self.previous_ripple_state


SCENES = [
    # It would be nicer to have the ripple OVER the launched effects, but c'est la vie.
    fm.FountainScene(
        "ripple",
        tags=[Scene.TAG_EXAMPLE, Scene.TAG_PRODUCTION],
        background_effects=[
            Ripple()
            # Ripple(
            #     color=blue,
            #     light_color=(200, 138, 255),
            #     dark_color=(20, 1, 85))
        ])
]
