import sys
sys.path.append('..')
import color_utils

__all__= ["MyAnimation"]

class MyAnimation:

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

        # make a moving white dot showing the order of the pixels in the layout file
        spark_ii = (t*80) % n_pixels
        spark_rad = 8
        spark_val = max(0, (spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / spark_rad)
        spark_val = min(1, spark_val*2)
        r += spark_val
        g += spark_val
        b += spark_val

        # apply gamma curve
        # only do this on live leds, not in the simulator
        #r, g, b = color_utils.gamma((r, g, b), 2.2)

        return (r*256, g*256, b*256)


    def clear_pixels(pixels, n_pixels):
        pixels=[(0,0,0)] * n_pixels
        return pixels


    def gentle_glow(t, coord, ii, n_pixels):
        x, y, z = coord
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

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