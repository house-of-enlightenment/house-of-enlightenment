import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe.state import STATE
from hoe import translations

N_ROWS = 2
N_STATIONS = 6

UP = translations.UP
DOWN = translations.DOWN
LEFT = translations.LEFT
RIGHT = translations.RIGHT


# Currently, moves a single "block" to whoever last pressed a button
class ArrangeBlocks(af.Effect):
    def __init__(self, grid):
        self.blocks = [Block((255, 0, 0), np.array((0, 0)), grid)]
        self.selectors = [Selector(i, grid) for i in range(N_STATIONS)]

    def scene_starting(self, now, osc_data):
        pass

    def next_frame(self, pixels, now, collab, osc):
        for i, station in enumerate(osc.stations):
            if station.contains_change:
                print i, station.button_presses
                # TODO: don't set the station manually!
                self.blocks[0].location[1] = i
        for block in self.blocks:
            block.next_frame(pixels, now)
        for selector in self.selectors:
            selector.next_frame(pixels, now)


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


class Selector(object):
    ON = 0
    OFF = 1

    def __init__(self, station, grid):
        self.station = station
        self.row = 0
        self.mode = Selector.OFF
        self.grid = grid
        self.grid.add(self.row, self.station, self)

    def move(self, motion):
        row, col = motion
        if col != 0:
            return
        # It is impossible for there to be a conflict
        self.grid.remove(self.row, self.station, self)
        self.row = np.clip(self.row + row, 0, N_ROWS)
        self.grid.add(self.row, self.station, self)

    def toggle(self):
        self.mode = (self.mode + 1) % 2

    def next_frame(self, pixels, now):
        station = STATE.layout.STATIONS[self.station]
        left = station.left + 1
        right = station.right - 1
        pixels[self.row, [left, right]] = (255, 255, 255)


class Block(object):
    def __init__(self, color, location, grid):
        self.color = color
        # the second item is 0 for bottom, 1 for top
        # first item in location is an in 0-6, representing the station
        self.location = location
        self.grid = grid
        self.grid.add(self.row, self.station, self)

    @property
    def row(self):
        return self.location[0]

    @property
    def station(self):
        return self.location[1]

    def move(self, motion):
        location = translations.move(self.location, motion, (N_ROWS, N_STATIONS), (True, False))
        if self.grid.has_instance(location[0], location[1], Selector):
            return
        self.grid.remove(self.row, self.station, self)
        self.location = location
        self.grid.add(self.row, self.station, self)

    def next_frame(self, pixels, now):
        station = STATE.layout.STATIONS[self.station]
        pixels[self.row, station.left:station.right] = self.color


SCENES = [
    af.Scene(
        'arrange-blocks',
        tags=[af.Scene.TAG_GAME],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[ArrangeBlocks(Grid.make())])
]
