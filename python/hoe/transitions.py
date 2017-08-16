"""Help provide smooth transitions between two values.

I generally like the effect of having an animation:
- start at one random value
- pick a target
- smoothly transition to that target
- once hitting the target, pick a new target and repeat


"""
import numpy as np


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
            [231, 239, 247, 255] * 4
        )
        # pick a value between 192-256 (probably a very minor effect)
        val = np.random.randint(196, 256)
        return np.array([sat, val])


class HueTransition(Transition):
    def rnd_pt(self):
        # pick a hue to start with
        start = np.random.randint(0, 256)
        # pick how much of the color wheel we're going to take
        # a longer slice will have more colors
        length = 64 #np.random.randint(32, 64)
        end = start + length
        return np.array([start, end])

    def update(self, now):
        # for hues, there are two ways that the transition can go, clockwise
        # and counterclockwise.
        # This is always going clockwise
        #
        # TODO: on reset, pick a direction
        return super(HueTransition, self).update(now)


class CoordinatedTransition(Transition):
    def __init__(self):
        self.state = 'low'
        Transition.__init__(self)
        self.first_point = 1

    def rnd_pt(self):
        return np.random.randint(1, 66, (2,))
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
        diff = max(np.abs(self.end_pt - self.start_pt))
        return max(2, diff / 2)

    def start(self, now):
        # if self.start_time and self.start_time != now:
        #     raise Exception('Tried starting twice. Bad')
        super(CoordinatedTransition, self).start(now)

    # this is the row rotation
    def first(self):
        class Dummy(object):
            def start(_, now):
                self.start(now)
            def update(_, now):
                return self.update(now)[0]
            def __call__(_, now):
                return self.__call__(now)[0]
        return Dummy()

    # this is the structure rotation
    def second(self):
        class Dummy(object):
            def start(_, now):
                self.start(now)
            def update(_, now):
                return self.update(now)[1]
            def __call__(_, now):
                return self.__call__(now)[1]
        return Dummy()
