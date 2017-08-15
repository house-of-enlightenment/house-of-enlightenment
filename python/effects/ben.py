import numpy as np
import colorsys
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from generic_effects import NoOpCollaborationManager
from generic_effects import SolidBackground
from generic_effects import FrameRotator

from hoe import color_utils
from hoe.state import STATE

class SeizureMode(Effect):
    def __init__(self):
        self.foo = 1
        self.slice = ( slice(0,STATE.layout.rows), slice(0, STATE.layout.columns))
        self.on = True
        self.delta_t = 0.05
        self.last_step = 0;

    def scene_starting(self, now):
        pass

    def next_frame(self, pixels, now, collaboration_state, osc_data):

        if now - self.last_step > self.delta_t:
            self.last_step = now
            self.on = not self.on

        if self.on:
            pixels[self.slice] = (255,255,255)
        else:
            pixels[self.slice] = (0,0,0)

class FiniteDifference(Effect):
    def __init__(self):
        self.pixels = []
        self.time = []
        self.forceConstant = 400
        self.velocityConstant = 45000.0
        self.diffusionConstant = self.velocityConstant/14.0
        self.influence = 0b1111
        self.isFixedBounary = False
        self.X_MAX = STATE.layout.rows
        self.Y_MAX = STATE.layout.columns / 2

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if len(self.pixels) == 0:
            self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))
            self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))
            self.time = [now*1000, (now-0.5)*1000]

        deltaT  = (now*1000 - self.time[0])
        deltaT2 = deltaT*(self.time[0]-self.time[1])
        self.time[1] = self.time[0]
        self.time[0] = now*1000

        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=np.uint16))

        #for i in range(self.X_MAX):
            #for j in range(self.Y_MAX):
                #is_on = True if pixels[i,j][0] > 0 else False
                #self.wave_old(i,j, is_on, deltaT2)

        self.wave(pixels, deltaT, deltaT2)
        self.setPixels(pixels)

    def setPixels(self, pixels):
        for i in range(self.X_MAX):
            for j in range(self.Y_MAX):
                #v = self.pixels[2][i,j] >> 8
                #pixels[i,j] = (v,v,v)
                v = float(self.pixels[2][i,j])
                (r,g,b) =  colorsys.hsv_to_rgb(v/0xFFFF,1,1)
                pixels[i,j] = (r*0xFF, g*0xFF, b*0xFF)

        self.pixels.pop(0)


    def wave(self, pixels, deltaT, deltaT2):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if deltaT2 < 10:
            return

        f = np.zeros([self.X_MAX,self.Y_MAX], dtype=np.uint16)
        for i in range(self.X_MAX):
            for j in range(self.Y_MAX):
                f[i,j] = self.forceConstant if pixels[i,j][0] > 0 else 0


        c = self.velocityConstant
        v = self.diffusionConstant
        h1 = self.pixels[0]
        h = np.zeros([self.X_MAX,self.Y_MAX], dtype=float)

        h0 = self.pixels[1]
        h, idx = self.hCalc()
        hDiff = (h - h0*idx)

        h = 2.0*h0 - 1.0*h1 + hDiff*deltaT2/c + f

        h = np.mod(h, 0xFFFF)
        h = np.clip(h, 0, 0xFFFF)
        self.pixels[2] = h

    def diffuse(self, delta_t):
        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=float))

        if delta_t < 10:
            return

        v = self.diffusionConstant
        h0 = self.pixels[1]
        h, idx = self.hCalc()
        hDiff = (h - h0*idx)
        h = hDif*delta_t/v + h0

        self.pixels[2] = np.clip(h, 0, 0xFFFF)

    def hCalc(self):
        h = np.zeros([self.X_MAX,self.Y_MAX], dtype=np.uint32)
        idx = 0
        h0 = self.pixels[1]

        if (self.influence & 0b0001) > 0:
            h[1:,:] = h[1:,:] + h0[:self.X_MAX-1,:]
            h[0,:] = h[0,:] + h0[self.X_MAX-1,:]
            idx = idx+1

        if (self.influence & 0b0010) > 0:
            h[:self.X_MAX-1,:] = h[:self.X_MAX-1,:] + h0[1:,:]
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

    def wave_old(self, x, y, is_on, deltaT2):
        if deltaT2 < 10:
            return

        u = [0,0,0,0]
        idx = 0

        boundary = 0 if self.isFixedBounary else self.pixels[1][x,y]

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

        c = self.velocityConstant
        h0 = self.pixels[1][x,y]
        h1 = self.pixels[0][x,y]
        h = 0.0

        for i in range(idx):
            h = h + u[i] - h0

        f = self.forceConstant if is_on else 0

        h = 2*h0 - h1 + h*deltaT2/c + f;

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
        self.diffusionConstant = 1000
        self.isFixedBounary = True
        self.X_MAX = STATE.layout.rows
        self.Y_MAX = STATE.layout.columns

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        if len(self.pixels) == 0:
            self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=np.uint16))

        delta_t = (now - self.last_step)*1000
        self.last_step = now

        self.pixels.append(np.empty([self.X_MAX, self.Y_MAX], dtype=np.uint16))

        for i in range(self.X_MAX):
            for j in range(self.Y_MAX):
                is_on = True if pixels[i,j][0] > 0 else False
                self.diffuse(i,j, is_on, delta_t)

        self.setPixels(pixels)

    def setPixels(self, pixels):
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

        boundary = 0 if self.isFixedBounary else self.pixels[0][x,y]

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

        v = self.diffusionConstant
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

__all__ = [
    Scene("seizure_mode",
         NoOpCollaborationManager(),
         SolidBackground(),
         SeizureMode()
        ),
    Scene("rotating_square",
        NoOpCollaborationManager(),
        SolidBackground(color=(255,255,255), start_col=0, end_col=2, start_row=100, end_row=105),
        FrameRotator(rate = 0.5),
        FiniteDifference()
        )
]


