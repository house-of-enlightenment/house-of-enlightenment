from __future__ import division

import json
import math
import random
import sys
import time

import numpy as np

from hoe import animation_framework as af
from hoe import color_transition
from hoe import color_utils
from hoe import distance
from hoe.fountain_models import FountainScene
from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import pixels
from hoe import transitions
from hoe import utils
from hoe.state import STATE


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


# I'm using uint8 overflows intentionally
# so don't need the error warnings
np.seterr(over='ignore')


class Static(af.Effect):
    """Red, green, blue pixels bounce around

    Interesting for maybe 30 seconds.
    """
    def scene_starting(self, now, osc):
        self.switch = 0
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)

    def next_frame(self, pixels, now, state, osc):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .1
        pixels[:] = self.my_pixels

    def _next_frame(self):
        sources = np.random.randint(0, 6, len(self.my_pixels))
        colors = np.array([RED, BLUE, GREEN, BLACK, BLACK, BLACK])
        for i in range(3):
            c = np.choose(sources, colors[:, i])
            self.my_pixels[:, i] = c


class AnalogousColorStatic(af.Effect):
    """A few colors of similar hue bounce around.

    At startup a base hue is picked, colors near it on the color
    wheel are picked and then those bounce around.

    Again, interesting for maybe 30 seconds.
    """
    def scene_starting(self, now, osc):
        hue = np.random.randint(0, 256)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:, 0] = (hue - 25, hue - 15, hue + 15, hue + 25)
        self.switch = 0
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)

    def next_frame(self, pixels, now, state, osc):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .15
        pixels[:] = color_utils.hsv2rgb(self.my_pixels)

    def _next_frame(self):
        sources = np.random.randint(0, 7, len(self.my_pixels))
        colors = np.concatenate((self.colors, [BLACK, BLACK, BLACK]))
        for i in range(3):
            c = np.choose(sources, colors[:, i])
            self.my_pixels[:, i] = c


class RainbowBlink(af.Effect):
    """Glitchy AF"""
    def scene_starting(self, now, osc):
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)
        hue = np.random.randint(0, 256)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:, 0] = (hue - 25, hue - 15, hue + 15, hue + 25)
        self.switch = 0

    def next_frame(self, pixels, now, state, osc):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .15
        pixels[:] = color_utils.hsv2rgb(self.my_pixels)

    def _next_frame(self):
        self.colors[:, 0] = self.colors[:, 0] + 119
        self.sources = np.random.randint(0, 7, len(self.my_pixels))
        colors = np.concatenate((self.colors, [BLACK, BLACK, BLACK]))
        for i in range(3):
            c = np.choose(self.sources, colors[:, i])
            self.my_pixels[:, i] = c


class Breathe(af.Effect):
    """An array of randomly places ColorTransitions

    Creates a pleasant, subdued effect.
    """
    def __init__(self, layout, n_colors):
        self.n_colors = n_colors
        self.layout = layout
        # randomly place each color into the pixel array
        self.sources = np.random.randint(0, self.n_colors, len(layout.pixels))

    def scene_starting(self, now, osc):
        hue = np.random.randint(0, 256)
        self.color_transitions = [
            color_transition.ColorTransition(hue).start(now)
            for _ in range(self.n_colors)]

    def next_frame(self, pixels, now, state, osc):
        pixels[:] = self.colors(now)[self.sources]

    def colors(self, now):
        return color_utils.hsv2rgb([ct.update(now) for ct in self.color_transitions])


class BreatheDown(af.Effect):
    """An array of randomly places ColorTransitions

    Creates a pleasant, subdued effect that slowly drifts down the HoE
    """
    def __init__(self, layout, n_colors):
        self.n_colors = n_colors
        self.layout = layout
        pixels_per_second = transitions.ConstantTransition(8)
        self.speed = distance.VaryingPixelsPerFrame(pixels_per_second) #
        # randomly place each color into the pixel array
        self.shade_factor = self._init_shade_factor()
        self.sources = np.random.randint(0, self.n_colors, (layout.rows, layout.columns))

    def _init_shade_factor(self):
        fade_out = np.stack([
            utils.randrange(.95, 1.0, self.layout.columns)**(40-i) for i in range(40)
        ])
        print fade_out.shape
        return (utils.randrange(.4, 1.0, (40, self.layout.columns)) * fade_out)

    def scene_starting(self, now, osc):
        self.speed.start(now)
        hue = np.random.randint(0, 256)
        self.color_transitions = [
            color_transition.ColorTransition(hue).start(now)
            for _ in range(self.n_colors)]

    def next_frame(self, pixels, now, state, osc):
        down = self.speed.update(now)
        if down > 0:
            self.sources = np.concatenate((
                self.sources[down:, :],
                np.random.randint(0, self.n_colors, (down, self.layout.columns))))
        pixels[:, :] = self.colors(now)[self.sources]
        self.darken(pixels, down)

    def darken(self, pixels, down):
        if down > 0:
            # some columns get darker than others
            col_fade = (utils.randrange(.95, 1.0, self.layout.columns)**down)
            # get darker as we move down.  .95**40 = .12; .97**40=.3
            self.shade_factor = np.concatenate((
                self.shade_factor[down:, :] * col_fade,
                utils.randrange(.4, 1.0, (down, self.layout.columns))))
        pixels[:40,:] = pixels[:40, :] * np.dstack([self.shade_factor] * 3)

    def colors(self, now):
        return color_utils.hsv2rgb([ct.update(now) for ct in self.color_transitions])


SCENES = [
    FountainScene(
        'rgb-static',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[Static()]
    ),
    FountainScene(
        'analogous-color-static',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[AnalogousColorStatic()]
    ),
    FountainScene(
        'rainbow-blink',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[RainbowBlink()]
    ),
    FountainScene(
        'color-breathe-8',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[Breathe(STATE.layout, 8)]
    ),
    FountainScene(
        'color-breathe-32',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[Breathe(STATE.layout, 32)]
    ),
    FountainScene(
        'color-breathe-down-32',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[BreatheDown(STATE.layout, 32)]
    ),

]
