from collections import namedtuple
from random import choice, randrange

from animation_framework import MultiEffect
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

DEFAULT_ARG_GENERATORS = {
    'section' : pass_section,
    'button' : pass_button,
    'start_col' : pick_random_start_column,
    'color' : pick_fader_color,
}

class FountainDefinition(object):
    def __init__(self, name, factory_or_class, tags=[], static_args=None, arg_generators='default'):
        self.name = name
        self.tags = tags
        self.factory = factory_or_class
        self.is_clazz = inspect.isclass(self.factory)

        arg_generators = DEFAULT_ARG_GENERATORS if arg_generators=='default' else arg_generators
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
        self.arg_generators = { kw : func for kw, func in arg_generators.items()
                                # if arg_generators != 'default' or  # if explicitly state just go with it
                                if kw in var_names and kw not in static_args }

    def create_fountain(self, section, button):
        kwargs = self._generate_kwargs(section=section, button=button)
        return self.factory(**kwargs)

    def _generate_kwargs(self, section, button):
        return { kw : func(section=section, button=button) for kw, func in self.arg_generators.items() }

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