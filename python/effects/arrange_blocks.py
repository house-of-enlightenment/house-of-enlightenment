"""Arrange blocks

An interactive mode where players attempt to arrange colored blocks
so that they are all in their target location.

Each player has control of the blocks that are in their section.
Blocks can be moved up/down or passed left/right to other sections.
Once passed to another section, other players have control of those blocks.

If there are two blocks in a section, only the one that is blinking
can be moved left/right. To switch which block is blinking, a player
can press up or down.

The middle button doesn't do anything.
"""
#
# In no way is this code meant to be emulated. This was a first
# pass to get something, anything working that resembled a game.
#
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
LABEL = ['UP', 'LEFT', 'MIDDLE', 'RIGHT', 'DOWN']

N_ROWS = 2
N_STATIONS = 6


def get_color(i):
    i = i % 6
    return color_utils.hsv2rgb((i * 255 / 6, 255, 255))


class ArrangeBlocks(af.Effect):
    def __init__(self, grid):
        # share a common blink so that they all blink at the same time
        blink = Blink(0.5)
        fast_blink = Blink(0.125)
        # the + 1 just makes sure the blocks are offset
        # Ideally I'd like to have them start in the same place as the targets
        # and then go thru a shuffle and then start the game
        self.blocks = [
            Block(blink, Block.ON, get_color(i + 1), (0, i), grid)
            for i in range(N_STATIONS)]
        self.selectors = [Selector((0, i), grid) for i in range(N_STATIONS)]
        self.targets = [
            Target(fast_blink, get_color(i), (0, i), grid) for i in range(N_STATIONS)]

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
    """Keeps track of where items are.

    Its probably a poor abstraction, but items are responsible for letting
    the grid know where they are.
    """
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

    def move(self, from_, to, item):
        self.grid.remove(from_[0], from_[1], item)
        self.grid.add(to[0], to[1], item)

    def get_items(self, row, col):
        return list(self.grid[row][col])

    def get_block(self, row, col):
        return self.get_item(row, col, Block)

    def get_target(self, row, col):
        return self.get_item(row, col, Target)

    def get_item(self, row, col, instance_type):
        items = [item for item in self.grid[row][col] if isinstance(item, instance_type)]
        assert len(items) <= 1
        if items:
            return items[0]
        else:
            return None

    def get_blocks(self, col):
        return [self.get_block(i, col) for i in range(N_ROWS)]


class GridItem(object):
    """A base class for items in the grid"""
    def __init__(self, color, location, grid):
        # the second item is 0 for bottom, 1 for top
        # first item in location is an in 0-6, representing the station
        # convert to a list because it needs to be mutable
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

    def get_block(self):
        return self.grid.get_block(self.row, self.station)

    station = property(_get_station, _set_station)


class Target(GridItem):
    """Indicates where a block is supposed to end up.

    Each target colors the two outside pixels of each block.

    Each time a block moves, it checks the target in that cell and if
    its a hit, the target and block blink quickly for a bit.
    """

    def __init__(self, blink, color, location, grid):
        GridItem.__init__(self, location, grid)
        self.color = color
        self.blink = blink
        self.target_blink = None

    def on_hit(self, block):
        if are_same_color(self, block):
            logger.debug('Block succesfully moved into the target')
            self.target_blink = BlinkCount(self.blink, 6)
            return self.target_blink
        else:
            return None

    def next_frame(self, pixels, now):
        if self._handle_target_blink(pixels, now):
            return
        station = STATE.layout.STATIONS[self.station]
        pixels[self.row, [station.left, station.right - 1]] = self.color

    def _handle_target_blink(self, pixels, now):
        if self.target_blink:
            blink_value = self.target_blink.update(now)
            if blink_value is None:
                self.target_blink = None
                return False
            else:
                self._handle_blink(blink_value, pixels)
                return True
        else:
            return False

    def _handle_blink(self, value, pixels):
        station = STATE.layout.STATIONS[self.station]
        if value:
            pixels[self.row, [station.left, station.right - 1]] = self.color
        else:
            pixels[self.row, [station.left, station.right - 1]] = 0



def are_same_color(a, b):
    return (a.color == b.color).all()


class Selector(GridItem):
    def __init__(self, location, grid):
        GridItem.__init__(self, location, grid)

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
        if button_press == 2:
            return
        motion = MOVEMENTS[button_press]
        label = LABEL[button_press]
        blocks = self.grid.get_blocks(self.station)
        if not blocks[0] and not blocks[1]:
            logger.debug('No blocks in station %s', self.station)
            return
        if blocks[0] and blocks[1]:
            logger.debug('There are two blocks in %s', self.station)
            assert not (blocks[0].mode == Block.ON and blocks[1].mode == Block.ON)
            if label == 'LEFT' or label == 'RIGHT':
                if blocks[0].mode == Block.ON:
                    if blocks[0].move(motion):
                        blocks[1].mode = Block.ON
                elif blocks[1].mode == Block.ON:
                    if blocks[1].move(motion):
                        blocks[0].mode = Block.ON
                else:
                    raise Exception('At least one block needs to be turned on')
            else:
                if label == 'UP':
                    blocks[1].mode = Block.ON
                    blocks[0].mode = Block.OFF
                elif label == 'DOWN':
                    blocks[1].mode = Block.OFF
                    blocks[0].mode = Block.ON
        else:
            block = next(b for b in blocks if b)
            block.move(motion)

    def next_frame(self, pixels, now):
        return


class Blink(object):
    def __init__(self, delay):
        self.item = (0, 1);
        self.idx = 0
        self.next_update = 0
        self.delay = delay

    def update(self, now):
        if now > self.next_update:
            self.next_update = now + self.delay
            self.idx = (self.idx + 1) % len(self.item)
        return self.item[self.idx]


class BlinkCount(object):
    """Blinks `count` times and then stops"""
    def __init__(self, blink, count):
        self.blink = blink
        self.target_count = 2*count
        self.current = None
        self.current_count = 0

    def update(self, now):
        blink = self.blink.update(now)
        if self.current is None:
            self.current = blink
            return blink
        elif self.current != blink:
            self.current_count += 1
            self.current = blink
            if self.current_count >= self.target_count:
                return None
            else:
                return blink
        else:
            return blink


class Block(GridItem):
    ON = 0
    OFF = 1

    def __init__(self, blink, mode, color, *args, **kwargs):
        GridItem.__init__(self, *args, **kwargs)
        self.blink = blink
        self.mode = mode
        self.color = color
        # set when this block is at the target
        self.target_blink = None

    def move(self, motion):
        assert self.mode == Block.ON
        location = translations.move(
            self.location, motion, (N_ROWS - 1, N_STATIONS), (True, False))
        if (location == self.location).all():
            logger.debug('Move failed; new location is the same as the old location')
            return False
        if self.grid.get_block(location[0], location[1]):
            logger.debug('Move failed; there is already a block at the new location')
            return False
        self.grid.remove(self.row, self.station, self)
        self.location = location
        self.grid.add(self.row, self.station, self)
        other_block = self.grid.get_block(other_row(self.row), self.station)
        if other_block and other_block.mode == Block.ON:
            self.mode = Block.OFF
        # see if we moved into the target
        target = self.grid.get_target(location[0], location[1])
        if target:
            self.target_blink = target.on_hit(self)
        return True

    def next_frame(self, pixels, now):
        if self._handle_target_blink(pixels, now):
            return
        if self.mode == Block.OFF:
            station = STATE.layout.STATIONS[self.station]
            pixels[self.row, station.left + 1:station.right - 1] = self.color
        else:
            self._handle_blink(self.blink.update(now), pixels)

    def _handle_target_blink(self, pixels, now):
        if self.target_blink:
            blink_value = self.target_blink.update(now)
            if blink_value is None:
                self.target_blink = None
                return False
            else:
                self._handle_blink(blink_value, pixels)
                return True
        else:
            return False

    def _handle_blink(self, value, pixels):
        station = STATE.layout.STATIONS[self.station]
        if value:
            pixels[self.row, station.left + 1:station.right - 1] = self.color
        else:
            pixels[self.row, station.left + 1:station.right - 1] = 0


def other_row(row):
    return (row + 1) % 2


SCENES = [
    af.Scene(
        'arrange-blocks',
        tags=[af.Scene.TAG_GAME],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[ArrangeBlocks(Grid.make())])
]
