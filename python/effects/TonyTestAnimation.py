import sys
sys.path.append('..')
from hoe import color_utils
from hoe.scene_manager import SceneDefinition
from hoe.scene_manager import EffectDefinition
from hoe.scene_manager import Effect
from pydoc import locate

class TonyEffect(Effect):
    """Always return red"""
    def next_frame(self, layout, time, n_pixels, osc_data):
        return [(0,255,0) for ii, coord in enumerate(layout)] #TODO: faster with proper python array usage

# a simple effect for the bottom of the ring in red
class background1(Effect):

    def next_frame(self, layout, time, n_pixels, osc_data):
        return [self.gentle_glow(time, coord, ii, n_pixels) for ii, coord in enumerate(layout)]

    def gentle_glow(self, t, coord, ii, n_pixels):
        x, y, z = coord
        g = 0
        b = 0
        r = min(1, (1 - z) + color_utils.scaled_cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

        return (r * 255, g * 255, b * 255)



__all__= [
    SceneDefinition("tony's scene", EffectDefinition("Tony's Effect", TonyEffect)),
    SceneDefinition("tony's next scene", EffectDefinition("Tony's Next Effect", background1))
 ]