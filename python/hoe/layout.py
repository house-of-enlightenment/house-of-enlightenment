import collections
import json

import numpy as np

_GROUPBY = [
    "address",
    "row",
    "section",
    "slice",
    "strip",
    "stripIndex",
    "topOrBottom",
]


class Layout(object):
    def __init__(self, pixels, rows=216, columns=66):
        self.pixels = pixels
        self.rows = rows
        self.columns = columns
        # for example, layout.row[0] will return a list of pixels in row 0.
        self.grid = np.zeros((rows, columns), np.int)

        for attr in _GROUPBY:
            setattr(self, attr, collections.defaultdict(list))

        for i, pixel in enumerate(self.pixels):
            self.grid[pixel['row'], pixel['slice']] = i
            for attr in _GROUPBY:
                getattr(self, attr)[pixel[attr]].append(i)

        for attr in _GROUPBY:
            setattr(self, attr, {k: v for k, v in getattr(self, attr).items()})
