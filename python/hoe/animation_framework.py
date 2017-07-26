#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import sys
import time
from threading import Thread
from layout import Layout
from opc import Client
from OSC import OSCServer
from functools import partial
import atexit


class AnimationFramework(object):
    def __init__(self, osc, opc, layout, fps):
        # OSCServer, Client, dict, int -> None
        self.osc_server = osc
        self.opc = opc
        self.layout = Layout(layout)
        self.fps = fps
        self.n_pixels = len(layout)

        # Load all scenes from effects package. Then set initial index and load it up
        self.scenes = AnimationFramework.load_scenes(self.layout, self.n_pixels)
        self.curr_scene = None
        self.queued_scene = self.scenes[self.scenes.keys()[0]]
        self.change_scene()

        self.serve = False
        self.is_running = False

        self.osc_data = StoredOSCData()
        self.setup_handlers({0: 50})

    @staticmethod
    def load_scenes(layout, n_pixels, effects_dir=None):
        # None -> [Scene]

        from os.path import dirname, join, isdir, abspath, basename
        from glob import glob
        import importlib
        import inspect

        if not effects_dir:
            pwd = dirname(__file__)
            effects_dir = pwd + '/../effects/'
        sys.path.append(effects_dir)

        scenes = {}
        for f in glob(join(effects_dir, '*.py')):
            pkg_name = basename(f)[:-3]
            if not pkg_name.startswith("_"):
                try:
                    effect_dict = importlib.import_module(pkg_name)
                    for scene in effect_dict.__all__:
                        if (isinstance(scene, Scene)):
                            if scene.name in scenes.keys():
                                print "Cannot register scene %s. Scene with name already exists" % scene.name
                                continue
                            print "Registering %s" % scene
                            # TODO clean this up
                            scene.initialize_layout(layout, n_pixels)
                            scenes[scene.name] = scene
                        else:
                            print "Got scene %s not of type Scene" % scene
                except ImportError:
                    print "WARNING: could not load effect %s" % pkg_name

        print "Loaded %s scenes from %s directory\n" % (len(scenes), effects_dir)

        return scenes

    # ----- Handlers -----

    def next_scene_handler(self, path, tags, args, source):
        if not args or args[0] == "":
            self.next_scene()
        else:
            self.next_scene(int(args[0]))

    def select_scene_handler(self, path, tags, args, source):
        # TODO: Call specific scenes
        print path, tags, args, source
        if args[0] == "":
            self.next_scene()
        else:
            self.pick_scene(args[0])

    def setup_handlers(self, faders={}):
        """
        :param faders: Dictionary of faders and their default values for each station
        :return:
        """

        # Set up scene control
        self.osc_server.addMsgHandler("/scene/next", self.next_scene_handler)
        self.osc_server.addMsgHandler("/scene/select", self.select_scene_handler)

        # Set up buttons
        def handle_button(path, tags, args, source):
            station, button_id = map(int, args)
            self.osc_data.button_pressed(station, button_id)

        self.osc_server.addMsgHandler("/input/button", handle_button)

        # Set up faders
        for fader in faders:
            self.osc_data.init_fader_on_all_stations(fader, faders[fader])

        def handle_fader(path, tags, args, source):
            station, button_id, value = map(int, args)
            self.osc_data.fader_changed(station, button_id, value)

        self.osc_server.addMsgHandler("/input/fader", handle_fader)

        print "Registered all OSC Handlers"

    # ---- EFFECT CONTROL METHODS -----
    def change_scene(self):
        self.queued_scene.scene_starting()
        self.curr_scene = self.queued_scene
        print '\tScene %s started\n' % self.curr_scene
        self.curr_scene.scene_ended()

    def get_osc_frame(self, clear=True):
        last_frame = self.osc_data
        self.osc_data = StoredOSCData(last_frame)
        return last_frame

    def next_scene(self, increment=1):
        curr_idx = self.scenes.keys().index(self.curr_scene.name)
        new_idx = (curr_idx + increment) % len(self.scenes)
        self.pick_scene(self.scenes.keys()[new_idx])

    def pick_scene(self, scene_name):
        self.queued_scene = self.scenes[scene_name]
        self.change_scene()

    # ---- LIFECYCLE (START/STOP) METHODS ----

    def serve_in_background(self):
        # [function] -> Thread

        # Run scene manager in the background
        thread = Thread(target=self.serve_forever)
        thread.setName("SceneManager")
        thread.setDaemon(True)
        thread.start()
        return thread

    def serve_forever(self):
        # [function] -> None

        self.serve = True

        start_time = time.time()
        fps_frame_time = 1 / self.fps
        print '\tsending pixels forever (quit or control-c to exit)...'
        self.is_running = True

        while self.serve:
            # TODO : Does this create lots of GC?
            frame_start_time = time.time()
            t = frame_start_time - start_time
            target_frame_end_time = frame_start_time + fps_frame_time

            # Create the pixels, set all, then put
            pixels = [None] * self.n_pixels
            self.curr_scene.render(pixels, t, self.get_osc_frame())
            # TODO: Check for None and replace with (0, 0, 0)
            self.opc.put_pixels(pixels, channel=0)

            # Crude way of trying to hit target fps
            time.sleep(max(0, target_frame_end_time - time.time()))
            # TODO: channel?

        self.is_running = False
        print "Scene Manager Exited"

    def shutdown(self):
        self.serve = False


# TODO: do the python way
def get_first_non_empty(pixels):
    for pix in pixels:
        if pix is not None:
            return pix


class StoredStationData(object):
    def __init__(self, last_data=None):
        self.buttons = {}
        if last_data is None:
            self.faders = {}
        else:
            # TODO Check with python folks. Is this a memory leak?
            self.faders = last_data.faders
        self.contains_change = False

    def __str__(self):
        return "%s{buttons=%s, faders=%s, changed=%s}" % (self.__class__.__name__,
                                                          str(self.buttons), str(self.faders),
                                                          str(self.contains_change))

    def button_pressed(self, button):
        self.buttons[button] = 1
        self.contains_change = True

    def fader_changed(self, fader, value):
        self.faders[fader] = value
        self.contains_change = True


class StoredOSCData(object):
    def __init__(self, last_data=None, num_stations=6):
        self.stations = [
            StoredStationData(last_data.stations[i] if last_data else None)
            for i in range(num_stations)
        ]
        self.contains_change = False

    def __str__(self):
        return "{}({})".format(self.__class__.__name__,
                               ','.join([str(station) for station in self.stations]))

    def button_pressed(self, station, button):
        self.stations[station].button_pressed(button)
        self.contains_change = True

    def fader_changed(self, station, fader, value):
        self.stations[station].fader_changed(fader, value)
        self.contains_change = True

    def init_fader_on_all_stations(self, fader, value):
        for station in self.stations:
            station.faders[fader] = value


class CollaborationManager(object):
    def compute_state(self, t, collaboration_state, osc_data):
        raise NotImplementedError("All feedback effects must implement compute_state")
        # TODO: use abc


class Effect(object):
    def __init__(self, layout=None, n_pixels=None):
        self.layout = layout
        self.n_pixels = n_pixels

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        raise NotImplementedError("All effects must implement next_frame")
        # TODO: Use abc

    def initialize_layout(self, layout, n_pixels):
        self.layout = layout
        self.n_pixels = n_pixels

    def scene_starting(self):
        pass

    def scene_ended(self):
        pass

    def is_completed(self, t, osc_data):
        return False


class MultiEffect(Effect):
    def __init__(self, layout=None, n_pixels=None, *effects):
        Effect.__init__(self, layout, n_pixels)
        self.effects = list(effects)

    def scene_starting(self):
        """Initialize a scene"""
        for e in self.effects:
            e.scene_starting()

    def scene_ended(self):
        for e in self.effects:
            e.scene_ended()

    def initialize_layout(self, layout, n_pixels):
        Effect.initialize_layout(self, layout, n_pixels)
        for effect in self.effects:
            effect.initialize_layout(layout, n_pixels)

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.before_rendering(pixels, t, collaboration_state, osc_data)

        for e in self.effects:
            e.next_frame(pixels, t, collaboration_state, osc_data)

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        self.cleanup_terminated_effects(pixels, t, collaboration_state, osc_data)

    def cleanup_terminated_effects(self, pixels, t, collaboration_state, osc_data):
        # TODO Debugging code here?
        self.effects[:] = [e for e in self.effects if not e.is_completed(t, osc_data)]


"""
class EffectLauncher(MultiEffect):
    def __init__(self, factory, layout=None, n_pixels=None, **kwargs):
        MultiEffect.__init__(layout, n_pixels)
"""


class Scene(MultiEffect):
    def __init__(self, name, collaboration_manager, *effects):
        # str, CollaborationManager, List[Effect] -> None
        MultiEffect.__init__(self, None, None, *effects)
        self.name = name
        self.collaboration_manager = collaboration_manager
        if isinstance(collaboration_manager, Effect) and collaboration_manager not in self.effects:
            # print "WARNING: Scene %s has collaboration manager %s that is an effect but is not part of layers. Inserting as top layer" % (name, collaboration_manager)
            self.effects = [collaboration_manager] + self.effects
        self.collaboration_state = {}

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def render(self, pixels, t, osc_data):
        self.collaboration_state = self.collaboration_manager.compute_state(
            t, self.collaboration_state, osc_data)
        # TODO Why didn't super(MultiEffect, self) work?
        self.next_frame(pixels, t, self.collaboration_state, osc_data)


class EffectFactory(object):
    def __init__(self, name, clazz, **kwargs):  # TODO inputs
        # str, class -> None
        self.clazz = clazz
        self.name = name
        self.kwargs = kwargs

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def create_effect(self, layout, n_pixels):
        # None -> Effect
        print "\tCreating instance of effect %s" % self
        return self.clazz(layout=layout, n_pixels=n_pixels, **self.kwargs)
