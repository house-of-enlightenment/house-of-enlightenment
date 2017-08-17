"""Creates an effect that feels like a rainbow
flowing and twisting up the House of Enlightenment
"""

from __future__ import division
import argparse
import json
import math
import Queue
import random
import sys
import time

import numpy as np

from hoe import color_utils
from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import pixels
from hoe.state import STATE
# sorry, got lazy
from hoe.distance import *
from hoe.translations import *
from hoe.sources import *
from hoe.transitions import *
from hoe import utils

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--row', choices=['sine', 'single', 'fader', 'rainbow', 'linear'], default='rainbow')
    args = parser.parse_args()

    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    STATE.fps = 30

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    osc_queue = Queue.Queue()
    server = osc_utils.create_osc_server()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/input/fader", lambda *args: osc_queue.put(args[2][-1]))

    coordinated = CoordinatedTransition()
    rotation = Rotate(hoe_layout.columns, coordinated.first())

    if args.row == 'single':
        row = SingleColumn(hoe_layout, rotation)
    elif args.row == 'rainbow':
        r_row = RainbowRow(hoe_layout, rotation)
        b_row = ConstantRow(hoe_layout, 5)
        row = r_row
        #row = SwapRow(
        #    (r_row, b_row),
        #    (lambda: utils.randrange(10, 25), lambda: utils.randrange(4, 5)))
    elif args.row == 'fader':
        row = FaderRow(hoe_layout, osc_queue)
    elif args.row == 'sine':
        row = SineRow(hoe_layout)
    elif args.row == 'linear':
        row = LinearBrightness(hoe_layout)
    if args.row == 'linear':
        effect = UpAndRotateEffect(hoe_layout, row, rotate_speed=consistent_speed_to_pixels(0))
    else:
        effect = UpAndRotateEffect(hoe_layout, row, rotate_speed=coordinated.second())
    #effect = UpAndExpandEffect(hoe_layout)
    render = Render(client, osc_queue, hoe_layout, [effect])
    render.run_forever()


class Render(object):
    def __init__(self, opc_client, osc_queue, hoe_layout, effects):
        self.client = opc_client
        self.queue = osc_queue
        self.layout = hoe_layout
        self.fps = STATE.fps
        self.effects = effects
        self.frame_count = 0

    def run_forever(self):
        now = time.time()
        for effect in self.effects:
            effect.start(now)
        self.pixels = pixels.Pixels(self.layout)
        while True:
            now = time.time()
            self.pixels[:] = 0
            for effect in self.effects:
                effect.next_frame(now, self.pixels)
            # make half very dark gray for a more realistic view
            self.pixels[:, 44:] = 5
            self.pixels.put(self.client)
            self.sleep_until_next_frame(now)

    def sleep_until_next_frame(self, now):
        self.frame_count += 1
        frame_took = time.time() - now
        remaining_until_next_frame = (1 / self.fps) - frame_took
        if remaining_until_next_frame > 0:
            # print time.time(), self.frame_count, '{:0.2f}%'.format(frame_took * self.fps * 100), \
            #     frame_took, remaining_until_next_frame
            time.sleep(remaining_until_next_frame)
        else:
            print "!! Behind !!", remaining_until_next_frame


class SingleColumn(object):
    """Creates a row that is just one red pixel.

    Can be useful to see how the shape flows up the HoE.
    """

    def __init__(self, layout, rotate=None):
        self.layout = layout
        self.rotate = rotate or Rotate(layout.columns)
        self.hue = 0

    def start(self, now):
        self.rotate.start(now)

    def __call__(self, now):
        row = np.zeros((self.layout.columns, 3), np.uint8)
        row[10, :] = (255, 0, 0)  #color_utils.hsv2rgb((self.hue, 255, 255))
        self.hue = (self.hue + 16) % 256
        return self.rotate(row, now)


if __name__ == '__main__':
    sys.exit(main())
