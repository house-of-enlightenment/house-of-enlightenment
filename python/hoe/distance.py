"""Methods for converting time to distance

Here are two modes for calculating distance. The accurate method
allows for a variable number of pixels per frame, so if you want
to travel 100 pixels in a second, it will. This method also keeps
a consistent speed regardless of the frame rate

The consistent method only allows for movements in a fixed amount.
That means that if you want to move 100 pixels a second at 30fps,
you'll actually end up going 3pixels / frame or 90 pixels per second.

There is potentially another approach where, for example, if you
wanted 50 pixels / sec you would move 2 pixels / frame unles
frame_number % 3 == 0 then move only 1 pixel. I haven't figured out
how to generalize this or what it would look like in practice so it
hasn't been implemented.

The accurate method can cause a flicker.

"""
from __future__ import division

from hoe.state import STATE


def consistent_speed_to_pixels(speed, fps=None):
    if speed == 0:
        return PixelsPerFrame(0)
    fps = fps or STATE.fps
    if speed == fps:
        return PixelsPerFrame(1)
    # only one of these will have a value, depending
    # on whether we move fast or slow
    frames_per_pixel = fps // speed
    pixels_per_frame = speed // fps
    assert not (frames_per_pixel and pixels_per_frame)
    if frames_per_pixel:
        return FramesPerPixel(frames_per_pixel)
    else:
        return PixelsPerFrame(pixels_per_frame)


class FramesPerPixel(object):
    def __init__(self, frames_per_pixel):
        self.frames_per_pixel = frames_per_pixel
        self.count = 0

    def start(self, now):
        pass

    def update(self, now):
        self.count += 1
        if self.count >= self.frames_per_pixel:
            self.count = 0
            return 1
        else:
            return 0


# TODO: refactor this, it is essentially a constant transition
class PixelsPerFrame(object):
    def __init__(self, pixels_per_frame):
        self.pixels_per_frame = pixels_per_frame

    def start(self, now):
        pass

    def update(self, now):
        return self.pixels_per_frame


# this class will move the proper number of pixels regardless
# of FPS; But it looks funny as the output isn't
# consistent, so I haven't really found a use for it.
class AccurateSpeedToPixels(object):
    def __init__(self, speed):
        self.speed = speed
        self.residual = 0

    def start(self, now):
        self.last_time = now

    def update(self, now):
        elapsed = now - self.last_time
        self.last_time = now
        distance = self.speed * elapsed + self.residual
        px, self.residual = divmod(distance, 1)
        return int(px)


class VaryingPixelsPerFrame(object):
    """Calculate the number of pixels needed to move each frame for a speed

    Unlike AccurateSpeedToPixels, this ignores time and depends on an
    accurate frames / second.

    Args:
        speed: transition object, returns a value that is pixels / sec
    """
    def __init__(self, speed):
        self.speed = speed
        self.idx = 0

    def start(self, now):
        self.speed.start(now)

    def update(self, now):
        speed = self.speed.update(now)
        n_pixels = pixels_per_frame(speed, self.idx, STATE.fps)
        self.idx = (self.idx + 1) % STATE.fps
        return n_pixels


def pixels_per_frame(speed, i, fps):
    rate = speed / fps
    now = int(rate * (i + 1))
    before = int(rate * i)
    return now - before
