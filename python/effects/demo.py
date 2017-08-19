from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
from random import randrange
from random import randint

from hoe.state import STATE


class SolidRow(Effect):
    def __init__(self, color=(0, 255, 0), start_row=2, start_col=0, end_col=None):
        self.color = color
        self.start_row = start_row
        self.curr_row = start_row
        # TODO wraparound
        end_col = end_col if end_col else STATE.layout.columns
        self.col_slice = slice(start_col, end_col)

    def scene_starting(self, osc_data):
        self.curr_row = self.start_row

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        pixels[self.curr_row, self.col_slice] = self.color
        self.curr_row += 1

    def is_completed(self, t, osc_data):
        return self.curr_row >= STATE.layout.rows


class LaunchRows(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for sid, station in enumerate(osc_data.stations):
            if station.button_presses:
                self.add_effect(
                    SolidRow(
                        color=(randrange(0, 255), randrange(0, 255), randrange(0, 255)),
                        start_col=11 * sid + randint(0, 11),
                        end_col=11 * (sid + 1) + randint(0, 11)))


SCENES = [
    Scene(
        "groupdemo",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 LaunchRows()])
]
