import numpy as np


class Pixels(object):
    def __init__(self, layout):
        self.layout = layout
        self.pixels = np.zeros((len(self.layout.pixels), 3), np.uint8)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            idx = self.layout.grid[key]
            return self.pixels[idx]
        else:
            return self.pixels[key]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            print key
            # TODO: deal with wrap-around slices
            #       for the columns
            # r, c = key
            # if isinstance(c, slice):
            #     if is_wrap_around_slice(c):
            idx = self.layout.grid[key]
            self.pixels[idx] = value
        else:
            self.pixels[key] = value

    def __len__(self):
        return len(self.pixels)

    def put(self, client):
        client.put_pixels(self.pixels)


def is_wrap_around_slice(sl):
    if sl.start is not None and sl.stop is not None:
        return sl.start > sl.stop
    else:
        return False
