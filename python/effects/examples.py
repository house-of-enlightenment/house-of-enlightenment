from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import EffectFactory
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from random import randrange
import generic_effects
import debugging_effects


class SpatialStripesBackground(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            self.spatial_stripes(pixels, t, coord, ii)

    #-------------------------------------------------------------------------------
    # color function
    def spatial_stripes(self, pixels, t, coord, ii):
        """Compute the color of a given pixel.

        t: time in seconds since the program started.
        ii: which pixel this is, starting at 0
        coord: the (x, y, z) position of the pixel as a tuple
        n_pixels: the total number of pixels

        Returns an (r, g, b) tuple in the range 0-255

        """
        # make moving stripes for x, y, and z
        x, y, z = coord["point"]
        r = color_utils.scaled_cos(x, offset=t / 4, period=1, minn=0, maxx=0.7)
        g = color_utils.scaled_cos(y, offset=t / 4, period=1, minn=0, maxx=0.7)
        b = color_utils.scaled_cos(z, offset=t / 4, period=1, minn=0, maxx=0.7)
        r, g, b = color_utils.contrast((r, g, b), 0.5, 2)
        pixels[ii] = (r * 256, g * 256, b * 256)


class ColumnStreak(Effect):
    def __init__(self, column, color=(255, 255, 255), streak_length=5, row_start=2):
        self.column = column
        self.streak_length = streak_length
        self.bottom_row = row_start
        self.row = row_start

        self.colors = [(color[0] - i * color[0] / 4, color[1] - i * color[1] / 4,
                        color[2] - i * color[2] / 4) for i in range(streak_length)]

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        tail = max(self.row - self.streak_length + 1, self.bottom_row)
        # print self.row, tail, pixels[tail:self.row+1,self.column], self.colors[self.row-tail::-1]
        pixels[tail:self.row + 1, self.column] = self.colors[self.row - tail::-1]

        self.row += 1

    def is_completed(self, t, osc_data):
        # TODO run off the top
        return self.row >= STATE.layout.rows


class SampleEffectLauncher(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s in range(STATE.layout.sections):
            if osc_data.stations[s].buttons:
                self.launch_effect(t, s)

    def launch_effect(self, t, s):
        print "Adding Effect"
        per_section = int(STATE.layout.columns / STATE.layout.sections)
        e = ColumnStreak(
            column=randrange(0 + s * per_section, (s + 1) * per_section), color=(255, 0, 0))
        self.effects.append(e)


class SampleFeedbackEffect(CollaborationManager, Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        pixels[0:2, :] = (0, 255, 0)

    def compute_state(self, t, collaboration_state, osc_data):
        pass


osc_printing_effect = debugging_effects.PrintOSC()
spatial_background = SpatialStripesBackground()
red_background = generic_effects.SolidBackground((255, 0, 0))
blue_background = generic_effects.SolidBackground((0, 0, 255))
moving_dot = debugging_effects.MovingDot()

default_feedback_effect = SampleFeedbackEffect()

__all__ = [
    Scene("launchdots", default_feedback_effect,
          generic_effects.SolidBackground((100, 100, 100)), SampleEffectLauncher(), generic_effects.FrameRotator(rate=.5)),
    Scene("redgreenprinting", default_feedback_effect, osc_printing_effect,
          generic_effects.SolidBackground()),
    Scene("adjustablebackground", default_feedback_effect, red_background,
          generic_effects.AdjustableFillFromBottom()),
    Scene("bluewithdot", default_feedback_effect, blue_background, moving_dot),
    Scene("spatial scene", default_feedback_effect, spatial_background)
]
