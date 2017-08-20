import sys
import colorsys
import random as rand
import numpy as np

from hoe import color_utils
from hoe.animation_framework import Scene, Effect, MultiEffect
from hoe import color_utils
from hoe.state import STATE
from hoe.utils import fader_interpolate

from generic_effects import NoOpCollaborationManager, FrameRotator
from shared import SolidBackground

from zigzag import ZigZag


class SeizureMode(Effect):
    def __init__(self, station=None, duration=None):
        self.foo = 1
        if station is None:
            self.slice = (slice(0, STATE.layout.rows), slice(0, STATE.layout.columns))
        else:
            self.slice = (slice(0, STATE.layout.rows), slice(STATE.layout.STATIONS[station].left,
                                                             STATE.layout.STATIONS[station].right))

        self.on = True
        self.delta_t = 0.05
        self.last_step = 0
        self.duration = duration
        self.station = station
        self.start_time = None

    def scene_starting(self, now, osc_data):
        self.start_time = now

    def next_frame(self, pixels, now, collaboration_state, osc_data):

        if self.start_time is None:
            self.start_time = now

        self._set_speed_from(osc_data)

        if now - self.last_step > self.delta_t:
            self.last_step = now
            self.on = not self.on

        if self.on:
            pixels[self.slice] = (255, 255, 255)
        else:
            pixels[self.slice] = (0, 0, 0)

    def is_completed(self, now, osc_data):
        if self.duration is None:
            return False  # Run Forevas

        return now > self.start_time + self.duration

    def _set_speed_from(self, osc_data):
        if self.station is None:
            return

        fader = osc_data.stations[self.station].faders[0]
        self.delta_t = fader_interpolate(fader, 0.0005, 0.2)


class UpBlock(Effect):
    def __init__(self, station=0, speed=20, height=5, width=1, color=(0xFF, 0, 0)):
        self.station = station
        self.height = height
        self.width = width
        self.color = color
        self.speed = speed
        self.offset = int(self.station * 11 + 11 / 2 - self.width / 2)
        self.start_time = None

    def scene_starting(self, now, osc_data):
        self.start_time = now

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if self.start_time is None:
            self.start_time = now

        height = self._height(now)
        height_slice = slice(height, height + self.height)
        width_slice = slice(self.offset, self.offset + self.width)
        pixels[height_slice, width_slice] = self.color

    def _height(self, now):
        if self.start_time is None:
            self.start_time = now

        return int((now - self.start_time) * self.speed + self.height)

    def is_completed(self, now, osc_data):
        return self._height(now) >= STATE.layout.rows


class WaveLauncher(MultiEffect):
    def __init__(
            self,
            except_station=None,
            time_out=15):
        MultiEffect.__init__(self)
        self.except_station = except_station
        self.last_launch = None
        self.time_out = time_out

    def _color(self):
        if bool(rand.getrandbits(1)):
            return (0xFF, 0, 0)
        else:
            return (0, 0xFF, 0)

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)

        if self._did_time_out(now):
            self._launch_effect(now)
            return

        for sid, station in enumerate(osc_data.stations):
            if station.button_presses:
                if sid != self.except_station:
                    self._launch_effect(now, sid)

    def _did_time_out(self, now):
        return self.last_launch is None or now - self.last_launch > self.time_out

    def _launch_effect(self, now, station_id=None):
        self.last_launch = now
        if station_id is None:
            station_id = rand.randint(0, 5)
        self.add_effect(self.launch_effect(station_id))

    def launch_effect(self, station_id):
        raise NotImplementedError


class LaunchUpBlock(WaveLauncher):

    def launch_effect(self, sid):
        return UpBlock(station=sid, speed=rand.randint(10, 50), color=self._color())


class LaunchZigZag(WaveLauncher):

    def launch_effect(self, sid):
        return ZigZag(color=self._color(), start_col=sid * 11)


class LaunchSeizure(MultiEffect):
    def __init__(self, button=4):
        MultiEffect.__init__(self)
        self.button = button

    def _is_effect_on_in(self, sid):
        return len([s for s in self.effects if s.station == sid]) > 0

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)

        for sid, station in enumerate(osc_data.stations):
            buttons = station.button_presses
            if buttons and self.button in buttons and not self._is_effect_on_in(sid):
                self.add_effect(SeizureMode(station=sid, duration=3))


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

    def __init__(self,
                 station=None,
                 master_station=None,
                 auto_damp=True,
                 base_hue=0xFFFF >> 1,
                 boundary=CONTINUOUS,
                 pde=WAVE):
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

    def _should_zero(self, osc_data):
        if self.master_station is None:
            return

        buttons = osc_data.stations[self.master_station].button_presses
        return buttons and 4 in buttons

    def _set_force(self, osc_data):
        if self.master_station is None:
            return

        buttons = osc_data.stations[self.master_station].button_presses
        if not buttons:
            return

        if 2 in buttons:
            self.force_constant = max(-1000, self.force_constant - 100)
            print(self.force_constant)

        if 3 in buttons:
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

        if 0 in buttons:
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

        hsv = np.zeros((self.X_MAX, self.Y_MAX, 3), np.uint8)
        hsv[:, :, 0] = self.pixels[2] / 0xFFFF * 0xFF
        hsv[:, :, 1] = 0xFF
        hsv[:, :, 2] = 0xFF

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
        if chaos > 2.5 and self.diffusion_constant < 0.001:
            self.diffusion_constant = self.diffusion_constant * 1.1

        if chaos < 0.35 and self.diffusion_constant > 0.00000001:
            self.diffusion_constant = self.diffusion_constant * 0.9

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
        f = np.where(color == 0xFF0000, 0xFFFF,
                     np.where(color == 0xFF00, 0 - 0xFFFF,
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

#========================================================================

SCENES = [
    Scene(
        "full_seizuree",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(), SeizureMode()]),
    Scene(
        "seizure_mode",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[LaunchSeizure()]),
    Scene(
        "waves_of_diffusion",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(0xFF, 0, 0), start_col=0, end_col=2, start_row=30, end_row=34),
            #SolidBackground(color=(0,0xFF,0), start_col=0, end_col=2, start_row=120, end_row=124),
            FrameRotator(rate=0.5),
            FiniteDifference(
                master_station=0,
                boundary=FiniteDifference.NEUMANN,
                base_hue=0)
        ]),
    Scene(
        "up_bloc",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            LaunchUpBlock(except_station=0),
            FiniteDifference(master_station=0, boundary=FiniteDifference.NEUMANN)
        ]),
    Scene(
        "zig_wave",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(0, 0, 0xFF)),
            LaunchZigZag(except_station=0),
            FiniteDifference(master_station=0, boundary=FiniteDifference.NEUMANN)
        ]),
    Scene(
        "zig_fusion",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(0, 0, 0xFF)),
            LaunchZigZag(except_station=0),
            FiniteDifference(
                master_station=0,
                boundary=FiniteDifference.NEUMANN,
                pde=FiniteDifference.DIFFUSION)
        ])
]
