#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import sys, time
from threading import Thread
from opc import Client
from OSC import OSCServer
import atexit


class SceneManager(object):
    def __init__(self, osc, opc, layout, fps):
        # OSCServer, Client, dict, int -> None
        self.osc_server = osc
        self.opc = opc
        self.layout=layout
        self.fps=fps

        self.sceneIndex=0
        self.scenes = []
        self.init_scenes()
        self.curr_scene = self.scenes[self.sceneIndex]
        self.serve=False
        self.is_running=False

        self.osc_data = StoredOSCData()


    def init_scenes(self):

        from os.path import dirname, join, isdir, abspath, basename
        from glob import glob
        import importlib
        import inspect

        pwd = dirname(__file__)
        effectsDir = pwd+'./effects/'
        sys.path.append(effectsDir)
        for f in glob(join(effectsDir, '*.py')):
            pkgName = basename(f)[:-3]
            if not pkgName.startswith("_"):
                try:
                    effectDict = importlib.import_module(pkgName)
                    for scene in effectDict.__all__:
                        if(isinstance(scene, SceneDefinition)):
                            print "Registering %s" % scene
                            #TODO clean this up
                            self.scenes.append([effectDict,scene])
                        else:
                            print "Got scene %s not of type SceneDefinition" % scene
                        """
                        effectFunc = getattr(effectDict, effectName)
                        args, varargs, keywords, defaults = inspect.getargspec(effectFunc)
                        params = {} if defaults == None or args == None else dict(
                            zip(reversed(args), reversed(defaults)))
                        self.scenes[pkgName + "-" + effectName] = {
                            'action': effectFunc,
                            'opacity': 0.0,
                            'params': params
                        }"""
                except ImportError:
                    print "WARNING: could not load effect %s" % pkgName

    def load_palettes(self, rootDir):
        #TODO: palettes existed in wheel. (1) Are they needed here and (2) what is the palettes module to import?
        """
        sys.path.append(rootDir + '/palettes')

        from palettes import palettes

        # expand palettes
        for p in palettes:
            p = reduce(lambda a, b: a + b, map(lambda c: [c] * 16, p))
        """

    def init_scene(self):
        scene_info = self.scenes[self.sceneIndex]
        # TODO: Clean this up
        self.curr_scene=scene_info[1].init_scene(scene_info[0])
        pass

    def get_osc_frame(self, clear=True):
        last_frame=self.osc_data
        self.osc_data = StoredOSCData(last_frame)
        return last_frame

    def serve_forever(self):
        self.serve=True
        self.is_running=True
        self.init_scene()
        n_pixels = len(self.layout)
        pixels = [(0, 0, 0,)] * n_pixels
        start_time = time.time()

        print '    sending pixels forever (quit or control-c to exit)...'
        print

        while self.serve:
            t = time.time() - start_time

            pixels = self.curr_scene.next_frame(self.layout, t, n_pixels, self.get_osc_frame())
            self.opc.put_pixels(pixels, channel=0)
            # TODO: channel?
            time.sleep(1/self.fps)

        self.is_running=False
        print "Scene Manager Exited"

    def next_scene(self, args):
        #TODO: concurrency issues
        self.sceneIndex = (self.sceneIndex + 1) % len(self.scenes)
        print '    New scene has index %s. Initializing now' % self.sceneIndex
        self.init_scene()
        print '    Scene changed'

    def shutdown(self):
        self.serve=False

#----- Handlers -----
    def next_scene_handler(self, path, tags, args, source):
        #TODO: Call specific scenes
    	if args[0] > 0:
    		self.next_scene(args)

    def handle_button(self, path, tags, args, source):
        print "Got button path=[%s], tags=[%s], args=[%s], source=[%s]" % (path, tags, args, source)
        button_name = str.split(path, '/')[-1]
        #TODO: handle wildcards (ie: input/button/*)
        #button_name=path
        self.osc_data.buttons[button_name]= 1
        self.osc_data.contains_change=True

    def handle_fader(self, path, tags, args, source):
        print "Got fader path=[%s], tags=[%s], args=[%s], source=[%s]" % (path, tags, args, source)
        fader_name = str.split(path, '/')[-1]
        #fader_name=path
        fader_value=args[0]
        self.osc_data.faders[fader_name] = fader_value
        self.osc_data.contains_change=True

    def add_button(self, name):
        print "Registering button at /input/button/%s" % name
        self.osc_server.addMsgHandler("/input/button/%s" % name, self.handle_button)
        pass

    def add_fader(self, name):
        print "Adding fader at /input/fader/%s" % name
        self.osc_server.addMsgHandler("/input/fader/%s" % name, self.handle_fader)
        pass


#TODO: do the python way
def get_first_non_empty(pixels):
    for pix in pixels:
        if pix is not None:
            return pix


class StoredOSCData(object):
    def __init__(self, last_data=None):
        self.buttons={}
        if last_data is None:
            self.faders = {}
        else:
            # TODO is this a memory leak?
            self.faders=last_data.faders
        self.contains_change=False


    def __str__(self):
        return "{%s,%s}" % (str(self.buttons), str(self.faders))


class Effect(object):
    def next_frame(self, layout, time, n_pixels, osc_data):
        raise NotImplementedError("All effects must implement next_frame")
        # TODO: Use abc


class EffectDefinition(object):
    def __init__(self, name, clazz): #TODO inputs
        # str, class -> None
        self.clazz=clazz
        self.name=name

    def __str__(self):
        #TODO: What's the python way of doing this?
        return "EffectDefinition(%s)" % self.name

    def create_effect(self):
        # None -> Effect
        print "Creating instance of effect %s" % self
        #TODO: pass args
        return self.clazz()


class SceneDefinition(object):
    def __init__(self, name, *layers):
        # str, List[EffectDefinition] -> None
        self.name = name
        self.layer_definitions = layers
        self.instances = []


    def __str__(self):
        #TODO: What's the python way of doing this?
        return "Scene(%s)" % self.name


    def init_scene(self, package):
        """Initialize a scene"""
        #TODO: init instances
        #TODO: cleanup
        self.instances = [layer_def.create_effect() for layer_def in self.layer_definitions]
        return self


    def next_frame(self, layout, time, n_pixels, osc_data):
        # Now get all the pixels, ordering from the first foreground to the last foreground to the background
        # TODO We mixed the model and implementation. This is the first thing to go when separating them
        all_pixels = [layer.next_frame(layout, time, n_pixels, osc_data) for layer in self.instances]
        #Smush them together, taking the first non-None pixel available
        pixels = [get_first_non_empty(pixs) for pixs in zip(*all_pixels)]
        return pixels