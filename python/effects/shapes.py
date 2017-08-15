from hoe.animation_framework import Effect
from hoe.animation_framework import Scene
from hoe.state import STATE
from hoe.pixels import cleanup_pairwise_indicies
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
import numpy as np

def no_movement(indices, row, col, **kwargs):
    return indices, row, col

def move_up(indices, row, col, **kwargs):
    return indices, row+1, col

class Shape(Effect):
    def __init__(self, color=(255, 255, 255), indices=[(0, 0)], movement_function=None, start_col=0, start_row=0):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        # normalize indices:
        min_row = min(indices, key=lambda x: x[0])[0]
        self.indices = np.array(indices)
        self.curr_row = start_row
        self.curr_col = start_col
        self.movement_function = movement_function if movement_function else no_movement

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # print map(lambda x: (x[0]+self.row, x[1]), self.indices)
        # pixels[map(lambda x: (x[0]+self.row, x[1]), self.indices)] = self.color
        self.indices, self.curr_row, self.curr_col = self.movement_function(indices=self.indices, row=self.curr_row, col=self.curr_col)
        frame_indices = cleanup_pairwise_indicies(self.indices+(self.curr_row, self.curr_col))
        pixels.update_pairwise(additive=False, color=self.color, pairwise=frame_indices)

    def is_completed(self, t, osc_data):
        return self.curr_row >= STATE.layout.rows


__all__ = [
    Scene(
        "diamond",
        NoOpCollaborationManager(),
        SolidBackground(),
        Shape(indices=[(0, 0), (0, 1), (1, 0), (-1, 0), (0, -1)], movement_function=move_up)
    ),
    Scene(
        "uptriangle",
        NoOpCollaborationManager(),
        SolidBackground(),
        Shape(movement_function=move_up,
              indices=[(0,-2),(0,-1),(0,0),(0,1),(0,2),(1,-1),(1,0),(1,1),(2,0)])
    )
]
