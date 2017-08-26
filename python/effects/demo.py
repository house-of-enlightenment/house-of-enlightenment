from random import randrange
from random import randint

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from hoe.collaboration import NoOpCollaborationManager
import hoe.fountain_models as fm
from hoe.state import STATE

from shared import SolidBackground


class SolidRow(Effect):
    def __init__(self, color=(0, 255, 0), start_row=2, start_col=0, end_col=None):
        self.color = color
        self.start_row = start_row
        self.curr_row = start_row

        # TODO wraparound
        end_col = end_col or STATE.layout.columns
        if end_col<start_col:
            end_col,start_col = start_col,end_col
        self.col_slice = slice(start_col, end_col)

    def scene_starting(self, now, osc_data):
        self.curr_row = self.start_row

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        pixels[self.curr_row, self.col_slice] = self.color
        self.curr_row += 1

    def is_completed(self, t, osc_data):
        return self.curr_row >= STATE.layout.rows


class LaunchRows(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for sid, buttons in osc_data.buttons.items():
            if buttons:
                self.add_effect(
                    SolidRow(
                        color=(randrange(0, 255), randrange(0, 255), randrange(0, 255)),
                        start_col=11 * sid + randint(0, 11),
                        end_col=11 * (sid + 1) + randint(0, 11)))


FOUNTAINS = [
    fm.FountainDefinition("simple_rising_row", SolidRow, arg_generators=fm.get_default_arg_generators(end_col=fm.pick_random_start_column))
]

SCENES = [
    fm.FountainScene(
        "groupdemo",
        tags=[Scene.TAG_EXAMPLE],
        background_effects=[SolidBackground(color=(30, 30, 30))],
        foreground_names=["simple_rising_row"]
    )
]
