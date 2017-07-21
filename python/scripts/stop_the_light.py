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

    pixels = [WHITE]*len(hoe_layout.pixels)

    bottom_rows = set(hoe_layout.row[0] + hoe_layout.row[1])
    target_idx = bottom_rows & set(hoe_layout.slice[0])
    for idx in target_idx:
        pixels[idx] = RED
    client.put_pixels(pixels)

    max_slice = max(hoe_layout.slice)
    rotation_speed = .5  # rotation / second
    fps = 30
    start = time.time()
    location = 0
    while True:
        # when starting a loop, don't want any previous (perhaps old)
        # commands to be around, so empty this out
        empty_queue(queue)

        while True:
            now = time.time()
            sprite_rotation = (now - start) * rotation_speed
            sprite_location = int(max_slice * sprite_rotation) + location
            sprite_idx = (
                bottom_rows &
                set.union(
                    *[
                        set(hoe_layout.slice[i % (max_slice + 1)])
                        for i in
                        (sprite_location - 1, sprite_location, sprite_location + 1)
                    ])
            )

            pixels = [WHITE]*len(hoe_layout.pixels)
            for idx in target_idx:
                pixels[idx] = RED

            for idx in sprite_idx:
                pixels[idx] = BLUE

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

            next_frame = now + 1 / fps - time.time()
            if next_frame > 0:
                time.sleep(next_frame)
            else:
                # dammit, we're running too slow!
                pass


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
