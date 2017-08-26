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
# pass to get something, anything, working that resembled a game.
#
# Particularly gross is the mechanism by which the block and target
# do a fast blink when a block moves into a target.
#
import collections
import itertools
import logging
import random

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import color_utils
from hoe.state import STATE
from hoe import translations
from hoe import transitions

import shared

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

EASY = 6
MEDIUM = 8
HARD = 10


def shuffle_locations(mode='all'):
    if mode == 'all':
        l = list(itertools.product(range(N_ROWS), range(N_STATIONS)))
        random.shuffle(l)
        return l
    elif mode == 'by_row':
        result = []
        for row in range(N_ROWS):
            l = list(itertools.product([row], range(N_STATIONS)))
            random.shuffle(l)
            result.extend(l)
        return result


def get_color(i, n=6):
    # at the hard level, there are two greens that look nearly identical
    # but I wasn't able to find alternative color choices that are any better
    # I tried the 10 color qualitative colormap from
    # http://colorbrewer2.org/#type=qualitative&scheme=Paired&n=10
    # but the light colors all looked the same on the simulator
    i = i % n
    return color_utils.hsv2rgb((i * 255 / n, 255, 255))


class ArrangeBlocks(collaboration.CollaborationManager, af.Effect):
    def __init__(self, grid):
        # share a common blink so that they all blink at the same time
        self.grid = grid
        blink = Blink(0.5)
        fast_blink = Blink(0.125)
        # TODO: how to make this change?
        #       Maybe ask the user to push one of top, middle, bottom
        n_blocks = EASY
        colors = [get_color(i, n_blocks) for i in range(n_blocks)]
        locations = shuffle_locations('by_row')
        self.targets = [Target(fast_blink, c, l, grid) for c, l in zip(colors, locations)]
        self.blocks = [Block(blink, Block.OFF, t.color, t, t.location, grid) for t in self.targets]
        self.station_handlers = [StationHandler(i, grid) for i in range(N_STATIONS)]
        self.needs_shuffle = True
        self.we_won = False

    def shuffle(self, pixels, now):
        self.needs_shuffle = False
        # a nicer shuffle would show the players the target blocks
        # and then move them (quickly) to the shuffle starting positions
        for block in self.blocks:
            self.grid.remove(block.row, block.station_id, block)
            block.mode = Block.OFF
        open_cells = shuffle_locations()
        for cell, block in zip(open_cells, self.blocks):
            self.grid.add(cell[0], cell[1], block)
            block.location = cell
        if self.did_we_win():
            # crap, that was a terrible shuffle
            self.shuffle(pixels, now)
        else:
            for station_id in range(N_STATIONS):
                blocks = self.grid.get_blocks(station_id)
                block = next((b for b in blocks if b), None)
                if block:
                    block.mode = Block.ON

    def scene_starting(self, now, osc_data):
        pass

    def compute_state(self, now, old_state, osc):
        state = {}
        block_scores = collections.defaultdict(list)
        total = 0
        n_blocks = len(self.blocks)
        for b in self.blocks:
            at_target = 100.0 / n_blocks if b.at_target() else 0
            block_scores[b.station_id].append(at_target)
            total += at_target
        for i, targets in block_scores.items():
            state[i] = int(np.mean(targets))
        state['total'] = int(total)

    def next_frame(self, pixels, now, collab, osc):
        if self.needs_shuffle:
            self.shuffle(pixels, now)
        if self.we_won:
            self.draw(pixels, now)
            pixels[:2, :] = self.rotate(pixels[:2, :], now)
            # TODO: how do I tell the framework that I'm done?
        else:
            self._continue_playing(pixels, now, collab, osc)

    def _continue_playing(self, pixels, now, collab, osc):
        # each station has one, and only one, handler
        # if we get a key press we pass it along to the handler
        # and it will deal with moving blocks
        for station_id, buttons in osc.buttons.items():
            if not buttons:
                continue
            station_handler = self.station_handlers[station_id]
            station_handler.handle_button_presses(buttons)
        if self.did_we_win():
            self.on_winning(now)
        self.draw(pixels, now)

    def draw(self, pixels, now):
        for block in self.blocks:
            block.next_frame(pixels, now)
        for target in self.targets:
            target.next_frame(pixels, now)

    def on_winning(self, now):
        for block in self.blocks:
            block.led_override = On()
        for target in self.targets:
            target.led_override = On()
        self.we_won = True
        self.rotate = translations.Rotate(STATE.layout.columns,
                                          transitions.ConstantTransition(
                                              STATE.layout.columns / 2)).start(now)

    def did_we_win(self):
        return all(b.at_target() for b in self.blocks)


class On(object):
    """led_override to keep an item on"""

    def update(self, now):
        return 1


class Grid(object):
    """Keeps track of where items are.

    Items are responsible for letting the grid know where they are.
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

    def __init__(self, location, grid):
        # the second item is 0 for bottom, 1 for top
        # first item in location is an in 0-6, representing the station
        # convert to a list because it needs to be mutable
        self.location = np.array(location)
        self.grid = grid
        self.grid.add(self.row, self.station_id, self)

    def _get_row(self):
        return self.location[0]

    def _set_row(self, val):
        self.location[0] = val

    row = property(_get_row, _set_row)

    def _get_station_id(self):
        return self.location[1]

    def _set_station_id(self, val):
        self.location[1] = val

    station_id = property(_get_station_id, _set_station_id)

    def get_block(self):
        return self.grid.get_block(self.row, self.station_id)


class OnOffOverride(object):
    def __init__(self):
        self.led_override = None

    def next_frame(self, pixels, now):
        if self._handle_led_override(pixels, now):
            return
        self._next_frame(pixels, now)

    def _handle_led_override(self, pixels, now):
        if not self.led_override:
            return False
        blink_value = self.led_override.update(now)
        if blink_value is None:
            self.led_override = None
            return False
        else:
            self._handle_blink(blink_value, pixels)
            return True

    def _handle_blink(self, is_on, pixels):
        if is_on:
            self._leds_on(pixels)
        else:
            self._leds_off(pixels)

    def _next_frame(self, pixels, now):
        pass

    def _leds_on(self, pixels):
        pass

    def _leds_off(self, pixels):
        pass


class Target(GridItem, OnOffOverride):
    """Indicates where a block is supposed to end up.

    Each target colors the two outside pixels of each cell.

    Each time a block moves, it checks the target in that cell and if
    it is a hit, the target and block blink quickly for a bit.
    """

    def __init__(self, blink, color, location, grid):
        GridItem.__init__(self, location, grid)
        OnOffOverride.__init__(self)
        self.color = color
        self.blink = blink

    def on_hit(self, block):
        assert are_same_color(self, block)
        logger.debug('Block succesfully moved into the target')
        self.led_override = BlinkCount(self.blink, 6)
        block.led_override = self.led_override

    def _next_frame(self, pixels, now):
        self._leds_on(pixels)

    def get_station(self):
        return STATE.layout.STATIONS[self.station_id]

    def _leds_on(self, pixels):
        station = self.get_station()
        pixels[self.row, [station.left, station.right - 1]] = self.color

    def _leds_off(self, pixels):
        station = self.get_station()
        pixels[self.row, [station.left, station.right - 1]] = 0


def are_same_color(a, b):
    return (a.color == b.color).all()


class StationHandler(object):
    def __init__(self, station_id, grid):
        self.station_id = station_id
        self.grid = grid

    def handle_button_presses(self, button_presses):
        # if you mash keys, we're just taking the first one
        # From Dave: this may not be ordered and we're talking micro-second order, so just taking one randomly with pop
        for button_press in button_presses:
            break
        logger.debug('For station %s, button %s was pressed', self.station_id, button_press)
        label = LABEL[button_press]
        if label == 'MIDDLE':
            return
        motion = MOVEMENTS[button_press]
        blocks = self.grid.get_blocks(self.station_id)
        if not blocks[0] and not blocks[1]:
            logger.debug('No blocks in station %s', self.station_id)
            return
        if blocks[0] and blocks[1]:
            self._handle_two_blocks(blocks, label, motion)
        else:
            block = next(b for b in blocks if b)
            block.move(motion)

    def _handle_two_blocks(self, blocks, label, motion):
        logger.debug('There are two blocks in %s', self.station_id)
        assert not (blocks[0].mode == Block.ON and blocks[1].mode == Block.ON)
        if label == 'LEFT' or label == 'RIGHT':
            self._move_the_on_block(blocks, motion)
        else:
            self._change_the_on_block(blocks, label)

    def _move_the_on_block(self, blocks, motion):
        if blocks[0].mode == Block.ON:
            if blocks[0].move(motion):
                blocks[1].mode = Block.ON
        elif blocks[1].mode == Block.ON:
            if blocks[1].move(motion):
                blocks[0].mode = Block.ON
        else:
            raise Exception('At least one block needs to be turned on')

    def _change_the_on_block(self, blocks, label):
        if label == 'UP':
            blocks[1].mode = Block.ON
            blocks[0].mode = Block.OFF
        elif label == 'DOWN':
            blocks[1].mode = Block.OFF
            blocks[0].mode = Block.ON


class Blink(object):
    def __init__(self, delay):
        self.item = (0, 1)
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
        self.target_count = 2 * count
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


class Block(GridItem, OnOffOverride):
    ON = 0
    OFF = 1

    def __init__(self, blink, mode, color, target, location, grid):
        GridItem.__init__(self, location, grid)
        OnOffOverride.__init__(self)
        self.blink = blink
        self.mode = mode
        self.color = color
        self.target = target

    def at_target(self):
        return (self.target.location == self.location).all()

    def move(self, motion):
        assert self.mode == Block.ON
        was_at_target = self.at_target()
        location = translations.move(self.location, motion, (N_ROWS - 1, N_STATIONS), (True, False))
        if (location == self.location).all():
            logger.debug('Move failed; new location is the same as the old location')
            return False
        if self.grid.get_block(location[0], location[1]):
            logger.debug('Move failed; there is already a block at the new location')
            return False
        self.grid.remove(self.row, self.station_id, self)
        self.location = location
        self.grid.add(self.row, self.station_id, self)
        self._check_if_mode_should_be_turned_off()
        self._check_target_status(was_at_target)
        # see if we moved into the target
        return True

    def _check_if_mode_should_be_turned_off(self):
        other_block = self.grid.get_block(other_row(self.row), self.station_id)
        if other_block and other_block.mode == Block.ON:
            self.mode = Block.OFF

    def _check_target_status(self, was_at_target):
        if self.at_target():
            self.target.on_hit(self)
        elif was_at_target:
            logger.warning('We left the target, what should happen?')
            # TODO, somebody else should probably turn this off
            self.led_override = None

    def _next_frame(self, pixels, now):
        if self.mode == Block.OFF:
            self._leds_on(pixels)
        else:
            self._handle_blink(self.blink.update(now), pixels)

    def get_station(self):
        return STATE.layout.STATIONS[self.station_id]

    def _leds_on(self, pixels):
        station = self.get_station()
        pixels[self.row, station.left + 1:station.right - 1] = self.color

    def _leds_off(self, pixels):
        station = self.get_station()
        pixels[self.row, station.left + 1:station.right - 1] = 0


def other_row(row):
    return (row + 1) % 2


class TestKeyboardInputs(af.Effect):
    def __init__(self, effect, pause=0.5):
        # effect should be an effect and collaboration manager
        self.effect = effect
        self.pause = pause
        self.next_input = None

    def scene_starting(self, now, osc_data):
        self.next_input = now
        return self.effect.scene_starting(now, osc_data)

    def compute_state(self, now, old_state, osc):
        self.effect.compute_state(now, old_state, osc)

    def next_frame(self, pixels, now, collab, _):
        osc_data = af.OSCDataAccumulator()
        if now >= self.next_input:
            self.next_input = now + self.pause
            buttons = list(itertools.product(range(6), range(5)))
            pushed_buttons = random.sample(buttons, random.randrange(1, 5))
            for station, button in pushed_buttons:
                osc_data.button_pressed(station, button)
        self.effect.next_frame(pixels, now, collab, osc_data)


SCENES = [
    af.Game(
        'arrange-blocks',
        tags=[],
        collaboration_manager=ArrangeBlocks(Grid.make()),
        effects=[shared.BarelyGray()]
    ),
    af.Game(
        'arrange-blocks-debug',
        tags=[af.Scene.TAG_TEST],
        collaboration_manager=TestKeyboardInputs(ArrangeBlocks(Grid.make())),
        effects=[shared.BarelyGray()]
    )
]
