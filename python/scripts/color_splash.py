"""When a player hits a target, a color splash flows up HoE
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

# TODO: fix this. Move the stream_up code somewhere shared
import stream_up as su
import stop_the_light as stl

FADER_VALUES = {i: 0 for i in range(6)}


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
    server.addMsgHandler("/input/button", lambda *args: stl.add_station_id(osc_queue, *args))
    server.addMsgHandler("/input/fader", handle_fader)
    background = su.Effect(hoe_layout, TargetRow(hoe_layout, osc_queue))
    render = su.Render(client, osc_queue, hoe_layout, [background])
    render.run_forever()


def handle_fader(addr, types, values, src):
    station_id, fader_id, value = values
    # screw thread safety!
    FADER_VALUES[station_id] = value


def print_fn(*args):
    print args


def fader_value_to_color(n):
    return color_utils.hsv2rgb(np.array((n * 255 / 100, 255, 255)))


class TargetRow(object):
    """Creates a row that is red when a button is pressed"""

    def __init__(self, layout, queue):
        self.layout = layout
        self.queue = queue

    def start(self, now):
        pass

    def __call__(self, now):
        row = np.zeros((self.layout.columns, 3), np.uint8)
        try:
            station_id = self.queue.get_nowait()
            center = station_id * 11 - 5
            left = (center - 15) % self.layout.columns
            right = (center + 15) % self.layout.columns
            color = fader_value_to_color(FADER_VALUES[station_id])
            if left < right:
                row[left:right] = color
            else:
                print left, right
                row[left:] = color
                row[:right] = color
        except Queue.Empty:
            pass
        return row


if __name__ == '__main__':
    sys.exit(main())
