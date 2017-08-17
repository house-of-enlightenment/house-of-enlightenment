"""Draw and rotate a color wheel on the two discs"""
from __future__ import division

import argparse
import collections
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
    args = parser.parse_args()

    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    STATE.layout = hoe_layout
    background = SinglePixelSourceDiamondShape(hoe_layout)
    render = su.Render(client, None, hoe_layout, [background])
    render.run_forever()


UP = np.array((1, 0))
DOWN = np.array((-1, 0))
LEFT1 = np.array((0, 1))
LEFT2 = np.array((0, 2))
RIGHT1 = np.array((0, -1))
RIGHT2 = np.array((0, -2))


def get_next_movements(previous_move):
    if (previous_move == UP).all():
        return (UP, LEFT1, RIGHT1)
    if (previous_move == DOWN).all():
        return (DOWN, LEFT1, RIGHT1)
    if ((previous_move) == LEFT1).all():
        return (LEFT1, )
    if ((previous_move) == LEFT2).all():
        pass
    if ((previous_move) == RIGHT1).all():
        return (RIGHT1, )
    if ((previous_move) == RIGHT2).all():
        pass
    raise ValueError('{} is not a valid move'.format(previous_move))


class SinglePixelSourceDiamondShape(object):
    """One pixel in the middle changes, everything else feeds from that
    in a diamond shape
    """

    def __init__(self, layout):
        self.layout = layout
        self.hue_shift = 0
        c = self.layout.BOTTOM_DISC.center
        self.center = (c, 15)
        self.color = color_utils.rainbow(60, 0, 255)
        self.idx = 0
        self.my_pixels = pixels.Pixels(layout)
        self.my_pixels[:] = 25
        before_idx = []
        after_idx = []
        queue = collections.deque(((self.center, np.array([UP, DOWN, LEFT1, RIGHT1])), ))
        top = 215  #layout.BOTTOM_DISC.top
        bottom = 0  #layout.BOTTOM_DISC.bottom
        left = 48
        while queue:
            pt, movements = queue.popleft()
            for move in movements:
                assert len(move) == 2
                new_pt = pt + move
                row, col = new_pt
                col = layout.colmod(col)
                if bottom > row or top < row:
                    continue
                # TODO: this will leave a weird black line as `left' column
                if col in (47, 48, 49):
                    continue
                before_idx.append(self.layout.grid[pt])
                after_idx.append(self.layout.grid[(row, col)])
                next_moves = get_next_movements(move)
                queue.append(((row, col), next_moves))
        self.before_idx = before_idx
        self.after_idx = after_idx
        self.my_pixels[self.center] = (255, 0, 0)
        #print before_idx
        #print after_idx

    def start(self, now):
        pass

    def get_hue(self, i):
        return ((i + self.hue_shift) % 66) / 66.0 * 255

    def get_color(self, i):
        return (self.get_hue(i), 255, 255)

    def next_frame(self, now, pixels):
        self.my_pixels[self.after_idx] = self.my_pixels[self.before_idx]
        self.my_pixels[self.center] = self.color[self.idx]
        self.idx = (self.idx + 1) % 60
        # TODO: add this method to the Pixel class
        pixels[:] = self.my_pixels.pixels

        # rainbow = color_utils.rainbow(self.layout.columns, self.hue_shift, 255 + self.hue_shift)
        # rows = slice(self.layout.BOTTOM_DISC.bottom, self.layout.BOTTOM_DISC.top)
        # pixels[rows, :] = rainbow

        # rainbow = rainbow[::-1]
        # rows = slice(self.layout.TOP_DISC.bottom, self.layout.TOP_DISC.top)
        # pixels[rows, :] = rainbow

        # black out the back for a more realistic view
        pixels[:, 33:] = 5

    def random_step(self, color):
        c = (color + np.array([[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0], [1, 0, 0], [-1, 0, 0]
                               ])[np.random.randint(0, 6)]) % 256
        print c
        return c


if __name__ == '__main__':
    sys.exit(main())
