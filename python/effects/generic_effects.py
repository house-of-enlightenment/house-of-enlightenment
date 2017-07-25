from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import EffectDefinition
from hoe.animation_framework import Effect
from hoe.animation_framework import FeedbackEffect


class SolidBackground(Effect):
    """Always return a color"""

    def __init__(self, color=(255, 0, 0), layout=None, n_pixels=None):
        Effect.__init__(self, layout, n_pixels)
        self.color = color
        print "Created with color", self.color

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii in range(self.n_pixels):
            pixels[ii] = pixels[ii] if pixels[ii] else self.color


class AdjustableFillFromBottom(Effect):
    def __init__(self, max_in=100, layout=None, n_pixels=None):
        Effect.__init__(self, layout, n_pixels)
        self.color_scale = 255.0 / max_in
        self.row_scale = 216.0 / max_in

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(self.layout.pixels):
            self.fill(pixels, t, coord, ii, osc_data)

    def fill(self, pixels, time, coord, ii, osc_data):
        # TODO Check for existance of fade
        if not pixels[ii] and osc_data.stations[5].faders[0] * self.row_scale > coord["row"]:
            pixels[ii] = tuple(
                [int(osc_data.stations[i].faders[0] * self.color_scale) for i in range(3)])


__all__ = []
