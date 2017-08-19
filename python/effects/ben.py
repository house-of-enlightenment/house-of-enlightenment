import numpy as np
from hoe import color_utils
import colorsys
import sys
from hoe.animation_framework import Scene, Effect, MultiEffect
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
from generic_effects import FrameRotator

from hoe import color_utils
from hoe.state import STATE
from hoe.utils import fader_interpolate

import random as rand

class SeizureMode(Effect):
    def __init__(self, station = None, duration = None):
        self.foo = 1
        if station is None:
            self.slice = ( slice(0,STATE.layout.rows), slice(0, STATE.layout.columns))
        else:
            self.slice = (
                    slice(0,STATE.layout.rows),
                    slice(STATE.layout.STATIONS[station].left, STATE.layout.STATIONS[station].right))

        self.on = True
        self.delta_t = 0.05
        self.last_step = 0;
        self.duration = duration
        self.station = station
        self.start_time = None

    def scene_starting(self, now):
        self.start_time = now

    def next_frame(self, pixels, now, collaboration_state, osc_data):

        if self.start_time is None:
            self.start_time = now

        self._set_speed_from(osc_data)

        if now - self.last_step > self.delta_t:
            self.last_step = now
            self.on = not self.on

        if self.on:
            pixels[self.slice] = (255,255,255)
        else:
            pixels[self.slice] = (0,0,0)

    def is_completed(self, now, osc_data):
        if self.duration is None:
            return False # Run Forevas

        return now > self.start_time + self.duration

    def _set_speed_from(self, osc_data):
        if self.station is None:
            return

        fader = osc_data.stations[self.station].faders[0]
        self.delta_t = fader_interpolate(fader, 0.0005, 0.2)


class UpBlock(Effect):
    def __init__(self, station = 0, speed=20, height = 5, width = 1, color = (0xFF,0,0)):
        self.station = station
        self.height = height
        self.width = width
        self.color = color
        self.speed = speed
        self.offset = int(self.station*11 + 11/2 - self.width/2)
        self.start_time = None

    def scene_starting(self, now, osc_data ):
        self.start_time = now

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if self.start_time is None:
            self.start_time = now

        height = self._height(now)
        height_slice = slice(height, height + self.height)
        width_slice = slice(self.offset, self.offset+self.width)
        pixels[height_slice, width_slice] = self.color

    def _height(self, now):
        if self.start_time is None:
            self.start_time = now

        return int( (now - self.start_time)*self.speed + self.height);

    def is_completed(self, now, osc_data):
        return self._height(now) >= STATE.layout.rows


class LaunchUpBlock(MultiEffect):
    def __init__(self, except_station = None):
        MultiEffect.__init__(self)
        self.except_station = except_station
        self.positive_force = True

    def _color(self):
        if self.positive_force:
            return (0xFF,0,0)
        else:
            return (0,0xFF,0)

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)
        for sid, station in enumerate(osc_data.stations):
            if station.button_presses:
                if sid != self.except_station:
                    self.add_effect( UpBlock(station=sid, speed=rand.randint(10,50), color=self._color() ) )
                    self.positive_force = bool(rand.getrandbits(1))


class LaunchSeizure(MultiEffect):

    def __init__(self, station = None, button = 0 ):
        MultiEffect.__init__(self)
        self.station = station
        self.button = 0

    def before_rendering(self, pixels, now, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, now, collaboration_state, osc_data)
        if self.count() > 0:
            return

        buttons = osc_data.stations[self.station].button_presses
        if buttons and self.button in buttons:
            self.add_effect( SeizureMode(station=self.station, duration = 3) )


##
# This runs an explicit 2d wave equation.
#
# OSC Button / Fader Input:
#   Slider => Damping: Higher value, more damping
#   Up/Down (3/2): => Input force from strong negitive to strong positive, force is applied based on all white pixels
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

    def __init__(self, station = None, master_station=None, auto_damp = True, base_hue = 0xFF >> 1, boundary = CONTINUOUS):
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

    def _reset(self, now):
        # Reset Constants
        self.force_constant = rand.randint(300,700)
        self.velocity_constant = rand.randint(10000,30000) # Lower Value == Faster Speed
        self.diffusion_constant = rand.uniform(0.0000001,0.0001) # Bigger Value == More Damping

        print("force: " + str(self.force_constant))
        print("1/velocity: " + str(self.velocity_constant))
        print("damping: " + str(self.diffusion_constant))

        # Reset Pixels
        self.pixels = []
        self._append_base_pixels()
        self._append_base_pixels()

        self.time = [(now-0.3)*1000, (now-0.6)*1000]

    def _append_base_pixels(self):
        # pylint: disable=no-member
        self.pixels.append(np.full((self.X_MAX, self.Y_MAX), self.base_hue, dtype=float))

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if len(self.pixels) == 0 or self._should_zero(osc_data):
            self._reset(now)

        delta_t  = (now*1000 - self.time[0])
        delta_t2 = delta_t*(self.time[0]-self.time[1])
        self.time[1] = self.time[0]
        self.time[0] = now*1000

        self._append_base_pixels()

        self._set_damping(osc_data)
        self._set_velocity(osc_data)
        self._set_force(osc_data)

        self.wave(pixels, delta_t, delta_t2)
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
            self.velocity_constant = min(50000, self.velocity_constant*1.1)
            print(self.velocity_constant)

        if 0 in buttons:
            self.velocity_constant = max(3000, self.velocity_constant*0.9)
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
        hsv[:,:,0] = self.pixels[2]/0xFFFF*0xFF
        hsv[:,:,1] = 0xFF
        hsv[:,:,2] = 0xFF

        rgb = color_utils.hsv2rgb(hsv)
        pixels[:self.X_MAX,:self.Y_MAX] = rgb

        self.pixels.pop(0)

    ##
    # Calculate next frame of explicit finite difference wave
    #
    def wave(self, pixels, delta_t, delta_t2):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if delta_t2 < 10:
            return

        # Calculate Force based on if if pixel is all white
        # pylint: disable=no-member
        pix = np.array(pixels[:,:][:], dtype=np.uint32)
        color = (pix[:,:,0] << 16) | (pix[:,:,1] << 8) | (pix[:,:,2])
        f = np.where(color == 0xFF0000, self.force_constant, np.where(color == 0xFF00, 0-self.force_constant, 0))[:self.X_MAX,:self.Y_MAX]

        c = self.velocity_constant
        beta = self.diffusion_constant
        h1 = self.pixels[0]

        h0 = self.pixels[1]
        h, idx = self.hCalc()
        h = (h - h0*idx)/c
        self._auto_damp(h, delta_t, delta_t2)
        h = (h - beta*(h0-h1)/delta_t)*delta_t2 + 2*h0 - h1 + f

        h = np.clip(h, 0, 0xFFFF)
        self.pixels[2] = h

    def _auto_damp(self, h_diff, delta_t, delta_t2):
        if not self.auto_damp:
            return

        chaos = np.sum(np.fabs(h_diff))/delta_t2
        if chaos > 2.5 and self.diffusion_constant < 0.001:
            self.diffusion_constant = self.diffusion_constant * 1.1

        if chaos < 0.35 and self.diffusion_constant > 0.00000001:
            self.diffusion_constant = self.diffusion_constant * 0.9


    def diffuse(self, delta_t):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if delta_t < 10:
            return

        v = self.diffusion_constant
        h0 = self.pixels[1]
        h, idx = self.hCalc()
        hDiff = (h - h0*idx)
        h = hDiff*delta_t/v + h0

        self.pixels[2] = np.clip(h, 0, 0xFFFF)

    ##
    # This is the differences between node i,j and it's closest neighbors
    # it's used in calculateing spatial derivitives
    #
    def hCalc(self):
        # pylint: disable=no-member
        h = np.zeros([self.X_MAX,self.Y_MAX], dtype=np.uint32)
        idx = 0
        h0 = self.pixels[1]

        if (self.influence & 0b0001) > 0:
            h[1:,:] = h[1:,:] + h0[:self.X_MAX-1,:]
            if self.boundary == self.NEUMANN:
                h[0,:] = h[0,:] + h0[1,:]
            elif self.boundary == self.CONTINUOUS:
                h[0,:] = h[0,:] + h0[self.X_MAX-1,:]

            idx = idx+1

        if (self.influence & 0b0010) > 0:
            h[:self.X_MAX-1,:] = h[:self.X_MAX-1,:] + h0[1:,:]
            if self.boundary == self.NEUMANN:
                h[self.X_MAX-1:,:] = h[self.X_MAX-1,:] + h0[self.X_MAX-2,:]
            elif self.boundary == self.CONTINUOUS:
                h[self.X_MAX-1:,:] = h[self.X_MAX-1,:] + h0[0,:]

            idx = idx+1

        if (self.influence & 0b0100) > 0:
            h[:,1:] = h[:,1:] + h0[:,:self.Y_MAX-1]
            h[:,0] = h[:,0] + h0[:,self.Y_MAX-1]
            idx = idx+1

        if (self.influence & 0b1000) > 0:
            h[:,:self.Y_MAX-1] = h[:,:self.Y_MAX-1] + h0[:,1:]
            h[:,self.Y_MAX-1] = h[:,self.Y_MAX-1] + h0[:,0]
            idx = idx+1

        return h, idx

    def wave_old(self, x, y, is_on, delta_t2):
        if delta_t2 < 10:
            return

        u = [0,0,0,0]
        idx = 0

        boundary = 0 if self.is_fixed_boundary else self.pixels[1][x,y]

        if (self.influence & 0b0001) > 0:
            value = boundary if x == 0 else self.pixels[1][x-1, y]
            u[idx] = value
            idx = idx + 1
        if (self.influence & 0b0010) > 0:
            value = boundary if x == self.X_MAX-1 else self.pixels[1][x+1, y]
            u[idx] = value
            idx = idx + 1
        if (self.influence & 0b0100) > 0:
            value = self.pixels[1][x, self.Y_MAX-1] if y == 0 else self.pixels[1][x, y-1]
            u[idx] = value
            idx = idx + 1
        if (self.influence & 0b0100) > 0:
            value = self.pixels[1][x,0] if y == self.Y_MAX-1 else self.pixels[1][x, y+1]
            u[idx] = value
            idx = idx + 1

        c = self.velocity_constant
        h0 = self.pixels[1][x,y]
        h1 = self.pixels[0][x,y]
        h = 0.0

        for i in range(idx):
            h = h + u[i] - h0

        f = self.force_constant if is_on else 0

        h = 2*h0 - h1 + h*delta_t2/c + f;

        if h < 0 :
            h = 0
        elif h > 0xFFFF:
            h = 0xFFFF

        self.pixels[2][x,y] = h


class Diffusion(Effect):
    def __init__(self):
        self.pixels = []
        self.last_step = 0
        self.influence = 0b1111
        self.diffusion_constant = 1000
        self.is_fixed_boundary = True
        self.X_MAX = STATE.layout.rows
        self.Y_MAX = STATE.layout.columns

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if len(self.pixels) == 0:
            # pylint: disable=no-member
            self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=np.uint16))

        delta_t = (now - self.last_step)*1000
        self.last_step = now

        # pylint: disable=no-member
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=np.uint16))

        for i in range(self.X_MAX):
            for j in range(self.Y_MAX):
                is_on = True if pixels[i,j][0] > 0 else False
                self.diffuse(i,j, is_on, delta_t)

        self.set_pixels(pixels)

    def set_pixels(self, pixels):
        for i in range(self.X_MAX):
            for j in range(self.Y_MAX):
                v = float(self.pixels[1][i,j])
                if v < 0xFFFF:
                    (r,g,b) =  colorsys.hsv_to_rgb(v/0xFFFF,1,1)
                    pixels[i,j] = (r*255, g*255, b*255)

        self.pixels.pop(0)

    def diffuse(self, x, y, is_on, delta_t):
        if delta_t < 10:
            return

        if is_on:
            self.pixels[1][x,y] = 0xFFFF
            return

        u = []
        idx = 0

        boundary = 0 if self.is_fixed_boundary else self.pixels[0][x,y]

        if (self.influence & 0b0001) > 0:
            value = boundary if x == 0 else self.pixels[0][x-1, y]
            u.append(value)
            idx = idx + 1
        if (self.influence & 0b0010) > 0:
            value = boundary if x == self.X_MAX-1 else self.pixels[0][x+1, y]
            u.append(value)
            idx = idx + 1
        if (self.influence & 0b0100) > 0:
            value = self.pixels[0][x, self.Y_MAX-1] if y == 0 else self.pixels[0][x, y-1]
            u.append(value)
            idx = idx + 1
        if (self.influence & 0b0100) > 0:
            value = self.pixels[0][x,0] if y == self.Y_MAX-1 else self.pixels[0][x, y+1]
            u.append(value)
            idx = idx + 1

        v = self.diffusion_constant
        h0 = self.pixels[0][x,y]
        h = 0.0

        for i in range(idx):
            h = h + u[i] - h0

        h = h*delta_t/v + h0

        if h < 0 :
            h = 0
        elif h > 0xFFFF:
            h = 0xFFFF

        #if h > 0 and h < 0xFFFF:
            #print(h)

        self.pixels[1][x,y] = h

SCENES = [
    Scene("seizure_mode",
         collaboration_manager=NoOpCollaborationManager(),
         effects=[
             SolidBackground(),
             SeizureMode()
         ]
        ),
    Scene("seizure",
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            LaunchSeizure(station = 0)
         ]
        ),
    Scene("waves_of_diffusion",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(0xFF,0,0), start_col=0, end_col=2, start_row=30, end_row=34),
            #SolidBackground(color=(0,0xFF,0), start_col=0, end_col=2, start_row=120, end_row=124),
            FrameRotator(rate = 0.5),
            FiniteDifference(master_station=0, boundary = FiniteDifference.NEUMANN)
            ]
        ),
    Scene("up_bloc",
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            LaunchUpBlock(except_station=0),
            #FrameRotator(rate = 0.5),
            FiniteDifference(master_station=0, boundary = FiniteDifference.NEUMANN)
            ]
        )
]


