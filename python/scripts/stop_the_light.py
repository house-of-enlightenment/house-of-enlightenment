"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code, but its getting better

from __future__ import division
import json
import math
import Queue
import random
import sys
import time

import numpy as np

from hoe import layout
from hoe import opc
from hoe import osc_utils

# TODO: fix this. Move the stream_up code somewhere shared
import stream_up as su

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


def main():
    # TODO: copy and paste is bad, mkay.
    client = opc.Client('localhost:7890')
    if not client.can_connect():
        print('Connection Failed')
        return 1

    with open('layout/hoeLayout.json') as f:
        hoe_layout = layout.Layout(json.load(f))

    osc_queue = Queue.Queue()
    server = osc_utils.create_osc_server()
    # pylint: disable=no-value-for-parameter
    server.addMsgHandler("/input", lambda *args: add_station_id(osc_queue, *args))
    background = su.Effect(hoe_layout)
    interaction = Effect(hoe_layout, osc_queue)
    render = su.Render(client, osc_queue, hoe_layout, [background, interaction])
    render.run_forever()


class Effect(object):
    def __init__(self, hoe_layout, queue):
        self.state = State.ACTIVE
        self.successful_sections = [False] * hoe_layout.sections
        self.fps = 30
        rotation_speed = .5  # rotation / second
        location = 0
        self.sprite = Sprite(hoe_layout, location, rotation_speed)
        self.layout = hoe_layout
        self.queue = queue

    def set_target_idx(self):
        unhit_centers = [
            c for suc, c in zip(self.successful_sections, self.section_centers) if not suc
        ]
        self.target_idx = self.layout.grid[self.bottom, unhit_centers]

    def start(self, now):
        self.bottom = slice(None, 10, None)
        self.top = slice(10, None, None)
        self.section_centers = range(6, 66, 11)
        self.set_target_idx()
        self.now = now
        self.ignore_buttons_until = self.now + random.random() * 2 + .5
        self.sprite.start(self.now)

    def init_pixels(self):
        self.pixels[self.bottom, :] = 32

    def blackout_unsuccessful_sections(self):
        start = range(0, 66, 11)
        end = range(11, 67, 11)
        for suc, s, e in zip(self.successful_sections, start, end):
            if not suc:
                self.pixels[self.top, s:e] = 0

    def next_frame(self, now, pixels):
        self.now = time.time()
        self.pixels = pixels
        self.init_pixels()
        if self.state == State.ACTIVE:
            self.sprite.update(self.now)
            self.pixels[self.target_idx] = YELLOW
            columns = self.sprite.columns()
            # want to allow the sprite to move for a little while
            # before allowing any buttons to be pressed
            if self.now < self.ignore_buttons_until:
                empty_queue(self.queue)
                # have the sprite be light blue until a button can be
                # pressed
                # TODO: maybe increase the wait time if a button
                # is pressed while the sprite is light blue; this will stop
                # people from just spamming the buttons, although
                # that is not a useful strategy.
                self.pixels[self.bottom, columns] = (135, 206, 250)
                self.blackout_unsuccessful_sections()
                return
            else:
                self.pixels[self.bottom, columns] = BLUE
            try:
                section = self.queue.get_nowait()
                if self.successful_sections[section]:
                    # Ignore buttons for already succesful sections
                    self.blackout_unsuccessful_sections()
                    return
                target = self.section_centers[section]
                sprite_idx = self.layout.grid[self.bottom, columns]
                if target in columns:
                    self.state = State.HIT
                    self.flash = Flash(sprite_idx, .25, (GREEN, BLACK))
                    self.wait_until = self.now + 3
                    self.successful_sections[section] = True
                    self.set_target_idx()
                else:
                    self.state = State.MISS
                    self.flash = Flash(sprite_idx, .25, (RED, BLACK))
                    self.wait_until = self.now + 2
            except Queue.Empty:
                pass
        elif self.state == State.HIT:
            # Note that there is no call to sprite.update()
            self.pixels[self.target_idx] = YELLOW
            columns = self.sprite.columns()
            self.flash.render(self.now, self.pixels)
            if self.now >= self.wait_until:
                self.sprite.reverse(self.now)
                self.wait_until = None
                self.ignore_buttons_until = self.now + random.random() * 2 + .5
                self.state = State.ACTIVE
        elif self.state == State.MISS:
            # Note that there is no call to sprite.update()
            self.pixels[self.target_idx] = YELLOW
            columns = self.sprite.columns()
            self.flash.render(self.now, self.pixels)
            if self.now >= self.wait_until:
                self.sprite.reverse(self.now)
                self.wait_until = None
                self.ignore_buttons_until = self.now + random.random() * 2 + .5
                self.state = State.ACTIVE
        else:
            raise Exception('You are in a bad state: {}'.format(self.state))
        self.blackout_unsuccessful_sections()


class Flash(object):
    def __init__(self, idx, duration, colors):
        self.idx = idx
        self.duration = duration
        self.colors = colors
        self.next_switch = time.time() + duration
        self.color_idx = 0

    def current_color(self):
        return self.colors[self.color_idx]

    def switch(self, now):
        self.next_switch = now + self.duration
        self.color_idx = (self.color_idx + 1) % len(self.colors)

    def render(self, now, pixels):
        if self.next_switch < now:
            self.switch(now)
        pixels[self.idx] = self.current_color()


class State(object):
    ACTIVE = 'active'
    HIT = 'hit'
    MISS = 'miss'


class Sprite(object):
    def __init__(self, layout, start_location, rotation_speed, width=3):
        self.layout = layout
        self.start_location = start_location
        self.rotation_speed = rotation_speed
        self.location = start_location
        self.width = width
        self.start_time = None

    def start(self, now):
        self.start_time = now

    def reverse(self, now):
        self.start_location = self.location
        self.rotation_speed = -self.rotation_speed
        self.start(now)

    def update(self, now):
        sprite_rotation = (now - self.start_time) * self.rotation_speed
        location = int(self.layout.columns * sprite_rotation) + self.start_location
        self.location = location % self.layout.columns

    def columns(self):
        left = int(self.width / 2)
        right = self.width - left
        return map(self.layout.colmod, range(self.location - left, self.location + right))


def empty_queue(queue):
    while True:
        try:
            queue.get_nowait()
        except Queue.Empty:
            return


def add_station_id(queue, address, types, payload, *args):
    print address, types, payload, args
    station_id, control_type, control_id, value = payload
    queue.put(station_id)


if __name__ == '__main__':
    sys.exit(main())
