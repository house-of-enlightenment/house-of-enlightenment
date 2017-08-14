import numpy as np


class Pixels(object):
    def __init__(self, layout):
        self.layout = layout
        self.pixels = allocate_pixel_array(layout)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            idx = self.layout.grid[key]
            return self.pixels[idx]
        else:
            return self.pixels[key]

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            idx = self.layout.grid[key]
            self.pixels[idx] = value
        else:
            self.pixels[key] = value

    def __len__(self):
        return len(self.pixels)

    def put(self, client):
        # print_avg_brightness(self.pixels)
        client.put_pixels(self.pixels)

    def update(self, slices, additive, color):
        for r, c in slices:
            if additive:
                self[r, c] += color
            else:
                self[r, c] = color


def print_avg_brightness(pixels):
    # Generally looks ugly if there are massive changes in brightness
    # on the structure. Can be useful to print this out if you're
    # worried about changes like that
    #
    # percieved luminance: https://stackoverflow.com/a/596243/2752242
    print 'Bright:', pixels.dot([.299, .587, .114]).mean()


def allocate_pixel_array(layout):
    return np.zeros((len(layout.pixels), 3), np.uint8)
