from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import EffectFactory
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
from random import randrange


class TonyTestEffect(Effect):
    """Always return red"""

    def next_frame(self, pixels, t, collaborative_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            pixels[ii] = (255, 0, 0)


# a simple effect for the bottom of the ring in red
class Background1(Effect):
    def next_frame(self, pixels, t, collaborative_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            self.gentle_glow(pixels, t, coord, ii)

    def gentle_glow(self, pixels, t, coord, ii):
        #if pixels[ii]:
        #    return

        x, y, z = coord['point']
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

        pixels[ii] = (r * 255, g * 255, b * 255)


__all__ = [
    # Scene("tonyscene1", collaboration_manager=NoOpCollaborationManager()),
    # Scene("tonyscene2", collaboration_manager=NoOpCollaborationManager())
]
