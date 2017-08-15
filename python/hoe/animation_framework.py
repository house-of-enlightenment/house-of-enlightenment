#!/usr/bin/env python

# House of Enlightenment
# Manager for scene selection

import os.path
import glob
import importlib
import sys
import time
from threading import Thread
from pixels import Pixels
from itertools import ifilter
from functools import partial
import atexit
from collections import OrderedDict

from OSC import OSCServer

from hoe.state import STATE
from hoe.opc import Client


class AnimationFramework(object):
    def __init__(self,
                 osc_server,
                 opc_client,
                 osc_station_clients=[],
                 scenes=None,
                 first_scene=None):
        # type: (OSCServer, Client, List(OSCClient), {str, Scene}) -> None
        self.osc_server = osc_server
        self.opc_client = opc_client
        self.osc_station_clients = osc_station_clients
        self.fps = STATE.fps

        # Load all scenes from effects package. Then set initial index and load it up
        self.scenes = scenes or load_scenes()
        self.curr_scene = None
        self.queued_scene = self.scenes[first_scene if first_scene else self.scenes.keys()[0]]
        self.change_scene()

        self.serve = False
        self.is_running = False

        self.osc_data = StoredOSCData(clients=osc_station_clients)
        self.setup_osc_input_handlers({0: 50})

    def next_scene_handler(self, path, tags, args, source):
        if not args or args[0] == "":
            self.next_scene()
        else:
            self.next_scene(int(args[0]))

    def select_scene_handler(self, path, tags, args, source):
        # TODO: Call specific scenes
        if args[0] == "":
            self.next_scene()
        else:
            self.pick_scene(args[0])

    def setup_osc_input_handlers(self, faders={}):
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

        def handle_lidar(path, tags, args, source):
            object_id = args[0]
            data = LidarData(
                object_id,
                args[1],
                args[2],
                args[3],  # Pose
                args[4],
                args[5],
                args[6])  # Velocity?
            # TODO Parse, queue, and erase
            self.osc_data.add_lidar_data(object_id, data)

        self.osc_server.addMsgHandler("/input/fader", handle_fader)
        self.osc_server.addMsgHandler("/lidar", handle_lidar)

        print "Registered all OSC Handlers"

    # ---- EFFECT CONTROL METHODS -----
    def change_scene(self):
        now = time.time()
        self.queued_scene.scene_starting(now)
        self.curr_scene = self.queued_scene
        print '\tScene %s started\n' % self.curr_scene
        self.curr_scene.scene_ended()

    def get_osc_frame(self, clear=True):
        # type: (bool) -> StoredOSCData
        """Get the last frame of osc data and initialize the next frame"""
        # TODO: Do we need to explicitly synchronize here?
        last_frame = self.osc_data
        self.osc_data = StoredOSCData(last_data=last_frame)
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
        fps_frame_time = 1.0 / self.fps

        print '\tsending pixels forever (quit or control-c to exit)...'
        self.is_running = True
        pixels = Pixels(STATE.layout)

        while self.serve:
            # TODO : Does this create lots of GC?
            frame_start_time = time.time()
            t = frame_start_time - start_time
            target_frame_end_time = frame_start_time + fps_frame_time

            # Create the pixels, set all, then put
            pixels[:] = 0
            self.curr_scene.render(pixels, t, self.get_osc_frame())
            # TODO: Check for None and replace with (0, 0, 0)
            self.opc_client.put_pixels(pixels.pixels, channel=0)

            # Crude way of trying to hit target fps
            wait_for_next_frame(
                target_frame_end_time, )

            # TODO: channel?

        self.is_running = False
        print "Scene Manager Exited"

    def shutdown(self):
        self.serve = False


def wait_for_next_frame(wait_until):
    time.sleep(max(0, wait_until - time.time()))


def load_scenes(effects_dir=None):
    # type: (str) -> {str, Scene}
    if not effects_dir:
        pwd = os.path.dirname(__file__)
        effects_dir = os.path.abspath(os.path.join(pwd, '..', 'effects'))
    sys.path.append(effects_dir)
    scenes = OrderedDict()
    for filename in glob.glob(os.path.join(effects_dir, '*.py')):
        pkg_name = os.path.basename(filename)[:-3]
        if pkg_name.startswith("_"):
            continue
        load_scenes_from_file(pkg_name, scenes)
    print "Loaded %s scenes from %s directory\n" % (len(scenes), effects_dir)
    return scenes


def load_scenes_from_file(pkg_name, scenes):
    # type: (str, {str, Scene}) -> None
    try:
        effect_dict = importlib.import_module(pkg_name)
        for scene in effect_dict.__all__:
            if not isinstance(scene, Scene):
                print "Got scene %s not of type Scene" % scene
                continue
            if scene.name in scenes:
                print("Cannot register scene %s. Scene with name already exists") % scene.name
                continue
            print "Registering %s" % scene
            scenes[scene.name] = scene
    except ImportError:
        print "WARNING: could not load effect %s" % pkg_name


def get_first_non_empty(pixels):
    return next(pix for pix in pixels if pix is not None)


class LidarData(object):
    def __init__(self, object_id, pose_x, pose_y, pose_z, width, height, depth):
        self.object_id = object_id
        self.pose_x = pose_x
        self.pose_y = pose_y
        self.pose_z = pose_z
        self.width = width
        self.height = height
        self.depth = depth  # Actually depth?
        self.last_updated = time.time()


class StoredStationData(object):
    def __init__(self, client=None, last_data=None):
        self.buttons = {}
        if last_data is None:
            self.faders = {}
            self.client = client
        else:
            # TODO Check with python folks. Is this a memory leak?
            self.faders = last_data.faders
            self.client = last_data.client
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
    def __init__(self, clients=None, last_data=None, num_stations=6, lidar_removal_time=.5):
        self.stations = [
            StoredStationData(
                last_data=last_data.stations[i] if last_data else None,
                client=clients[i] if clients and i < len(clients) else None)
            for i in range(num_stations)
        ]
        self.contains_change = False
        self.lidar_removal_time = lidar_removal_time
        expired = time.time() - lidar_removal_time
        self.lidar_objects = {
            k: lidar
            for (k, lidar) in last_data.lidar_objects.iteritems() if lidar.last_updated > expired
        } if last_data else {}  # type: {str, LidarData}

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

    def add_lidar_data(self, object_id, data):
        # type: (int, LidarData) -> None
        self.lidar_objects[object_id] = data


class CollaborationManager(object):
    def compute_state(self, t, collaboration_state, osc_data):
        raise NotImplementedError("All feedback effects must implement compute_state")
        # TODO: use abc


class Effect(object):
    def __init__(self):
        pass

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # type: (Pixels, float, {}, StoredOscData) -> None
        """Implement this method to render the next frame.

        Args:
            pixels: rgb values to be modified in place
            now: represents the time (in seconds)
            collaboration_state: a dictionary that can be modified by
                a CollaborationManager before any effects apply
            osc_data: contains the data sent in since the last frame
                (for buttons), as well as store fader states Use the
                osc data to get station clients if you need to send
                button feedback.
        """
        raise NotImplementedError("All effects must implement next_frame")
        # TODO: Use abc

    def scene_starting(self, now):
        pass

    def scene_ended(self):
        pass

    def is_completed(self, t, osc_data):
        return False


class MultiEffect(Effect):
    def __init__(self, *effects):
        Effect.__init__(self)
        self.effects = list(effects)

    def scene_starting(self, now):
        """Initialize a scene
        :param now:
        """
        for e in self.effects:
            e.scene_starting(now)

    def scene_ended(self):
        for e in self.effects:
            e.scene_ended()

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.before_rendering(pixels, t, collaboration_state, osc_data)

        for e in self.effects:
            e.next_frame(pixels, t, collaboration_state, osc_data)

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        self.cleanup_terminated_effects(pixels, t, collaboration_state, osc_data)

    def cleanup_terminated_effects(self, pixels, t, collaboration_state, osc_data):
        # type: (Pixel, long, {}, OscStoredData) -> None
        # TODO Debugging code here?
        self.effects[:] = [e for e in self.effects if not e.is_completed(t, osc_data)]

    def add_effect(self, effect, before=False):
        # type: (Effect) -> None
        if effect:  # Ignore None
            if before:
                self.effects.insert(0, effect)
            else:
                self.effects.append(effect)


"""
class EffectLauncher(MultiEffect):
    def __init__(self, factory, layout=None, n_pixels=None, **kwargs):
        MultiEffect.__init__(layout, n_pixels)
"""


class Scene(MultiEffect):
    def __init__(self, name, collaboration_manager, *effects):
        # str, CollaborationManager, List[Effect] -> None
        MultiEffect.__init__(self, *effects)
        self.name = name
        self.collaboration_manager = collaboration_manager
        if isinstance(collaboration_manager, Effect) and collaboration_manager not in self.effects:
            # print "WARNING: Scene %s has collaboration manager %s
            # that is an effect but is not part of layers. Inserting
            # as top layer" % (name, collaboration_manager)
            self.effects = self.effects + [collaboration_manager]
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

    def create_effect(self):
        # None -> Effect
        print "\tCreating instance of effect %s" % self
        return self.clazz(**self.kwargs)
