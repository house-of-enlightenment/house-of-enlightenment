import sys
sys.path.append('..')
import color_utils
from scene_manager import SceneDefinition
from scene_manager import EffectDefinition
#from scene_manager import Effect
from pydoc import locate


def dad_jokes(layout, time, n_pixels, osc_data):
    """Always return red"""
    return [(255,0,0) for ii, coord in enumerate(layout)] #TODO: faster with proper python array usage


def spatial_stripes_background_frame(layout, time, n_pixels, osc_data):
    return [spatial_stripes_pixel(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

#-------------------------------------------------------------------------------
# color function
def spatial_stripes_pixel(t, coord, ii, n_pixels):
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



def moving_dot_frame(layout, time, n_pixels, osc_data):
    return [moving_dot_pixel(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

def moving_dot_pixel(t, coord, ii, n_pixels):
    # make a moving white dot showing the order of the pixels in the layout file
    spark_ii = (t*80) % n_pixels
    spark_rad = 8
    spark_val = max(0, (spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / spark_rad)
    if spark_val==0 :
        #Spark does not draw here so skip it and fallback to next layer
        return None
    spark_val = min(1, spark_val*2)

    spark_val*=256
    return (spark_val, spark_val, spark_val)


def adjustable_fill_from_bottom_frame(layout, time, n_pixels, osc_data):
    row_limit = 0 if "bottom_fill" not in osc_data.faders else int(osc_data.faders["bottom_fill"])
    pixel_color = tuple([int(osc_data.faders[key]) for key in ['r','g','b']])
    # TODO: Slice and return None more easily
    return [adjustable_fill_pixel(time, coord, ii, n_pixels, row_limit, pixel_color) for ii,coord in enumerate(layout)]


def adjustable_fill_pixel(time, coord, ii, n_pixels, row_limit, pixel_color):
    return pixel_color if row_limit > int(coord["row"]) else None


def gentle_glow_frame(layout, time, n_pixels, osc_data):
    return [gentle_glow_pixel(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]


def gentle_glow_pixel(t, coord, ii, n_pixels):
    x, y, z = tuple(coord["points"])
    g = 0
    b = 0
    r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

    #For some reason, this is zeroing out some pixels. Needs debugging
    return (r*256, g*256, b*256)


def print_osc_if_changed_frame(layout, time, n_pixels, osc_data):
    """A effect layer that just prints OSC info when it changes"""
    if osc_data.contains_change:
        print "Frame's osc_data is", osc_data

    return [None] * n_pixels


osc_printing_effect = EffectDefinition("print osc", print_osc_if_changed_frame)
red_effect=EffectDefinition("all red", dad_jokes)
spatial_background=EffectDefinition("spatial background", spatial_stripes_background_frame)
moving_dot = EffectDefinition("moving dot", moving_dot_frame)
green_fill = EffectDefinition("green fill", adjustable_fill_from_bottom_frame)

__all__= [
    SceneDefinition("red printing scene", osc_printing_effect, red_effect),
    SceneDefinition("red with green bottom", osc_printing_effect, green_fill, red_effect),
    SceneDefinition("spatial scene", spatial_background),
    SceneDefinition("red scene with dot", moving_dot, red_effect),
    SceneDefinition("spatial scene with dot", moving_dot, spatial_background)
]