import numpy as np

from hoe.state import STATE


def randrange(low, high):
    return np.random.rand() * (high - low) + low


def fader_interpolate(fader, my_low, my_high):
    h = float(my_high)
    l = float(my_low)
    return (fader / 100.0) * (h - l) + l
