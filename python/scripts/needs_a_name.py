"""Draw and rotate a color wheel on the two discs"""
from __future__ import division
import json
import math
import Queue
import random
import sys
import time

import numpy as np

from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import color_utils
from hoe import pixels
from hoe.state import STATE

# TODO: fix this. Move the stream_up code somewhere shared
import stream_up as su

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


def main():
    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    STATE.layout = hoe_layout
    background = Breathe(hoe_layout)
    render = su.Render(client, None, hoe_layout, [background])
    render.run_forever()


class Static(object):
    def start(self, now):
        self.switch = 0
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)

    def next_frame(self, now, pixels):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .1
        pixels[:] = self.my_pixels

    def _next_frame(self):
        sources = np.random.randint(0, 6, len(self.my_pixels))
        colors = np.array([
            RED, BLUE, GREEN,
            BLACK, BLACK, BLACK
        ])
        for i in range(3):
            c = np.choose(sources, colors[:,i])
            self.my_pixels[:,i] = c


class AnalogousColorStatic(object):
    def start(self, now):
        hue = np.random.randint(0, 255)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:,0] = (hue - 25, hue - 15, hue + 15, hue + 25)
        self.switch = 0
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)

    def next_frame(self, now, pixels):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .15
        pixels[:] = color_utils.hsv2rgb(self.my_pixels)

    def _next_frame(self):
        sources = np.random.randint(0, 7, len(self.my_pixels))
        colors = np.concatenate((self.colors, [BLACK, BLACK, BLACK]))
        for i in range(3):
            c = np.choose(sources, colors[:,i])
            self.my_pixels[:,i] = c


class RainbowBlink(object):
    def start(self, now):
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)
        hue = np.random.randint(0, 255)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:,0] = (hue - 25, hue - 15, hue + 15, hue + 25)
        self.switch = 0

    def next_frame(self, now, pixels):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .15
        pixels[:] = color_utils.hsv2rgb(self.my_pixels)

    def _next_frame(self):
        self.colors[:,0] = self.colors[:,0] + 119
        self.sources = np.random.randint(0, 7, len(self.my_pixels))
        colors = np.concatenate((self.colors, [BLACK, BLACK, BLACK]))
        for i in range(3):
            c = np.choose(self.sources, colors[:,i])
            self.my_pixels[:,i] = c


class Breathe(object):
    def __init__(self, layout):
        self.n_colors = 41
        self.n_black = 5
        self.max_hue = 20
        self.min_hue = -20
        self.sources = np.random.randint(0, self.n_colors + self.n_black - 1, len(layout.pixels))

    def start(self, now):
        hue = np.random.randint(0, 255)
        self.color_transitions = [
            ColorTransition(hue + step, now)
            for step in np.linspace(self.min_hue, self.max_hue, self.n_colors, dtype=int)
        ]

    def swap(self):
        # this method of swapping looked
        # like crap
        # pick a random point
        r = np.random.randint(0, STATE.layout.rows - 1)
        c = np.random.randint(0, STATE.layout.columns - 1)
        pt = np.array((r, c))
        a = STATE.layout.grid[pt]
        # and then a random neighbor
        neighbor = pt + np.random.randint(-1, 1, 2)
        b = STATE.layout.grid[neighbor]
        self.sources[a], self.sources[b] = self.sources[b], self.sources[a]

    def next_frame(self, now, pixels):
        #self.swap()
        colors = np.concatenate((self.colors(now), [BLACK] * self.n_black))
        pixels.pixels[:] = colors[self.sources]

    def colors(self, now):
        return color_utils.hsv2rgb([ct.update(now) for ct in self.color_transitions])


class ColorTransition(su.Transition):
    def __init__(self, hue, now):
        self.hue = hue % 256
        self.full = False
        su.Transition.__init__(self, now)

    def rnd_pt(self):
        # 119 is just off of half (128) so we make a slow, pretty walk
        # around the color wheel
        self.hue += np.random.randint(119, 137)
        if self.full:
            pt = (self.hue, np.random.randint(24, 31), np.random.randint(24, 31))
        else:
            pt = (self.hue, np.random.randint(3, 28), np.random.randint(3, 28))
        self.full = not self.full
        return np.array(pt)

    def transition_period(self):
        # if there is no randomness, all of the pixels change hues at the same time
        # Too much randomness and each pixel will quickly end up a totally different color
        # in my judgement, 1 / 3 is a good ratio
        return np.random.rand() * 1 + 3

    def update(self, now):
        hue, sat, val = su.Transition.update(self, now)
        hsv = np.array((
            hue,
            color_utils.linear_brightness(sat),
            color_utils.linear_brightness(val)
        ))
        return hsv


class GoDarkAndSwap(object):
    pass



if __name__ == '__main__':
    sys.exit(main())
