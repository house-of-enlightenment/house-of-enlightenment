import sys
sys.path.append('..')
from hoe import color_utils
from hoe.animation_framework import SceneDefinition
from hoe.animation_framework import EffectDefinition
from hoe.animation_framework import Effect
from pydoc import locate


class DadJokes(Effect):
    """Always return red"""
    def next_frame(self, pixels, t, osc_data):
        for ii in range(self.n_pixels):
            pixels[ii] = pixels[ii] if pixels[ii] else (255, 0, 0)


class SpatialStripesBackground(Effect):
    def next_frame(self, pixels, t, osc_data):
        for ii, coord in enumerate(self.layout):
            self.spatial_stripes(pixels,t, coord, ii)

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
        pixels[ii] = (r*256, g*256, b*256)


class MovingDot(Effect):
    def __init__(self, layout, n_pixels, spark_rad=8):
        Effect.__init__(self, layout, n_pixels)
        self.spark_rad = spark_rad

    def next_frame(self, pixels, t, osc_data):
        spark_ii = (t*80) % self.n_pixels

        for ii in range(self.n_pixels):
            self.moving_dot(pixels, ii, spark_ii, self.n_pixels)

    def moving_dot(self, pixels, ii, spark_ii, n_pixels):
        """ make a moving white dot showing the order of the pixels in the layout file """

        if pixels[ii]:
            return

        spark_val = max(0, (self.spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / self.spark_rad)
        if spark_val == 0:
            return
        spark_val = min(1, spark_val*2)*256
        pixels[ii] = (spark_val, spark_val, spark_val)


class AdjustableFillFromBottom(Effect):
    def next_frame(self, pixels, t, osc_data):
        for ii, coord in enumerate(self.layout):
            self.fill(pixels, t, coord, ii, osc_data)

    def fill(self, pixels, time, coord, ii, osc_data):
        if (not pixels[ii]) and "bottom_fill" in osc_data.faders and int(osc_data.faders["bottom_fill"]) > int(coord["row"]):
            pixels[ii] = tuple([int(osc_data.faders[key]) for key in ['r','g','b']])


class PrintOSC(Effect):
    """A effect layer that just prints OSC info when it changes"""
    def next_frame(self, pixels, t, osc_data):
        if osc_data.contains_change:
            print "Frame's osc_data is", osc_data


osc_printing_effect = EffectDefinition("print osc", PrintOSC)
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
]