from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import EffectFactory
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from random import choice
from random import randint
from itertools import product
from generic_effects import SolidBackground
from generic_effects import NoOpCollaborationManager
import numpy as np
import debugging_effects
import hoe.osc_utils


class ButtonChaseController(Effect, CollaborationManager):
    def __init__(
            self,
            draw_bottom_layer=True,
            num_stations=6,
            buttons_colors={
                0: (255, 0, 0),
                1: (0, 255, 0),
                2: (0, 0, 255),
                3: (255, 255, 0),
                4: (255, 255, 255)
            }, ):
        # TODO Is this super initialization needed?
        Effect.__init__(self)
        CollaborationManager.__init__(self)
        self.num_stations = num_stations
        self.button_colors = buttons_colors
        self.num_buttons = len(buttons_colors)
        self.next = None
        self.on = None
        self.all_combos = [c for c in product(range(num_stations), buttons_colors.keys())]
        self.off = []
        self.draw_bottom_layer = draw_bottom_layer

    def compute_state(self, t, collaboration_state, osc_data):
        if self.next[1] in osc_data.stations[self.next[0]].buttons:
            self.pick_next()
        # TODO Fail on miss
        # TODO Put into collaboration_state

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if not self.draw_bottom_layer:
            return

        pixels[0:2, :] = (0, 0, 0)
        for s, b in self.on:
            # TODO: Calculate based on section size and span 2 columns
            pixels[0:2, s * 11 + b * 2] = self.button_colors[b]

    def scene_starting(self):
        self.on = []
        self.off = [c for c in self.all_combos]
        self.pick_next()
        for s, client in enumerate(STATE.station_osc_clients):
            hoe.osc_utils.update_buttons(
                client=client,
                station_id=s,
                updates={
                    b: hoe.osc_utils.BUTTON_ON if (s, b) in self.on else hoe.osc_utils.BUTTON_OFF
                    for b in range(STATE.button_count)
                })

    def pick_next(self):
        if len(self.on) == self.num_stations * len(self.button_colors):  # TODO: Standardize this
            print "Finished!"
            self.on = []
        local_next = choice(self.off)
        self.next = local_next
        self.off.remove(local_next)
        self.on.append(local_next)  # Surprisingly this is not by-ref, and thus safe, so that's nice

        client = STATE.station_osc_clients[self.next[0]]
        if client:
            hoe.osc_utils.update_buttons(
                station_id=self.next[0],
                client=client,
                updates={self.next[1]: hoe.osc_utils.BUTTON_ON})
        else:
            print "Hit, but client is not initialized"

        # TODO Update the controller with the new next!
        print "Next is now", local_next


class RotatingWedge(Effect):
    def __init__(self,
                 color=(255, 255, 0),
                 width=5,
                 direction=1,
                 angle=1,
                 start_col=0,
                 additive=False,
                 scale_ratio=True):
        self.color = np.asarray(color, np.uint8)
        self.width = width
        self.direction = direction
        self.angle = angle * 1.0 * STATE.layout.columns / STATE.layout.rows if scale_ratio else angle
        self.start_col = 0
        self.end_col = start_col + width
        self.additive = additive

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.angle == 0:
            if self.start_col < self.end_col:
                self.update_pixels(
                    pixels=pixels, slices=[(slice(None), slice(self.start_col, self.end_col))])
            else:
                self.update_pixels(
                    pixels=pixels,
                    slices=[(slice(None), slice(self.start_col, None)), (slice(None), slice(
                        None, self.end_col))])
        else:
            # TODO Combine Slices or get Indexes?
            slices = [(slice(r, min(r + self.width, STATE.layout.rows)),
                       int(c) % STATE.layout.columns)
                      for r, c in enumerate(
                          np.arange(self.start_col, self.start_col + self.angle * STATE.layout.rows,
                                    self.angle))]
            self.update_pixels(pixels=pixels, slices=slices)
        self.start_col = (self.start_col + self.direction) % STATE.layout.columns
        self.end_col = (self.end_col + self.direction) % STATE.layout.columns

    def update_pixels(self, pixels, slices):
        for r, c in slices:
            if self.additive:
                pixels[r, c] += self.color
            else:
                pixels[r, c] = self.color


def button_launch_checker(t, collaboration_state, osc_data):
    for i in range(len(osc_data.stations)):
        if osc_data.stations[i].buttons:
            return True
    return False


class GenericStatelessLauncher(MultiEffect):
    def __init__(self, factory_method, launch_checker=button_launch_checker, **kwargs):
        MultiEffect.__init__(self)
        self.launch_checker = launch_checker
        self.factory_method = factory_method
        self.factory_args = kwargs

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        # TODO : Performance
        if self.launch_checker(t=t, collaboration_state=collaboration_state, osc_data=osc_data):
            self.add_effect(
                self.factory_method(
                    pixels=pixels,
                    t=t,
                    collaboration_state=collaboration_state,
                    osc_data=osc_data,
                    **self.factory_args))
            print "Effect count", len(self.effects)


def wedge_factory(**kwargs):
    varnames = RotatingWedge.__init__.__func__.__code__.co_varnames
    args = {n: kwargs[n] for n in varnames if n in kwargs}
    if "color" not in args:
        args["color"] = (randint(0, 255), randint(0, 255), randint(0, 255))
    if "direction" not in args:
        args["direction"] = randint(0, 1) * 2 - 1  # Cheap way to get -1 or 1
    if "angle" not in args:
        args["angle"] = randint(-1, 1)
    return RotatingWedge(**args)


__all__ = [
    Scene("buttonchaser", ButtonChaseController(draw_bottom_layer=True), SolidBackground()),
    Scene("wedges",
          NoOpCollaborationManager(),
          RotatingWedge(), GenericStatelessLauncher(wedge_factory, width=3, additive=False))
]
