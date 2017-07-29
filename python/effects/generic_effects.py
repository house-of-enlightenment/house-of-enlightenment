from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import MultiEffect
from random import getrandbits
from hoe.layout import layout


class SolidBackground(Effect):
    """Always return a color"""

    def __init__(self, color=(255, 0, 0)):
        Effect.__init__(self)
        self.color = color
        print "Created with color", self.color

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        pixels[:] = self.color


class AdjustableFillFromBottom(Effect):
    def __init__(self, max_in=100):
        Effect.__init__(self)
        self.color_scale = 255.0 / max_in
        self.row_scale = 216.0 / max_in

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(layout().pixels):
            self.fill(pixels, t, coord, ii, osc_data)

    def fill(self, pixels, time, coord, ii, osc_data):
        # TODO Check for existance of fade
        if osc_data.stations[5].faders[0] * self.row_scale > coord["row"]:
            pixels[ii] = tuple(
                [int(osc_data.stations[i].faders[0] * self.color_scale) for i in range(3)])


class RisingTide(Effect):
    def __init__(self,
                 target_color=(255, 255, 255),
                 start_color=(10, 10, 10),
                 start_column=0,
                 end_column=None,
                 bottom_row=2,
                 top_row=None):
        self.target_color = target_color
        self.start_color = start_color
        self.start_column = start_column
        self.end_column = end_column
        self.bottom_row = bottom_row
        self.top_row = top_row
        self.curr_top = self.bottom_row
        self.curr_bottom = self.bottom_row
        self.completed = False

        self.colors = [start_color]
        self.color_inc = tuple(
            map(lambda t, s: (0.0 + t - s) / (self.top_row - self.bottom_row), target_color,
                start_color))
        print self.start_color, self.target_color, self.color_inc

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.curr_top < self.top_row:
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]

            self.colors = [tuple(map(lambda c, i: c + i, self.colors[0], self.color_inc))
                           ] + self.colors
            self.curr_top += 1
        elif self.curr_bottom < self.top_row:
            self.colors = self.colors[:-1]
            self.curr_bottom += 1
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]
        else:
            self.completed = True

    def is_completed(self, t, osc_data):
        return self.completed


class TideLauncher(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s in range(layout().sections):
            if osc_data.stations[s].buttons:
                self.launch_effect(t, s)

    def launch_effect(self, t, s):
        per_section = int(layout().columns / layout().sections)
        c = (bool(getrandbits(1)), bool(getrandbits(1)), bool(getrandbits(1)))
        print c
        if not any(c):  #  Deal with all 0's case
            c = (True, True, True)
        print c
        start_color = (c[0] * 10, c[1] * 10, c[2] * 10)
        target_color = (c[0] * 255, c[1] * 255, c[2] * 255)
        e = RisingTide(
            start_column=s * per_section,
            end_column=(s + 1) * per_section,
            bottom_row=0,
            top_row=216,
            target_color=target_color,
            start_color=start_color)
        self.effects.append(e)


class NoOpCollaborationManager(CollaborationManager):
    def compute_state(self, t, collaboration_state, osc_data):
        pass


__all__ = [Scene("risingtide", NoOpCollaborationManager(), SolidBackground(), TideLauncher())]
