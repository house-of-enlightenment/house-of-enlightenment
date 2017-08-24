from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from generic_effects import NoOpCollaborationManager
from hoe.state import STATE
from shared import SolidBackground


class ZigZag(Effect):
    def __init__(self, color=(255, 255, 0), start_row=2, start_col=16, height=50):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        self.height = height

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

    def is_completed(self, t, osc_data):
        return self.cur_bottom >= STATE.layout.rows - 1


SCENES = [
    Scene(
        "zigzag",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)), ZigZag()])
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
