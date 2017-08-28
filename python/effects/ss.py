import functools
import logging


import numpy as np

from hoe import animation_framework as af
from hoe import stations
from hoe.state import STATE
from hoe.simon_says import tutorial
from hoe.simon_says import game


logger = logging.getLogger(__name__)


class SimonSays(af.Effect, af.CollaborationManager):
    def __init__(self):
        self.points = {i: 0 for i in range(6)}
        self.points['total'] = 0
        self.step = tutorial.MultiLevelTutorial(on_finished=self.start_game)

    def start_game(self):
        self.step = game.SimonSaysGame(self.on_end_of_game)

    def compute_state(self, now, state, osc):
        new_points = self.step.compute_state(now, state, osc)
        if new_points:
            print 'new points', new_points
            total = sum(new_points.values())
            self.points['total'] += total
            for k, v in new_points.items():
                self.points[k] += v
            print self.points
        return self.points

    def on_end_of_game(self, winner):
        # nobody could be a winner
        print '%s is a winner' % winner
        # TODO: what does the end of a game look like?

    def next_frame(self, pixels, now, state, osc):
        self.step.next_frame(pixels, now, state, osc)


SCENES = [
    af.Game('simon-says', tags=[], collaboration_manager=SimonSays(), effects=[])
]
