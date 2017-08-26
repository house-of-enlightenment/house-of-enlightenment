from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from generic_effects import NoOpCollaborationManager
from hoe.state import STATE
from shared import SolidBackground
# from ripple import Ripple
import time
import numpy as np
from collections import deque
import colorsys


class RisingLine(Effect):
    """
    base effect that is used for all the launchers below
    """

    def __init__(self,
                 color=(255, 255, 0),
                 border_color=None,
                 border_thickness=0,
                 start_row=2,
                 start_col=16,
                 height=5,
                 delay=0,
                 ceil=STATE.layout.rows - 1):
        self.color = color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.start_row = start_row
        self.start_col = start_col
        self.height = height
        self.delay = delay  # ms
        self.ceil = ceil

        self.cur_top = self.start_row
        self.cur_bottom = self.start_row
        self.start_ms = time.time() * 1000

    def next_frame(self, pixels, now, collaboration_state, osc_data):

        # don't start until after the delay
        elapsed_ms = now * 1000 - self.start_ms
        if (elapsed_ms < self.delay):
            return

        self.cur_top = self.cur_top + 4
        self.cur_bottom = self.cur_top - self.height

        # min/max to make sure we don't render out of bounds
        bottom = max(self.cur_bottom, self.start_row)
        top = min(self.cur_top, STATE.layout.rows - 1)

        for y in range(bottom, top):
            pixels[y, self.start_col] = self.color

        if self.border_color:
            for y in range(0, self.border_thickness):
                pixels[bottom + y, self.start_col] = self.border_color
                pixels[top - y, self.start_col] = self.border_color

    def is_completed(self, t, osc_data):
        return self.cur_bottom >= self.ceil


class RomanCandleLauncher(MultiEffect):
    """
    Roman Candle - go from left to right and back
    """

    def __init__(self, start_col=16, end_col=24, color=(255, 0, 0)):

        forward_cols = range(start_col, end_col)
        backward_cols = forward_cols[::-1]  # reverse

        sequence = forward_cols + backward_cols

        #+ forward_cols + backward_cols

        # print "forward_cols", forward_cols
        # print "backward_cols", backward_cols
        # print "sequence", sequence

        def make_line((i, col)):
            return RisingLine(height=30, start_col=col, delay=i * 100, color=color)

        effects = map(make_line, enumerate(sequence))

        MultiEffect.__init__(self, *effects)


class AroundTheWorldLauncher(MultiEffect):
    """
    Arround the world launcher - shoot small lines all the way around the gazebo

    Define border_color and border_thickness to add a border.
    The border will be drawn *inside* the height, so make sure
    2*border_thickness < height
    """

    def __init__(self,
                 start_col=16,
                 color=(0, 255, 0),
                 border_color=(255, 0, 0),
                 border_thickness=3,
                 height=9,
                 reverse=True):

        # [0, ..., 65]
        all_cols = range(0, STATE.layout.columns)
        # [start_col, ..., 65, 0, ..., start_col - 1]
        shifted = np.roll(all_cols, -start_col)

        if reverse:
            shifted = shifted[::-1]  # reverse

        # print "start_col", start_col
        # print "shifted", shifted

        def make_line((i, col)):
            return RisingLine(
                height=height,
                start_col=col,
                delay=i * 30,
                color=color,
                border_color=border_color,
                border_thickness=border_thickness,
                ceil=50)

        effects = map(make_line, enumerate(shifted))

        MultiEffect.__init__(self, *effects)


class FZeroLauncher(MultiEffect):
    """
    F-Zero Launcher - make a f-zero speed boost arrow around the start_col
    """

    def __init__(self, start_col=16, color=(0, 255, 255)):

        # get 5 pixels to either side to select the 11 columns in this section
        section = range(start_col - 5, start_col + 5 + 1)

        # group them by levels to make an f-zero speed boost arrow
        levels = [[section[5]],
                  [section[4], section[6]],
                  [section[3], section[7]],
                  [section[2], section[8]],
                  [section[1], section[9]],
                  [section[0], section[10]]]


        def make_line((i, col)):

            # fade the colors on the edges
            def get_color():
                hsv = colorsys.rgb_to_hsv(color[0] // 255, color[1] // 255, color[2] // 255)
                rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2] - (i * 0.12))
                return (rgb[0] * 255, rgb[1] * 255, rgb[2] * 255)

            return RisingLine(height=50, start_col=col, delay=i * 80, color=get_color())

        effects = map(make_line, enumerate(levels))

        MultiEffect.__init__(self, *effects)


SCENES = [
    Scene(
        "roman-candle",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 RomanCandleLauncher(start_col=16)]),
    Scene(
        "around-the-world",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 AroundTheWorldLauncher(start_col=16)]),
    Scene(
        "f-zero",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 FZeroLauncher(start_col=16)]),
]
