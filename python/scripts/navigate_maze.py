from __future__ import division
import csv
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

# TODO: fix this. Move the stream_up code somewhere shared
import stream_up as su


WALL = (255, 255, 255)
OPEN = (0, 0, 0)
OUTSIDE = (255, 0, 0)
PLAYER = (0, 255, 0)

BORDER = 10


def read_maze(border=BORDER):
    with open('maze.csv') as f:
        data = list(reversed(list(csv.reader(f))))
    height = len(data) + 2*border
    width = len(data[0]) + 2*border
    depth = 3
    maze = np.full((height, width, depth), OUTSIDE, np.uint8)
    start = None
    finish = None
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            val = val.lower()
            maze[i + border, j + border] = (WALL if val == 'x' else OPEN)
            if val == '*':
                start = (i + border, j + border)
            if val == '!':
                finish = (i + border, j + border)
    return maze, start, finish


# when centering a window, we're generally
# given a width and need to split that around
# a center position.
# If the width is odd (9) and we want to center
# that on 10, we'll do (6,15) which is (-4, 5)
# If the width is even (10), we'd do (-5, 5)
# [which, isn't centered, but its the best we can do]
def split(val):
    half = val // 2
    if 2 * half == val:
        return (half, half)
    else:
        return (half, half + 1)


def get_extents(center, area):
    height, width = area
    x, y = center
    l, r = split(width)
    d, u = split(height)
    return x - l, x + r, y - d, y + u


def get_center(area):
    return (area[0] // 2, area[1] // 2)


def slice_maze(maze, position, area):
    left, right, bottom, top  = get_extents(position, area)
    sub_maze = maze[left:right, bottom:top]
    return sub_maze


# This is deprecated
def draw_maze(maze, position):
    """Return a new array with pixel values based on maze.

    maze is an array of True / False. WALLs are drawn where
    True. False values are replaced with OPENs
    """
    shape = maze.shape + (3,)
    # need to "broadcast" the T/F values 3 times, one
    # for each RGB value
    maze_3 = np.repeat(maze, 3).reshape(shape)
    walls = np.full(shape, WALL)
    opens = np.full(shape, OPEN)
    pixels = np.where(maze, walls, opens)
    pixels[position] = PLAYER


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
    server.addMsgHandler("/input/button", lambda *args: set_direction(osc_queue, *args))
    interaction = MazeEffect(hoe_layout, osc_queue)
    render = su.Render(client, osc_queue, hoe_layout, [interaction])
    render.run_forever()


class MazeEffect(object):
    def __init__(self, layout, queue):
        self.layout = layout
        self.queue = queue
        self.maze, self.position, self.goal = read_maze()
        self.area = (11, 11)

    def start(self, now):
        pass

    def next_frame(self, now, pixels):
        self.update_position()
        viewable = slice_maze(self.maze, self.position, self.area)
        pixels[:self.area[0], 30:30+self.area[1]] = viewable
        center = get_center(self.area)
        pixels[center[0], 30+center[1]] = PLAYER

    def update_position(self):
        try:
            move = self.queue.get_nowait()
            new_position = self.position + move
            print new_position
            print self.maze[new_position[0], new_position[1]]
            is_wall = (self.maze[new_position[0], new_position[1]] == WALL).all()
            if not is_wall:
                self.position = new_position
        except Queue.Empty:
            pass


UP = (1, 0)
DOWN = (-1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
STAY = (0, 0)
DIRECTIONS = [np.array(d) for d in (UP, DOWN, STAY, LEFT, RIGHT)]


def set_direction(queue, *args):
    address, types, (station_id, button_id), source = args
    direction = DIRECTIONS[button_id]
    print direction
    queue.put(direction)


if __name__ == '__main__':
    sys.exit(main())
