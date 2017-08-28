from hoe import color_utils
from hoe.animation_framework import Scene, Game, Effect, MultiEffect
from hoe.collaboration import CollaborationManager
from hoe.animation_framework import OSCDataAccumulator
import hoe.lidar
import hoe.fountain_models as fm
from hoe.stations import StationButtons, BUTTON_COLORS
from hoe.state import STATE

from functools import partial
from random import choice, randint, getrandbits
from itertools import product
from math import ceil
from shared import SolidBackground
from generic_effects import Rainbow
from generic_effects import NoOpCollaborationManager
from generic_effects import FrameRotator
from generic_effects import FunctionFrameRotator

import examples
import numpy as np
import debugging_effects
import hoe.osc_utils


class ButtonChaseController(Effect, CollaborationManager):
    def __init__(
            self,
            buttons_colors=None,  # Button colors. Defaults to RED, GREEN, BLUE, YELLOW, WHITE
            num_stations=6,  # Deprecated
            draw_bottom_layer=True,  # Turn the bottom layer on or off
            flash_rate=10,  # Flash on (or off) every X frames
            # Time to hit before picking a new one (if backwards_progress, also lose progress)
            selection_time=1):

        # TODO Is this super initialization needed? Probably not, but future-proofs it
        Effect.__init__(self)
        CollaborationManager.__init__(self)

        # Don't use a dictionary as a default argument (mutable)
        if buttons_colors is None:
            buttons_colors = {
                0: (255, 0, 0),
                1: (0, 255, 0),
                2: (0, 0, 255),
                3: (255, 255, 0),
                4: (255, 255, 255)
            }

        self.button_colors = buttons_colors
        self.draw_bottom_layer = draw_bottom_layer
        self.flash_rate = flash_rate
        self.backwards_progress = None
        self.selection_time = selection_time

        # TODO Get from STATE
        self.num_stations = num_stations
        self.num_buttons = len(buttons_colors)
        self.all_combos = [c for c in product(range(num_stations), buttons_colors.keys())]

        # These all get set in the reset_state method called during scene initialization
        self.on = None
        self.off = []
        self.next_button = None
        self.flash_timer = 0

    def reset_state(self):
        """Resets the state for on, off, buttons, and timer"""
        self.on = []
        self.off = [c for c in self.all_combos]
        self.next_button = None
        self.flash_timer = 0
        for station in STATE.stations:
            station.buttons.set_all(on=False)

        sum_faders = sum(map(lambda station: station.fader_value, STATE.stations))
        self.backwards_progress = sum_faders > 51*6  # Faders cranked up - make it harder!
        self.pick_next()

    def compute_state(self, t, collaboration_state, osc_data):
        # type: (long, {}, OSCDataAccumulator) -> {}
        if self.next_button[1] in osc_data.buttons[self.next_button[0]]:
            collaboration_state["last_hit_button"] = self.next_button
            collaboration_state["last_hit_time"] = t
            if self.pick_next():
                collaboration_state.clear()
        else:
            collaboration_state.pop("last_hit_button", None)
            late = ("last_hit_time" in collaboration_state
                    and collaboration_state["last_hit_time"] + self.selection_time < t)
            if late:
                # Too late!
                self.pick_next(missed=True)
                # Tick forward
                collaboration_state["last_hit_time"] = t
            # collaboration_state.pop("last_hit_time", None)  # Leave this for now for timing

        self.flash_timer = (self.flash_timer + 1) % 20

        if self.flash_timer == 0:
            STATE.stations[self.next_button[0]].buttons[self.next_button[
                1]] = StationButtons.BUTTON_ON
        elif self.flash_timer == 10:
            STATE.stations[self.next_button[0]].buttons[self.next_button[
                1]] = StationButtons.BUTTON_OFF

        collaboration_state["on"] = self.on
        collaboration_state["off"] = self.off
        collaboration_state["next"] = self.next_button
        return collaboration_state
        # TODO Fail on miss
        # TODO Put into collaboration_state

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if not self.draw_bottom_layer:
            return

        pixels[0:2, :] = (0, 0, 0)
        for s, b in self.on:
            # TODO: Calculate based on section size and span 2 columns
            c = s * 11 + b * 2
            pixels[0:2, c:c + 2 + b / 4] = self.button_colors[b]

        # Flash the target
        if self.flash_timer < 10:
            c = self.next_button[0] * 11 + self.next_button[1] * 2
            pixels[0:2, c:c + 2 + self.next_button[1] / 4] = self.button_colors[self.next_button[1]]

    def scene_starting(self, now, osc_data):
        self.reset_state()

    def pick_next(self, missed=False):
        # type: (bool) -> bool
        self.flash_timer = 0

        if not missed and not self.off:
            # TODO: Terminate the animation
            print "Finished!"
            self.reset_state()
            return True

        last_button = self.next_button
        lost_button = None
        if last_button:
            if missed:
                self.off.append(
                    last_button)  # Do this before selecting in case it was the last one left!
                if self.backwards_progress and len(self.on):
                    lost_button = choice(self.on)
                    self.off.append(lost_button)
                    self.on.remove(lost_button)
            else:
                self.on.append(last_button)

        local_next = choice(self.off)
        self.next_button = local_next
        self.off.remove(local_next)

        if missed:
            if last_button and last_button != local_next:
                # Turn off unless in edge case
                STATE.stations[last_button[0]].buttons[last_button[1]] = StationButtons.BUTTON_OFF
            if lost_button and lost_button != local_next:
                STATE.stations[lost_button[0]].buttons[lost_button[1]] = StationButtons.BUTTON_OFF
        else:
            if last_button:
                STATE.stations[last_button[0]].buttons[last_button[1]] = StationButtons.BUTTON_ON

        STATE.stations[self.next_button[0]].buttons[self.next_button[1]] = StationButtons.BUTTON_ON
        print "Next is now", local_next
        return False


class ButtonRainbow(Effect):
    def __init__(self,
                 bottom_row=2,
                 top_row=STATE.layout.rows,
                 hue_start=0,
                 hue_end=255,
                 saturation=255,
                 max_value=255):
        self.bottom_row = bottom_row
        self.top_row = top_row
        self.hue_start = hue_start
        self.hue_end = hue_end
        self.saturation = saturation
        self.max_value = max_value
        self.column_success = None
        self.frame = 0

    def scene_starting(self, now, osc_data):
        self.column_success = color_utils.bi_rainbow(
            STATE.layout.columns,
            hue_start=self.hue_start,
            hue_end=self.hue_end,
            saturation=self.saturation,
            value=self.max_value)
        self.frame = 0

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame += 1

        # Do this each time so we avoid storing bases state
        column_bases = np.full(shape=(STATE.layout.columns, 3), fill_value=0, dtype=np.uint8)
        for s, b in collaboration_state["on"]:
            col = s * 11 + b * 2
            column_bases[col:col + 2 + b / 4] = self.column_success[col:col + 2 + b / 4]

        pixels[self.bottom_row:self.top_row, :] = column_bases


class Pulser(Effect):
    def __init__(self, pulse_length=10, bottom_row=2, top_row=None, after_fill=30):
        self.pulse_length = pulse_length
        self.bottom_row = bottom_row
        self.top_row = top_row if top_row else STATE.layout.rows
        self.after_fill = after_fill

        self.frame = 0

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame += 1
        for r in range(self.pulse_length):
            pixels[self.bottom_row + r:self.top_row:self.pulse_length, :] /= (
                (self.frame - r) % self.pulse_length) + 1
        pixels[self.bottom_row:self.top_row, :] += self.after_fill


class DiskPulsers(Effect):
    def __init__(self, pulse_length=10, bottom_row=0, top_row=None, after_fill=30):
        self.pulse_length = pulse_length
        self.bottom_row = bottom_row
        self.top_row = top_row if top_row else STATE.layout.rows
        self.after_fill = after_fill
        self.frame = 0
        self.row_indices = [
            range(STATE.layout.BOTTOM_DISC.center - r, self.bottom_row - 1, -self.pulse_length) +
            range(STATE.layout.BOTTOM_DISC.center + r, STATE.layout.DISC_MIDPOINT + 1,
                  self.pulse_length) + range(STATE.layout.TOP_DISC.center - r,
                                             STATE.layout.DISC_MIDPOINT, -self.pulse_length) +
            range(STATE.layout.TOP_DISC.center + r, self.top_row, self.pulse_length)
            for r in range(self.pulse_length)
        ]

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.frame += 1
        for r, row_indices in enumerate(self.get_row_indices_array()):
            pixels[row_indices, :] /= ((self.frame - r) % self.pulse_length) + 1
        pixels[self.bottom_row:self.top_row, :] += self.after_fill

    def get_row_indices_array(self):
        # return [self.row_indices[-1]]+self.row_indices[0:-1]
        return self.row_indices


class RotatingWedge(Effect):
    def __init__(self,
                 color=(255, 255, 0),
                 start_col=0,
                 width=5,
                 direction=1,
                 angle=1,
                 max_rotations=1,
                 additive=False,
                 scale_ratio=True):
        self.color = np.asarray(color, np.uint8)
        self.width = width
        self.direction = direction
        self.angle = (angle * 1.0 * STATE.layout.columns / STATE.layout.rows
                      if scale_ratio else angle)
        self.start_col = start_col
        self.end_col = start_col + width
        self.additive = additive
        self.max_frames = abs(1.0*max_rotations*STATE.layout.columns / direction)
        self.frame_count=0

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.angle == 0:
            if self.start_col < self.end_col:
                pixels.update_slices(
                    additive=self.additive,
                    color=self.color,
                    slices=[(slice(0, None), slice(self.start_col, self.end_col))])
            else:
                pixels.update_slices(
                    additive=self.additive,
                    color=self.color,
                    slices=[(slice(0, None), slice(self.start_col, None)), (slice(0, None), slice(
                        0, self.end_col))])

        else:
            # TODO Combine Slices or get Indexes?
            slices = [(slice(r, min(r + self.width, STATE.layout.rows)),
                       int(c) % STATE.layout.columns)
                      for r, c in enumerate(
                          np.arange(self.start_col, self.start_col + self.angle * STATE.layout.rows,
                                    self.angle))]
            pixels.update_slices(additive=self.additive, color=self.color, slices=slices)
        self.frame_count += 1
        self.start_col = (self.start_col + self.direction) % STATE.layout.columns
        self.end_col = (self.end_col + self.direction) % STATE.layout.columns

    def is_completed(self, t, osc_data):
        return self.frame_count > self.max_frames


def distortion_rotation(offsets, t, start_t, frame):
    offsets *= frame
    print offsets



class RisingTide(Effect):
    def __init__(self,
                 target_color=(255, 255, 255),
                 start_color=(10, 10, 10),
                 section=None,
                 bottom_row=2,
                 top_row=None):
        self.target_color = target_color
        self.start_color = start_color
        self.start_column = section*11
        self.end_column = (section+1)*11
        self.bottom_row = bottom_row
        self.top_row = top_row or STATE.layout.rows
        self.curr_top = self.bottom_row
        self.curr_bottom = self.bottom_row
        self.completed = False

        self.colors = [start_color]
        self.color_inc = tuple(
            map(lambda t, s: (0.0 + t - s) / (self.top_row - self.bottom_row), target_color,
                start_color))
        print self.start_color, self.target_color, self.color_inc

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.curr_top < self.top_row:
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]

            self.colors = [tuple(map(lambda c, i: c + i, self.colors[0], self.color_inc))
                           ] + self.colors
            self.curr_top += 1
        elif self.curr_bottom < self.top_row:
            self.colors = self.colors[:-1]
            self.curr_bottom += 1
            for i, r in enumerate(range(self.curr_bottom, self.curr_top)):
                pixels[r, self.start_column:self.end_column] = self.colors[i]
        else:
            self.completed = True

    def is_completed(self, t, osc_data):
        return self.completed


def pick_mod_n(columns, mod=2, value=0, **kwargs):
    return filter(lambda x: x % mod == value, columns)


class Columns(Effect):
    def __init__(self, color=(0, 0, 0), column_picker=pick_mod_n, additive=False):
        Effect.__init__(self, )
        self.picker = column_picker
        self.color = np.array(color, dtype=np.uint8)
        self.additive = additive

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # TODO : row limiter
        columns = self.picker(columns=range(STATE.layout.columns))
        if self.additive:
            pixels[:, columns] += self.color
        else:
            pixels[:, columns] = self.color

FOUNTAINS = [
    fm.FountainDefinition('wedge',
                          RotatingWedge,
                          arg_generators = { 'start_col' : fm.pick_random_start_column,
                                             'direction' : lambda section, button: choice([-1,1]),
                                             'angle' : lambda section, button: choice([-1,0,1]),
                                             'color' : fm.pick_button_color
                                            }
                         ),
    # fm.FountainDefinition('tide', RisingTide.factory,
    #                       arg_generators= {
    #                           'target_color' : lambda section, button: BUTTON_COLORS[button],
    #                           'start_color' : lambda section, button: map(lambda c: c*0.1, BUTTON_COLORS[button]),
    #                           'section' : fm.pass_section
    #                       }
    #                       )
]

SCENES = [
    Game(
        "buttonchaser",
        tags=[],
        collaboration_manager=ButtonChaseController(draw_bottom_layer=True),
        effects=[ButtonRainbow(max_value=255 - 30), Pulser()]),
    fm.FountainScene(
        name="wedges",
        tags=[Scene.TAG_EXAMPLE],
        background_effects=[],
        foreground_names=['wedge']
    ),
    fm.FountainScene(
        name="plainfountain",
        background_effects=[SolidBackground(color=(30,30,30))]
    ),
    Scene(
        "sinedots",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            SolidBackground(color=(30, 30, 30)),
            examples.SampleEffectLauncher(),
            FunctionFrameRotator(
                func=FunctionFrameRotator.no_op,
                start_offsets=5 * np.sin(np.linspace(0, 8 * np.pi, STATE.layout.rows)))
        ]),
    Scene(
        "lidaropaque",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 hoe.lidar.OpaqueLidar()]),
    Scene(
        "lidarswap",
        tags=[Scene.TAG_WIP],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[Rainbow(hue_start=0, hue_end=255),
                 hoe.lidar.SwappingLidar()]),
    Scene(
        "rainbowblackoutcolumns",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[
            Rainbow(hue_start=0, hue_end=255),
            FrameRotator(rate=-.25),
            Columns(color=(0, 0, 0), column_picker=partial(pick_mod_n, mod=10)),
            FrameRotator(rate=.25)
        ]),
    Scene(
        "diskrainbow",
        tags=[Scene.TAG_BACKGROUND],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[Rainbow(hue_start=0, hue_end=255),
                 DiskPulsers()])
]
