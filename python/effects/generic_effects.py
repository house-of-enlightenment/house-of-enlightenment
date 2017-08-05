from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import MultiEffect
from random import getrandbits
from hoe.state import STATE
from hoe.osc_utils import update_buttons
from debugging_effects import PrintOSC
import hoe.color_utils
import numpy as np

class SolidBackground(Effect):
    """Always return a color"""

    def __init__(self, color=(255, 0, 0), start_col=0, end_col=None, start_row=0, end_row=None):
        Effect.__init__(self)
        self.color = color
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))
        print "Created with color", self.color

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        pixels[self.slice] = self.color


class Rainbow(Effect):
    def __init__(self, hue_start, hue_end, saturation=255, max_value=255,
                 start_col=0, end_col=None, start_row=0, end_row=None):
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))
        size = (end_col if end_col else STATE.layout.columns) - start_col
        self.rainbow = hoe.color_utils.bi_rainbow(size, hue_start=hue_start, hue_end=hue_end, saturation=saturation, value=max_value)


    def next_frame(self, pixels, t, collaboration_state, osc_data):
        pixels[self.slice] = self.rainbow


class FrameRotator(Effect):
    """Rotate the entire frame each frame based on the rate"""
    def __init__(self, rate=1, bottom_row=0, top_row=None):
        Effect.__init__(self)
        self.frame=0
        self.rate = rate
        self.row_slice = slice(bottom_row, top_row)

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame = (self.frame + self.rate) % STATE.layout.columns
        real_shift = int(self.frame)
        pixels[self.row_slice,:] = np.concatenate((pixels[self.row_slice,real_shift:], pixels[self.row_slice,:real_shift]), axis=1)


class FunctionFrameRotator(Effect):
    @staticmethod
    def no_op(offsets, t, start_t, frame):
        pass

    @staticmethod
    def sample_rotating_offset(offsets, t, start_t, frame):
        """A sample function. Just increment the offsets by 1 each time.
        A good way to see this in effect is by passing in a range for your initial offsets"""
        offsets[:] = (offsets[:] + 1) % STATE.layout.columns

    @staticmethod
    def sample_roll_offset(offsets, t, start_t, frame):
        """A sample function. Just increment the offsets by 1 each time.
        A good way to see this in effect is by passing in a range for your initial offsets"""
        offsets[:] = np.roll(offsets, 1)



    """Rotate the entire frame each frame based on a function"""
    def __init__(self, func, bottom_row=0, top_row=None, start_offsets=None):
        self.update_offsets_func = func
        self.bottom_row = bottom_row
        self.top_row = top_row if top_row else STATE.layout.rows
        self.offsets = np.array(start_offsets, dtype=np.float) if start_offsets is not None else np.zeros(self.top_row-self.bottom_row, dtype=np.float)
        self.frame = 0
        self.start_t = None

    def scene_starting(self):
        self.frame = 0
        self.start_t = None

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if not self.start_t:
            self.start_t = t

        self.frame += 1

        self.update_offsets_func(offsets=self.offsets, t=t, start_t=self.start_t, frame=self.frame)

        for r,offset in zip(range(self.bottom_row,self.top_row), self.offsets):
            #print r, offset, pixels[r,int(offset):].shape, pixels[r,:int(offset)].shape
            pixels[r,:] = np.concatenate((pixels[r,int(offset):], pixels[r,:int(offset)]), axis=0)


class AdjustableFillFromBottom(Effect):
    def __init__(self, max_in=100):
        Effect.__init__(self)
        self.color_scale = 255.0 / max_in
        self.row_scale = 216.0 / max_in

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            self.fill(pixels, t, coord, ii, osc_data)

    def fill(self, pixels, time, coord, ii, osc_data):
        # TODO Check for existance of fade
        if osc_data.stations[5].faders[0] * self.row_scale > coord["row"]:
            pixels[ii] = tuple(
                [int(osc_data.stations[i].faders[0] * self.color_scale) for i in range(3)])


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


class ButtonToggleResponderManager(CollaborationManager):
    def compute_state(self, t, collaboration_state, osc_data):
        for s, station in enumerate(osc_data.stations):
            for b in station.buttons:
                if station.client:
                    update_buttons(station_id=s, client=station.client, updates={b: 2}, timeout=1)


class NoOpCollaborationManager(CollaborationManager):
    def compute_state(self, t, collaboration_state, osc_data):
        pass


__all__ = [
    Scene("risingtide", NoOpCollaborationManager(), SolidBackground(), TideLauncher(), FrameRotator()),
    Scene("buttontoggler", ButtonToggleResponderManager(), SolidBackground(), PrintOSC())
]
