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

__all__= [
    #SceneDefinition("tony's scene", EffectDefinition("Tony's Effect", TonyEffect))
 ]