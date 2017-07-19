#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import sys
import time
from threading import Thread
from opc import Client
from OSC import OSCServer
from functools import partial
import atexit


class SceneManager(object):
    def __init__(self, osc, opc, layout, fps):
        # OSCServer, Client, dict, int -> None
        self.osc_server = osc
        self.opc = opc
        self.layout = layout
        self.fps = fps

        # Load all scenes from effects package. Then set initial index and load it up
        self.scenes = SceneManager.load_scenes()
        self.scene_index = 0
        self.init_scene()

        self.serve = False
        self.is_running = False

        self.osc_data = StoredOSCData()

    @staticmethod
    def load_scenes(effects_dir=None):
        # None -> [SceneDefinition]

        from os.path import dirname, join, isdir, abspath, basename
        from glob import glob
        import importlib
        import inspect

        if not effects_dir:
            pwd = dirname(__file__)
            effects_dir = pwd + '/../effects/'
        sys.path.append(effects_dir)

        scenes = []
        for f in glob(join(effects_dir, '*.py')):
            pkg_name = basename(f)[:-3]
            if not pkg_name.startswith("_"):
                try:
                    effect_dict = importlib.import_module(pkg_name)
                    for scene in effect_dict.__all__:
                        if (isinstance(scene, SceneDefinition)):
                            print "Registering %s" % scene
                            # TODO clean this up
                            scenes.append([effect_dict, scene])
                        else:
                            print "Got scene %s not of type SceneDefinition" % scene
                except ImportError:
                    print "WARNING: could not load effect %s" % pkg_name

        print "Loaded %s scenes from %s directory\n" % (len(scenes), effects_dir)

        return scenes

    def load_palettes(self, rootDir):
        # TODO: palettes existed in wheel. (1) Are they needed here
        # and (2) what is the palettes module to import?
        pass

    def init_scene(self):
        scene_info = self.scenes[self.scene_index]
        # TODO: Clean this up
        print '\tInitializing scene %s' % scene_info[1]
        self.curr_scene = scene_info[1].init_scene(scene_info[0])
        print '\tScene %s initialized\n' % self.curr_scene

    def get_osc_frame(self, clear=True):
        last_frame = self.osc_data
        self.osc_data = StoredOSCData(last_frame)
        return last_frame

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

        n_pixels = len(self.layout)
        pixels = [(0, 0, 0, )] * n_pixels

        start_time = time.time()
        fps_frame_time = 1 / self.fps
        print '\tsending pixels forever (quit or control-c to exit)...'
        self.is_running = True

        while self.serve:
            # TODO : Does this create lots of GC?
            frame_start_time = time.time()
            t = frame_start_time - start_time
            target_frame_end_time = frame_start_time + fps_frame_time

            pixels = self.curr_scene.next_frame(self.layout, t, n_pixels, self.get_osc_frame())
            self.opc.put_pixels(pixels, channel=0)

            # Crude way of trying to hit target fps
            time.sleep(max(0, target_frame_end_time - time.time()))
            # TODO: channel?

        self.is_running = False
        print "Scene Manager Exited"

    def next_scene(self, args):
        # TODO: concurrency issues
        self.scene_index = (self.scene_index + 1) % len(self.scenes)
        print '\tChanged scene to index %s. Initializing now' % (self.scene_index)
        self.init_scene()

    def shutdown(self):
        self.serve = False

# ----- Handlers -----

    def next_scene_handler(self, path, tags, args, source):
        # TODO: Call specific scenes
        if args[0] > 0:
            self.next_scene(args)

    def add_button(self, button_name):
        print "Registering button at /input/button/%s" % button_name

        def handle_button(path, tags, args, source):
            print "Button [%s] received message: path=[%s], tags=[%s], args=[%s], source=[%s]" % (
                button_name, path, tags, args, source)
            self.osc_data.buttons[button_name] = 1
            self.osc_data.contains_change = True

        self.osc_server.addMsgHandler("/input/button/%s" % button_name, handle_button)
        pass

    def add_fader(self, handler_name, default=""):
        print "Registering fader at /input/fader/%s" % handler_name

        def handle_fader(path, tags, args, source):
            print("Fader [{}] received message: "
                  "path=[{}], tags=[{}], args=[{}], source=[{}], name=[{}]").format(
                      handler_name, path, tags, args, source, handler_name)
            fader_value = args[0]
            self.osc_data.faders[handler_name] = fader_value
            self.osc_data.contains_change = True

        self.osc_server.addMsgHandler("/input/fader/%s" % handler_name, handle_fader)
        self.osc_data.faders[handler_name] = default
        pass


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
    def next_frame(self, layout, time, n_pixels, osc_data):
        raise NotImplementedError("All effects must implement next_frame")
        # TODO: Use abc


class EffectDefinition(object):
    def __init__(self, name, clazz):  # TODO inputs
        # str, class -> None
        self.clazz = clazz
        self.name = name

    def __str__(self):
        # TODO: What's the python way of doing this?
        return "EffectDefinition(%s)" % self.name

    def create_effect(self):
        # None -> Effect
        print "\tCreating instance of effect %s" % self
        # TODO: pass args
        return self.clazz()
        # return [child.create_effect() for child in self.children] + [self.clazz()]


class SceneDefinition(object):
    def __init__(self, name, *layers):
        # str, List[EffectDefinition] -> None
        self.name = name
        self.layer_definitions = layers
        self.instances = []

    def __str__(self):
        # TODO: What's the python way of doing this?
        return "Scene(%s)" % self.name

    def init_scene(self, package):
        """Initialize a scene"""
        # TODO: init child instances
        # TODO: cleanup
        self.instances = [layer_def.create_effect() for layer_def in self.layer_definitions]
        return self

    def next_frame(self, layout, time, n_pixels, osc_data):
        # Now get all the pixels, ordering from the first foreground
        # to the last foreground to the background TODO We mixed the
        # model and implementation. This is the first thing to go when
        # separating them
        all_pixels = [
            layer.next_frame(layout, time, n_pixels, osc_data) for layer in self.instances
        ]
        # Smush them together, taking the first non-None pixel available
        pixels = [get_first_non_empty(pixs) for pixs in zip(*all_pixels)]
        return pixels
