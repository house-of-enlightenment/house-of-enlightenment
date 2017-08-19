import numpy as np

from hoe.state import STATE


def randrange(low, high):
    return np.random.rand() * (high - low) + low


def faderInterpolate(fader, my_low, my_high):
    h = float(my_high)
    l = float(my_low)
    return (fader / 100.0) * (h - l) + l


def sliceForStation(station_id):
    station_id = (station_id + 3) % 6
    return (slice(0, STATE.layout.rows), slice(station_id * 11, (station_id + 1) * 11))
