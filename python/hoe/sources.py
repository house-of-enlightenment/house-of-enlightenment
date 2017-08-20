import numpy as np

from hoe import color_utils
from hoe import translations
from hoe import transitions


class _Row(object):
    def __init__(self, layout):
        self.layout = layout

    def start(self, now):
        pass

    def __call__(self, now, **kwargs):
        return np.zeros((self.layout.columns, 3), np.uint8)


class SineRow(_Row):
    def __call__(self, now, **kwargs):
        v = np.sin(np.pi * now)
        val = color_utils.remap(v, -1, 1, 0, 255)
        color = color_utils.hsv2rgb((0, 255, val))
        color = (val, 0, 0)
        return np.array([color] * self.layout.columns)


BRIGHTNESS_B = np.linspace(0, 255, 32).astype(int)


class LinearBrightness(_Row):
    # used to compare the difference between a linear brightness
    # adjustment and not making one
    #
    # The Red color has the linear adjustment
    # The Green color does not
    def start(self, now):
        self.idx = 0
        self.delta = 1

    def __call__(self, now, **kwargs):
        v = np.sin(np.pi * now)
        c = color_utils.remap(v, -1, 1, 0, 31)
        color_a = (color_utils.linear_brightness(c), 0, 0)
        color_b = (0, BRIGHTNESS_B[int(c)], 0)
        color_a = (color_utils.linear_brightness(self.idx), 0, 0)
        color_b = (0, BRIGHTNESS_B[self.idx], 0)
        self.idx += self.delta
        if self.idx == 0 or self.idx == 31:
            self.delta *= -1
        n = int(self.layout.columns / 4)
        return np.array([color_a] * n + [(0, 0, 0)] * (n + 1) + [color_b] * n + [(0, 0, 0)] *
                        (n + 1))


# This doesn't fit within the framework right now, the osc
# messages should be processed by the framework instead of
# using the queue
class FaderRow(_Row):
    """A row that has its color controlled by a slider / fader"""

    def __init__(self, layout, queue):
        self.layout = layout
        self.rotate = translations.Rotate(self.layout.columns)
        # osc messages go here.
        self.queue = queue
        self.color = np.array((255, 255, 255))  # RED in HSV

    def start(self, now):
        self.rotate.start(now)

    def __call__(self, now, **kwargs):
        self.update_color()
        row = np.zeros((self.layout.columns, 3), np.uint8)
        row[10, :] = color_utils.hsv2rgb(self.color)
        return self.rotate(row, now)

    def update_color(self):
        value = None
        # this feels like a hacky way to drain the queue and only
        # get the last entry
        try:
            while True:
                value = self.queue.get_nowait()
        except:
            if value is not None:
                self.color = np.array((value * 255 / 100, 255, 255))


class RainbowRow(_Row):
    """Creates a row that is an arc in the HSV color space.

    Each update gradually shifts the original arc towards another
    arc. Once that is hit, another random arc is choosen and we
    continue the process. Additionally the row is rotated.

    The speed of the transitions and rotations vary randomly.
    """

    # TODO: the roation seems like it could be a layer ontop of this
    #       and not coupled with the row
    def __init__(self, layout, rotate=None, sv=None, hue=None):
        self.layout = layout
        self.rotate = rotate or translations.Rotate(self.layout.columns)
        self.sv = sv or transitions.SVTransition()
        self.hue = hue or transitions.HueTransition()

    def start(self, now):
        self.rotate.start(now)
        self.sv.start(now)
        self.hue.start(now)

    def __call__(self, now, **kwargs):
        rainbow = self.get_rainbow(now)
        return self.rotate(rainbow, now)

    def get_rainbow(self, now):
        hue = self.hue.update(now)
        sat, val = self.sv.update(now)
        # mirror the hues so that we don't get any sharp edges
        return color_utils.bi_rainbow(self.layout.columns, hue[0], hue[1], sat, val)


class ComplimentaryRow(_Row):
    # Returns a row where we have the target color
    # and a transition to its compliment (hue + 128)
    def __init__(self, size, hue, frac, min_gray=128):
        self.size = size
        self.hue = hue
        self.frac = frac
        self.min_gray = min_gray

    def start(self, now):
        self.hue.start(now)

    def __call__(self, now, **kwargs):
        hue = self.hue.update(now)

        primary = int(self.size / 2 * self.frac)
        compliment = self.size / 2- primary
        pixels = np.zeros((self.size / 2, 3), np.uint8)

        pixels[:primary, 0] = hue
        steps = color_utils.color_correct(
            np.linspace(255, self.min_gray, primary, dtype=np.uint8))
        pixels[:primary, 1] = steps
        pixels[:primary, 2] = steps

        pixels[primary:, 0] = hue + 128
        steps = color_utils.color_correct(
            np.linspace(self.min_gray, 255, compliment, dtype=np.uint8))
        pixels[primary:, 1] = steps
        pixels[primary:, 2] = steps
        pixels = color_utils.hsv2rgb(pixels)
        return np.concatenate((pixels, pixels[::-1]))


class ConstantRow(_Row):
    def __init__(self, layout, pixel):
        _Row.__init__(self, layout)
        self.pixel = pixel

    def __call__(self, now, **kwargs):
        return np.full((self.layout.columns, 3), self.pixel)


class SwapRow(_Row):
    def __init__(self, rows, times):
        self.rows = rows
        self.times = times
        self.idx = 0
        self.until = None

    def start(self, now):
        self.rows[self.idx].start(now)
        time = self.times[self.idx]
        self.until = now + self.times[self.idx]()

    def __call__(self, now, **kwargs):
        if now > self.until:
            self.idx = (self.idx + 1) % len(self.rows)
            self.start(now)
        return self.rows[self.idx](now)
