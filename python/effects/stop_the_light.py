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

from hoe.animation_framework import SceneDefinition
from hoe.animation_framework import EffectDefinition
from hoe.animation_framework import Effect

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

class StopTheLight(Effect):
    def __init__(self, layout, n_pixels, strip_bottom=5, strip_top=20):
        Effect.__init__(self, layout, n_pixels)
        self.target_location = 15 # Moved to not deal with wrap-around case at 2am
        # self.rotation_speed = .5 # rotation / second
        self.sprite_location=20
        self.direction=1
        self.hit_countdown=0
        self.sprite_color=BLUE

        # Framework currently does not support args to vary effects, but when it does, this will come in handy
        self.strip_bottom=strip_bottom
        self.strip_top=strip_top

        self.hoe_layout = Layout(self.layout)
        self.bottom_rows = set(reduce(lambda a,b: a+b, [self.hoe_layout.row[i] for i in range(self.strip_bottom, self.strip_top)]))
        self.target_idx = self.bottom_rows & set(self.hoe_layout.slice[self.target_location])

        self.max_slice = max(self.hoe_layout.slice)

    def next_frame(self, pixels, t, osc_data):

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
                self.sprite_location = (self.sprite_location + self.direction) % self.max_slice
                self.sprite_color = BLUE

        sprite_idx = (
            self.bottom_rows &
            set.union(
                *[
                    set(self.hoe_layout.slice[i % (self.max_slice + 1)])
                    for i in
                    (self.sprite_location - 1, self.sprite_location, self.sprite_location + 1)
                ])
        )

        # Now we are ready to color things in:

        # Since this will be a foreground layer, we can't fall back to other pix in the bottoms rows
        for idx in self.bottom_rows:
            pixels[idx] = pixels[idx] if pixels[idx] else \
                self.sprite_color if idx in sprite_idx else \
                    RED if idx in self.target_idx else \
                        BLACK


class SolidColor(Effect):
    def __init__(self, layout, n_pixels, color=(100, 100, 100)):
        Effect.__init__(self, layout, n_pixels)
        self.color = color

    """Always return color"""
    def next_frame(self, pixels, t, osc_data):
        for ii in range(self.n_pixels):
            pixels[ii] = pixels[ii] if pixels[ii] else self.color


__all__ = [
    SceneDefinition("stoplight", EffectDefinition("stoplight", StopTheLight), EffectDefinition("solid background", SolidColor))
]