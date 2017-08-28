"""Framework for running animations and effects"""
import glob
import importlib
import os.path
import sys
import time
from collections import OrderedDict
from collections import defaultdict
from random import choice
from threading import Thread

from OSC import OSCServer

from hoe.opc import Client
from hoe.pixels import Pixels
from hoe.state import STATE
from hoe.collaboration import NoOpCollaborationManager, CollaborationManager


FAIL_ON_LOAD = True


class AnimationFramework(object):
    def __init__(self,
                 osc_server,
                 opc_client,
                 scenes=None,
                 first_scene=None,
                 no_interaction_timeout=5 * 60,
                 max_scene_timeout=15 * 60,
                 tags=[]):
        # type: (OSCServer, Client, List(OSCClient), {str, Scene}) -> None
        self.osc_server = osc_server
        self.opc_client = opc_client
        self.fps = STATE.fps
        self.no_interaction_timeout = no_interaction_timeout
        self.max_scene_timeout = max_scene_timeout

        # Load all scenes from effects package. Then set initial index and load it up
        if not tags:
            print "Tags not specified. Using only scenes with tags [production]"
            tags = [Scene.TAG_PRODUCTION]
        loaded_scenes = load_scenes_and_fountains(tags=tags)
        self.scenes = scenes or loaded_scenes
        self.non_game_scenes = [name for name, scene in self.scenes.items()
                                if not scene.is_game()]  #  TODO: validation

        map(lambda s: s.after_all_scenes_loaded(), self.scenes.values())

        self.curr_scene = None
        self.queued_scene = self.scenes[first_scene if first_scene else self.non_game_scenes[0]]
        self._last_scene_change_timestamp = time.time()

        self.serve = False
        self.is_running = False

        self.osc_data = OSCDataAccumulator(last_data=None)
        self.setup_osc_input_handlers({0: 50})

    def next_scene_handler(self, path, tags, args, source):
        if not args or args[0] == "":
            self.next_scene()
        else:
            self.next_scene(int(args[0]))

    def select_scene_handler(self, path, tags, args, source):
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

        # self.osc_server.addMsgHandler("/scene/picknew", self.pick_new_scene_handler)

        # Set up buttons
        def handle_button(path, tags, args, source):
            station, button_id = map(int, args)
            self.osc_data.button_pressed(station, button_id)

        self.osc_server.addMsgHandler("/input/button", handle_button)

        # # Set up faders
        # for fader in faders:
        #     self.osc_data.init_fader_on_all_stations(fader, faders[fader])

        def handle_fader(path, tags, args, source):
            station = int(args[0])
            value = int(args[1+(len(args) == 3)])
            self.osc_data.fader_changed(station, value)

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

        def handle_set_timeout_command(path, tags, args, source):
            try:
                assert len(args) == 2
                self.no_interaction_timeout, self.max_scene_timeout = float(args[0]), float(args[1])
            except (AssertionError, ValueError):
                print "Received invalid set timeout message with args {}. Usage (times in seconds): \n /set/timeouts <no_interaction> <max_on_single_scene>".format(
                    args)

        self.osc_server.addMsgHandler("/set/timeouts", handle_set_timeout_command)
        print "Registered all OSC Handlers"

    # ---- EFFECT CONTROL METHODS -----
    def poll_next_scene(self, now, osc_data):
        """Change the scene by taking the queued scene and swapping it in.
        """

        self.check_game_state(now, osc_data)

        if self.queued_scene:
            self._last_scene_change_timestamp = time.time()
            # Cache the scene queue locally so it can't be changed on us
            next_scene, last_scene, self.queued_scene = self.queued_scene, self.curr_scene, None
            next_scene.scene_starting(self._last_scene_change_timestamp, osc_data)
            self.curr_scene = next_scene  # Go!
            print '\tScene %s started\n' % self.curr_scene
            # Now give the last scene a chance to cleanup
            if last_scene:
                last_scene.scene_ended()

    def get_osc_frame(self, clear=True):
        # type: (bool) -> OSCDataAccumulator
        """Get the last frame of osc data and initialize the next frame"""
        # TODO: Do we need to explicitly synchronize here?
        last_frame, self.osc_data = self.osc_data, OSCDataAccumulator(last_data=self.osc_data)
        # We polled, now update the fader before the next frame
        for fader, value in last_frame.faders.items():
            STATE.stations[fader].fader_value = value # pylint: disable=unsubscriptable-object
        return last_frame

    def next_scene(self, increment=1):
        """ Move the selected scene forward or back from the at-large pool"""
        curr_idx = self.scenes.keys().index(self.curr_scene.name)
        new_idx = (curr_idx + increment) % len(self.scenes)
        self.pick_scene(self.scenes.keys()[new_idx])

    def pick_scene(self, scene_name):
        """ Change to a specific scene """
        if scene_name in self.scenes.keys():
            self.queued_scene = self.scenes[scene_name]
        else:
            print "Could not change scenes. Scene %s does not exist" % scene_name

    def check_game_state(self, now, osc_data):
        if self.curr_scene is None:
            return

        last_interaction = max(STATE.stations.last_interaction(), self._last_scene_change_timestamp)
        if self.curr_scene.is_completed(
                now, osc_data
        ) or last_interaction < now - self.no_interaction_timeout or last_interaction < now - self.max_scene_timeout:
            # Pick new scene
            self.pick_scene(choice(self.non_game_scenes))
        elif not self.curr_scene.is_game():
            # TODO if we want to optimize this, use a binary search tree (sparse?)
            curr_state = STATE.stations.get_buttons_code()
            if curr_state in STATE.codes.codes_to_scenes:
                print "Picking new scene"
                self.pick_scene(STATE.codes.codes_to_scenes[curr_state])

    # ---- LIFECYCLE (START/STOP) METHODS ----

    def serve_in_background(self, daemon=True):
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

        self.fps_frame_time = 1.0 / self.fps
        self.fps_warn_threshold = self.fps_frame_time * .2  # Warn if 20% overage

        print '\tsending pixels forever (quit or control-c to exit)...'
        self.is_running = True
        self.pixels = Pixels(STATE.layout)

        try:
            while self.serve:
                self._serve()
        finally:
            self.is_running = False
            print "Scene Manager Exited"

    def _serve(self):
        # TODO : Does this create lots of GC?
        frame_start_time = time.time()
        target_frame_end_time = frame_start_time + self.fps_frame_time
        osc_data = self.get_osc_frame()

        self.poll_next_scene(now=frame_start_time, osc_data=osc_data)

        # Create the pixels, set all, then put
        self.pixels[:] = 0
        self.curr_scene.render(self.pixels, frame_start_time, osc_data)
        render_timestamp = time.time()

        #Now send
        self.pixels.put(self.opc_client)

        # Update all the button light as needed!
        STATE.stations.send_button_updates()

        # Okay, now we're done for real. Wait for target FPS and warn if too slow
        completed_timestamp = time.time()
        sleep_amount = target_frame_end_time - completed_timestamp
        self._log_timings(frame_start_time, render_timestamp, completed_timestamp, sleep_amount)
        if sleep_amount > 0:
            time.sleep(sleep_amount)

    def _log_timings(self, frame_start_time, render_ts, completed_ts, sleep_amount):
        if sleep_amount < 0 and -sleep_amount > self.fps_warn_threshold:
            print sleep_amount, self.fps_warn_threshold
            # Note: possible change_scene() is called in between. Issue is trivial though
            msg = "WARNING: scene {} is rendering slowly. Total: {} Render: {} OPC: {}"
            print msg.format(self.curr_scene.name, completed_ts - frame_start_time,
                             render_ts - frame_start_time, completed_ts - render_ts)

    def shutdown(self):
        self.serve = False


def load_scenes_and_fountains(effects_dir=None, tags=[]):
    # type: (str) -> {str, Scene}
    if not effects_dir:
        pwd = os.path.dirname(__file__)
        effects_dir = os.path.abspath(os.path.join(pwd, '..', 'effects'))
    # effects might import other sub-effects from the effects directory
    # so we need it to be on the path
    sys.path.append(effects_dir)
    scenes = OrderedDict()
    fountains = []
    for filename in glob.glob(os.path.join(effects_dir, '*.py')):
        pkg_name = os.path.basename(filename)[:-3]
        if pkg_name.startswith("_"):
            continue
        load_scenes_from_file(pkg_name, scenes, tags)
        load_fountains_from_file(pkg_name, fountains)
    print "Loaded %s scenes from %s directory\n" % (len(scenes), effects_dir)
    STATE.fountains = fountains
    return scenes


def load_scenes_from_file(pkg_name, scenes, tags):
    # type: (str, {str, Scene}) -> None
    try:
        effect_dict = importlib.import_module(pkg_name)
        if hasattr(effect_dict, '__all__'):
            print('WARNING. Usage of __all__ to define scenes is deprecated. '
                  'Use the SCENES variable instead')
            return
        if not hasattr(effect_dict, 'SCENES'):
            print 'Skipping {}. No SCENES are defined'.format(pkg_name)
            return
        save_scenes(effect_dict.SCENES, scenes, tags)
    except (ImportError, SyntaxError) as e:
        if FAIL_ON_LOAD:
            raise
        import traceback
        print "WARNING: could not load effect %s" % pkg_name
        traceback.print_exc()
        print


def save_scenes(input_scenes, output_scenes, tags):
    for scene in input_scenes:
        if not isinstance(scene, Scene):
            print "Got scene %s not of type Scene" % scene
            continue
        if scene.name in output_scenes:
            print "Cannot register scene %s. Scene with name already exists" % scene.name
            continue
        if not tags or any(tag in tags for tag in scene.tags):
            print "Registering %s" % scene
            output_scenes[scene.name] = scene
        else:
            print "Skipped %s. Tags %s not in %s" % (scene, scene.tags, tags)


def load_fountains_from_file(pkg_name, fountains):
    try:
        if pkg_name in sys.modules:
            fountain_dict = sys.modules[pkg_name]
            if hasattr(fountain_dict, 'FOUNTAINS'):
                fountains.extend(fountain_dict.FOUNTAINS)
    except (ImportError, SyntaxError) as e:
        import traceback
        print "WARNING: could not load fountains from %s" % pkg_name
        traceback.print_exc()
        print

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


class OSCDataAccumulator(object):
    """ Used by OSC Handlers to update data. Reset each frame except for lidar
    Should also reset itself but doesn't. Just create a new object each time instead, passing the old.
    """

    def __init__(self, last_data=None, lidar_removal_time=.5):
        self.faders = {}  # station_id -> new value
        self.buttons = defaultdict(set)  # station_id -> [buttons that were pressed]
        # Lidar is a little tricker - need to store it for a little in a dictionary and then purge if it goes stale
        self.lidar_removal_time = lidar_removal_time
        expired = time.time() - lidar_removal_time
        self.lidar_objects = { k: lidar
                         for (k, lidar) in last_data.lidar_objects.iteritems() if lidar.last_updated > expired
           } if last_data else {}  # type: {str, LidarData}

    def button_pressed(self, station, button):
        self.buttons[station].add(button)

    def fader_changed(self, station, value):
        self.faders[station] = value

    def add_lidar_data(self, object_id, data):
        # type: (int, LidarData) -> None
        self.lidar_objects[object_id] = data


class Effect(object):
    def __init__(self):
        pass

    def next_frame(self, pixels, now, collaboration_state, osc_data):
        # type: (Pixels, float, {}, OSCDataAccumulator) -> None
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

    def after_all_scenes_loaded(self):
        pass

    def scene_starting(self, now, osc_data):
        pass

    def scene_ended(self):
        pass

    def is_completed(self, t, osc_data):
        return False


class MultiEffect(Effect):
    def __init__(self, *effects):
        Effect.__init__(self)
        self.effects = list(effects)
        self.clear_effects_after = True

    def after_all_scenes_loaded(self):
        for e in self.effects:
            e.after_all_scenes_loaded()

    def scene_starting(self, now, osc_data):
        """Initialize a scene
        :param osc_data:
        """
        for e in self.effects:
            e.scene_starting(now, osc_data)

    def count(self):
        return len(self.effects)

    def scene_ended(self):
        for e in self.effects:
            e.scene_ended()
        if self.clear_effects_after:
            self.effects = []

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        self.before_rendering(pixels, t, collaboration_state, osc_data)

        for e in self.effects:
            e.next_frame(pixels, t, collaboration_state, osc_data)

    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        self.cleanup_terminated_effects(pixels, t, collaboration_state, osc_data)

    def cleanup_terminated_effects(self, pixels, t, collaboration_state, osc_data):
        # type: (Pixel, long, {}, OSCDataAccumulator) -> None
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
    TAG_BACKGROUND = 'background'
    TAG_PRODUCTION = 'production'
    TAG_TEST = 'test'
    TAG_EXAMPLE = 'example'
    TAG_WIP = 'wip'  # Work in Progress

    def __init__(self, name, tags, collaboration_manager=None, effects=[]):
        # str, CollaborationManager, List[Effect] -> None
        MultiEffect.__init__(self, *effects)
        self.name = name
        self.tags = tags
        self.collaboration_manager = collaboration_manager or NoOpCollaborationManager()
        if isinstance(collaboration_manager, Effect) and collaboration_manager not in self.effects:
            # print "WARNING: Scene %s has collaboration manager %s
            # that is an effect but is not part of layers. Inserting
            # as top layer" % (name, collaboration_manager)
            self.effects = self.effects + [collaboration_manager]
        self.collaboration_state = {}
        self.clear_effects_after = False

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def render(self, pixels, t, osc_data):
        self.collaboration_state = self.collaboration_manager.compute_state(
            t, self.collaboration_state, osc_data)
        # TODO Why didn't super(MultiEffect, self) work?
        self.next_frame(pixels, t, self.collaboration_state, osc_data)

    def is_game(self):
        return False


class Game(Scene):
    def __init__(self, name, tags, collaboration_manager, effects):
        Scene.__init__(self, name=name, tags=tags, collaboration_manager=collaboration_manager, effects=effects)

    def is_game(self):
        return True
