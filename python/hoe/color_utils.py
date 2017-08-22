#!/usr/bin/env python
"""Helper functions to make color manipulations easier."""

from __future__ import division
from math import cos, sin, pi

import numpy as np


def remap(x, oldmin, oldmax, newmin, newmax):
    """Remap the float x from the range oldmin-oldmax to the range newmin-newmax

    Does not clamp values that exceed min or max.
    For example, to make a sine wave that goes between 0 and 256:
        remap(sin(time.time()), -1, 1, 0, 256)

    """
    zero_to_one = (x - oldmin) / (oldmax - oldmin)
    return zero_to_one * (newmax - newmin) + newmin


def clamp(x, minn, maxx):
    """Restrict the float x to the range minn-maxx."""
    return max(minn, min(maxx, x))


def scaled_cos(x, offset=0, period=1, minn=0, maxx=1):
    """A cosine curve scaled to fit in a 0-1 range and 0-1 domain by default.

    offset: how much to slide the curve across the domain (should be 0-1)
    period: the length of one wave
    minn, maxx: the output range

    """
    value = cos((x / period - offset) * pi * 2) / 2 + 0.5
    return value * (maxx - minn) + minn


def contrast(color, center, mult):
    """Expand the color values by a factor of mult around the pivot value of center.

    color: an (r, g, b) tuple
    center: a float -- the fixed point
    mult: a float -- expand or contract the values around the center point

    """
    r, g, b = color
    r = (r - center) * mult + center
    g = (g - center) * mult + center
    b = (b - center) * mult + center
    return (r, g, b)


def clip_black_by_luminance(color, threshold):
    """If the color's luminance is less than threshold, replace it with black.

    color: an (r, g, b) tuple
    threshold: a float

    """
    r, g, b = color
    if r + g + b < threshold * 3:
        return (0, 0, 0)
    return (r, g, b)


def clip_black_by_channels(color, threshold):
    """Replace any individual r, g, or b value less than threshold with 0.

    color: an (r, g, b) tuple
    threshold: a float

    """
    r, g, b = color
    if r < threshold:
        r = 0
    if g < threshold:
        g = 0
    if b < threshold:
        b = 0
    return (r, g, b)


def mod_dist(a, b, n):
    """Return the distance between floats a and b, modulo n.

    The result is always non-negative.
    For example, thinking of a clock:
    mod_dist(11, 1, 12) == 2 because you can "wrap around".

    """
    return min((a - b) % n, (b - a) % n)


def gamma(color, gamma):
    """Apply a gamma curve to the color.  The color values should be in the range 0-1."""
    r, g, b = color
    return (max(r, 0)**gamma, max(g, 0)**gamma, max(b, 0)**gamma)


# adopted from
# https://gist.github.com/PolarNick239/691387158ff1c41ad73c#file-rgb_to_hsv_np-py-L68
#
# An alternative can be found here
# https://github.com/scikit-image/scikit-image/blob/master/skimage/color/colorconv.py#L299
def hsv2rgb(hsv):
    hsv = np.array(hsv)
    input_shape = hsv.shape
    hsv = hsv.reshape(-1, 3)
    h, s, v = hsv[:, 0] / 255, hsv[:, 1] / 255, hsv[:, 2]

    i = np.uint32(h * 6.0)  # pylint: disable=no-member
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6

    rgb = np.zeros_like(hsv, np.uint8)
    v, t, p, q = v.reshape(-1, 1), t.reshape(-1, 1), p.reshape(-1, 1), q.reshape(-1, 1)
    # This could probably be much faster if replaced with np.choose
    rgb[i == 0] = np.hstack([v, t, p])[i == 0]
    rgb[i == 1] = np.hstack([q, v, p])[i == 1]
    rgb[i == 2] = np.hstack([p, v, t])[i == 2]
    rgb[i == 3] = np.hstack([p, q, v])[i == 3]
    rgb[i == 4] = np.hstack([t, p, v])[i == 4]
    rgb[i == 5] = np.hstack([v, p, q])[i == 5]
    rgb[s == 0.0] = np.hstack([v, v, v])[s == 0.0]

    return rgb.reshape(input_shape)


def rainbow(size, hue_start, hue_end, saturation=255, value=255):
    hsv_pixels = np.zeros((int(size), 3), np.uint8)
    # converting to uint8 here automatically wraps around
    # so if we can use something like hue_start = 250 and hue_end = 286 => 30
    hsv_pixels[:, 0] = np.linspace(hue_start, hue_end, size).astype(np.uint8)
    hsv_pixels[:, 1] = saturation
    hsv_pixels[:, 2] = value
    return hsv2rgb(hsv_pixels)


def bi_rainbow(size, hue_start, hue_end, saturation=255, value=255):
    """Create a rainbow using color_utils.rainbow that returns to the start value"""
    r1 = rainbow(
        size=(size + 1) // 2,
        hue_start=hue_start,
        hue_end=hue_end,
        saturation=saturation,
        value=value)
    # Note that hue_end and hue_start are reversed
    r2 = rainbow(
        size=size // 2, hue_start=hue_end, hue_end=hue_start, saturation=saturation, value=value)
    return np.concatenate((r1, r2))


# Perception of LED brightness is not linear. This applies a correction
# so that we get approximately 32 equal steps of brightness
#
# Lookup table from:
# https://ledshield.wordpress.com/2012/11/13/led-brightness-to-your-eye-gamma-correction-no/
#
_BRIGHTNESS = [
    0, 1, 2, 3, 4, 5, 7, 9, 12, 15, 18, 22, 27, 32, 38, 44, 51, 58, 67, 76, 86, 96, 108, 120, 134,
    148, 163, 180, 197, 216, 235, 255
]
MAX_BRIGHTNESS = len(_BRIGHTNESS)


def linear_brightness(val):
    return _BRIGHTNESS[int(val)]


# from http://rgb-123.com/ws2812-color-output/
_GAMMA_CORRECTION = np.array([
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2,
    2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 11,
    11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 21, 21, 22, 22,
    23, 23, 24, 25, 25, 26, 27, 27, 28, 29, 29, 30, 31, 31, 32, 33, 34, 34, 35, 36, 37, 37, 38, 39,
    40, 40, 41, 42, 43, 44, 45, 46, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
    62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 83, 84, 85, 86, 88,
    89, 90, 91, 93, 94, 95, 96, 98, 99, 100, 102, 103, 104, 106, 107, 109, 110, 111, 113, 114, 116,
    117, 119, 120, 121, 123, 124, 126, 128, 129, 131, 132, 134, 135, 137, 138, 140, 142, 143, 145,
    146, 148, 150, 151, 153, 155, 157, 158, 160, 162, 163, 165, 167, 169, 170, 172, 174, 176, 178,
    179, 181, 183, 185, 187, 189, 191, 193, 194, 196, 198, 200, 202, 204, 206, 208, 210, 212, 214,
    216, 218, 220, 222, 224, 227, 229, 231, 233, 235, 237, 239, 241, 244, 246, 248, 250, 252, 255
])


def color_correct(rgbs):
    return _GAMMA_CORRECTION[rgbs]
