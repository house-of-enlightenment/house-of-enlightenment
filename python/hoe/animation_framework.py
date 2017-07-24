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
        # TODO: Call specific scenes
        print path, tags, args, source
        if args[0] == "":
            self.next_scene()
        else:
            self.next_scene(int(args[0]))

    def add_button(self, button_id, path=None):
        path = path if path else "/input/button/%s" % button_id
        print "Registering button %s at path %s" % (button_id, path)

        def handle_button(path, tags, args, source):
            print "Button [%s] received message: path=[%s], tags=[%s], args=[%s], source=[%s]" % (
                button_id, path, tags, args, source)
            self.osc_data.buttons[button_id] = 1
            self.osc_data.contains_change = True

        self.osc_server.addMsgHandler(path, handle_button)
        pass

    def add_fader(self, fader_id, path=None, default="0"):
        path = path if path else "/input/fader/%s" % fader_id
        print "Registering fader %s at %s" % (fader_id, path)

        def handle_fader(path, tags, args, source):
            print("Fader [{}] received message: "
                  "path=[{}], tags=[{}], args=[{}], source=[{}], name=[{}]").format(
                fader_id, path, tags, args, source, fader_id)
            fader_value = args[0]
            self.osc_data.faders[fader_id] = fader_value
            self.osc_data.contains_change = True

        # TODO : force check for slashes
        self.osc_server.addMsgHandler(path, handle_fader)
        self.osc_data.faders[fader_id] = default
        pass

    # ---- EFFECT CONTROL METHODS -----
    def change_scene(self):
        self.queued_scene.start_scene()
        self.curr_scene = self.queued_scene
        print '\tScene %s started\n' % self.curr_scene
        self.curr_scene.scene_ended()

    def get_osc_frame(self, clear=True):
        last_frame = self.osc_data
        self.osc_data = StoredOSCData(last_frame)
        return last_frame

    def next_scene(self, increment=1):
        curr_idx = self.scenes.keys().index(self.curr_scene.name)
        new_idx = (curr_idx+increment)%len(self.scenes)
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
            self.curr_scene.next_frame(pixels, t, self.get_osc_frame())
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


class StoredOSCData(object):
    def __init__(self, last_data=None):
        self.buttons = {}
        if last_data is None:
            self.faders = {}
        else:
            # TODO Check with python folks. Is this a memory leak?
            self.faders = last_data.faders
        self.contains_change = False

    def __str__(self):
        return "StoredOSCData{buttons=%s, faders=%s, changed=%s}" % (str(self.buttons),
                                                                     str(self.faders),
                                                                     str(self.contains_change))


class Effect(object):
    def __init__(self, layout=None, n_pixels=None):
        self.layout=layout
        self.n_pixels=n_pixels

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        raise NotImplementedError("All effects must implement next_frame")
        # TODO: Use abc

    def initialize_layout(self, layout, n_pixels):
        self.layout = layout
        self.n_pixels = n_pixels

    def scene_starting(self, scene):
        pass

    def scene_ended(self, scene):
        pass


class FeedbackEffect(Effect):
    def compute_state(self, t, collaboration_state, osc_data):
        raise NotImplementedError("All feedback effects must implement compute_state")
        # TODO: use abc


class EffectDefinition(object):
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


class Scene(object):
    def __init__(self, name, feedback_effect, *layer_effects):
        # str, FeedbackEffect, List[Effect] -> None
        self.name = name
        self.feedback_effect = feedback_effect
        self.layer_effects = layer_effects
        self.collaboration_state={}

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def initialize_layout(self, layout, n_pixels):
        self.feedback_effect.initialize_layout(layout, n_pixels)
        for layer_effect in self.layer_effects:
            layer_effect.initialize_layout(layout, n_pixels)

    def start_scene(self):
        """Initialize a scene"""
        self.feedback_effect.scene_starting(self)
        for layer_effect in self.layer_effects:
            layer_effect.scene_starting(self)

    def scene_ended(self):
        self.feedback_effect.scene_ended(self)
        for layer_effect in self.layer_effects:
            layer_effect.scene_ended(self)

    def next_frame(self, pixels, t, osc_data):
        self.collaboration_state = self.feedback_effect.compute_state(t, self.collaboration_state, osc_data)

        self.feedback_effect.next_frame(pixels, t, self.collaboration_state, osc_data)

        for layer_effect in self.layer_effects:
            layer_effect.next_frame(pixels, t, self.collaboration_state, osc_data)
