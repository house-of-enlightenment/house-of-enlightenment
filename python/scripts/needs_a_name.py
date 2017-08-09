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


MIN_HUE = -20
MAX_HUE = 20

class Breathe(object):
    def __init__(self, layout):
        self.n_colors = 21
        self.n_black = 1
        self.max_hue = 20
        self.min_hue = -20
        self.sources = np.random.randint(0, self.n_colors + self.n_black - 1, len(layout.pixels))
        self.sources[:] = 0

    def start(self, now):
        hue = np.random.randint(0, 255)
        self.color_transitions = [ColorTransition(hue, now) for _ in range(self.n_colors)]

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

STEPS = []

class ColorTransition(su.Transition):
    N_STAGES = 2
    def __init__(self, hue, now):
        # TODO: make hue the target hue and
        #       on transition, pick whether to be complementary or not
        #       and then pick a random hue within 30 of that
        self.reference_hue = hue % 256
        self.set_hue()
        self.stage = 0
        self.idx = len(STEPS)
        self.target_time = now
        STEPS.append(0)
        su.Transition.__init__(self, now)

    def set_hue(self):
        if np.random.rand() < .2:
            hue = (self.reference_hue + 128) % 256
        else:
            hue = self.reference_hue
        offset = np.random.randint(MIN_HUE, MAX_HUE)
        self.hue = hue + offset

    def rnd_pt(self):
        # 119 is just off of half (128) so we make a slow, pretty walk
        # around the color wheel
        if self.stage == 0:
            self.reference_hue = (self.reference_hue + 119) % 256
            self.set_hue()
            pt = (self.hue, 31, np.random.randint(18, 31))
        else:
            pt = (self.hue, 31, np.random.randint(3, 12))
        self.stage = (self.stage + 1) % self.N_STAGES
        return np.array(pt)

    PERIOD = 2
    GAP = 0.025
    def transition_period(self, now):
        self.target_time += self.PERIOD
        rand_time = randrange(-self.PERIOD / 2 + self.GAP, self.PERIOD / 2 - self.GAP)
        period = (self.target_time + rand_time) - now
        assert period > self.GAP, period
        assert period < 2 * (self.PERIOD - self.GAP), period
        return period
        # return 3
        # # if there is no randomness, all of the pixels change hues at the same time
        # # Too much randomness and each pixel will quickly end up a totally different color
        # # in my judgement, 1 / 3 is a good ratio
        # was_max = (STEPS[self.idx] == max(STEPS))
        # STEPS[self.idx] += 1
        # am_min = (STEPS[self.idx] == min(STEPS))
        # print max(STEPS), min(STEPS), self.idx, STEPS[self.idx]
        # wt = 2
        # if was_max:
        #     print 'Run slower'
        #     wt = 3
        # elif am_min:
        #     print 'Run faster'
        #     wt = 1
        # return np.random.rand() * wt + 2

    def update(self, now):
        hue, sat, val = su.Transition.update(self, now)
        hsv = np.array((
            hue,
            color_utils.linear_brightness(sat),
            color_utils.linear_brightness(val)
        ))
        return hsv


def randrange(low, high):
    return np.random.rand() * (high - low) + low


class GoDarkAndSwap(object):
    pass



if __name__ == '__main__':
    sys.exit(main())
