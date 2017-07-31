"""Creates an effect that feels like a rainbow
flowing and twisting up the House of Enlightenment
"""

from __future__ import division
import argparse
import json
import math
import Queue
import random
import sys
import time

import numpy as np

from hoe import color_utils
from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import pixels


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


def main():
    global ROTATION_SPEED
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--row', choices=['sine', 'single', 'fader', 'rainbow', 'linear'], default='rainbow')
    args = parser.parse_args()

    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    osc_queue = Queue.Queue()
    server = osc_utils.create_osc_server()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/input/fader", lambda *args: osc_queue.put(args[2][-1]))
    if args.row == 'single':
        row = SingleColumn(hoe_layout)
    elif args.row == 'rainbow':
        row = RainbowRow(hoe_layout)
    elif args.row == 'fader':
        row = FaderRow(hoe_layout, osc_queue)
    elif args.row == 'sine':
        row = SineRow(hoe_layout)
    elif args.row == 'linear':
        row = LinearBrightness(hoe_layout)
    effect = UpAndRotateEffect(hoe_layout, row)
    #effect = UpAndExpandEffect(hoe_layout)
    render = Render(client, osc_queue, hoe_layout, [effect])
    render.run_forever()


class Render(object):
    def __init__(self, opc_client, osc_queue, hoe_layout, effects):
        self.client = opc_client
        self.queue = osc_queue
        self.layout = hoe_layout
        self.fps = 30
        self.effects = effects
        self.frame_count = 0

    def run_forever(self):
        now = time.time()
        for effect in self.effects:
            effect.start(now)
        self.pixels = pixels.Pixels(self.layout)
        while True:
            now = time.time()
            self.pixels[:] = 0
            for effect in self.effects:
                effect.next_frame(now, self.pixels)
            self.pixels.put(self.client)
            self.sleep_until_next_frame(now)

    def sleep_until_next_frame(self, now):
        self.frame_count += 1
        frame_took = time.time() - now
        remaining_until_next_frame = (1 / self.fps) - frame_took
        if remaining_until_next_frame > 0:
            print time.time(), self.frame_count, '{:0.2f}%'.format(frame_took * self.fps * 100), \
                frame_took, remaining_until_next_frame
            time.sleep(remaining_until_next_frame)
        else:
            print "!! Behind !!", remaining_until_next_frame


class UpAndRotateEffect(object):
    def __init__(self, layout, row):
        self.layout = layout
        self.up_speed = SpeedToPixels(100)  # rows / second
        # is this redundant with the bottom row also rotating?
        self.rotate_speed = SpeedToPixels(50)  # columns / second
        self.row = row

    def start(self, now):
        self.last_time = now
        self.row.start(now)
        self.up_speed.start(now)
        self.rotate_speed.start(now)
        # need my own copy of pixels
        self.pixels = pixels.Pixels(self.layout)

    def next_frame(self, now, pixels):
        pixels_up = self.up_speed(now)
        pixels_rotate = self.rotate_speed(now)
        rainbow = self.row(now)
        # copy to the first few rows
        # TODO: can I do this not in a loop?
        for i in range(pixels_up):
            self.pixels[10 + i, :] = rainbow
        # copy everything else up and rotate
        self.up_and_rotate(pixels_up, pixels_rotate)
        pixels[:] = self.pixels[:]

    def up_and_rotate(self, up, rotate):
        if up == 0 and rotate == 0:
            return
        if up == 0:
            before_idx = self.layout.grid[10:, :]
        else:
            before_idx = self.layout.grid[10:-up, :]
        if rotate == 0:
            after_idx = self.layout.grid[10 + up:, :]
        else:
            a = self.layout.grid[10 + up:, rotate:]
            b = self.layout.grid[10 + up:, :rotate]
            after_idx = np.concatenate((a, b), axis=1)
        self.pixels[after_idx] = self.pixels[before_idx]


class UpAndExpandEffect(object):
    def __init__(self, layout):
        self.layout = layout
        self.count = 0
        # track a color and width
        self.center = 40
        self.color = np.zeros((216, 3), np.uint8)
        self.width = np.zeros(216, np.float)
        self.speed = SpeedToPixels(50)

    def start(self, now):
        self.speed.start(now)
        self.color[0] = (255, 0, 0)
        self.width[0] = 1
        self.clr = 0

    def next_frame(self, now, pixels):
        # This has a jitter to it at the edges. I think its a result of
        # the way I am mapping speed to pxs.
        for row, (color, width) in enumerate(zip(self.color, self.width)):
            width = int(width)
            if (2 * width) + 1 > self.layout.columns:
                pixels[row, :] = color
                continue
            start = (self.center - width) % self.layout.columns
            end = (self.center + width + 1) % self.layout.columns
            if start < end:
                pixels[row, start:end] = color
            else:
                pixels[row, start:] = color
                pixels[row, :end] = color
        px = self.speed(now)
        if px > 0:
            self.color[px:] = self.color[:-px]
            self.color[:px] = (self.clr, 0, 0)
            self.clr = color_utils.remap(np.sin(2*np.pi*time.time()), -1, 1, 0, 255)
            self.width[px:] = self.width[:-px] + .25
            self.width[px] = 1


# Here are two modes for calculating distance. The accurate method
# allows for a variable number of pixels per frame, so if you want
# to travel 100 pixels in a second, it will. This method also keeps
# a consistent speed regardless of the frame rate
#
# The consistent method only allows for movements in a fixed amount.
# That means that if you want to move 100 pixels a second at 30fps,
# you'll actually end up going 3pixels / frame or 90 pixels per second.
#
# The accurate method can cause a flicker.
def consistent_speed_to_pixels(speed, fps):
    # only one of these will have a value, depending
    # on whether we move fast or slow
    frames_per_pixel = fps // speed
    pixels_per_framae = speed // fps
    assert not (frames_per_pixel and pixels_per_frame)
    if frames_per_pixel:
        return FramesPerPixel(frames_per_pixel)
    else:
        return PixelsPerFrame(pixels_per_frame)


class FramesPerPixel(object):
    def __init__(self, frames_per_pixel):
        self.frames_per_pixel = self.frames_per_pixel
        self.count = 0

    def start(self, now):
        pass

    def __call__(self, now):
        self.count += 1
        if self.count >= self.frames_per_pixel:
            self.count = 0
            return 1


class PixelsPerFrame(object):
    def __init__(self, pixels_per_frame):
        self.pixels_per_frame = pixels_per_frame

    def start(self, now):
        pass

    def __call__(self, now):
        return self.pixels_per_frame


class AccurateSpeedToPixels(object):
    def __init__(self, speed):
        self.speed = speed
        self.residual = 0

    def start(self, now):
        self.last_time = now

    def __call__(self, now):
        elapsed = now - self.last_time
        self.last_time = now
        distance = self.speed * elapsed + self.residual
        px, self.residual = divmod(distance, 1)
        return int(px)


class _Row(object):
    def __init__(self, layout):
        self.layout = layout

    def start(self, now):
        pass

    def __call__(self, now):
        return np.zeros((self.layout.columns, 3), np.uint8)


class SineRow(_Row):
    def __call__(self, now):
        v = np.sin(np.pi*now)
        val = color_utils.remap(v, -1, 1, 0, 255)
        color = color_utils.hsv2rgb((0, 255, val))
        color = (val, 0, 0)
        return np.array([color]*self.layout.columns)


# Perception of LED brightness is not linear. This applies a correction
# so that we get approximately 32 equal steps of brightness
#
# Lookup table from:
# https://ledshield.wordpress.com/2012/11/13/led-brightness-to-your-eye-gamma-correction-no/
#
BRIGHTNESS_A = [
    0, 1, 2, 3, 4, 5, 7, 9, 12, 15, 18, 22, 27, 32, 38, 44, 51, 58,
    67, 76, 86, 96, 108, 120, 134, 148, 163, 180, 197, 216, 235, 255
]

# Using this, as a comparison
#
BRIGHTNESS_B = np.linspace(0, 255, 32).astype(int)


class LinearBrightness(_Row):
    def start(self, now):
        self.idx = 0
        self.delta = 1

    def __call__(self, now):
        v = np.sin(np.pi*now)
        c = color_utils.remap(v, -1, 1, 0, 31)
        color_a = (BRIGHTNESS_A[int(c)], 0, 0)
        color_b = (0, BRIGHTNESS_B[int(c)], 0)
        color_a = (BRIGHTNESS_A[self.idx], 0, 0)
        color_b = (0, BRIGHTNESS_B[self.idx], 0)
        self.idx += self.delta
        if self.idx == 0 or self.idx == 31:
            self.delta *= -1
        n = int(self.layout.columns / 4)
        return np.array(
            [color_a] * n + [(0, 0, 0)] * (n + 1) +
            [color_b] * n + [(0, 0, 0)] * (n + 1))


class FaderRow(object):
    """A row that has its color controlled by a slider / fader"""

    def __init__(self, layout, queue):
        self.layout = layout
        self.rotate = Rotate(self.layout.columns)
        # osc messages go here.
        self.queue = queue
        self.color = np.array((255, 255, 255))  # RED in HSV

    def start(self, now):
        self.rotate.start(now)

    def __call__(self, now):
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


class RainbowRow(object):
    """Creates a row that is an arc in the HSV color space.

    Each update gradually shifts the original arc towards another
    arc. Once that is hit, another random arc is choosen and we
    continue the process.  Additionally the row is rotated.

    The speed of the transitions and rotations vary randomly.
    """

    def __init__(self, layout):
        self.layout = layout
        self.rotate = Rotate(self.layout.columns)

    def start(self, now):
        self.rotate.start(now)
        self.sv = SVTransition(now)
        self.hue = HueTransition(now)

    def __call__(self, now):
        rainbow = self.get_rainbow(now)
        return self.rotate(rainbow, now)

    def get_rainbow(self, now):
        hue = self.hue.update(now)
        sat, val = self.sv.update(now)
        # mirror the hues so that we don't get any sharp edges
        return np.concatenate(
            (color_utils.rainbow(self.layout.columns / 2, hue[0], hue[1], sat, val),
             color_utils.rainbow(self.layout.columns / 2, hue[1], hue[0], sat, val)))


class SingleColumn(object):
    """Creates a row that is just one red pixel.

    Can be useful to see how the shape flows up the HoE.
    """

    def __init__(self, layout):
        self.layout = layout
        self.rotate = Rotate(layout.columns)

    def start(self, now):
        self.rotate.start(now)

    def __call__(self, now):
        row = np.zeros((self.layout.columns, 3), np.uint8)
        row[10, :] = (255, 0, 0)
        return self.rotate(row, now)


class Rotate(object):
    def __init__(self, n):
        self.rotation = 0
        self.n = n

    def start(self, now):
        self.last_time = now
        self.rotation_speed = SpeedTransition(now)

    def __call__(self, arr, now):
        # vary the rotation speed
        delta = (now - self.last_time) * self.rotation_speed.update(now)
        self.last_time = now
        self.rotation = (self.rotation + delta) % self.n
        # using negative rotation here seems to be less impressive
        # I think its because it matches with the rotation of
        # the entire structure.
        return rotate(arr, int(self.rotation))


# idx can be negative
def rotate(arr, idx):
    if idx == 0:
        return arr
    else:
        return np.concatenate((arr[idx:], arr[:idx]))


class Transition(object):
    def __init__(self, now):
        self.end = self.rnd_pt()
        self._reset(now)

    def update(self, now):
        self.reset_if_needed(now)
        delta = (self.end - self.start) * (now - self.start_time) / self.length
        return self.start + delta

    def reset_if_needed(self, now):
        elapsed = now - self.start_time
        if elapsed > self.length:
            self._reset(now)

    def _reset(self, now):
        self.start = self.end
        self.end = self.rnd_pt()
        self.length = self.transition_period()
        self.start_time = now

    def transition_period(self):
        return np.random.rand() * 3 + 1

    def rnd_pt(self):
        pass


class SpeedTransition(Transition):
    """Every `delay` seconds, pick a new random value"""

    def rnd_pt(self):
        return np.random.randint(5, 55)


class SVTransition(Transition):
    """Transition from one plane in Saturation-Value space to another"""

    def rnd_pt(self):
        # pick a saturation between 128-256 (128 is very pastel, 256 is full saturation)
        # pick a value between 192-256 (probably a very minor effect)
        return np.array([np.random.randint(128, 256), np.random.randint(196, 256)])


class HueTransition(Transition):
    def rnd_pt(self):
        # pick a hue to start with
        start = np.random.randint(0, 256)
        # pick how much of the color wheel we're going to take
        # a longer slice will have more colors
        length = np.random.randint(32, 35)
        end = start + length
        return np.array([start, end])

    def update(self, now):
        # for hues, there are two ways that the transition can go, clockwise
        # and counterclockwise.
        # This is always going clockwise
        #
        # TODO: on reset, pick a direction
        return super(HueTransition, self).update(now)


if __name__ == '__main__':
    sys.exit(main())
