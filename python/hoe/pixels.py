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
        # print_avg_brightness(self.pixels)
        client.put_pixels(self.pixels)

    def update_slices(self, additive, color, slices):
        for r, c in slices:
            if additive:
                self[r, c] += color
            else:
                self[r, c] = color

    def update_pairwise(self, additive, color, pairwise):
        zipped = zip(*pairwise)
        if zipped:
            self.update_indicies(
                additive=additive, color=color, x_values=zipped[0], y_values=zipped[1])

    def update_indicies(self, additive, color, x_values, y_values):
        if additive:
            self[x_values, y_values] += color
        else:
            self[x_values, y_values] = color


def is_wrap_around_slice(sl):
    if sl.start is not None and sl.stop is not None:
        return sl.start > sl.stop
    else:
        return False


def print_avg_brightness(pixels):
    # Generally looks ugly if there are massive changes in brightness
    # on the structure. Can be useful to print this out if you're
    # worried about changes like that
    #
    # percieved luminance: https://stackoverflow.com/a/596243/2752242
    print 'Bright:', pixels.dot([.299, .587, .114]).mean()


def allocate_pixel_array(layout):
    return np.zeros((len(layout.pixels), 3), np.uint8)


def DROP(x, max_val):
    if x >= 0 and x < max_val:
        return x
    else:
        return None


def WRAP(x, max_val):
    return x % max_val


def IGNORE(x, max_val):
    return x


def cleanup_pairwise_indicies(indices, row_mode=DROP, col_mode=WRAP, row_max=216, col_max=66):
    return filter(
        lambda x: x[0] is not None and x[1] is not None,
        map(lambda x: (row_mode(x=x[0], max_val=row_max), col_mode(x[1], max_val=col_max)),
            indices))
