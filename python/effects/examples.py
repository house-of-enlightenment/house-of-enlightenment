from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import EffectDefinition
from hoe.animation_framework import Effect
from hoe.animation_framework import FeedbackEffect
import generic_effects
import debugging_effects


class SpatialStripesBackground(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(self.layout.pixels):
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
        if pixels[ii]:
            return

        # make moving stripes for x, y, and z
        x, y, z = coord["point"]
        r = color_utils.scaled_cos(x, offset=t / 4, period=1, minn=0, maxx=0.7)
        g = color_utils.scaled_cos(y, offset=t / 4, period=1, minn=0, maxx=0.7)
        b = color_utils.scaled_cos(z, offset=t / 4, period=1, minn=0, maxx=0.7)
        r, g, b = color_utils.contrast((r, g, b), 0.5, 2)
        pixels[ii] = (r * 256, g * 256, b * 256)


class MovingDot(Effect):
    def __init__(self, spark_rad=8, layout=None, n_pixels=None):
        Effect.__init__(self, layout, n_pixels)
        self.spark_rad = spark_rad

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        spark_ii = (t * 80) % self.n_pixels

        for ii in range(self.n_pixels):
            self.moving_dot(pixels, ii, spark_ii, self.n_pixels)

    def moving_dot(self, pixels, ii, spark_ii, n_pixels):
        """ make a moving white dot showing the order of the pixels in the layout file """

        if pixels[ii]:
            return

        spark_val = max(
            0, (self.spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / self.spark_rad)
        if spark_val == 0:
            return
        spark_val = min(1, spark_val * 2) * 256
        pixels[ii] = (spark_val, spark_val, spark_val)


"""osc_printing_effect = Effect("print osc", PrintOSC)
red_effect=EffectDefinition("all red", DadJokes)
spatial_background=EffectDefinition("spatial background", SpatialStripesBackground)
moving_dot = EffectDefinition("moving dot", MovingDot)
green_fill = EffectDefinition("green fill", AdjustableFillFromBottom)

__all__= [
    SceneDefinition("red printing scene", osc_printing_effect, red_effect),
    SceneDefinition("red with green bottom", osc_printing_effect, green_fill, red_effect),
    SceneDefinition("spatial scene", spatial_background),
    SceneDefinition("red scene with dot", moving_dot, red_effect),
    SceneDefinition("spatial scene with dot", moving_dot, spatial_background)
]"""


class SampleFeedbackEffect(FeedbackEffect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii in self.layout.row[0] + self.layout.row[1]:
            pixels[ii] = (0, 255, 0)

    def compute_state(self, t, collaboration_state, osc_data):
        pass


osc_printing_effect = debugging_effects.PrintOSC()
spatial_background = SpatialStripesBackground()
red_background = generic_effects.SolidBackground((255, 0, 0))
blue_background = generic_effects.SolidBackground((0, 0, 255))
moving_dot = MovingDot()

default_feedback_effect = SampleFeedbackEffect()

__all__ = [
    Scene("redgreenprinting", default_feedback_effect, osc_printing_effect,
          generic_effects.SolidBackground()),
    Scene("blueredgreen", default_feedback_effect,
          generic_effects.AdjustableFillFromBottom(), red_background),
    Scene("bluewithdot", default_feedback_effect, moving_dot, blue_background),
    Scene("spatial scene", default_feedback_effect, spatial_background)
]
