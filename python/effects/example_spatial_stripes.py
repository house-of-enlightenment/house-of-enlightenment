import sys
sys.path.append('..')
import color_utils
from scene_manager import SceneDefinition

__all__= [
    SceneDefinition("DadJokes"),
    SceneDefinition("SpatialStripesBackground"),
    SceneDefinition("DadJokes", "MovingDot"),
    SceneDefinition("SpatialStripesBackground", "MovingDot"),
    SceneDefinition("GentleGlow")
]

#TODO: base class
class DadJokes(object):
    """Always return red"""
    def next_frame(self, layout, time, n_pixels):
        return [(255,0,0) for ii, coord in enumerate(layout)] #TODO: faster with proper python array usage

class SpatialStripesBackground(object):

    def next_frame(self, layout, time, n_pixels):
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
        x, y, z = coord
        r = color_utils.scaled_cos(x, offset=t / 4, period=1, minn=0, maxx=0.7)
        g = color_utils.scaled_cos(y, offset=t / 4, period=1, minn=0, maxx=0.7)
        b = color_utils.scaled_cos(z, offset=t / 4, period=1, minn=0, maxx=0.7)
        r, g, b = color_utils.contrast((r, g, b), 0.5, 2)
        return (r*256, g*256, b*256)

class MovingDot(object):
    def next_frame(self, layout, time, n_pixels):
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

class GentleGlow(object):

    def next_frame(self, layout, time, n_pixels):
        return [self.gentle_glow(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]


    def gentle_glow(self, t, coord, ii, n_pixels):
        x, y, z = coord
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

        #For some reason, this is zeroing out some pixels. Needs tuning
        return (r*256, g*256, b*256)

    """
    def colorFader(pixels):
        pixels=[(globalParams["colorR"] * 256, globalParams["colorG"] * 256, globalParams["colorB"] * 256)] * n_pixels
    
        return pixels
    """


    #def pixel_color(t, coord, ii, n_pixels):


    # def singlePixelSelector(xPos, yPos, color):
    #     pixels=[(0,0,0,)] * n_pixels
    #     pixels[(yPos * 30) + xPos] = color


#TODO move me
def clear_pixels(pixels, n_pixels):
    pixels=[(0,0,0)] * n_pixels
    return pixels
