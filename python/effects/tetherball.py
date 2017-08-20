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
# BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
BLUE = ()
# ORANGE = (255, 127, 0)
ORANGE = (255, 127, 99)
BLUE = (0, 127, 255)


#
# - Corkscrew effect will get more "tight" as its wound
class TetherBall(CollaborationManager, Effect):
    def __init__(self):
        Effect.__init__(self)
        CollaborationManager.__init__(self)
        self.x = 0
        self.i = 0
        self.data = None
        self.direction = None

    def reset_state(self, osc_data):
        # type: (StoredOSCData) -> None
        """Resets the state for on, off, buttons, and timer"""
        # self.on = []
        # self.off = [c for c in self.all_combos]
        # self.next_button = None
        # self.flash_timer = 0
        for station in STATE.stations:
            station.buttons.set_all(on=False)
            station.buttons[1] = 1
            station.buttons[3] = 1
            # print station.buttons
        # self.pick_next(osc_data=osc_data)
        # def before_rendering(self, pixels, t, collaboration_state, osc_data):
        # MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        # for s in range(STATE.layout.sections):
        #     if osc_data.stations[s].button_presses:
        #         print osc_data.stations[s].button_presses
        # self.launch_effect(t, s)

    def scene_starting(self, now, osc_data):
        self.reset_state(osc_data=osc_data)

    def _button_press_is_valid(self, station_id):
        # self.x
        return True

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        # MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s in range(STATE.layout.sections):
            if osc_data.stations[s].button_presses:
                if 3 in osc_data.stations[s].button_presses and self._button_press_is_valid(s):
                    self.direction = "right"
                if 1 in osc_data.stations[s].button_presses and self._button_press_is_valid(s):
                    self.direction = "left"

        pixels[:, :] = ORANGE
        # slope = (0 - self.x)/216
        # slope = .02
        # print slope
        # pixels[215:216,0:2] = GREEN
        slope = (0 - self.x) / 216
        # print slope
        x = self.x

        for y in xrange(216):
            # pixels[216 - y - 1:216 - y, int(x):int(x +2)] = GREEN
            offset_x = x
            if x > 66:
                offset_x = x % 66

            if x < -66:
                offset_x = x % 66

            # print x
            pixels[y - 1:y, int(offset_x):int(offset_x + 5)] = BLUE

            x = x + slope

        # if self.i % 1 == 1:
        if self.direction == "right":
            self.x -= 1
        if self.direction == "left":
            self.x += 1

        self.i += 1

    def compute_state(self, t, collaboration_state, osc_data):
        pass


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


SCENES = [
    Scene(
        "tetherball",
        tags=[Scene.TAG_GAME, Scene.TAG_WIP],
        collaboration_manager=TetherBall(),
        # effects=[CollaborationCountBasedBackground()]
    )
]
