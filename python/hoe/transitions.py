"""Help provide smooth transitions between two values.

I generally like the effect of having an animation:
- start at one random value
- pick a target
- smoothly transition to that target
- once hitting the target, pick a new target and repeat
"""
import operator as op

import numpy as np

from hoe import utils


class Transition(object):
    def __init__(self):
        self.start_time = None

    def start(self, now):
        self.end_pt = self.rnd_pt()
        self._reset(now)
        return self

    def update(self, now):
        self.reset_if_needed(now)
        # make a linear step towards the end target
        delta = (self.end_pt - self.start_pt) * (now - self.start_time) / self.length
        return self.start_pt + delta

    def __call__(self, now):
        return self.update(now)

    def reset_if_needed(self, now):
        elapsed = now - self.start_time
        if elapsed > self.length:
            self._reset(now)

    def _reset(self, now):
        self.start_pt = self.end_pt
        self.end_pt = self.rnd_pt()
        self.length = self.transition_period(now)
        self.start_time = now

    def transition_period(self, now):
        return np.random.rand() * 3 + 1

    def rnd_pt(self):
        pass


class SpeedTransition(Transition):
    """Every `delay` seconds, pick a new random value"""

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        Transition.__init__(self)

    def rnd_pt(self):
        return np.random.randint(self.lower, self.upper)


class SVTransition(Transition):
    """Transition from one plane in Saturation-Value space to another"""

    def rnd_pt(self):
        # pick a saturation between 128-256 (128 is very pastel, 256 is full saturation)
        # drastically favoring full saturation
        sat = np.random.choice(
            #[135, 143, 151, 159] * 1 +
            #[167, 175, 183, 191] * 2 +
            #[199, 207, 215, 223] * 3 +
            [231, 239, 247, 255] * 4)
        # pick a value between 192-256 (probably a very minor effect)
        val = np.random.randint(196, 256)
        return np.array([sat, val])


class Fn(object):
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return self.fn(*args, **kwargs)


class RangeTransition(Transition):
    """Transition from one range (start, end) to another.

    This class provides 'raw' values. If you want things clipped or wrapped
    around, you'll need to provide a layer ontop of this.

    For example, if you want a range of hues, this class could output
    250 - 270 and you would need to map that to be from 250 - 14.

    Args:
        start: callable that returns a value for the start of the range
        length: callable that returns how long the range should be
    """
    def __init__(self, start, length):
        self.start = start
        self.length = length

    def rnd_pt(self):
        start = self.start()
        length = self.length()
        end = start + length
        return np.array([start, end])


class HueTransition(RangeTransition):
    def __init__(self, start=None, length=None):
        self.start = start or functools.partial(np.random.randint, 0, 256)
        self.length = length or functools.partial(np.random.randint, 48, 80)

    def update(self, now):
        # for hues, there are two ways that the transition can go, clockwise
        # and counterclockwise.
        # This is always going clockwise
        #
        # TODO: on reset, pick a direction
        return super(HueTransition, self).update(now)

    @classmethod
    def all(cls):
        start = functools.partial(np.random.randint, 0, 256)
        # 32 is already a pretty small contrast.  This basically returns one color
        length = functools.partial(np.random.randint, 32, 256)
        return cls(start, length)


class CoordinatedTransition(Transition):
    # allows for two transitions to act in a coordinated fashion
    #
    # This class is very much so a work in progress
    def __init__(self):
        self.state = 'low'
        Transition.__init__(self)
        self.pts_a = list(self.yield_pts_a())
        self.pts_a = np.array(self.pts_a + list(reversed(self.pts_a)))
        # pylint: disable=invalid-unary-operand-type
        self.pts_a = np.concatenate((self.pts_a, -self.pts_a))
        self.idx_a = np.random.randint(0, len(self.pts_a))

        self.pts_b = list(self.yield_pts_b())
        # pylint: disable=invalid-unary-operand-type
        self.pts_b = np.array(self.pts_b + list(reversed(self.pts_b)))
        self.pts_b = np.concatenate((self.pts_b, -self.pts_b))
        self.idx_b = np.random.randint(0, len(self.pts_b))

    def yield_pts_b(self):
        val = 0
        diffs = [8, -4]
        while val < 70:
            for d in diffs:
                val += d
                yield val

    def yield_pts_a(self):
        val = 0
        diffs = [10, -5]
        while val < 56:
            for d in diffs:
                val += d
                yield val

    def rnd_pt(self):
        # row, structure
        # --, rotation
        # first value is pixels / second that the bottom row rotates
        # the second value is pixels / frame
        #return np.array([26, 26])
        if self.state == 'low':
            self.state = 'high'
            return np.array((16, 18))
            return np.array([4, 11])
        else:
            self.state = 'low'
            return np.array((16, 8))
            return np.array([13, 4])
        pt = np.array((self.pts_a[self.idx_a], self.pts_b[self.idx_b]))
        self.idx_a = (self.idx_a + 1) % len(self.pts_a)
        self.idx_b = (self.idx_b + 1) % len(self.pts_b)
        return pt
        # return np.random.randint(1, 66, (2,))
        # if np.random.rand() < .5:

        # else:
        #     return np.random.randint(1, 66, (2,))
        #     return np.array((60, 40))

        # print 'state:', self.state
        # if self.state == 'low':
        #     self.state = 'high'
        #     print 'state:', self.state
        #     if np.random.rand() < .5:
        #         return np.array((40, 60))
        #     else:
        #         return np.array((60, 40))
        # else:
        #     self.state = 'low'
        #     self.first_point += 1
        #     print 'faster structure rotation', self.first_point
        #     return np.array((self.first_point, 60))

    def transition_period(self, now):
        return utils.randrange(4, 9)
        diff = max(np.abs(self.end_pt - self.start_pt))
        return max(2, diff / 2)

    def start(self, now):
        # if self.start_time and self.start_time != now:
        #     raise Exception('Tried starting twice. Bad')
        super(CoordinatedTransition, self).start(now)

    # this is the row rotation
    def first(self):
        return _SingleCoordinatedTransition(self, op.itemgetter(0))

    # this is the structure rotation
    def second(self):
        return _SingleCoordinatedTransition(self, op.itemgetter(1))


class _SingleCoordinatedTransition(object):
    """Helper class for Coordinated Transition.

    Each transition in coordinated transition need to follow the transition
    interface, so this provides that.

    Args:
        trans: the parent coordinated transition
        getter: callable that extracts the individual results from the grouped results
    """
    def __init__(self, trans, getter):
        self.trans = trans
        self.getter = getter

    def start(self, now):
        return self.trans.start(now)

    def update(self, now):
        return self.getter(self.trans.update(now))

    def __call__(self, now):
        return self.getter(self.trans(now))
