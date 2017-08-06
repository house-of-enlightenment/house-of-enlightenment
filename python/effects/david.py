from hoe import color_utils
from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import CollaborationManager
from hoe.animation_framework import EffectFactory
from hoe.animation_framework import MultiEffect
from hoe.state import STATE
from random import choice
from random import randint
from itertools import product
from generic_effects import SolidBackground
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
            backwards_progress=False,  # If true, missing a button actually removes a target
            selection_time=5  # Time to hit before picking a new one (if backwards_progress, also lose progress)
    ):

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
        self.backwards_progress = backwards_progress
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
        self.pick_next()

        for s, client in enumerate(STATE.station_osc_clients):
            hoe.osc_utils.update_buttons(
                client=client,
                station_id=s,
                updates={
                    b: hoe.osc_utils.BUTTON_ON if (s, b) in self.on else hoe.osc_utils.BUTTON_OFF
                    for b in range(STATE.button_count)
                })

    def compute_state(self, t, collaboration_state, osc_data):
        # type: (long, {}, StoredOSCData) -> {}
        if self.next_button[1] in osc_data.stations[self.next_button[0]].buttons:
            collaboration_state["last_hit_button"] = self.next_button
            collaboration_state["last_hit_time"] = t
            if self.pick_next():
                collaboration_state.clear()
        else:
            collaboration_state.pop("last_hit_button", None)
            if "last_hit_time" in collaboration_state and collaboration_state["last_hit_time"] + self.selection_time < t:
                # Too late!
                self.pick_next(missed=True)
                # Tick forward
                collaboration_state["last_hit_time"] = t
            # collaboration_state.pop("last_hit_time", None)  # Leave this for now for timing

        self.flash_timer = (self.flash_timer + 1) % 20

        if self.flash_timer == 0:
            self.send_update(self.next_button, hoe.osc_utils.BUTTON_ON)
        elif self.flash_timer == 10:
            self.send_update(self.next_button, hoe.osc_utils.BUTTON_OFF)

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

    def scene_starting(self):
        self.reset_state()

    def pick_next(self, missed=False):
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
                self.send_update(last_button, hoe.osc_utils.BUTTON_OFF)
            if lost_button and lost_button != local_next:
                self.send_update(lost_button, hoe.osc_utils.BUTTON_OFF)
        else:
            if last_button:
                self.send_update(last_button, hoe.osc_utils.BUTTON_ON)

        self.send_update(self.next_button, hoe.osc_utils.BUTTON_ON)
        print "Next is now", local_next
        return False

    def send_update(self, button, update):
        """Actually update a button"""
        # TODO: Queue this and send when ready
        client = STATE.station_osc_clients[self.next_button[0]]
        if client:
            hoe.osc_utils.update_buttons(
                station_id=button[0], client=client, updates={button[1]: update})


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

    def scene_starting(self):
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


class RotatingWedge(Effect):
    def __init__(self,
                 color=(255, 255, 0),
                 width=5,
                 direction=1,
                 angle=1,
                 start_col=0,
                 additive=False,
                 scale_ratio=True):
        self.color = np.asarray(color, np.uint8)
        self.width = width
        self.direction = direction
        self.angle = angle * 1.0 * STATE.layout.columns / STATE.layout.rows if scale_ratio else angle
        self.start_col = 0
        self.end_col = start_col + width
        self.additive = additive

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if self.angle == 0:
            if self.start_col < self.end_col:
                self.update_pixels(
                    pixels=pixels, slices=[(slice(None), slice(self.start_col, self.end_col))])
            else:
                self.update_pixels(
                    pixels=pixels,
                    slices=[(slice(None), slice(self.start_col, None)), (slice(None), slice(
                        None, self.end_col))])
        else:
            # TODO Combine Slices or get Indexes?
            slices = [(slice(r, min(r + self.width, STATE.layout.rows)),
                       int(c) % STATE.layout.columns)
                      for r, c in enumerate(
                          np.arange(self.start_col, self.start_col + self.angle * STATE.layout.rows,
                                    self.angle))]
            self.update_pixels(pixels=pixels, slices=slices)
        self.start_col = (self.start_col + self.direction) % STATE.layout.columns
        self.end_col = (self.end_col + self.direction) % STATE.layout.columns

    def update_pixels(self, pixels, slices):
        for r, c in slices:
            if self.additive:
                pixels[r, c] += self.color
            else:
                pixels[r, c] = self.color


def button_launch_checker(t, collaboration_state, osc_data):
    for i in range(len(osc_data.stations)):
        if osc_data.stations[i].buttons:
            return True
    return False


class GenericStatelessLauncher(MultiEffect):
    def __init__(self, factory_method, launch_checker=button_launch_checker, **kwargs):
        MultiEffect.__init__(self)
        self.launch_checker = launch_checker
        self.factory_method = factory_method
        self.factory_args = kwargs

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        # TODO : Performance
        if self.launch_checker(t=t, collaboration_state=collaboration_state, osc_data=osc_data):
            self.add_effect(
                self.factory_method(
                    pixels=pixels,
                    t=t,
                    collaboration_state=collaboration_state,
                    osc_data=osc_data,
                    **self.factory_args))
            print "Effect count", len(self.effects)


def wedge_factory(**kwargs):
    varnames = RotatingWedge.__init__.__func__.__code__.co_varnames
    args = {n: kwargs[n] for n in varnames if n in kwargs}
    if "color" not in args:
        args["color"] = (randint(0, 255), randint(0, 255), randint(0, 255))
    if "direction" not in args:
        args["direction"] = randint(0, 1) * 2 - 1  # Cheap way to get -1 or 1
    if "angle" not in args:
        args["angle"] = randint(-1, 1)
    return RotatingWedge(**args)


def distortion_rotation(offsets, t, start_t, frame):
    offsets *= frame
    print offsets


class LidarDisplay(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if osc_data.lidar_objects:
            print osc_data.lidar_objects


__all__ = [
    Scene(
        "buttonchaser",
        ButtonChaseController(draw_bottom_layer=True),
        SolidBackground(),
        ButtonRainbow(max_value=255 - 30),
        Pulser()),
    Scene("buttonloser",
          ButtonChaseController(draw_bottom_layer=True, backwards_progress=True),
          SolidBackground(), ButtonRainbow(), Pulser()),
    Scene("wedges",
          NoOpCollaborationManager(),
          RotatingWedge(), GenericStatelessLauncher(wedge_factory, width=3, additive=False)),
    Scene(
        "rotatingrainbow",
        NoOpCollaborationManager(),
        Rainbow(hue_start=0, hue_end=255),
        FrameRotator(rate=.75)),
    Scene("funkrainbow",
          NoOpCollaborationManager(),
          Rainbow(hue_start=0, hue_end=255),
          FunctionFrameRotator(
              func=FunctionFrameRotator.sample_rotating_offset,
              start_offsets=range(STATE.layout.rows))),
    Scene("sinerainbow",
          NoOpCollaborationManager(),
          Rainbow(hue_start=0, hue_end=255),
          FunctionFrameRotator(
              func=FunctionFrameRotator.sample_roll_offset,
              start_offsets=5 * np.sin(np.linspace(0, 8 * np.pi, STATE.layout.rows)))),
    Scene("sinedots",
          NoOpCollaborationManager(),
          SolidBackground((100, 100, 100)),
          examples.SampleEffectLauncher(),
          FunctionFrameRotator(
              func=FunctionFrameRotator.no_op,
              start_offsets=5 * np.sin(np.linspace(0, 8 * np.pi, STATE.layout.rows)))),
    Scene("lidartest",
          NoOpCollaborationManager(),
          Rainbow(hue_start=0, hue_end=255),
          LidarDisplay()
          )

]
