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

from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import color_utils


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

    osc_queue = Queue.Queue()
    server = osc_utils.create_osc_server()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/input/button", lambda *args: add_button_id(osc_queue, *args))
    interaction = RotateDisc(hoe_layout, osc_queue)
    render = su.Render(client, osc_queue, hoe_layout, [interaction])
    render.run_forever()


class WalkRows(object):
    def __init__(self, hoe_layout, queue):
        self.layout = hoe_layout
        self.queue = queue
        self.row = 0

    def start(self, now):
        pass

    def next_frame(self, now, pixels):
        try:
            button = self.queue.get_nowait()
            self.row = (self.row + button - 2) % self.layout.rows
            print(self.row)
        except Queue.Empty:
            pass
        pixels[:] = 20
        pixels[self.row, :] = (255, 0, 0)


class RotateDisc(object):
    def __init__(self, layout, queue):
        self.layout = layout
        self.queue = queue
        self.hue_shift = 0

    def start(self, now):
        pass

    def get_hue(self, i):
        return ((i + self.hue_shift) % 66) / 66.0 * 255

    def get_color(self, i):
        return (self.get_hue(i), 255, 255)

    def next_frame(self, now, pixels):
        pixels[:] = 20
        self.hue_shift = (self.hue_shift + 10) % 256
        rainbow = color_utils.rainbow(self.layout.columns, self.hue_shift, 255 + self.hue_shift)
        rows = slice(self.layout.BOTTOM_DISC.bottom, self.layout.BOTTOM_DISC.top)
        pixels[rows,:] = rainbow

        rainbow = rainbow[::-1]
        rows = slice(self.layout.TOP_DISC.bottom, self.layout.TOP_DISC.top)
        pixels[rows,:] = rainbow

        # black out the back for a more realistic view
        pixels[:,33:] = 5


def add_button_id(queue, address, types, payload, *args):
    print address, types, payload, args
    station_id, control_id = payload
    queue.put(control_id)


if __name__ == '__main__':
    sys.exit(main())
