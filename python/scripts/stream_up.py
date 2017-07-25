"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code, but its getting better

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
    render = Render(client, osc_queue, hoe_layout)
    render.run_forever()


class Render(object):
    def __init__(self, opc_client, osc_queue, hoe_layout):
        self.client = opc_client
        self.queue = osc_queue
        self.layout = hoe_layout
        self.fps = 40
        self.pixels_per_frame = 3
        self.frame_count = 0
        self.rotation_speed = SpeedUpdate(3)
        self.rotation = 0

    def set_rainbow(self):
        hue = self.hue.update(self.now)
        sv = self.sv.update(self.now)
        # mirror the hues so that we don't get any sharp edges
        self.rainbow = np.concatenate((
            color_utils.rainbow(
                layout.COLUMNS / 2, hue[0], hue[1], sv[0], sv[1]),
            color_utils.rainbow(
                layout.COLUMNS / 2, hue[1], hue[0], sv[0], sv[1]),
        ))


    def run_forever(self):
        self.now = time.time()
        self.sv = SVTransition(self.now)
        self.hue = HueTransition(self.now)
        self.pixels = np.zeros((len(self.layout.pixels), 3), np.uint8)
        self.set_rainbow()
        self[10,:] = self.rainbow
        self.before_idx = self.layout.grid[10: -self.pixels_per_frame:, :]
        a = self.layout.grid[10 + self.pixels_per_frame:, 1:]
        b = self.layout.grid[10 + self.pixels_per_frame:, :1]
        self.after_idx = np.concatenate((a, b), axis=1)

        while True:
            self.now = time.time()
            self.next_frame()
            self.sleep_until_next_frame()

    def next_frame(self):
        # copy up and rotate
        self.pixels[self.after_idx] = self.pixels[self.before_idx]
        # grab the 10th row and copy up
        for i in range(self.pixels_per_frame):
            self[10 + i, :] = self[10,:]
        self.client.put_pixels(self.pixels)
        self.set_rainbow()
        # vary the rotation speed
        if np.random.random() < self.rotation_speed.update(self.now):
            self.rotation = (self.rotation + 1) % layout.COLUMNS
        if self.rotation == 0:
            self[10,:] = self.rainbow
        else:
            self[10,:-self.rotation] = self.rainbow[self.rotation:]
            self[10,-self.rotation:] = self.rainbow[:self.rotation]

    def __setitem__(self, key, value):
        idx = self.layout.grid[key]
        self.pixels[idx] = value

    def __getitem__(self, key):
        idx = self.layout.grid[key]
        return self.pixels[idx]

    def sleep_until_next_frame(self):
        self.frame_count += 1
        frame_took = time.time() - self.now
        remaining_until_next_frame = (1 / self.fps) - frame_took
        if remaining_until_next_frame > 0:
            print time.time(), self.frame_count, frame_took, remaining_until_next_frame
            time.sleep(remaining_until_next_frame)
        else:
            print "!! Behind !!", remaining_until_next_frame


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
        elapsed = now - self.start_time
        if elapsed > self.length:
            self._reset(now)
        delta = (self.end - self.start) * (now - self.start_time) / self.length
        return self.start + delta




if __name__ == '__main__':
    sys.exit(main())
