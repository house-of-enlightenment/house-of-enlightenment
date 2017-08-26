from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.collaboration import CollaborationManager
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from random import choice
from random import randint
from random import getrandbits
from itertools import product
from math import ceil
from shared import SolidBackground
from generic_effects import NoOpCollaborationManager
from generic_effects import FrameRotator
from generic_effects import FunctionFrameRotator
import examples
import numpy as np
import debugging_effects
import hoe.osc_utils
from random import randint


class ButtonRainbow(Effect):
    def __init__(self,
                 bottom_row=2,
                 top_row=STATE.layout.rows,
                 hue_start=0,
                 hue_end=255,
                 saturation=255,
                 max_value=255):
        self.bottom_row = bottom_row
        self.top_row = top_row
        self.hue_start = hue_start
        self.hue_end = hue_end
        self.saturation = saturation
        self.max_value = max_value
        self.column_success = None
        self.frame = 0

    def scene_starting(self):
        self.column_success = color_utils.bi_rainbow(
            STATE.layout.columns,
            hue_start=self.hue_start,
            hue_end=self.hue_end,
            saturation=self.saturation,
            value=self.max_value)
        self.frame = 0

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame += 1

        # Do this each time so we avoid storing bases state
        column_bases = np.full(shape=(STATE.layout.columns, 3), fill_value=0, dtype=np.uint8)
        for s, b in collaboration_state["on"]:
            col = s * 11 + b * 2
            column_bases[col:col + 2 + b / 4] = self.column_success[col:col + 2 + b / 4]

        pixels[self.bottom_row:self.top_row, :] = column_bases


class Pulser(Effect):
    def __init__(self, pulse_length=10, bottom_row=2, top_row=None, after_fill=30):
        self.pulse_length = pulse_length
        self.bottom_row = bottom_row
        self.top_row = top_row if top_row else STATE.layout.rows
        self.after_fill = after_fill

        self.frame = 0

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame += 1
        for r in range(self.pulse_length):
            pixels[self.bottom_row + r:self.top_row:self.pulse_length, :] /= (
                (self.frame - r) % self.pulse_length) + 1
        pixels[self.bottom_row:self.top_row, :] += self.after_fill


class RotatingWedge(Effect):
    def __init__(self,
                 color=(255, 255, 0),
                 width=5,
                 direction=1,
                 angle=1,
                 start_col=0,
                 additive=False,
                 scale_ratio=True):
        self.color = np.asarray(color, np.uint8)
        self.width = width
        self.direction = direction
        self.angle = (angle * 1.0 * STATE.layout.columns / STATE.layout.rows
                      if scale_ratio else angle)
        self.start_col = 0
        self.end_col = start_col + width
        self.additive = additive

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.angle == 0:
            if self.start_col < self.end_col:
                update_pixels(
                    pixels=pixels,
                    slices=[(slice(None), slice(self.start_col, self.end_col))],
                    additive=self.additive,
                    color=self.color)
            else:
                update_pixels(
                    pixels=pixels,
                    slices=[(slice(None), slice(self.start_col, None)), (slice(None), slice(
                        None, self.end_col))],
                    additive=self.additive,
                    color=self.color)

        else:
            # TODO Combine Slices or get Indexes?
            slices = [(slice(r, min(r + self.width, STATE.layout.rows)),
                       int(c) % STATE.layout.columns)
                      for r, c in enumerate(
                          np.arange(self.start_col, self.start_col + self.angle * STATE.layout.rows,
                                    self.angle))]
            update_pixels(pixels=pixels, slices=slices, additive=self.additive, color=self.color)
        self.start_col = (self.start_col + self.direction) % STATE.layout.columns
        self.end_col = (self.end_col + self.direction) % STATE.layout.columns


def update_pixels(pixels, slices, additive, color):
    for r, c in slices:
        if additive:
            pixels[r, c] += color
        else:
            pixels[r, c] = color


def button_launch_checker(t, collaboration_state, osc_data):
    for i in range(len(osc_data.stations)):
        if osc_data.stations[i].buttons:
            return True
    return False


class GenericStatelessLauncher(MultiEffect):
    def __init__(self, factory_method, launch_checker=button_launch_checker, **kwargs):
        MultiEffect.__init__(self)
        self.launch_checker = launch_checker
        self.factory_method = factory_method
        self.factory_args = kwargs

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        # TODO : Performance
        if self.launch_checker(t=t, collaboration_state=collaboration_state, osc_data=osc_data):
            self.add_effect(
                self.factory_method(
                    pixels=pixels,
                    t=t,
                    collaboration_state=collaboration_state,
                    osc_data=osc_data,
                    **self.factory_args))
            print "Effect count", len(self.effects)


def wedge_factory(**kwargs):
    varnames = RotatingWedge.__init__.__func__.__code__.co_varnames
    args = {n: kwargs[n] for n in varnames if n in kwargs}
    if "color" not in args:
        args["color"] = (randint(0, 255), randint(0, 255), randint(0, 255))
    if "direction" not in args:
        args["direction"] = randint(0, 1) * 2 - 1  # Cheap way to get -1 or 1
    if "angle" not in args:
        args["angle"] = randint(-1, 1)
    return RotatingWedge(**args)


def distortion_rotation(offsets, t, start_t, frame):
    offsets *= frame
    print offsets


class LidarDisplay(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        SCALE = 30

        ratio = STATE.layout.columns / (np.pi * 2)
        if osc_data.lidar_objects:
            objects = osc_data.lidar_objects
            for obj_id, data in objects.iteritems():
                # TODO Probably faster conversion mechanism or at least make a helper method
                bottom_row = max(0, int(data.pose_z * SCALE))
                top_row = min(STATE.layout.rows, int(bottom_row + 1 + abs(data.height * SCALE)))
                row_slice = slice(bottom_row, top_row)

                apothem = np.sqrt(data.pose_x**2 + data.pose_y**2)
                central_theta = np.arctan2(data.pose_y, data.pose_x)
                half_angle = abs(np.arctan2(data.width / 2, apothem))
                col_left = int((central_theta - half_angle) * ratio) % STATE.layout.columns
                col_right = int(ceil((central_theta + half_angle) * ratio)) % STATE.layout.columns
                col_slices = [slice(col_left, col_right)]
                if col_left < 0:
                    col_slices = [slice(0, col_right), slice(STATE.layout.columns + col_left, None)]
                elif col_right > STATE.layout.columns:
                    col_slices = [slice(col_left, None), slice(0, col_right % STATE.layout.columns)]
                color = np.asarray((0, 0, 0), np.uint8)
                color[data.object_id % 3] = (255 - 30) / 2
                update_pixels(
                    pixels=pixels,
                    additive=True,
                    color=color,
                    slices=[(row_slice, col_slice) for col_slice in col_slices])


class RisingTide(Effect):
    def __init__(self,
                 target_color=(255, 255, 255),
                 start_color=(10, 10, 10),
                 start_column=0,
                 end_column=None,
                 bottom_row=2,
                 top_row=None):
        self.target_color = target_color
        self.start_color = start_color
        self.start_column = start_column
        self.end_column = end_column
        self.bottom_row = bottom_row
        self.top_row = top_row
        self.curr_top = self.bottom_row
        self.curr_bottom = self.bottom_row
        self.completed = False

        self.colors = [start_color]
        self.color_inc = tuple(
            map(lambda t, s: (0.0 + t - s) / (self.top_row - self.bottom_row) + 30, target_color,
                start_color))
        print self.start_color, self.target_color, self.color_inc

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.curr_top < self.top_row:
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]

            self.colors = [tuple(map(lambda c, i: c + i, self.colors[0], self.color_inc))
                           ] + self.colors
            self.curr_top += 1
        elif self.curr_bottom < self.top_row:
            self.colors = self.colors[:-1]
            self.curr_bottom += 1
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]
        else:
            self.completed = True

    def is_completed(self, t, osc_data):
        return self.completed


class TideLauncher(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s in range(STATE.layout.sections):
            if osc_data.stations[s].buttons:
                self.launch_effect(t, s)

    def launch_effect(self, t, s):
        per_section = int(STATE.layout.columns / STATE.layout.sections)
        c = (bool(getrandbits(1)), bool(getrandbits(1)), bool(getrandbits(1)))
        print c
        if not any(c):  #  Deal with all 0's case
            c = (True, True, True)
        print c
        start_color = (c[0] * 10, c[1] * 10, c[2] * 10)
        target_color = (c[0] * 255, c[1] * 255, c[2] * 255)
        e = RisingTide(
            start_column=s * per_section,
            end_column=(s + 1) * per_section,
            bottom_row=0,
            top_row=216,
            target_color=target_color,
            start_color=start_color)
        self.effects.append(e)


class Noise(Effect):
    """Always return a singular color. Can be bound top/bottom and
    left-right (wrap-around not supported yet)"""

    def __init__(self, color=(255, 0, 255), start_col=0, end_col=None, start_row=0, end_row=None):
        Effect.__init__(self)
        self.color = color
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))
        self.range = 10
        self.min = 0
        self.i = 0
        print "Created with color", self.color

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        # print pixels
        for i, pixel in enumerate(pixels):
            pixels[i] = (randint(self.min, self.range), randint(self.min, self.range), randint(
                self.min, self.range))
        self.i += 1
        if self.i % 2 == 0:
            self.min += 1
            self.range += 10
        # pixels[0] = (randint(0, 255),randint(0, 255),randint(0, 255))
        # pixels[self.slice] =(randint(0, 255),randint(0, 255),randint(0, 255))


SCENES = [
    Scene("smash", tags=[], effects=[Noise()]),
]
