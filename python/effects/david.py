from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import EffectFactory
from hoe.animation_framework import MultiEffect
from hoe.layout import layout
from random import choice
from itertools import product
from generic_effects import SolidBackground
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
            client = osc_data.stations[self.next[0]].client
            if client:
                hoe.osc_utils.update_buttons(client, self.next[1], hoe.osc_utils.BUTTON_ON)
            else:
                print "Hit, but client is not initialized"
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

    def pick_next(self):
        if len(self.on) == self.num_stations * len(self.button_colors):  # TODO: Standardize this
            print "Finished!"
            self.on = []
        next = choice(self.off)
        self.next = next
        self.off.remove(next)
        self.on.append(next)  # Surprisingly this is not by-ref, and thus safe, so that's nice
        # TODO Update the controller with the new next!
        print "Next is now", next


__all__ = [Scene("buttonchaser", ButtonChaseController(draw_bottom_layer=True), SolidBackground())]
