from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.layout import layout
from examples import SampleFeedbackEffect


class TonyEffect(Effect):
    """Always return red"""

    def next_frame(self, pixels, t, collaborative_state, osc_data):
        for ii, coord in enumerate(layout().pixels):
            pixels[ii] = (0, 255, 0)


# a simple effect for the bottom of the ring in red
class Background1(Effect):
    def next_frame(self, pixels, t, collaborative_state, osc_data):
        for ii, coord in enumerate(layout().pixels):
            self.gentle_glow(pixels, t, coord, ii)

    def gentle_glow(self, pixels, t, coord, ii):
        if pixels[ii]:
            return

        x, y, z = coord['point']
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

        pixels[ii] = (r * 255, g * 255, b * 255)


__all__ = [
    # Scene("tony's scene", SampleFeedbackEffect(), TonyEffect()),
    # Scene("tony's next scene", SampleFeedbackEffect(), Background1())
]
