import functools

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import distance
import hoe.fountain_models as fm
from hoe import sources
from hoe.state import STATE
from hoe import translations
from hoe import transitions

# there should be at least three variations of this
# - gentle
# - Stroboscopic
# - Something maybe more chaotic, but with wipe up


#
# The stroboscopic effect comes from the varying rotation speeds which
# can make it look like the animation is flowing down while it is
# actually flowing up
#
# The cycling between 18-8 is the main cause. There are other
# combinations of rotation that cause this look, but I haven't figured
# out the right relationship and managed to find this one by accident.
#
def make_stroboscopic_effect_analogous():
    rotation = translations.Rotate(STATE.layout.columns, transitions.ConstantTransition(16))

    hue = transitions.HueTransition(
        start=functools.partial(np.random.randint, 0, 256),
        length=functools.partial(np.random.randint, 20, 80))
    # I wish this had more red in it
    row = sources.RainbowRow(
        STATE.layout, rotation, sv=transitions.ConstantTransition((255, 255)), hue=hue)

    effect = translations.UpAndRotateEffect(
        STATE.layout,
        row,
        up_speed=distance.PixelsPerFrame(1),
        rotate_speed=transitions.CycleTransition((18, 8)))
    return effect


def make_stroboscopic_effect_complement():
    hue = transitions.WalkTransition(
        start=np.random.randint(0, 256), step=functools.partial(np.random.randint, 20, 40))

    # TODO: apply rotation
    row = sources.ComplimentaryRow(STATE.layout.columns, hue, .3)

    effect = translations.UpAndRotateEffect(
        STATE.layout,
        row,
        up_speed=distance.PixelsPerFrame(1),
        rotate_speed=transitions.CycleTransition((18, 8)))
    return effect


def make_stream_up():
    # speed here is pixels / second
    rotation = translations.Rotate(STATE.layout.columns, transitions.UniformRandTransition(5, 55))

    hue = transitions.HueTransition(
        start=functools.partial(np.random.randint, 0, 256),
        length=functools.partial(
            np.random.choice, [32, 32, 32, 64, 64, 64, 96, 96, 96, 128, 128, 160, 160, 192, 224]))
    # I wish this had more red in it
    row = sources.RainbowRow(STATE.layout, rotation, sv=transitions.SvTransition(), hue=hue)

    # the rotation units here are pixels / frame
    # mostly prefer to be slow, but the occasional spike up is interesting
    structure_rotation = transitions.Choice(np.array([0, 0, 1, 1, 1, 2, 2, 3, 4]) * STATE.fps)

    effect = translations.UpAndRotateEffect(
        STATE.layout,
        row,
        up_speed=distance.PixelsPerFrame(1),
        rotate_speed=distance.VaryingPixelsPerFrame(structure_rotation)
    )
    return effect


def make_stream_up_single():
    # speed here is pixels / second
    rotation = translations.Rotate(
        STATE.layout.columns, transitions.ConstantTransition(1))

    # I wish this had more red in it
    row = SingleColumn(STATE.layout, rotation)

    # the rotation units here are pixels / frame
    # mostly prefer to be slow, but the occasional spike up is interesting
    structure_rotation = transitions.ConstantTransition(2)

    effect = translations.UpAndRotateEffect(
        STATE.layout,
        row,
        up_speed=distance.PixelsPerFrame(1),
        rotate_speed=distance.VaryingPixelsPerFrame(structure_rotation))
    return effect


class SingleColumn(object):
    """Creates a row that is just one red pixel.

    Can be useful to see how the shape flows up the HoE.
    """

    def __init__(self, layout, rotate):
        self.layout = layout
        self.rotate = rotate
        self.hue = 0

    def start(self, now):
        self.rotate.start(now)

    def __call__(self, now, **kwargs):
        row = np.zeros((self.layout.columns, 3), np.uint8)
        row[10, :] = (255, 0, 0)  #color_utils.hsv2rgb((self.hue, 255, 255))
        self.hue = (self.hue + 16) % 256
        return self.rotate(row, now)



SCENES = [
    fm.FountainScene(
        'stroboscopic-complement',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[make_stroboscopic_effect_complement()]),
    fm.FountainScene(
        'stroboscopic-analogous',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[make_stroboscopic_effect_analogous()]),
    fm.FountainScene(
        'stream-up',
        tags=[af.Scene.TAG_PRODUCTION],
        background_effects=[make_stream_up()]),
    # Not production
    fm.FountainScene(
        'stream-up-single',
        background_effects=[make_stream_up_single()])
]
