"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code.

from __future__ import division
import json
import Queue
import math
import sys
import time

import numpy as np

from hoe import layout
from hoe import opc
from hoe import osc_utils


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
        self.state = State.ACTIVE
        self.successful_sections = [False] * layout.SECTIONS
        self.fps = 30
        rotation_speed = .5  # rotation / second
        location = 0
        self.sprite = Sprite(location, rotation_speed)
        self.frame_count = 0
        self.client = opc_client
        self.queue = osc_queue
        self.layout = hoe_layout

    def run_forever(self):
        self.pixels = np.zeros((len(self.layout.pixels), 3), np.int8)
        self.bottom = slice(None, 10, None)
        self.top = slice(10, None, None)
        self.init_pixels()
        self.section_centers = range(6, 66, 11)
        self.target_idx = self.layout.grid[self.bottom, self.section_centers]
        self.pixels[self.target_idx] = YELLOW
        self.client.put_pixels(self.pixels)

        self.now = time.time()
        self.sprite.start(self.now)

        while True:
            self.now = time.time()
            self.next_frame()
            self.sleep_until_next_frame()


            # # when starting a loop, don't want any previous (perhaps old)
            # # commands to be around, so empty this out
            # empty_queue(queue)
            # state =
            # successful_sections = [False] * layout.SECTIONS
            # ignore_buttons = False
            # prev = start
            # while True:
            #     self.loop_until_interaction()

    def init_pixels(self):
        self[self.bottom,:] = 32
        self[self.top,:] = (64, 0, 0)

    # a convenience method to allow me to do, like:
    # self[rows, columns] = RED
    def __setitem__(self, key, value):
        idx = self.layout.grid[key]
        self.pixels[idx] = value

    def next_frame(self):
        self.now = time.time()
        self.init_pixels()
        if self.state == State.ACTIVE:
            self.sprite.update(self.now)
            self.pixels[self.target_idx] = YELLOW
            columns = self.sprite.columns()
            self[self.bottom, columns] = BLUE
            self.client.put_pixels(self.pixels)
            try:
                section = self.queue.get_nowait()
                # TODO: actually move into a hit or miss state
                self.state = None
                self.wait_until = self.now + 3
            except Queue.Empty:
                pass
        else:
            # Note that there is no call to sprite.update()
            self.pixels[self.target_idx] = YELLOW
            columns = self.sprite.columns()
            self[self.bottom, columns] = BLUE
            self.client.put_pixels(self.pixels)
            if self.now >= self.wait_until:
                self.sprite.reverse(self.now)
                self.wait_until = None
                self.state = State.ACTIVE
        #     try:
        #         section = queue.get_nowait()
        #         target = section_centers[section]
        #         if target in columns():


        #         if should_stop:
        #             # we'll pause for 5 seconds to see where we stopped it
        #             # and then continue on
        #             # Reset our timer and location
        #             time.sleep(5)
        #             sprite.reverse()
        #             break
        #         else:
        #             print 'should_stop'
        #             raise Exception('Queue should always return True')
        #     except Queue.Empty:
        #         pass
        # elif state == State.HIT:
        #     pass
        # elif state == State.MISS:
        #     pass
        # else:
        #     raise Exception('You are in a bad state: {}'.format(state))

    def sleep_until_next_frame(self):
        self.frame_count += 1
        frame_took = time.time() - self.now
        remaining_until_next_frame = (1 / self.fps) - frame_took
        if remaining_until_next_frame > 0:
            print time.time(), self.frame_count, frame_took, remaining_until_next_frame
            time.sleep(remaining_until_next_frame)
        else:
            print "!! Behind !!", remaining_until_next_frame


class State(object):
    ACTIVE = 'active'
    HIT = 'hit'
    MISS = 'miss'


class Sprite(object):
    def __init__(self, start_location, rotation_speed, width=3):
        self.start_location = start_location
        self.rotation_speed = rotation_speed
        self.location = start_location
        self.width = width
        self.start_time = None

    def start(self, now):
        self.start_time = now

    def reverse(self, now):
        self.start_location = self.location
        self.rotation_speed = -self.rotation_speed
        self.start(now)

    def update(self, now):
        sprite_rotation = (now - self.start_time) * self.rotation_speed
        location = int(layout.COLUMNS * sprite_rotation) + self.start_location
        self.location = location % layout.COLUMNS

    def columns(self):
        left = int(self.width / 2)
        right = self.width - left
        return map(colmod, range(self.location - left, self.location + right))


def colmod(i):
    return divmod(i, layout.COLUMNS)[1]


def empty_queue(queue):
    while True:
        try:
            queue.get_nowait()
        except Queue.Empty:
            return


def add_station_id(queue, address, types, payload, *args):
    print address, types, payload, args
    station_id, control_type, control_id, value = payload
    queue.put(station_id)


if __name__ == '__main__':
    sys.exit(main())
