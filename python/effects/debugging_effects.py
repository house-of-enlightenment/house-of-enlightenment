from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.state import STATE


class PrintOSC(Effect):
    """A effect layer that just prints OSC info when it changes"""

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if osc_data.contains_change:
            print "Frame's osc_data is", osc_data


class MovingDot(Effect):
    """ Draw a moving dot in the order of the pixels in the array"""

    def __init__(self, spark_rad=8, t=0):
        Effect.__init__(self)
        self.spark_rad = spark_rad
        self.start_time = t

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        spark_ii = ((t - self.start_time) * 80) % STATE.layout.n_pixels

        for ii, c in [(int((spark_ii + x) % STATE.layout.n_pixels), 255 - x * 128 / self.spark_rad)
                      for x in range(self.spark_rad)]:
            pixels[ii] = (c, c, c)


__all__ = []
