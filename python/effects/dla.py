"""Diffusion Limited Aggregation

Inspired by:
http://paulbourke.net/fractals/dla/
https://codepen.io/DonKarlssonSan/full/BopXpq

https://github.com/hemmer/pyDLA/blob/numpyFast/dla.py
"""
import time

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import color_utils
import hoe.fountain_models as fm
from hoe import pixels
from hoe.state import STATE
from hoe import translations as t

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)


class Dla(af.Effect):
    def __init__(self):
        self.set_points()
        self.max_row = 0
        self.location = self.get_starting_location()

    def set_points(self):
        self.hits = np.zeros((STATE.layout.rows, STATE.layout.columns), int)
        self.my_pixels = pixels.Pixels(STATE.layout)
        loc = (3, np.random.randint(STATE.layout.columns))
        # set a seed
        self.hits[loc] = 1
        self.n_hits = 1
        self.color_offset = np.random.randint(256)

    def needs_reset(self):
        if (self.n_hits // 4) >= 255 or self.max_row >= (STATE.layout.rows - 2):
            print self.n_hits, self.max_row
            return True

    def color(self):
        hue = (self.color_offset + min(255, self.n_hits // 4)) % 256
        return color_utils.hsv2rgb((hue, 255, 255))

    # this way is good if you only have one point
    def get_starting_location(self):
        rows_with_points = self.hits.max(axis=1)
        max_row = np.nonzero(rows_with_points)[0].max()
        # TODO: if max_row == 215, we should exit
        row = self.hits[max_row, :]
        idx = np.nonzero(row)[0]
        col = np.random.choice(idx)
        col = np.random.randint(col - 2, col + 2)
        loc = [min(STATE.layout.rows - 1, max_row + 10), col]
        assert self.max_row <= max_row
        self.max_row = max_row
        return loc

    #def get_starting_location(self):
    #    rows_with_points = self.hits.max(axis=1)
    #    max_row = np.nonzero(rows_with_points)[0].max()
    #    loc = [min(STATE.layout.rows - 1, max_row + 10), np.random.randint(STATE.layout.columns)]
        #assert self.max_row <= max_row
        #self.max_row = max_row
        #return loc


    def step(self):
        new_col = np.random.randint(self.location[1] - 1, self.location[1] + 2)
        new_col = new_col % STATE.layout.columns
        self.location = (self.location[0] - 1, new_col)

    def next_frame(self, pixels, now, state, osc):
        if self.needs_reset():
            self.max_row = 0
            self.set_points()
        # TODO: can I handle multiple locations?
        hits = 0
        end_of_frame = now + .5 / STATE.fps
        while time.time() < end_of_frame:
            if self.location[0] <= 2:
                self.location = self.get_starting_location()
            self.step()
            if self.is_near_collition(self.location):
                self.hits[self.location] = 1
                self.n_hits += 1
                self.my_pixels[self.location] = self.color()
                self.location = self.get_starting_location()
                hits += 1
        self.draw(pixels)

    def draw(self, pixels):
        pixels[:] = self.my_pixels[:]

    def is_near_collition(self, location):
        shape = (STATE.layout.rows, STATE.layout.columns)
        location = np.array(self.location)
        for move in (t.UP, t.DOWN, t.LEFT, t.RIGHT):
            loc = t.move(location, move, shape)
            pt = self.hits[tuple(loc)]
            if pt:
                return True
        else:
            return False


SCENES = [
    fm.FountainScene(
        'diffusion-limited-aggregation',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[Dla()]
    ),
]
