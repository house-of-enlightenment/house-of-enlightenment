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


def main():
    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    queue = Queue.Queue()

    server = osc_utils.create_osc_server()
    # any button will work
    server.addMsgHandler("/input", lambda *args: stop(queue, *args))

    pixels = np.zeros((len(hoe_layout.pixels), 3), np.int8)
    pixels[:] = 255

    bottom = slice(2)
    section_centers = range(6, 66, 11)
    # not sure what I want to do with the targets yet
    target_idx = hoe_layout.grid[bottom, section_centers]
    pixels[target_idx] = RED
    client.put_pixels(pixels)

    rotation_speed = .5  # rotation / second
    fps = 30
    start = time.time()
    location = 0
    sprite = Sprite(location, rotation_speed, start)
    frame_count = 1
    while True:
        # when starting a loop, don't want any previous (perhaps old)
        # commands to be around, so empty this out
        empty_queue(queue)

        prev = start
        while True:
            now = time.time()
            pixels[:] = 255
            sprite.update(now)
            sprite_idx = hoe_layout.grid[bottom, sprite.columns()]
            pixels[target_idx] = RED
            pixels[sprite_idx] = BLUE

            client.put_pixels(pixels)
            try:
                should_stop = queue.get_nowait()
                if should_stop:
                    # we'll pause for 5 seconds to see where we stopped it
                    # and then continue on
                    # Reset our timer and location
                    time.sleep(5)
                    start = time.time()
                    location = sprite_location
                    rotation_speed = -rotation_speed
                    # and restart the inner loop
                    break
                else:
                    print 'should_stop'
                    raise Exception('Queue should always return True')
            except Queue.Empty:
                pass

            frame_took = time.time() - now
            remaining_until_next_frame = (1 / fps) - frame_took
            if remaining_until_next_frame > 0:
                print time.time(), frame_count, frame_took, remaining_until_next_frame
                time.sleep(remaining_until_next_frame)
            else:
                print "!! Behind !!", next_frame
                # dammit, we're running too slow!
                pass
            frame_count += 1


class Sprite(object):
    def __init__(self, start_location, rotation_speed, start, width=3):
        self.start_location = start_location
        self.rotation_speed = rotation_speed
        self.location = start_location
        self.start = start
        self.width = width

    def update(self, now):
        sprite_rotation = (now - self.start) * self.rotation_speed
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


def parse_address(address):
    match = re.match('/input/stations/(\d+)/button/(\d+)', address)
    return dict(zip(('station', 'button'), match.groups()))


def stop(queue, address, types, payload, *args):
    print address, types, payload, args
    queue.put(True)


if __name__ == '__main__':
    sys.exit(main())
