from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
from generic_effects import Rainbow
from random import randrange
from random import randint
import math

from hoe.state import STATE


class Arc(Effect):
    def __init__(self, color=(0, 255, 0), start_row=2, start_col=16, height=214, end_row=2, end_col=26):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        self.height = height
        self.end_row = end_row
        self.end_col = end_col
        self.milliseconds = 0

    # def scene_starting(self, osc_data):
    #     self.curr_row = self.start_row


    def next_frame(self, pixels, now, collaboration_state, osc_data):
        for y in range(self.start_row, STATE.layout.rows):
            x = int(self.start_col + round(math.sin(y+6)))
            pixels[y, x] = self.color
            pixels[y, self.start_col] = (255, 0, 0)

    def is_completed(self, t, osc_data):
        return False


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
        "arc",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 Arc()])
]
