import logging

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import color_utils
from hoe.state import STATE
from hoe import translations


logger = logging.getLogger(__name__)


N_ROWS = 2
N_STATIONS = 6

UP = translations.UP
DOWN = translations.DOWN
LEFT = translations.LEFT
RIGHT = translations.RIGHT
STAY = translations.STAY

# maps to button locations
MOVEMENTS = [UP, LEFT, STAY, RIGHT, DOWN]

N_ROWS = 2
N_STATIONS = 6

# Currently, moves a single "block" to whoever last pressed a button
class ArrangeBlocks(af.Effect):
    def __init__(self, grid):
        # share a common blink so that they all blink at the same time
        blink = Blink()
        self.blocks = [Block(blink, (255, 0, 255), (0, 0), grid)]
        self.selectors = [Selector((0, i), grid, blink) for i in range(N_STATIONS)]
        self.targets = [Target((0, 255, 0), (0, i), grid) for i in range(N_STATIONS)]

    def scene_starting(self, now, osc_data):
        pass

    def next_frame(self, pixels, now, collab, osc):
        pixels[:] = 10
        # each station has one, and only one, selector
        # if we get a key press we pass it along to the selector
        # and it will deal with moving blocks
        for i, station in enumerate(osc.stations):
            if station.contains_change:
                station_selector = self.selectors[i]
                station_selector.handle_button_presses(station.button_presses)
        for block in self.blocks:
            block.next_frame(pixels, now)
        for selector in self.selectors:
            selector.next_frame(pixels, now)
        for target in self.targets:
            target.next_frame(pixels, now)


class Grid(object):
    def __init__(self, grid):
        self.grid = grid

    @classmethod
    def make(cls, rows=N_ROWS, cols=N_STATIONS):
        return cls([[set() for _ in range(cols)] for _ in range(rows)])

    def has_instance(self, row, col, instance):
        return any(isinstance(obj, instance) for obj in self.grid[row][col])

    def add(self, row, col, item):
        self.grid[row][col].add(item)

    def remove(self, row, col, item):
        self.grid[row][col].remove(item)

    def get_items(self, row, col):
        return list(self.grid[row][col])

    def get_block(self, row, col):
        blocks = [item for item in self.grid[row][col] if isinstance(item, Block)]
        assert len(blocks) <= 1
        if blocks:
            return blocks[0]
        else:
            return None


class GridItem(object):
    def __init__(self, color, location, grid):
        self.color = color
        # the second item is 0 for bottom, 1 for top
        # first item in location is an in 0-6, representing the station
        self.location = list(location)
        self.grid = grid
        self.grid.add(self.row, self.station, self)

    def _get_row(self):
        return self.location[0]

    def _set_row(self, val):
        self.location[0] = val

    row = property(_get_row, _set_row)

    def _get_station(self):
        return self.location[1]

    def _set_station(self, val):
        self.location[1] = val

    station = property(_get_station, _set_station)


# The target is a color and on the right
# It stays there.
# If a matching color block is added to the same
# cell, it will blink.
class Target(GridItem):
    def next_frame(self, pixels, now):
        station = STATE.layout.STATIONS[self.station]
        pixels[self.row, station.right - 1] = self.color


# the selector pixel is white and on the left.
# it blinks when the selector can be moved
# it is solid when a block has been selected (and then
# the block can move
class Selector(GridItem):
    ON = 0
    OFF = 1

    def __init__(self, location, grid, blink):
        GridItem.__init__(self, (255, 255, 255), location, grid)
        self.mode = Selector.OFF
        self.blink = blink

    def move(self, motion):
        row, col = motion
        if col != 0:
            return

        old_row = self.row
        self.row = np.clip(self.row + row, 0, N_ROWS - 1)
        if self.row != old_row:
            logger.debug('Station %s moving to row', self.row)
            self.grid.remove(old_row, self.station, self)
            self.grid.add(self.row, self.station, self)

    def get_block(self):
        return self.grid.get_block(self.row, self.station)

    def handle_button_presses(self, button_presses):
        # if you mash keys, we're just taking the first one
        button_press = list(button_presses.keys())[0]
        logger.debug('For station %s, button %s was pressed', self.station, button_press)
        motion = MOVEMENTS[button_press]
        if self.mode == Selector.OFF:
            if button_press == 2:
                logger.debug('Station %s selector is turned on', self.station)
                # TODO: check if there is actually a block here
                self.mode = Selector.ON
                block = self.get_block()
                if block:
                    block.mode = Block.ON
            else:
                self.move(motion)
        else:
            if button_press == 2:
                logger.debug('Station %s selector is turned off', self.station)
                self.mode = Selector.OFF
                block = self.get_block()
                if block:
                    block.mode = Block.OFF
            else:
                self.move_block(motion)

    def move_block(self, motion):
        block = self.get_block()
        if block:
            if block.move(motion):
                self.mode = Selector.OFF

    def next_frame(self, pixels, now):
        station = STATE.layout.STATIONS[self.station]
        if self.mode == Selector.OFF:
            if self.blink.update(now):
                pixels[self.row, station.left] = self.color
            else:
                pixels[self.row, station.left] = 0
        else:
            pixels[self.row, station.left] = self.color


class Blink(object):
    def __init__(self):
        self.item = (0, 1);
        self.idx = 0
        self.next_update = 0

    def update(self, now):
        if now > self.next_update:
            self.next_update = now + 0.5
            self.idx = (self.idx + 1) % len(self.item)
        return self.item[self.idx]


class Block(GridItem):
    ON = 0
    OFF = 1

    def __init__(self, blink, *args, **kwargs):
        GridItem.__init__(self, *args, **kwargs)
        self.blink = blink
        self.mode = Selector.OFF

    def move(self, motion):
        assert self.mode == Selector.ON
        location = translations.move(self.location, motion, (N_ROWS, N_STATIONS), (True, False))
        if (location == self.location).all():
            logger.debug('Move failed; new location is the same as the old location')
            return False
        if self.grid.has_instance(location[0], location[1], Block):
            logger.debug('Move failed; there is already a block at the new location')
            return False
        self.grid.remove(self.row, self.station, self)
        self.location = location
        self.grid.add(self.row, self.station, self)
        self.mode = Selector.OFF
        return True

    def next_frame(self, pixels, now):
        station = STATE.layout.STATIONS[self.station]
        if self.mode == Selector.OFF:
            pixels[self.row, station.left + 1:station.right - 1] = self.color
        else:
            if self.blink.update(now):
                pixels[self.row, station.left + 1:station.right - 1] = self.color
            else:
                pixels[self.row, station.left + 1:station.right - 1] = 0

SCENES = [
    af.Scene(
        'arrange-blocks',
        tags=[af.Scene.TAG_GAME],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[ArrangeBlocks(Grid.make())])
]
