import sys
sys.path.append('..')
import color_utils
from scene_manager import SceneDefinition
from scene_manager import EffectDefinition
from scene_manager import Effect
from pydoc import locate


#TODO: base class
class DadJokes(Effect):
    """Always return red"""
    def next_frame(self, layout, time, n_pixels, osc_data):
        return [(255,0,0) for ii, coord in enumerate(layout)] #TODO: faster with proper python array usage

class SpatialStripesBackground(Effect):

    def next_frame(self, layout, time, n_pixels, osc_data):
        return [self.spatial_stripes(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

    #-------------------------------------------------------------------------------
    # color function
    def spatial_stripes(self, t, coord, ii, n_pixels):
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
        return (r*256, g*256, b*256)


class MovingDot(Effect):
    def next_frame(self, layout, time, n_pixels, osc_data):
        return [self.moving_dot(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

    def moving_dot(self, t, coord, ii, n_pixels):
        # make a moving white dot showing the order of the pixels in the layout file
        spark_ii = (t*80) % n_pixels
        spark_rad = 8
        spark_val = max(0, (spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / spark_rad)
        if(spark_val==0):
            return None
        spark_val = min(1, spark_val*2)

        spark_val*=256
        return (spark_val, spark_val, spark_val)


class AdjustableFillFromBottom(Effect):
    def next_frame(self, layout, time, n_pixels, osc_data):
        return [self.fill(time, coord, ii, n_pixels, osc_data) for ii,coord in enumerate(layout)]

    def fill(self, time, coord, ii, n_pixels, osc_data):
        if("bottom_fill" in osc_data.faders and int(osc_data.faders["bottom_fill"]) > int(coord["row"])):
            return (osc_data.faders['r'], osc_data.faders['g'], osc_data.faders['b'])

        return None


class GentleGlow(Effect):

    def next_frame(self, layout, time, n_pixels, osc_data):
        return [self.gentle_glow(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

    def gentle_glow(self, t, coord, ii, n_pixels):
        x, y, z = coord
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

        #For some reason, this is zeroing out some pixels. Needs debugging
        return (r*256, g*256, b*256)


class PrintOSC(Effect):
    """A effect layer that just prints OSC info when it changes"""
    def next_frame(self, layout, time, n_pixels, osc_data):
        if osc_data.contains_change:
            print "Frame's osc_data is", osc_data

        return [None] * n_pixels


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