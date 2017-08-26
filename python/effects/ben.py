import sys
import colorsys
import random as rand
import numpy as np

from hoe import color_utils
from hoe.animation_framework import Scene, Effect, MultiEffect
from hoe.collaboration import NoOpCollaborationManager
from hoe.stations import StationButtons
from hoe.state import STATE
from hoe.utils import fader_interpolate

from generic_effects import FrameRotator
from shared import SolidBackground

from zigzag import ZigZag
from david import DavesAbstractLidarClass
from finite_difference import FiniteDifference


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

        fader = STATE.stations[self.station].fader_value
        self.delta_t = fader_interpolate(fader, 0.0005, 0.2)


##
# This effect is used in wedding0
# Instructions:
#   - Press white button on Station master_station (2) to setup scene
#     white and black sides of will be devided.
#   - Two people at the same time should press the red and green buttons on the
#     master_station (2). If they press the buttons at the same time, they should get a really
#     cool mixing effect. If one of them jumps the gun the scene will be overwelmed with
#     white or black.
#   - Pressing the white button will reset the effect.
#   - Pressing the yellow button is the same as pressing red & white at the same time.


# FYI: for wedding0, the FiniteDifference master_stationg (0) damper controlls damping.
#
class DevidedSouls(Effect):

    RED = 3
    GREEN = 1
    WHITE = 2
    YELLOW = 0

    def __init__(self, master_station=2):
        self.is_devided = True
        self.red_slice = (slice(0, STATE.layout.rows), slice(0, STATE.layout.columns / 2 - 1))
        self.green_slice = (slice(0, STATE.layout.rows), slice(STATE.layout.columns / 2 - 1,
                                                               STATE.layout.columns))
        self.is_green = True
        self.is_red = True
        self.master_station = master_station

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        self._update_red_green(osc_data)

        if self.is_red:
            pixels[self.red_slice] = (0xFF, 0, 0)
        if self.is_green:
            pixels[self.green_slice] = (0, 0xFF, 0)

    def _update_red_green(self, osc_data):

        buttons = osc_data.buttons[self.master_station]
        if not buttons:
            return

        if self.YELLOW in buttons:
            self.is_red = False
            self.is_green = False

        if self.RED in buttons:
            self.is_red = not self.is_red

        if self.GREEN in buttons:
            self.is_green = not self.is_green

        if self.WHITE in buttons:
            self.is_red = True
            self.is_green = True

        self._update_buttons()

    def _update_buttons(self):
        for sid in range(STATE.layout.sections):
            for bid in range(5):
                if sid == self.master_station and (bid == self.WHITE or
                                                   (bid == self.RED and self.is_red) or
                                                   (bid == self.GREEN and self.is_green)):
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_ON
                else:
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_OFF


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
    def __init__(self, except_station=None, time_out=15):
        MultiEffect.__init__(self)
        self.except_station = except_station
        self.last_launch = None
        self.time_out = time_out
        self.launch_button = 2
        #self._update_buttons()

    def _color(self):
        if bool(rand.getrandbits(1)):
            return (0xFF, 0, 0)
        else:
            return (0, 0xFF, 0)

    def _update_buttons(self):
        for sid in range(STATE.layout.sections):
            if sid == self.except_station:
                continue

            for bid in range(5):
                if bid == self.launch_button:
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_ON
                else:
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_OFF

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)

        if self._did_time_out(now):
            self._launch_effect(now)
            return

        for sid, buttons in osc_data.buttons.items():
            if buttons and self.launch_button in buttons:
                if sid != self.except_station:
                    self._launch_effect(now, sid)

    def _did_time_out(self, now):
        return self.last_launch is None or now - self.last_launch > self.time_out

    def _launch_effect(self, now, station_id=None):
        self.last_launch = now
        if station_id is None:
            station_id = rand.randint(0, 5)
        self.add_effect(self.launch_effect(station_id))
        #self._update_buttons()

    def launch_effect(self, station_id):
        raise NotImplementedError


class LaunchUpBlock(WaveLauncher):
    def launch_effect(self, sid):
        return UpBlock(station=sid, speed=rand.randint(10, 50), color=self._color())


class LaunchZigZag(WaveLauncher):
    def launch_effect(self, sid):
        return ZigZag(color=self._color(), start_col=sid * 11)


class LaunchSeizure(MultiEffect):
    def __init__(self, button=2):
        MultiEffect.__init__(self)
        self.button = button
        #self._update_buttons()

    def _update_buttons(self):
        for sid in range(STATE.layout.sections):
            for bid in range(5):
                if bid == self.button and not self._is_effect_on_in(sid):
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_ON
                else:
                    STATE.stations[sid].buttons[bid] = StationButtons.BUTTON_OFF

    def _is_effect_on_in(self, sid):
        return len([s for s in self.effects if s.station == sid]) > 0

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        old_count = self.count()
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)

        for sid, buttons in osc_data.buttons.items():
            if buttons and self.button in buttons and not self._is_effect_on_in(sid):
                self.add_effect(SeizureMode(station=sid, duration=3))


#========================================================================
# LIDAR


class RedGreenSquares(DavesAbstractLidarClass):
    def _color(self, obj_id):
        if obj_id % 2 == 0:
            return (0xFF, 0, 0)
        else:
            return (0, 0xFF, 0)

    def render_lidar_input(self, pixels, obj_id, row_bottom, row_top, col_left, col_right):
        if col_left <= col_right:
            pixels[row_bottom:row_top, col_left:col_right] = self._color(obj_id)
        else:
            pixels[row_bottom:row_top, col_left:STATE.layout.columns - 1] = self._color(obj_id)
            pixels[row_bottom:row_top, 0:col_right] = self._color(obj_id)


#========================================================================

SCENES = [
    Scene(
        "full_seizure",
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
            FiniteDifference(master_station=0, boundary=FiniteDifference.NEUMANN, base_hue=0)
        ]),
    Scene(
        "wedding0",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(0xFF, 0, 0), start_col=0, end_col=2, start_row=120, end_row=124),
            SolidBackground(
                color=(0, 0xFF, 0), start_col=33, end_col=35, start_row=120, end_row=124),
            SolidBackground(color=(0xFF, 0, 0), start_col=0, end_col=2, start_row=30, end_row=34),
            SolidBackground(color=(0, 0xFF, 0), start_col=33, end_col=35, start_row=30, end_row=34),
            FrameRotator(rate=0.24),
            DevidedSouls(),
            FiniteDifference(
                master_station=0,
                boundary=FiniteDifference.NEUMANN,
                auto_damp=False,
                base_hue=0,
                wave_type=FiniteDifference.VALUE)
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
            LaunchZigZag(except_station=0),
            FiniteDifference(master_station=0, boundary=FiniteDifference.NEUMANN)
        ]),
    Scene(
        "zig_fusion",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            LaunchZigZag(except_station=0),
            FiniteDifference(
                master_station=0, boundary=FiniteDifference.NEUMANN, pde=FiniteDifference.DIFFUSION)
            #darken_mids=bool(rand.getrandbits(1)))
        ]),
    Scene(
        "lidar_fusion",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            RedGreenSquares(),
            FiniteDifference(
                master_station=0,
                boundary=FiniteDifference.CONTINUOUS,
                pde=FiniteDifference.DIFFUSION,
                darken_mids=True)
        ]),
    Scene(
        "lidar_wave",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            RedGreenSquares(),
            FiniteDifference(
                master_station=0, boundary=FiniteDifference.CONTINUOUS, pde=FiniteDifference.WAVE)
        ])
]
