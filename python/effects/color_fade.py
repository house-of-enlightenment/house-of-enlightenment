from __future__ import division

import json
import math
import random
import sys
import time

import numpy as np

from hoe import animation_framework as af
from hoe import layout
from hoe import opc
from hoe import osc_utils
from hoe import color_utils
from hoe import pixels
from hoe.state import STATE


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


# I'm using uint8 overflows intentionally
# so don't need the error warnings
np.seterr(over='ignore')


class Static(af.Effect):
    def scene_starting(self, now, osc):
        self.switch = 0
        self.my_pixels = pixels.allocate_pixel_array(STATE.layout)

    def next_frame(self, pixels, now, state, osc):
        if now > self.switch:
            self._next_frame()
            self.switch = now + .1
        pixels[:] = self.my_pixels

    def _next_frame(self):
        sources = np.random.randint(0, 6, len(self.my_pixels))
        colors = np.array([RED, BLUE, GREEN, BLACK, BLACK, BLACK])
        for i in range(3):
            c = np.choose(sources, colors[:, i])
            self.my_pixels[:, i] = c


SCENES = [
    af.Scene(
        'rgb-static',
        tags=[],
        collaboration_manager=af.NoOpCollaborationManager(),
        effects=[Static()]
    ),
]
