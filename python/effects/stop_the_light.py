"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code.

from __future__ import division
import json
import Queue
import math
import sys
import time

from hoe.layout import Layout
from hoe import opc
from hoe import osc_utils

from hoe.scene_manager import SceneDefinition
from hoe.scene_manager import EffectDefinition
from hoe.scene_manager import Effect

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

class StopTheLight(Effect):
    def __init__(self, strip_bottom=0, strip_top=15):
        self.target_location = 15 # Moved to not deal with wrap-around case at 2am
        # self.rotation_speed = .5 # rotation / second
        self.sprite_location=20
        self.direction=1
        self.hit_countdown=0
        self.sprite_color=BLUE

        # Framework currently does not support args to vary effects, but when it does, this will come in handy
        self.strip_bottom=strip_bottom
        self.strip_top=strip_top

    def next_frame(self, layout, time, n_pixels, osc_data):
        hoe_layout = Layout(layout)
        bottom_rows = set(reduce(lambda a,b: a+b, [hoe_layout.row[i] for i in range(self.strip_bottom, self.strip_top)]))
        target_idx = bottom_rows & set(hoe_layout.slice[self.target_location])

        # Initialize the list of pixels.
        # TODO: Use None to allow this to be a foreground layer
        pixels = [WHITE] * len(hoe_layout.pixels)

        # Since this will be a foreground layer, we can't fall back to other pix in the bottoms rows
        for idx in bottom_rows:
            pixels[idx] = BLACK

        # Set the target to red.
        # Do this before drawing the moving object so we can overwrite it later if needed
        for idx in target_idx:
            pixels[idx] = RED

        max_slice = max(hoe_layout.slice)

        if self.hit_countdown:
            # Already hit, waiting to start moving again
            self.hit_countdown -= 1
        else:
            # A button was pressed!
            # For now just use b0
            if "b0" in osc_data.buttons and osc_data.buttons["b0"]:
                # Did it hit? TODO: Deal with wrap-around
                if self.target_location in (self.sprite_location-1, self.sprite_location, self.sprite_location+1):
                    # On a hit, set green and change directions. Wait 2 seconds
                    self.hit_countdown = 30*2  # TODO: make fps available or use time again
                    self.direction *= -1
                    self.sprite_color = GREEN
                else:
                    # On a miss, still pause, but for less, and change to the "bad" color
                    self.hit_countdown = 15
                    self.sprite_color = YELLOW
            else:  # No button pressed, so move and set the color back to blue (in case this is first frame back)
                self.sprite_location = (self.sprite_location + self.direction) % max_slice
                self.sprite_color = BLUE

        sprite_idx = (
            bottom_rows &
            set.union(
                *[
                    set(hoe_layout.slice[i % (max_slice + 1)])
                    for i in
                    (self.sprite_location - 1, self.sprite_location, self.sprite_location + 1)
                ])
        )

        for idx in sprite_idx:
            pixels[idx] = self.sprite_color

        return pixels

__all__ = [
    SceneDefinition("stoplight", EffectDefinition("stoplight", StopTheLight))
]