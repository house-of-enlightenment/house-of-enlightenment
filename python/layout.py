import collections
import json


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
    def __init__(self, pixels):
        self.pixels = pixels
        # for example, layout.row[0] will return a list of pixels in row 0.
        for attr in _GROUPBY:
            setattr(self, attr, collections.defaultdict(list))
        for i, pixel in enumerate(self.pixels):
            for attr in _GROUPBY:
                getattr(self, attr)[pixel[attr]].append(i)
        # TODO: it might be useful to know the max rows and max columns
