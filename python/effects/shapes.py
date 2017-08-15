from hoe.animation_framework import Effect
from hoe.animation_framework import Scene
from hoe.state import STATE
from hoe.pixels import cleanup_pairwise_indicies
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
import numpy as np


class Shape(Effect):
    def __init__(self, color=(255, 255, 255), indices=[(0, 0)], start_col=0, start_row=0):
        self.color = color
        self.start_col = start_col
        # normalize indices:
        min_row = min(indices, key=lambda x: x[0])[0]
        self.indices = indices
        self.row = start_row

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # print map(lambda x: (x[0]+self.row, x[1]), self.indices)
        # pixels[map(lambda x: (x[0]+self.row, x[1]), self.indices)] = self.color
        frame_indices = cleanup_pairwise_indicies(self.indices)
        pixels.update_pairwise(additive=False, color=self.color, pairwise=frame_indices)

    def is_completed(self, t, osc_data):
        return self.row >= STATE.layout.rows


__all__ = [
    Scene(
        "diamond",
        NoOpCollaborationManager(),
        SolidBackground(),
        Shape(indices=[(0, 0), (0, 1), (1, 0), (-1, 0), (0, -1)]))
]
