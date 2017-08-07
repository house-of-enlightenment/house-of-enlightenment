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
            idx = self.layout.grid[key]
            self.pixels[idx] = value
        else:
            self.pixels[key] = value

    def __len__(self):
        return len(self.pixels)

    def put(self, client):
        client.put_pixels(self.pixels)




def shift_slice(slice_, shift):
    helper = _ShiftSliceHelper(slice_, shift)
    return helper.calc()


class _ShiftSliceHelper(object):
    # this just deals with the simple, non-wrapping case.
    # Any slice that goes off the array just keeps the parts that are on
    # the array.
    def __init__(self, slice_, bounds):
        self.start = (slice_.start or 0) % bounds
        self.stop = bounds if slice_.stop is None else (slice_.stop % bounds)
        self.step = slice_.step
        self.bounds = bounds

    def calc(self, shift):
        if shift == 0:
            return slice(self.start, self.stop, None)
        if shift > 0:
            return self.shift_up(shift)
        else:
            return self.shift_down(-shift)

    def shift_up(self, shift):
        return [slice(self.start + shift, self.stop + shift, self.step)]

    def shift_down(self, shift):
        begin = max(0, self.start - shift)
        end = max(0, self.stop - shift)
        return [slice(begin, end, self.step)]


#
# TODO: this needs all of the testing
#
class _WrappingShiftSliceHelper(_ShiftSliceHelper):
    def __init__(self, slice_, bounds):
        # getting the steps right on the wrap-around requires more
        # work and I don't think we'll be using it, so not dealing
        # with that case yet.
        _ShiftSliceHelper.__init__(self, slice_)
        assert slice_.step is None, "Not ready to deal with steps yet"
        self.bounds = bounds

    def shift_up(self, shift):
        shift = shift % self.bounds
        if self.start is None and self.stop is None:
            # this is one example where a non-None step would be weird
            # if we had an array of length 10 and an original slice: (0,9,4)
            # that would grab indexes 0,4,8.
            # If we shift that 3, I would expect: 3, 7, 1.
            # But, this code would return 3,7,0
            return [
                slice(shift, None, self.step),
                slice(None, shift, self.step)
            ]
        elif self.start is None:
            end = self.stop + self.shift
            if end > self.bounds:
                return [
                    slice(shift, None, self.step),
                    slice(None, end - self.bounds, self.step),
                ]
        elif self.stop is None:
            length = self.bounds - self.start
            begin = self.start + shift
            if begin > self.bounds:
                begin = begin - self.bounds
                end = begin + length
                return [slice(begin, end, self.step)]
                # jerk
            else:
                return [
                    slice(begin, None, self.step),
                    slice(None, self.shift, self.step)
                ]
        else:
            begin = self.start + shift
            if begin > self.bounds:
                length = self.stop - self.start
                return [slice(begin, begin + length, self.step)]
            else:
                end = self.stop + shift
                if end > self.bounds:
                    return [
                        slice(begin, None, self.step),
                        slice(None, end - self.bounds, step)
                    ]
                else:
                    return [slice(begin, end, self.step)]

    def shift_down(self):
        if self.start is None and self.stop is None:
            return slice(None, -self.shift, self.step)
        elif self.start is None:
            end = self.stop - self.shift
            if end < 0:
                raise Exception('Shift is too large')
            else:
                return slice(None, end, self.step)
        elif self.stop is None:
            begin = max(0, self.start - self.shift)
            return slice(begin, -self.shift, self.step)
        else:
            begin = max(0, self.start - self.shift)
            return slice(begin, self.stop - self.shift, self.step)



# There are a few different shifts
# - simple shift
# - wrapping shift
#   - wrapping within a window
#


def translate(pixels, row_slice, column_slice, n_rows, n_columns):
    if n_row == 0 and rotate == 0:
        return pixels
    if n_row == 0:
        before_idx = pixels[row_slice, column_slice]
        
    before_idx = None
