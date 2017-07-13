#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import sys, time
from threading import Thread
from opc import Client
import atexit

class SceneManager(object):
    def __init__(self, osc, opc, layout, fps):
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
        #TODO: Clean this up
        self.curr_scene=scene_info[1].init_scene(scene_info[0])
        pass

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

            pixels = self.curr_scene.next_frame(self.layout, t, n_pixels)
            self.opc.put_pixels(pixels, channel=0) #TODO: channel?
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

#TODO: do the python way
def get_first_non_empty(pixels):
    for pix in pixels:
        if pix is not None:
            return pix

class SceneDefinition(object):
    def __init__(self, background, *foregrounds):
        self.background_class=background
        self.foreground_classes = [] if foregrounds is None else list(foregrounds)
        self.instances = []


    def __str__(self):
        #TODO: Include foregrounds
        #TODO: What's the python way of doing this?
        return "Scene: %s" % self.background_class


    def init_scene(self, package):
        """Initialize a scene"""
        #TODO: init instances
        #TODO: cleanup

        """
        #Debugging:
        print "Foreground:", self.foreground_classes, type(self.foreground_classes)
        print "Background:", self.background_class
        print "Foreground and background", self.foreground_classes + [self.background_class]
        print "Package: ", package
        """
        self.instances = [getattr(package, clazz)() for clazz in self.foreground_classes + [self.background_class]]
        return self


    def next_frame(self, layout, time, n_pixels):
        #Now get all the pixels, ordering from the first foreground to the last foreground to the background
        all_pixels = [layer.next_frame(layout, time, n_pixels) for layer in self.instances]
        #Smush them together, taking the first non-None pixel available
        pixels = [get_first_non_empty(pixs) for pixs in zip(*all_pixels)]
        return pixels