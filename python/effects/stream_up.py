import functools

import numpy as np

from hoe import animation_framework as af
from hoe import collaboration
from hoe import distance
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
        rotate_speed=distance.VaryingPixelsPerFrame(structure_rotation))
    return effect


SCENES = [
    af.Scene(
        'stroboscopic-complement',
        tags=[],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[make_stroboscopic_effect_complement()]),
    af.Scene(
        'stroboscopic-analogous',
        tags=[],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[make_stroboscopic_effect_analogous()]),
    af.Scene(
        'stream-up',
        tags=[],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[make_stream_up()])
]
