import numpy as np

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import MultiEffect
from hoe.animation_framework import OSCDataAccumulator
from hoe.animation_framework import ButtonFeedbackDisplay
from hoe.collaboration import ButtonToggleResponderManager, NoOpCollaborationManager
import hoe.color_utils
from hoe.osc_utils import update_buttons
from hoe.state import STATE
from hoe.stations import StationButtons

import debugging_effects


class Rainbow(Effect):
    """Draw a rainbow that returns to its base color

       Can be bounded with start_col/end_col and start_row/end_row

       Use HSV for the color range. See color_utils.bi_rainbow for more details.

       Note: No individual value in a color tuple will be greater than
        max_value, so this can be used to limit a range to preempt an
        additive operation later from rolling over the uint8 limit of
        255

    """

    def __init__(self,
                 hue_start,
                 hue_end,
                 saturation=255,
                 max_value=255,
                 start_col=0,
                 end_col=None,
                 start_row=0,
                 end_row=None):
        self.slice = (slice(start_row, end_row), slice(start_col, end_col))  # TODO: Wrap-around
        size = (end_col if end_col else STATE.layout.columns) - start_col
        self.rainbow = hoe.color_utils.bi_rainbow(
            size, hue_start=hue_start, hue_end=hue_end, saturation=saturation, value=max_value)

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        pixels[self.slice] = self.rainbow


class FrameRotator(Effect):
    """Rotate the entire frame each frame based on the rate

       Float values for rate are supported but will be rounded down at the time of calculation.
       For example, rate=0.5 will rotate the entire scene 1 column every TWO frames
    """

    def __init__(self, rate=1.0, bottom_row=0, top_row=None):
        Effect.__init__(self)
        self.frame = 0
        self.rate = rate
        self.row_slice = slice(bottom_row, top_row)

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame = (self.frame + self.rate) % STATE.layout.columns
        real_shift = int(self.frame)
        pixels[self.row_slice, :] = np.concatenate(
            (pixels[self.row_slice, real_shift:], pixels[self.row_slice, :real_shift]), axis=1)


class FunctionFrameRotator(Effect):
    """Rotate the entire frame each frame based on a function and initial offsets

        To use, you'll want to specify two main arguments:
        - An array of offsets the length of bottom_row to
         top_row. Each values represents a rightward shift in the
         corresponding row, from bottom up.
        - A function that modifies the offsets array IN-PLACE before
           each frame. It MUST accept named arguments: offsets, t,
           start_t, frame
    """

    def __init__(self, func, bottom_row=0, top_row=None, start_offsets=None):
        self.update_offsets_func = func
        self.bottom_row = bottom_row
        self.top_row = top_row if top_row else STATE.layout.rows
        self.offsets = np.array(
            start_offsets, dtype=np.float) if start_offsets is not None else np.zeros(
                self.top_row - self.bottom_row, dtype=np.float)
        self.frame = 0
        self.start_t = None

    def scene_starting(self, now, osc_data):
        self.frame = 0
        self.start_t = None

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if not self.start_t:
            self.start_t = t

        self.frame += 1

        self.update_offsets_func(offsets=self.offsets, t=t, start_t=self.start_t, frame=self.frame)

        for r, offset in zip(range(self.bottom_row, self.top_row), self.offsets):
            #print r, offset, pixels[r,int(offset):].shape, pixels[r,:int(offset)].shape
            pixels[r, :] = np.concatenate(
                (pixels[r, int(offset):], pixels[r, :int(offset)]), axis=0)

    # Below are static sample methods for rotation
    @staticmethod
    def no_op(offsets, t, start_t, frame):
        pass

    @staticmethod
    def sample_rotating_offset(offsets, t, start_t, frame):
        """A sample function. Just increment the offsets by 1 each time.
        Effectively the same as FrameRotator with rate=1, but initial offsets can be 1.
        A good way to see this in effect is by passing in a range for your initial offsets"""
        offsets[:] = (offsets[:] + 1) % STATE.layout.columns

    @staticmethod
    def sample_roll_offset(offsets, t, start_t, frame):
        """A sample function. Moves the offsets up 1 each time. See SineRainbow for an example"""
        offsets[:] = np.roll(offsets, 1)


rainbow = Rainbow(hue_start=0, hue_end=255)
SCENES = [
    Scene(
        "buttontoggler",
        tags=[Scene.TAG_TEST],
        collaboration_manager=ButtonToggleResponderManager(),
        effects=[ButtonFeedbackDisplay(), debugging_effects.PrintOSC()]),
    # A simple rainbow that rotates due to the FrameRotator
    Scene(
        "rotatingrainbow",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[rainbow, FrameRotator(rate=.75)]),
    # A rainbow that has been distorted into spirals by using a RANGE as the offset
    Scene(
        "funkrainbow",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=ButtonToggleResponderManager(),
        effects=[
            rainbow,
            FunctionFrameRotator(
                func=FunctionFrameRotator.sample_rotating_offset,
                start_offsets=range(STATE.layout.rows))
        ]),
    # A rainbow that follows a sine wave up (due to the offsets) and
    # moves upwards due to a rolling offset function
    Scene(
        "sinerainbow",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            rainbow,
            FunctionFrameRotator(
                func=FunctionFrameRotator.sample_roll_offset,
                start_offsets=5 * np.sin(np.linspace(0, 8 * np.pi, STATE.layout.rows)))
        ])
]
