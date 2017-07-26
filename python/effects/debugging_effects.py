from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import EffectDefinition
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager


class PrintOSC(Effect):
    """A effect layer that just prints OSC info when it changes"""

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if osc_data.contains_change:
            print "Frame's osc_data is", osc_data


__all__ = []
