from collections import namedtuple
from random import choice, randrange

import numpy as np

import hoe.lidar
import hoe.stations
from animation_framework import MultiEffect, Scene
from collaboration import ButtonToggleResponderManager
from hoe.animation_framework import Effect
from hoe.state import STATE
from state import STATE
import inspect

def pick_random_start_column(section, button):
    return randrange(section*11, (section+1)*11)


def pass_section(section, button):
    return section


def pass_button(section, button):
    return button


def pick_random_color(section, button):
    return (randrange(0, 255), randrange(0,255), randrange(0,255))


def pick_fader_color(section, button):
    # TODO make this more impactful
    color = [0,0,0]
    for i, station in enumerate(STATE.stations):
        color[i%3] += int(station.fader_value*1.27)  #  cap it
    return tuple(color)

def pick_button_color(section, button):
    return hoe.stations.BUTTON_COLORS[button]



_DEFAULT_ARG_GENERATORS = {
    'section' : pass_section,
    'button' : pass_button,
    'start_col' : pick_random_start_column,
    'color' : pick_button_color,
}

def get_default_arg_generators(**kwargs):
    gen = _DEFAULT_ARG_GENERATORS.copy()
    gen.update(**kwargs)
    return gen

class FountainDefinition(object):
    def __init__(self, name, factory_or_class, tags=[], static_args=None, arg_generators='default'):
        self.name = name
        self.tags = tags
        self.factory = factory_or_class
        self.is_clazz = inspect.isclass(self.factory)

        arg_generators = _DEFAULT_ARG_GENERATORS if arg_generators=='default' else arg_generators
        static_args = static_args or []

        # OH MY GOD THIS IS A HACK
        # This let's us take variable names off the class or the method, depending on the type we are dealing with
        # This means we don't have to create factories for each darn class,
        # and we don't have to accept **kwargs for each one either
        # Let's not think about partials quit yet...
        var_names = None
        if self.is_clazz:
            var_names = factory_or_class.__init__.__func__.__code__.co_varnames
        else:
            var_names = factory_or_class.__code__.co_varnames
        self.arg_generators = { kw : fnc for kw, fnc in arg_generators.items()
                                # if arg_generators != 'default' or  # if explicitly state just go with it
                                if kw in var_names and kw not in static_args }

    def create_fountain(self, section, button):
        kwargs = self._generate_kwargs(section=section, button=button)
        return self.factory(**kwargs)

    def is_in_pool(self, pool_names, pool_tags):
        if not pool_names and not pool_tags:
            return True

        if pool_names and pool_tags:
            return self.name in pool_names and any(tag in pool_tags for tag in self.tags)

        if pool_names:
            return self.name in pool_names

        # Tags logic could stand to improve. Just take it is one matches
        if pool_tags:
            return any(tag in pool_tags for tag in self.tags)

    def _generate_kwargs(self, section, button):
        return { kw : fnc(section=section, button=button) for kw, fnc in self.arg_generators.items() }


class FountainLaunchingController(MultiEffect):
    def __init__(self, fountain_pool):
        MultiEffect.__init__(self)
        for effect in fountain_pool:
            assert isinstance(effect, FountainDefinition), 'effect {} not instanceof FountainDefinition'.format(effect)
        self.fountain_pool = fountain_pool
        self.button_mapping = None

    def scene_starting(self, now, osc_data):
        self.button_mapping = self._generate_button_mapping()
        MultiEffect.scene_starting(self, now, osc_data)

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s_id, buttons in osc_data.buttons.items():
            for b_id in buttons:
                self.add_effect(self.button_mapping[s_id][b_id].create_fountain(section=s_id, button=b_id))

    def _generate_button_mapping(self):
        return { s_id : [choice(self.fountain_pool) for b in range(5)] for s_id in range(6) }

    def is_completed(self, t, osc_data):
        return False  # Never completes - a new button is always just around the corner ;)


class FountainScene(Scene):
    def __init__(self, name, background_effects, tags=[], foreground_names=None, foreground_tags=[], feedback=None, lidar=None):
        effects = background_effects
        if lidar is None:
            effects.append(hoe.lidar.NoiseyLidar())
        elif isinstance(lidar, Effect):
            effects.append(lidar)

        effects.append(feedback or ButtonStationFaderFeedbackDisplay())
        Scene.__init__(self, name, tags, ButtonToggleResponderManager(), effects=effects)
        # ^... Response Manager could probably be shared...

        self.foreground_names = foreground_names
        self.foreground_tags = foreground_tags
        self.fountain_effects_initialized = False

    def after_all_scenes_loaded(self):
        assert not self.fountain_effects_initialized, "Already initialized"
        definitions = filter(lambda definition: definition.is_in_pool(self.foreground_names, self.foreground_tags), STATE.fountains)
        launcher = FountainLaunchingController(definitions)
        self.add_effect(launcher, before=False)


class ButtonStationFaderFeedbackDisplay(Effect):
    count_to_indices = {
        0: [],
        1: [(1, 10)],
        2: [(1, 5), (6, 10)],
        3: [(1, 4), (4, 7), (7, 10)],
        4: [(1, 3), (3, 5), (6, 8), (8, 10)],
        5: [(1, 3), (3, 5), (5, 6), (6, 8), (8, 10)]
    }
    bottom_row = [STATE.codes.get_station_rgb_color(c/11) if c % 11 not in [0,10] else (0,0,0) for c in range(STATE.layout.columns) ]

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        pixels[0, :] = self.bottom_row

        button_colors = np.zeros((STATE.layout.columns, 3), np.uint8)
        for s_id, station in enumerate(STATE.stations):
            high_buttons = station.buttons.get_high_buttons()
            for i, sli in zip(high_buttons,
                              ButtonStationFaderFeedbackDisplay.count_to_indices[len(high_buttons)]):
                button_colors[sli[0] + s_id * 11:sli[1] + s_id * 11, :] = hoe.stations.colors_to_rgb[
                    hoe.stations.id_to_color_names[i]]

        pixels[1, :] = button_colors