from hoe import animation_framework as af
from hoe import collaboration
from hoe.state import STATE


# Currently, moves a single "block" to whoever last pressed a button
class ArrangeBlocks(af.Effect):
    def __init__(self):
        self.blocks = [(255, 0, 0)]
        self.block_locations = [0]

    def next_frame(self, pixels, now, collab, osc):
        for i, station in enumerate(osc.stations):
            if station.contains_change:
                print i, station.button_presses
                self.block_locations[0] = i
        for block, loc in zip(self.blocks, self.block_locations):
            station = STATE.layout.STATIONS[loc]
            pixels[0, station.left:station.right] = block


SCENES = [
    af.Scene(
        'arrange-blocks',
        tags=[af.Scene.TAG_GAME],
        collaboration_manager=collaboration.NoOpCollaborationManager(),
        effects=[ArrangeBlocks()])
]
