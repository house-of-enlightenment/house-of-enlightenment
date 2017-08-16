"""Methods for converting time to distance

Here are two modes for calculating distance. The accurate method
allows for a variable number of pixels per frame, so if you want
to travel 100 pixels in a second, it will. This method also keeps
a consistent speed regardless of the frame rate

The consistent method only allows for movements in a fixed amount.
That means that if you want to move 100 pixels a second at 30fps,
you'll actually end up going 3pixels / frame or 90 pixels per second.

The accurate method can cause a flicker.
"""

from hoe.state import STATE


def consistent_speed_to_pixels(speed, fps=None):
    fps = fps or STATE.fps
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
        self.frames_per_pixel = self.frames_per_pixel
        self.count = 0

    def start(self, now):
        pass

    def __call__(self, now):
        self.count += 1
        if self.count >= self.frames_per_pixel:
            self.count = 0
            return 1


class PixelsPerFrame(object):
    def __init__(self, pixels_per_frame):
        self.pixels_per_frame = pixels_per_frame

    def start(self, now):
        pass

    def __call__(self, now):
        return self.pixels_per_frame


class AccurateSpeedToPixels(object):
    def __init__(self, speed):
        self.speed = speed
        self.residual = 0

    def start(self, now):
        self.last_time = now

    def __call__(self, now):
        elapsed = now - self.last_time
        self.last_time = now
        distance = self.speed * elapsed + self.residual
        px, self.residual = divmod(distance, 1)
        return int(px)
