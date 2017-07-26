"""Creates an effect that feels like a rainbow
flowing and twisting up the House of Enlightenment
"""

from __future__ import division
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

    osc_queue = Queue.Queue()
    server = osc_utils.create_osc_server()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/input", lambda *args: add_station_id(osc_queue, *args))
    effect = Effect(hoe_layout)
    render = Render(client, osc_queue, hoe_layout, [effect])
    render.run_forever()


class Render(object):
    def __init__(self, opc_client, osc_queue, hoe_layout, effects):
        self.client = opc_client
        self.queue = osc_queue
        self.layout = hoe_layout
        self.fps = 40
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
            self.pixels.put(self.client)
            self.sleep_until_next_frame(now)

    def sleep_until_next_frame(self, now):
        self.frame_count += 1
        frame_took = time.time() - now
        remaining_until_next_frame = (1 / self.fps) - frame_took
        if remaining_until_next_frame > 0:
            print time.time(), self.frame_count, '{:0.2f}%'.format(frame_took * self.fps * 100), \
                frame_took, remaining_until_next_frame
            time.sleep(remaining_until_next_frame)
        else:
            print "!! Behind !!", remaining_until_next_frame


class Effect(object):
    def __init__(self, layout):
        self.layout = layout
        self.pixels_per_frame = 3
        self.rotation_speed = SpeedUpdate(3)
        self.rotation = 0

    def start(self, now):
        self.sv = SVTransition(now)
        self.hue = HueTransition(now)
        # need my own copy of pixels
        self.pixels = pixels.Pixels(self.layout)

        self.before_idx = self.layout.grid[10:-self.pixels_per_frame:, :]
        a = self.layout.grid[10 + self.pixels_per_frame:, 1:]
        b = self.layout.grid[10 + self.pixels_per_frame:, :1]
        self.after_idx = np.concatenate((a, b), axis=1)

    def next_frame(self, now, pixels):
        rainbow = self.get_rainbow(now)
        self.rotate(rainbow, now)
        # copy up and rotate
        self.pixels[self.after_idx] = self.pixels[self.before_idx]
        # grab the 10th row and copy up
        for i in range(self.pixels_per_frame):
            self.pixels[10 + i, :] = self.pixels[10, :]
        pixels[:] = self.pixels[:]

    def get_rainbow(self, now):
        hue = self.hue.update(now)
        sat, val = self.sv.update(now)
        # mirror the hues so that we don't get any sharp edges
        return np.concatenate((color_utils.rainbow(layout.COLUMNS / 2, hue[0], hue[1], sat, val),
                               color_utils.rainbow(layout.COLUMNS / 2, hue[1], hue[0], sat, val), ))

    def rotate(self, rainbow, now):
        # vary the rotation speed
        if np.random.random() < self.rotation_speed.update(now):
            self.rotation = (self.rotation + 1) % layout.COLUMNS
        if self.rotation == 0:
            self.pixels[10, :] = rainbow
        else:
            self.pixels[10, :-self.rotation] = rainbow[self.rotation:]
            self.pixels[10, -self.rotation:] = rainbow[:self.rotation]

    def __setitem__(self, key, value):
        idx = self.layout.grid[key]
        self.pixels[idx] = value

    def __getitem__(self, key):
        idx = self.layout.grid[key]
        return self.pixels[idx]


class SpeedUpdate(object):
    def __init__(self, delay):
        self.next_update = 0
        self.delay = delay
        self.value = None

    def update(self, now):
        if now >= self.next_update:
            self.next_update = now + self.delay
            self.value = np.random.rand() * 0.7 + .3
        return self.value


class SVTransition(object):
    def __init__(self, now):
        self.end = np.array([np.random.randint(128, 256), np.random.randint(196, 256)])
        self._reset(now)

    def _reset(self, now):
        self.start = self.end
        # pick a saturation between 128-256 (128 is very pastel, 256 is full saturation)
        # pick a value between 192-256 (probably a very minor effect)
        self.end = np.array([np.random.randint(128, 256), np.random.randint(196, 256)])
        self.length = np.random.rand() * 3 + 1
        self.start_time = now

    def update(self, now):
        elapsed = now - self.start_time
        if elapsed > self.length:
            self._reset(now)
        delta = (self.end - self.start) * (now - self.start_time) / self.length
        return self.start + delta


class HueTransition(object):
    def __init__(self, now):
        self.end = self.rnd_pt()
        self._reset(now)

    def _reset(self, now):
        self.start = self.end
        self.end = self.rnd_pt()
        self.length = np.random.rand() * 3 + 1
        self.start_time = now

    def rnd_pt(self):
        # pick a hue to start with
        start = np.random.randint(0, 256)
        # pick how much of the color wheel we're going to take
        # a longer slice will have more colors
        length = np.random.randint(32, 96)
        end = start + length
        return np.array([start, end])

    def update(self, now):
        # for hues, there are two ways that the transition can go, clockwise
        # and counterclockwise.
        # This is always going clockwise
        #
        # TODO: on reset, pick a direction
        elapsed = now - self.start_time
        if elapsed > self.length:
            self._reset(now)
        delta = (self.end - self.start) * (now - self.start_time) / self.length
        return self.start + delta


if __name__ == '__main__':
    sys.exit(main())
