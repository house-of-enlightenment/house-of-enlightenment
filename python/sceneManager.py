#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import sys, time
from osc import Controller
from opc import Client

class SceneManager(object):
    def __init__(self, osc, opc, layout, fps):
        self.osc = osc
        self.opc = opc
        self.layout=layout
        self.fps=fps

        self.sceneIndex=0
        self.scenes = []
        self.init_scenes()
        self.curr_scene = self.scenes[self.sceneIndex]



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
                    for effectName in effectDict.__all__:
                        print "Registering %s" % effectName
                        #TODO clean this up
                        self.scenes.append([effectDict,effectName])
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

    def init_handlers(self):
        self.server.addMsgHandler("/nextEffect", self.next_scene_handler)
        #TODO: Buttons, Lidar from file

    def init_scene(self):
        scene_names = self.scenes[self.sceneIndex]
        self.curr_scene=getattr(scene_names[0], scene_names[1])()
        pass

    def start(self):
        self.init_scene()

        n_pixels = len(self.layout)
        pixels = [(0, 0, 0,)] * n_pixels
        start_time = time.time()

        print '    sending pixels forever (control-c to exit)...'
        print

        while True:
            t = time.time() - start_time

            pixels = self.curr_scene.next_frame(self.layout, t, n_pixels)
            self.opc.put_pixels(pixels, channel=0) #TODO: channel?
            time.sleep(1/self.fps)

    def next_scene(self, args):
        #TODO: concurrency issues
        self.sceneIndex = (self.sceneIndex + 1) % len(self.scenes)

#----- Handlers -----
    def next_scene_handler(self, path, tags, args, source):
        #TODO: Call specific scenes
    	if args[0] > 0:
    		self.next_scene(args)
