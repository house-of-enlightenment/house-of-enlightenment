import logging

import numpy as np

from hoe.state import STATE

DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s"
DEFAULT_FORMATTER = logging.Formatter(DEFAULT_FORMAT)


def randrange(low, high, shape=1):
    return np.random.random(shape) * (high - low) + low


def fader_interpolate(fader, my_low, my_high):
    h = float(my_high)
    l = float(my_low)
    return (fader / 100.0) * (h - l) + l


def configure_logging(level='INFO'):
    logging.basicConfig(format=DEFAULT_FORMAT, level=level)
