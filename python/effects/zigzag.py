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


class ZigZag(Effect):
    def __init__(self, color=(0, 255, 0), start_row=2, start_col=16, height=214, end_row=2, end_col=26):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        self.cur_height = 0
        self.end_row = end_row
        self.end_col = end_col
        self.milliseconds = 0

    # def scene_starting(self, osc_data):
    #     self.curr_row = self.start_row


    def next_frame(self, pixels, now, collaboration_state, osc_data):
        self.cur_height = self.cur_height + 4
        for y in range(self.start_row, self.cur_height):
            # zig zag is 11 wide
            # there is probably a better way to do this...
            mod = (y % (10*2))
            if mod <= 5:
                x = mod
            elif mod > 5 and mod < 16:
                x = -mod + 11 - 1
            else: # >= 16
                x = mod - 20

            # pixels[y, self.start_col] = (255, 0, 0)
            pixels[y, self.start_col + x] = self.color
            pixels[y, self.start_col + x-1] = self.color
            pixels[y, self.start_col + x+1] = self.color

    def is_completed(self, t, osc_data):
        return self.cur_height >= STATE.layout.rows-1


SCENES = [
    Scene(
        "zigzag",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 ZigZag()])
]
