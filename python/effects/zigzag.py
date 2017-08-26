from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
import hoe.fountain_models as fm
from generic_effects import NoOpCollaborationManager
from hoe.state import STATE
import hoe.stations
from shared import SolidBackground
from random import choice
# from ripple import Ripple


class ZigZag(Effect):
    """
      Fountain effect that zigzags to the top.
      define border_color to add a border
    """

    def __init__(self,
                 color=(255, 255, 0),
                 border_color=(255, 0, 0),
                 start_row=2,
                 start_col=16,
                 height=50):
        self.color = color
        self.border_color = border_color
        self.start_row = start_row
        self.start_col = start_col
        self.height = height
        self.cur_top = self.start_row
        self.cur_bottom = self.start_row

    def scene_starting(self, now, osc_data):
        self.cur_top = self.start_row
        self.cur_bottom = self.start_row

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        self.cur_top = self.cur_top + 4
        self.cur_bottom = self.cur_top - self.height

        # min/max to make sure we don't render out of bounds
        bottom = max(self.cur_bottom, self.start_row)
        top = min(self.cur_top, STATE.layout.rows - 1)

        for y in range(bottom, top):
            # zig zag is 11 wide
            # there is probably a better way to do this...
            # 0-19 repeated
            mod = (y % (10 * 2))
            if mod <= 5:
                x = mod
            elif mod > 5 and mod < 16:
                x = -mod + 11 - 1
            else:  # >= 16
                x = mod - 20

            # draw it 3 pixels wide
            pixels[y, self.start_col + x] = self.color
            pixels[y, self.start_col + x - 1] = self.color
            pixels[y, self.start_col + x + 1] = self.color

            # add a border if border_color is defined
            if self.border_color:
                pixels[y, self.start_col + x - 2] = self.border_color
                pixels[y, self.start_col + x + 2] = self.border_color
                pixels[y, self.start_col + x - 3] = self.border_color
                pixels[y, self.start_col + x + 3] = self.border_color

    def is_completed(self, t, osc_data):
        return self.cur_bottom >= STATE.layout.rows - 1

def pick_different_border_color(section, button):
    return hoe.stations.BUTTON_COLORS[choice([i for i in range(5) if i!=button])]

FOUNTAINS = [
    fm.FountainDefinition("zigzag", ZigZag, arg_generators=fm.get_default_arg_generators(border_color=pick_different_border_color))
]

SCENES = [

]
"""
5 |             x
4 |          x     x
3 |       x           x
2 |    x                 x
1 | x                       x 10 11 12 13 14 15 16 17 18 19
  x---------------------------x-----------------------------------
-1| 1  2  3  4  5  6  7  8  9    x                       x
-2|                                 x                 x
-3|                                    x           x
-4|                                       x     x
-5|                                          x
"""
