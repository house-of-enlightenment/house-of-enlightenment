from hoe import color_utils
from hoe.animation_framework import Scene, Effect, MultiEffect, LaunchedEffect, LaunchedEffectPool
from hoe.state import STATE
import hoe.fountain_models as fm
from generic_effects import NoOpCollaborationManager
from shared import SolidBackground
from random import randrange


class SpatialStripesBackground(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            self.spatial_stripes(pixels, t, coord, ii)

    #-------------------------------------------------------------------------------
    # color function
    def spatial_stripes(self, pixels, t, coord, ii):
        """Compute the color of a given pixel.

        t: time in seconds since the program started.
        ii: which pixel this is, starting at 0
        coord: the (x, y, z) position of the pixel as a tuple
        n_pixels: the total number of pixels

        Returns an (r, g, b) tuple in the range 0-255

        """
        # make moving stripes for x, y, and z
        x, y, z = coord["point"]
        r = color_utils.scaled_cos(x, offset=t / 4, period=1, minn=0, maxx=0.7)
        g = color_utils.scaled_cos(y, offset=t / 4, period=1, minn=0, maxx=0.7)
        b = color_utils.scaled_cos(z, offset=t / 4, period=1, minn=0, maxx=0.7)
        r, g, b = color_utils.contrast((r, g, b), 0.5, 2)
        pixels[ii] = (r * 256, g * 256, b * 256)


class ColumnStreak(Effect):
    def __init__(self, start_col, color=(255, 255, 255), streak_length=5, row_start=2):
        self.column = start_col
        self.streak_length = streak_length
        self.bottom_row = row_start
        self.row = row_start

        self.colors = [(color[0] - i * color[0] / 4, color[1] - i * color[1] / 4,
                        color[2] - i * color[2] / 4) for i in range(streak_length)]

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        tail = max(self.row - self.streak_length + 1, self.bottom_row)
        pixels[tail:self.row + 1, self.column] = self.colors[self.row - tail::-1]
        self.row += 1

    def is_completed(self, t, osc_data):
        # TODO run off the top
        return self.row >= STATE.layout.rows

class AdjustableFillFromBottom(Effect):
    def __init__(self, max_in=100):
        Effect.__init__(self)
        self.color_scale = 255.0 / max_in
        self.row_scale = 216.0 / max_in

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        for ii, coord in enumerate(STATE.layout.pixels):
            self.fill(pixels, t, coord, ii, osc_data)

    def fill(self, pixels, time, coord, ii, osc_data):
        # TODO Check for existance of fade
        if osc_data.stations[5].faders[0] * self.row_scale > coord["row"]:
            pixels[ii] = tuple(
                [int(osc_data.stations[i].faders[0] * self.color_scale) for i in range(3)])


class SampleEffectLauncher(MultiEffect):
    def before_rendering(self, pixels, t, collaboration_state, osc_data):
        MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        for s_id, buttons in osc_data.buttons.items():
            if buttons:
                self.launch_effect(t, s_id)

    def launch_effect(self, t, s):
        per_section = int(STATE.layout.columns / STATE.layout.sections)
        e = ColumnStreak(
            start_col=randrange(0 + s * per_section, (s + 1) * per_section), color=(255, 0, 0))
        self.effects.append(e)

FOUNTAINS = [
    fm.FountainDefinition('streak', ColumnStreak)
]

SCENES = [
    # These scenes are too slow
    # Scene(
    #     "spatial scene",
    #     tags=[Scene.TAG_BACKGROUND],
    #     collaboration_manager=NoOpCollaborationManager(),
    #     effects=[SpatialStripesBackground()]),
    # Scene(
    #     "adjustablebackground",
    #     tags=[Scene.TAG_EXAMPLE],
    #     collaboration_manager=NoOpCollaborationManager(),
    #     effects=[SolidBackground(), AdjustableFillFromBottom()]),
    Scene(
        "launchdots",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 SampleEffectLauncher()]),
    Scene(
        "fountaindots",
        tags=[Scene.TAG_EXAMPLE],
        collaboration_manager=NoOpCollaborationManager(),
        effects=[SolidBackground(color=(30, 30, 30)),
                 fm.FountainLaunchingController(fountain_pool=FOUNTAINS)]
    )
]
