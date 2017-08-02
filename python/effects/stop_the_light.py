"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code.

from __future__ import division

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.state import STATE

from generic_effects import SolidBackground


WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)


class StopTheLight(CollaborationManager, Effect):
    def __init__(self, strip_bottom=5, strip_top=20):
        Effect.__init__(self)
        self.target_location = 15  # Moved to not deal with wrap-around case at 2am
        # self.rotation_speed = .5 # rotation / second
        self.sprite_location = 20
        self.direction = 1
        self.hit_countdown = 0
        self.sprite_color = BLUE

        # Framework currently does not support args to vary effects, but when it does, this will come in handy
        self.strip_bottom = strip_bottom
        self.strip_top = strip_top

        self.bottom_rows = set(
            reduce(lambda a, b: a + b,
                   [STATE.layout.row[i] for i in range(self.strip_bottom, self.strip_top)]))
        self.target_idx = self.bottom_rows & set(STATE.layout.slice[self.target_location])

        self.max_slice = max(STATE.layout.slice)

    def compute_state(self, t, collaboration_state, osc_data):
        if not "count" in collaboration_state.keys():
            collaboration_state["count"] = 1
        # A button was pressed!
        # For now just use b0
        if 0 in osc_data.stations[0].buttons:
            # Did it hit? TODO: Deal with wrap-around
            if self.target_location in (self.sprite_location - 1, self.sprite_location,
                                        self.sprite_location + 1):
                # On a hit, set green and change directions. Wait 2 seconds
                self.hit_countdown = 30 * 2  # TODO: make fps available or use time again
                self.direction *= -1
                self.sprite_color = GREEN
                collaboration_state["count"] = min(6, collaboration_state["count"] + 1)
            else:
                # On a miss, still pause, but for less, and change to the "bad" color
                self.hit_countdown = 15
                self.sprite_color = YELLOW
                collaboration_state["count"] = max(1, collaboration_state["count"] - 1)

        return collaboration_state

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.hit_countdown:
            # Already hit, waiting to start moving again
            self.hit_countdown -= 1
        else:
            # No button pressed, so move and set the color back to blue (in case this is first frame back)
            self.sprite_location = (self.sprite_location + self.direction) % self.max_slice
            self.sprite_color = BLUE

        sprite_idx = (self.bottom_rows & set.union(*[
            set(STATE.layout.slice[i % (self.max_slice + 1)])
            for i in (self.sprite_location - 1, self.sprite_location, self.sprite_location + 1)
        ]))

        # Now we are ready to color things in:

        # Since this will be a foreground layer, we can't fall back to other pix in the bottoms rows
        for idx in self.bottom_rows:
            pixels[idx] = self.sprite_color if idx in sprite_idx else \
                    RED if idx in self.target_idx else \
                        BLACK


class CollaborationCountBasedBackground(Effect):
    def __init__(self, color=(0, 255, 0), max_count=6, bottom_row=3, max_row=216):
        Effect.__init__(self)
        self.color = color
        self.bottom_row = bottom_row
        self.top_row_dict = {
            i: int(bottom_row + i * (max_row - bottom_row) / max_count)
            for i in range(1, max_count + 1)
        }
        self.current_level = int(bottom_row + (max_row - bottom_row) / max_count)
        self.target_row = self.current_level

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.target_row = self.top_row_dict[collaboration_state["count"]]
        if self.target_row > self.current_level:
            self.current_level += 1
        elif self.target_row < self.current_level:
            self.current_level -= 1

        for ii in set(
                reduce(lambda a, b: a + b,
                       [STATE.layout.row[i] for i in range(self.bottom_row, self.current_level)])):
            pixels[ii] = self.color


__all__ = [
    Scene("stoplight",
          StopTheLight(0, 2), SolidBackground((150, 150, 150)), CollaborationCountBasedBackground())
]
