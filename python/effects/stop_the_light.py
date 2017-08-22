import collections
import itertools
import logging
import random

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import color_utils
from hoe.state import STATE
from hoe import translations
from hoe import transitions

logger = logging.getLogger(__name__)

N_ROWS = 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
# the color of the sprite when its not active
LIGHT_BLUE = (135, 206, 250)


# Each time a certain section hits a target, that
# section gets less additional points.
# The easiest way to get to 100 is to have each
# section hit the target once (6 hits)
# The hardest way is to only have one section
# (12 hits)
PTS = (17, 14, 12, 11, 10, 9, 8, 7, 6, 4, 2, 1)

# start slow and fat
WidthSpeed = collections.namedtuple('WidthSpeed', 'width speed')

EASY = [5, 4, 3]
MEDIUM = [4, 3, 2]
HARD = [3, 3, 1]


ACTIVE = 'active'
HIT = 'hit'
MISS = 'miss'


class Level(object):
    def __init__(self, widths):
        self.widths = widths

    def width(self, hits, misses):
        idx = min(len(self.widths) - 1, hits // 4)
        return self.widths[idx]

    def speed(self, hits, misses):
        return .25 + .05 * hits

    @classmethod
    def easy(cls):
        return cls(EASY)

    @classmethod
    def medium(cls):
        return cls(MEDIUM)

    @classmethod
    def hard(cls):
        return cls(HARD)


class StopTheLight(collaboration.CollaborationManager, af.Effect):
    def __init__(self, layout):
        self.state = ACTIVE
        self.successful_sections = [0] * layout.sections
        self.fps = STATE.fps
        self.level = Level.medium()
        location = 0
        self.sprite = Sprite(
            layout, location,
            self.level.speed(0, 0),
            self.level.width(0, 0),
        )
        self.layout = layout
        self.misses = 0

    def hits(self):
        return sum(self.successful_sections)

    def update_sprite_difficulty(self):
        hits = self.hits()
        self.sprite.rotation_speed = self.level.speed(hits, self.misses)
        self.sprite.width = self.level.width(hits, self.misses)

    def set_target_idx(self):
        self.target_idx = self.layout.grid[self.bottom, self.section_centers]

    def scene_starting(self, now, osc):
        self.bottom = slice(None, N_ROWS, None)
        self.section_centers = [(s.left + s.right) / 2 for s in self.layout.STATIONS]
        self.set_target_idx()
        self.now = now
        self.ignore_buttons_until = self.now + random.random() * 2 + .5
        self.sprite.start(self.now)

    def init_pixels(self):
        self.pixels[self.bottom, :] = 32

    def compute_state(self, now, old_state, osc_data):
        if not self._ignore_buttons(now):
            self._read_osc_data(now, osc_data)
        return self._compute_scores()

    def _ignore_buttons(self, now):
        return self.state != ACTIVE or now < self.ignore_buttons_until

    def _compute_scores(self):
        scores = {}
        total = 0
        for i, hits in enumerate(self.successful_sections):
            score = sum(PTS[:hits])
            total += score
            scores[i] = score
        scores['total'] = total
        return scores

    def _read_osc_data(self, now, osc_data):
        button_pressed, hit_section = self._find_hit_section(now, osc_data)
        if not button_pressed:
            return
        columns = self.sprite.columns(now)
        sprite_idx = self.layout.grid[self.bottom, columns]
        if hit_section is None:
            logger.debug('a button was pressed, but missed the target')
            self.state = MISS
            self.flash = Flash(sprite_idx, .25, (RED, BLACK)).start(now)
            self.wait_until = self.now + 2
            self.misses += 1
        else:
            logger.debug('section %s was hit!', hit_section)
            self.state = HIT
            self.flash = Flash(sprite_idx, .25, (GREEN, BLACK)).start(now)
            self.wait_until = self.now + 3
            self.successful_sections[hit_section] += 1
            self.set_target_idx()
            self.update_sprite_difficulty()

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        self.now = now
        self.pixels = pixels
        self.init_pixels()
        self.pixels[self.target_idx] = YELLOW
        if self.state == ACTIVE:
            self._handle_active(pixels, now, collaboration_state, osc_data)
        elif self.state == HIT:
            self._flash_until_active(pixels, now)
        elif self.state == MISS:
            self._flash_until_active(pixels, now)
        else:
            raise Exception('You are in a bad state: {}'.format(self.state))

    def _flash_until_active(self, pixels, now):
        self.flash.render(now, self.pixels)
        if now >= self.wait_until:
            self.sprite.reverse(now)
            self.wait_until = None
            self.ignore_buttons_until = now + random.random() * 2 + .5
            self.state = ACTIVE

    def _handle_active(self, pixels, now, collaboration_state, osc_data):
        self.sprite.update(self.now)
        self.pixels[self.target_idx] = YELLOW
        columns = self.sprite.columns(now)
        # want to allow the sprite to move for a little while
        # before allowing any buttons to be pressed
        if self.now < self.ignore_buttons_until:
            # have the sprite be light blue until a button can be
            # pressed
            # TODO: maybe increase the wait time if a button
            # is pressed while the sprite is light blue; this will stop
            # people from just spamming the buttons, although
            # that is not a useful strategy.
            self.pixels[self.bottom, columns] = LIGHT_BLUE
            return
        else:
            self.pixels[self.bottom, columns] = BLUE

    def _find_hit_section(self, now, osc_data):
        """Returns whether a button was pressed and whether a target was hit.

        Returns:
            button_pressed: True if a button was pressed
            section_hit: if a target was hit, return the id of the section
                otherwise, it is a miss: return None.
        """
        columns = self.sprite.columns(now)
        button_pressed = False
        for i, station in enumerate(osc_data.stations):
            if station.button_presses:
                button_pressed = True
                target = self.section_centers[i]
                if target in columns:
                    return True, i
        return button_pressed, None


class Flash(object):
    def __init__(self, idx, duration, colors):
        self.idx = idx
        self.duration = duration
        self.colors = colors
        self.next_switch = None
        self.color_idx = 0

    def start(self, now):
        self.next_switch = now + self.duration
        return self

    def current_color(self):
        return self.colors[self.color_idx]

    def switch(self, now):
        self.next_switch = now + self.duration
        self.color_idx = (self.color_idx + 1) % len(self.colors)

    def render(self, now, pixels):
        if self.next_switch < now:
            self.switch(now)
        pixels[self.idx] = self.current_color()




class Sprite(object):
    def __init__(self, layout, start_location, rotation_speed, width):
        self.layout = layout
        self.start_location = start_location
        self._rotation_speed = rotation_speed
        self.location = start_location
        self.width = width
        self.start_time = None
        self._reversed = False

    def _get_rotation(self):
        if self._reversed:
            return -self._rotation_speed
        else:
            return self._rotation_speed

    def _set_rotation(self, val):
        self._rotation_speed = val
    rotation_speed = property(_get_rotation, _set_rotation)

    def start(self, now):
        self.start_time = now

    def reverse(self, now):
        self.start_location = self.location
        self._reversed = not self._reversed
        self.start(now)

    def update(self, now):
        sprite_rotation = (now - self.start_time) * self.rotation_speed
        location = int(self.layout.columns * sprite_rotation) + self.start_location
        self.location = location % self.layout.columns

    def columns(self, now):
        left = int(self.width / 2)
        right = self.width - left
        return map(self.layout.colmod, range(self.location - left, self.location + right))


class BarelyGray(af.Effect):
    def next_frame(self, pixels, *args, **kwargs):
        pixels[2:,:] = 10


SCENES = [
    af.Scene(
        'stop-the-light',
        tags=[af.Scene.TAG_GAME],
        collaboration_manager=StopTheLight(STATE.layout),
        effects=[BarelyGray()]
    )
]
