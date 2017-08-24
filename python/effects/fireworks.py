from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import MultiEffect
from generic_effects import NoOpCollaborationManager
from hoe.state import STATE
from shared import SolidBackground
import time
from collections import deque



class RisingLine(Effect):
    def __init__(self, color=(255, 255, 0), start_row=2, start_col=16, height=5, delay=0):
        self.color = color
        self.start_row = start_row
        self.start_col = start_col
        self.height = height
        self.delay = delay # ms

        self.cur_top = self.start_row
        self.cur_bottom = self.start_row
        self.start_ms = time.time() * 1000

    def next_frame(self, pixels, now, collaboration_state, osc_data):

        # don't start until after the delay
        elapsed_ms = now * 1000 - self.start_ms
        if (elapsed_ms < self.delay):
            return

        self.cur_top = self.cur_top + 4
        self.cur_bottom = self.cur_top - self.height

        # min/max to make sure we don't render out of bounds
        bottom = max(self.cur_bottom, self.start_row)
        top = min(self.cur_top, STATE.layout.rows - 1)

        for y in range(bottom, top):
            pixels[y, self.start_col] = self.color

    def is_completed(self, t, osc_data):
        return self.cur_bottom >= STATE.layout.rows - 1



class RomanCandleLauncher(MultiEffect):
    def __init__(self, start_col = 16, end_col = 24, color = (255, 0, 0)):

        forward_cols = range(start_col, end_col)
        backward_cols = forward_cols[::-1] ## reverse

        sequence = forward_cols + backward_cols
        #+ forward_cols + backward_cols

        # print "forward_cols", forward_cols
        # print "backward_cols", backward_cols
        # print "sequence", sequence

        def make_line((i, col)):
            return RisingLine(
                height = 30,
                start_col = col,
                delay = i * 100,
                color = color
            )

        effects = map(make_line, enumerate(sequence))

        MultiEffect.__init__(self, *effects)




class AroundTheWorldLauncher(MultiEffect):
    def __init__(self, start_col = 16, color = (0, 255, 0)):

        def shift(key, array):
            a = deque(array) # turn list into deque
            a.rotate(key)    # rotate deque by key
            return list(a)   # turn deque back into a list

        # [0, ..., 65]
        all_cols = range(0, STATE.layout.columns)
        # [start_col, ..., 65, 0, ..., start_col - 1]
        shifted = shift(start_col, all_cols)

        # print "start_col", start_col
        # print "shifted", shifted

        def make_line((i, col)):
            return RisingLine(
                height = 9,
                start_col = col,
                delay = i * 30,
                color = color
            )

        effects = map(make_line, enumerate(shifted))

        MultiEffect.__init__(self, *effects)


SCENES = [
    Scene(
        "roman-candle",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(30, 30, 30)),
            RomanCandleLauncher(start_col = 16)
        ]),

    Scene(
        "around-the-world",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(30, 30, 30)),
            AroundTheWorldLauncher(start_col = 16)
        ])
]
