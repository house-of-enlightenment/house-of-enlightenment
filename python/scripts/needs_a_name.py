"""Draw and rotate a color wheel on the two discs"""
from __future__ import division

import argparse
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

np.seterr(over='ignore')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('n', type=int)
    args = parser.parse_args()
    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    STATE.layout = hoe_layout
    STATE.fps = 30

    background = Breathe(hoe_layout, args.n)
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
        colors = np.array([RED, BLUE, GREEN, BLACK, BLACK, BLACK])
        for i in range(3):
            c = np.choose(sources, colors[:, i])
            self.my_pixels[:, i] = c


class AnalogousColorStatic(object):
    def start(self, now):
        hue = np.random.randint(0, 256)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:, 0] = (hue - 25, hue - 15, hue + 15, hue + 25)
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
            c = np.choose(sources, colors[:, i])
            self.my_pixels[:, i] = c


class RainbowBlink(object):
    def start(self, now):
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)
        hue = np.random.randint(0, 256)
        self.colors = np.full((4, 3), 255, np.uint8)
        self.colors[:, 0] = (hue - 25, hue - 15, hue + 15, hue + 25)
        self.switch = 0

    def next_frame(self, now, pixels):
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


MIN_HUE = -15
MAX_HUE = 15


class Breathe(object):
    def __init__(self, layout, n_colors):
        self.n_colors = n_colors
        self.layout = layout
        # randomly place each color into the pixel array
        self.sources = np.random.randint(0, self.n_colors , len(layout.pixels))

    def start(self, now):
        self.count = 0
        hue = np.random.randint(0, 256)
        self.color_transitions = [ColorTransition(hue, now, i) for i in range(self.n_colors)]

    def swap(self):
        # this method of swapping looked like crap
        r = np.random.randint(0, STATE.layout.rows)
        c = np.random.randint(0, STATE.layout.columns)
        pt = np.array((r, c))
        a = STATE.layout.grid[pt]
        # and then a random neighbor
        neighbor = pt + np.random.randint(-1, 2, 2)
        b = STATE.layout.grid[neighbor]
        self.sources[a], self.sources[b] = self.sources[b], self.sources[a]

    def next_frame(self, now, pixels):
        # rotation does not look good
        # if self.count == 0:
        #     self.rotate()
        # self.count = (self.count + 1) % 3
        pixels[:] = self.colors(now)[self.sources]

    def rotate(self):
        part_a = self.layout.grid[:, 1:]
        part_b = self.layout.grid[:, :1]
        before_idx = self.layout.grid[:,:]
        after_idx = np.concatenate((part_a, part_b), axis=1)
        self.sources[after_idx] = self.sources[before_idx]

    def colors(self, now):
        return color_utils.hsv2rgb([ct.update(now) for ct in self.color_transitions])


class ColorTransition(su.Transition):
    N_STAGES = 4
    PERIOD = 2
    GAP = 0.025

    def __init__(self, hue, now, idx):
        # using uint8 so that we don't have to take mod all of the time
        self.reference_hue = np.uint8(hue)
        self.switched_reference_hue = False
        self.set_hue()
        self.stage = -1
        self.target_time = now
        self.value = 0
        self.idx = idx
        self.switch_stage = np.random.randint(0, self.N_STAGES)
        self.switch_ref_hue_on_next_reset = False
        su.Transition.__init__(self, now)

    def set_hue(self):
        if np.random.rand() < .2:
            # 30% chance of picking the complementary color
            hue = self.reference_hue + np.uint8(128)
        else:
            hue = self.reference_hue
        offset = np.random.random_integers(MIN_HUE, MAX_HUE)
        self.hue = np.uint8(hue + offset)

    def update_reference_hue(self):
        # 119 is just off of half (128) so we make a slow, pretty walk
        # around the color wheel
        self.reference_hue = self.reference_hue + np.uint8(119)
        self.switched_reference_hue = True

    def _reset(self, now):
        # handle actions from the end of last stage
        if self.switch_ref_hue_on_next_reset:
            # print 'Updating hue', self.stage, self.idx
            assert self.end < 12
            self.update_reference_hue()
            self.set_hue()
            self.switch_ref_hue_on_next_reset = False

        # now increment counter for this stage
        self.stage = (self.stage + 1) % self.N_STAGES
        # print 'stage:', self.stage, self.idx
        if self.stage == 0:
            self.switch_stage = np.random.randint(0, self.N_STAGES)
            self.switched_reference_hue = False
        super(ColorTransition, self)._reset(now)

    def rnd_pt(self):
        if self.switched_reference_hue:
            return weighted_bright()
        else:
            if self.switch():
                # print 'Need update', self.stage, self.idx
                self.switch_ref_hue_on_next_reset = True
                return dark()
            else:
                return weighted_bright()

    def switch(self):
        return self.stage == self.switch_stage

    def transition_period(self, now):
        return 1 + randrange(-.2, .2)

    def update(self, now):
        val = su.Transition.update(self, now)
        print(val)
        val = int(val / 31.0 * 255)
        # In playing around, full saturation looked the best
        sat = 255
        hsv = np.array((
            self.hue,
            sat,
            color_utils._GAMMA_CORRECTION[val]
        ))
        return hsv


def randrange(low, high):
    return np.random.rand() * (high - low) + low


def bright():
    return np.random.randint(18, 32)


def twinkle():
    return np.random.randint(12, 32)


def dark():
    return 11
    return np.random.randint(0, 12)


# def weighted_bright():
#     """Returns a medium to high bright value, with preference towards bright"""
#     return np.random.choice(
#         [12, 13, 14, 15, 16] +
#         [17, 18, 19, 20, 21] * 2 +
#         [22, 23, 24, 25, 26] * 3 +
#         [27, 28, 29, 30, 31] * 4
#     )


def weighted_bright():
    """Returns a medium to high bright value, with preference towards bright"""
    return np.random.choice(
        [17, 18, 19, 20, 21] * 1 +
        [22, 23, 24, 25, 26] * 2 +
        [27, 28, 29, 30, 31] * 3
    )



if __name__ == '__main__':
    sys.exit(main())
