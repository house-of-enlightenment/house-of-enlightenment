"""Draw and rotate a color wheel on the two discs"""
from __future__ import division

import argparse
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
    parser.add_argument('n', type=int)
    args = parser.parse_args()
    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    STATE.layout = hoe_layout
    STATE.fps = 30

    background = Breathe(hoe_layout, args.n)
    render = su.Render(client, None, hoe_layout, [background])
    render = su.Render(client, None, hoe_layout, [Static()s])
    render.run_forever()















def bright():
    return np.random.randint(18, 32)


def twinkle():
    return np.random.randint(12, 32)




if __name__ == '__main__':
    sys.exit(main())
