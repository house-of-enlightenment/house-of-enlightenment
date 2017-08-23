import random as rand
import numpy as np

from hoe import color_utils
from hoe.utils import fader_interpolate
from hoe.stations import StationButtons
from hoe.state import STATE
from hoe.animation_framework import Scene, Effect, MultiEffect


##
# This runs an explicit 2d wave equation.
#
# OSC Button / Fader Input:
#   Slider => Damping: Higher value, more damping
#
#   Up/Down (3/2): => Input force from strong negitive to strong
#   positive, force is applied based on all white pixels
#
#   Left/Right (1/0): => Slower / Faster wave propagation.
#   Center (4): Reset => Zeros out waves
#
# Forcing Function:
#   Is positive if a pixel is compleatly red (0xFF, 0, 0)
#   Is negitive is a pixel is compleatly green (0, 0xFF, 0)
#
class FiniteDifference(Effect):
    NEUMANN = "neumann"
    CONTINUOUS = "continuous"

    WAVE = "wave"
    DIFFUSION = "diffusion"

    HUE = 0
    SATURATION = 1
    VALUE = 2

    def __init__(self,
                 station=None,
                 master_station=None,
                 auto_damp=True,
                 base_hue=0xFFFF >> 1,
                 boundary=CONTINUOUS,
                 pde=WAVE,
                 darken_mids=False,
                 wave_type=HUE):
        self.pixels = []
        self.time = []
        self.fader_value = None
        self.influence = 0b1111
        self.X_MAX = STATE.layout.rows
        self.Y_MAX = STATE.layout.columns
        self.master_station = master_station
        self.auto_damp = auto_damp
        self.base_hue = base_hue
        self.boundary = boundary
        self.pde = pde
        self.darken_mids = darken_mids
        self.wave_type = wave_type

    def _reset(self, now):
        # Reset Constants
        self.force_constant = rand.randint(300, 700)
        self.velocity_constant = rand.randint(10000, 30000)  # Lower Value == Faster Speed
        self.diffusion_constant = rand.uniform(0.0000001, 0.0001)  # Bigger Value == More Damping

        print("force: " + str(self.force_constant))
        print("1/velocity: " + str(self.velocity_constant))
        print("damping: " + str(self.diffusion_constant))

        # Reset Pixels
        self.pixels = []
        self._append_base_pixels()
        self._append_base_pixels()

        self.time = [(now - 0.3) * 1000, (now - 0.6) * 1000]

    def _append_base_pixels(self):
        # pylint: disable=no-member
        self.pixels.append(np.full((self.X_MAX, self.Y_MAX), self.base_hue, dtype=float))

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if len(self.pixels) == 0 or self._should_zero(osc_data):
            self._reset(now)

        delta_t = (now * 1000 - self.time[0])
        delta_t2 = delta_t * (self.time[0] - self.time[1])
        self.time[1] = self.time[0]
        self.time[0] = now * 1000

        self._append_base_pixels()

        self._set_damping(osc_data)
        self._set_velocity(osc_data)
        self._set_force(osc_data)

        if self.pde == self.WAVE:
            self.wave(pixels, delta_t, delta_t2)
        elif self.pde == self.DIFFUSION:
            self.diffuse(pixels, delta_t)

        self.set_pixels(pixels)
        #self._update_buttons(osc_data)

    def _update_buttons(self, osc_data):
        buttons = osc_data.stations[self.master_station].button_presses
        if not buttons:
            return

        for bid in range(5):
            STATE.stations[self.master_station].buttons[bid] = StationButtons.BUTTON_ON

    def _should_zero(self, osc_data):
        if self.master_station is None:
            return

        buttons = osc_data.stations[self.master_station].button_presses
        return buttons and 2 in buttons

    def _set_force(self, osc_data):
        if self.master_station is None:
            return

        buttons = osc_data.stations[self.master_station].button_presses
        if not buttons:
            return

        if 4 in buttons:
            self.force_constant = max(-1000, self.force_constant - 100)
            print(self.force_constant)

        if 0 in buttons:
            self.force_constant = min(1000, self.force_constant + 100)
            print(self.force_constant)

    def _set_velocity(self, osc_data):
        if self.master_station is None:
            return

        buttons = osc_data.stations[self.master_station].button_presses
        if not buttons:
            return

        if 1 in buttons:
            self.velocity_constant = min(50000, self.velocity_constant * 1.1)
            print(self.velocity_constant)

        if 3 in buttons:
            self.velocity_constant = max(3000, self.velocity_constant * 0.9)
            print(self.velocity_constant)

    def _set_damping(self, osc_data):
        if self.master_station is None:
            return

        fader = osc_data.stations[self.master_station].faders[0]
        if self.fader_value is not None and fader != self.fader_value:
            self.diffusion_constant = fader_interpolate(fader, 0.00000001, 0.001)
            print(self.diffusion_constant)

        self.fader_value = fader

    def set_pixels(self, pixels):

        hsv = np.full((self.X_MAX, self.Y_MAX, 3), 0xFF, dtype=np.uint8)
        hsv[:, :, self.wave_type] = self.pixels[2] / 0xFFFF * 0xFF
        if self.wave_type == self.VALUE:
            hsv[:, :, 1] = 0
        if self.darken_mids:
            hsv[:, :, 2] = np.abs(self.pixels[2] - (0xFFFF >> 1)) / 0xFFFF * 0xFF

        rgb = color_utils.hsv2rgb(hsv)
        pixels[:self.X_MAX, :self.Y_MAX] = rgb

        self.pixels.pop(0)

    ##
    # Calculate next frame of explicit finite difference wave
    #
    def wave(self, pixels, delta_t, delta_t2):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if delta_t2 < 10:
            return

        # Calculate Force based on if pixels is red or green
        # pylint: disable=no-member
        pix = np.array(pixels[:, :][:], dtype=np.uint32)
        color = (pix[:, :, 0] << 16) | (pix[:, :, 1] << 8) | (pix[:, :, 2])
        f = np.where(color == 0xFF0000, self.force_constant,
                     np.where(color == 0xFF00, 0 - self.force_constant,
                              0))[:self.X_MAX, :self.Y_MAX]

        c = self.velocity_constant
        beta = self.diffusion_constant
        h1 = self.pixels[0]

        h0 = self.pixels[1]
        h, idx = self.hCalc()
        h = (h - h0 * idx) / c
        self._auto_damp(h, delta_t, delta_t2)
        h = (h - beta * (h0 - h1) / delta_t) * delta_t2 + 2 * h0 - h1 + f

        h = np.clip(h, 0, 0xFFFF)
        self.pixels[2] = h

    def _auto_damp(self, h_diff, delta_t, delta_t2):
        if not self.auto_damp:
            return

        chaos = np.sum(np.fabs(h_diff)) / delta_t2
        if chaos > 2.7 and self.diffusion_constant < 0.001:
            self.diffusion_constant = self.diffusion_constant * 1.1
            #print("AutoDamp: " + str(self.diffusion_constant))

        if chaos < 0.80 and self.diffusion_constant > 0.00000001:
            self.diffusion_constant = self.diffusion_constant * 0.98
            #print("AutoDamp: " + str(self.diffusion_constant))

    def diffuse(self, pixels, delta_t):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if delta_t < 5:
            return

        v = self.diffusion_constant
        h0 = self.pixels[1]
        h, idx = self.hCalc()
        hDiff = (h - h0 * idx)
        h = hDiff * delta_t * v + h0

        # pylint: disable=no-member
        pix = np.array(pixels[:, :][:], dtype=np.int64)
        color = (pix[:, :, 0] << 16) | (pix[:, :, 1] << 8) | (pix[:, :, 2])
        f = np.where(color == 0xFF0000, 0xFFFF, np.where(color == 0xFF00, 0 - 0xFFFF,
                                                         0))[:self.X_MAX, :self.Y_MAX]
        h = h + f
        h = np.clip(h, 0, 0xFFFF)
        self.pixels[2] = np.clip(h, 0, 0xFFFF)

    ##
    # This is the differences between node i,j and it's closest neighbors
    # it's used in calculateing spatial derivitives
    #
    def hCalc(self):
        # pylint: disable=no-member
        h = np.zeros([self.X_MAX, self.Y_MAX], dtype=np.uint32)
        idx = 0
        h0 = self.pixels[1]

        if (self.influence & 0b0001) > 0:
            h[1:, :] = h[1:, :] + h0[:self.X_MAX - 1, :]
            if self.boundary == self.NEUMANN:
                h[0, :] = h[0, :] + h0[1, :]
            elif self.boundary == self.CONTINUOUS:
                h[0, :] = h[0, :] + h0[self.X_MAX - 1, :]

            idx = idx + 1

        if (self.influence & 0b0010) > 0:
            h[:self.X_MAX - 1, :] = h[:self.X_MAX - 1, :] + h0[1:, :]
            if self.boundary == self.NEUMANN:
                h[self.X_MAX - 1:, :] = h[self.X_MAX - 1, :] + h0[self.X_MAX - 2, :]
            elif self.boundary == self.CONTINUOUS:
                h[self.X_MAX - 1:, :] = h[self.X_MAX - 1, :] + h0[0, :]

            idx = idx + 1

        if (self.influence & 0b0100) > 0:
            h[:, 1:] = h[:, 1:] + h0[:, :self.Y_MAX - 1]
            h[:, 0] = h[:, 0] + h0[:, self.Y_MAX - 1]
            idx = idx + 1

        if (self.influence & 0b1000) > 0:
            h[:, :self.Y_MAX - 1] = h[:, :self.Y_MAX - 1] + h0[:, 1:]
            h[:, self.Y_MAX - 1] = h[:, self.Y_MAX - 1] + h0[:, 0]
            idx = idx + 1

        return h, idx
