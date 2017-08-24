import numpy as np

from hoe import color_utils
from hoe import transitions
from hoe import utils

MIN_HUE = -15
MAX_HUE = 15


class ColorTransition(transitions.Transition):
    """Walks around a color wheel.

    Starts at a given hue and then transitions to
    a very near complement and so on. Each hue transition
    happens while the color is dark.

    The parameters here are tuned so that this looks
    attractive amongst a group of other pixels that
    are driven by a `ColorTransition`.
    """
    N_STAGES = 4
    PERIOD = 2
    GAP = 0.025

    def __init__(self, hue):
        # using uint8 so that we don't have to take mod all of the time
        self.reference_hue = np.uint8(hue)
        self.switched_reference_hue = False
        self.set_hue()
        self.stage = -1
        self.value = 0
        self.switch_stage = np.random.randint(0, self.N_STAGES)
        self.switch_ref_hue_on_next_reset = False
        transitions.Transition.__init__(self)

    def set_hue(self):
        if np.random.rand() < .2:
            # 30% chance of picking the complementary color
            hue = self.reference_hue + np.uint8(128)
        else:
            hue = self.reference_hue
        offset = np.random.random_integers(MIN_HUE, MAX_HUE)
        self.hue = np.uint8(hue + offset)

    def update_reference_hue(self):
        # 119 is just off of half (128) so we make a slow, pretty walk
        # around the color wheel
        self.reference_hue = self.reference_hue + np.uint8(119)
        self.switched_reference_hue = True

    def _reset(self, now):
        # handle actions from the end of last stage
        if self.switch_ref_hue_on_next_reset:
            # print 'Updating hue', self.stage, self.idx
            assert self.end_pt < 12
            self.update_reference_hue()
            self.set_hue()
            self.switch_ref_hue_on_next_reset = False

        # now increment counter for this stage
        self.stage = (self.stage + 1) % self.N_STAGES
        # print 'stage:', self.stage, self.idx
        if self.stage == 0:
            self.switch_stage = np.random.randint(0, self.N_STAGES)
            self.switched_reference_hue = False
        super(ColorTransition, self)._reset(now)

    def next_pt(self):
        if self.switched_reference_hue:
            return weighted_bright()
        else:
            if self.switch():
                # print 'Need update', self.stage, self.idx
                self.switch_ref_hue_on_next_reset = True
                return dark()
            else:
                return weighted_bright()

    def switch(self):
        return self.stage == self.switch_stage

    def transition_period(self, now):
        return 1 + utils.randrange(-.2, .2)

    def update(self, now):
        # In playing around, full saturation looked the best
        sat = 255
        val = super(ColorTransition, self).update(now)
        val = int(val / 31.0 * 255)
        hsv = np.array((self.hue, sat, color_utils._GAMMA_CORRECTION[val]))
        return hsv


def dark():
    return 11


def weighted_bright():
    """Returns a medium to high bright value, with preference towards bright"""
    return np.random.choice([17, 18, 19, 20, 21] * 1 + [22, 23, 24, 25, 26] * 2 +
                            [27, 28, 29, 30, 31] * 3)
