from hoe.animation_framework import Effect
from hoe.animation_framework import Scene
from hoe.state import STATE
from hoe.pixels import cleanup_pairwise_indicies
from generic_effects import NoOpCollaborationManager
from shared import SolidBackground
import numpy as np
import math

# ---------------- Movement Functions -----------


def no_movement(shape, **kwargs):
    pass


def move_up(shape, **kwargs):
    shape.curr_row += 1


def move_along_horizontal_sine_wave(shape, period=2, amplitude=5, **kwargs):
    """Move along a sine wave around the structure P times with amplitude A

    Note that when used with shape this will never terminate unless
    your start row is near the top (which is not ideal)
    """
    shape.curr_col += 1
    shape.curr_row = int(
        math.sin(shape.curr_col * 2 * np.pi /
                 (STATE.layout.columns / period)) * amplitude + .5) + shape.start_row


def rotate_in_place(shape, **kwargs):
    shape.frame_indices[:] = _rotate_around_center(shape.base_indices, kwargs['now'])


# ----------- Index Functions ------------


def _populate_quadrants(quad1):
    return reduce(lambda x, p: x + [(p[0], p[1]), (-p[0], p[1]), (p[0], -p[1]), (-p[0], -p[1])],
                  quad1, [])


def _flip_across_row_axis(indices):
    return map(lambda x: (-x[0], x[1]), indices)


def _flip_across_column_axis(indices):
    return map(lambda x: (x[0], -x[1]), indices)


def _rotate_around_center(indices, theta):
    cos = math.cos(theta)
    sin = math.sin(theta)
    return map(lambda x: (cos * x[0] - sin * x[1], sin * x[0] + cos * x[1]), indices)


def _upward_triangle_indicies(height=3):
    """Create an upward triangle with a central point.
        The "center" of of the indicies is the bottom-middle of the triangle
        TODO: Accept width/height for ratios
    """
    return [(height - r, c) for r in range(height) for c in range(-abs(r), abs(r) + 1)]


def _downward_triangle_indicies(height=3):
    return _flip_across_row_axis(_upward_triangle_indicies(height))


def _hex_diamond_thing_indicies(half_height=3, half_width=3):
    """Create a hexi-diamond (or diamond is height/width are equal.
    This shape was a happy accident so don't expect much
    Note: actual height and width are *2+1 due to 0 indexing
    """
    return _populate_quadrants([(r, c) for r in range(half_height) for c in range(half_width)
                                if r + c < (half_width + half_height) / 2])


def _slope_indices(height, width):
    slope = 1.0 * height / width
    indicies = filter(lambda x: x[0] <= (width - x[1]) * slope, [(r, c)
                                                                 for r in range(height)
                                                                 for c in range(width)])
    return indicies


def _diamond_indicies(half_height, half_width):
    return _populate_quadrants(
        _slope_indices(half_height, half_width) + [(0, half_width), (half_height, 0)])


class Shape(Effect):
    def __init__(self,
                 color=(255, 255, 255),
                 indices=[(0, 0)],
                 movement_function=None,
                 start_col=0,
                 start_row=0):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        # normalize indices:
        min_row = min(indices, key=lambda x: x[0])[0]
        self.base_indices = np.array(indices)
        self.frame_indices = None
        self.curr_row = start_row
        self.curr_col = start_col
        self.movement_function = movement_function if movement_function else no_movement

    def scene_starting(self, now, osc_data):
        self.curr_row, self.curr_col = self.start_row, self.start_col

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # print map(lambda x: (x[0]+self.row, x[1]), self.indices)
        # pixels[map(lambda x: (x[0]+self.row, x[1]), self.indices)] = self.color
        # TODO Just pass this?
        self.frame_indices = np.copy(self.base_indices)
        self.movement_function(shape=self, now=now)
        cleaned_indices = cleanup_pairwise_indicies(self.frame_indices + (self.curr_row,
                                                                          self.curr_col))
        pixels.update_pairwise(additive=False, color=self.color, pairwise=cleaned_indices)

    def is_completed(self, t, osc_data):
        return self.curr_row >= STATE.layout.rows


SCENES = [
    Scene(
        "sinediamond",
        tags=[Scene.TAG_WIP],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(),
            Shape(
                indices=_diamond_indicies(4, 4),
                movement_function=move_along_horizontal_sine_wave,
                start_row=20)
        ]),
    Scene(
        "distortingdiamond",
        tags=[Scene.TAG_WIP],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(),
            Shape(indices=_diamond_indicies(5, 5), movement_function=rotate_in_place, start_row=20)
        ]),
    Scene(
        "uptriangle",
        tags=[Scene.TAG_WIP],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(),
            Shape(movement_function=move_up, indices=_upward_triangle_indicies(height=5))
        ])
]
