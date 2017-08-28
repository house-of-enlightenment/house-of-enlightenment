"""Recreate the classic arcade game where a light rotates around and
the player has to hit the button to stop the light at a target.
"""
# sorry for the spaghetti like nature of this code.

from __future__ import division

from hoe.animation_framework import Scene
from hoe.animation_framework import Effect
from hoe.animation_framework import Game
from hoe.state import STATE
from hoe.collaboration import CollaborationManager

from shared import SolidBackground

WHITE = (255, 255, 255)
RED = (255, 0, 0)
# BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
BLUE = ()
# ORANGE = (255, 127, 0)
ORANGE = (255, 127, 99)
BLUE = (0, 127, 255)
PURPLE = (255, 2, 255)

ROWS = 216
COLUMNS = 66
STATIONS = 6

FRAME_RATE = 30 / 5

ROTATION_DIRECTION_FORWARDS = True

BOTTOM_RING_HEIGHT = 2


#
# - Corkscrew effect will get more "tight" as its wound
class TetherBall(CollaborationManager, Effect):
    def __init__(self):
        Effect.__init__(self)
        CollaborationManager.__init__(self)
        STARTING_PLAYER = 4
        STATION_WINDOW_SIZE = 3
        self.MAX_ROTATIONS = 6
        self.BALL_SIZE = 5
        self.station_window_size = STATION_WINDOW_SIZE

        # print self._get_ball_starting_position(STARTING_PLAYER)
        # x_start is the starting point for the top anchor point
        self.x_start = self._get_ball_starting_position(STARTING_PLAYER)
        # x is the current position of the bottom of the ball
        self.x = self.x_start
        # print ">>>>>>>>>>>>>>>"
        # print "INITIAL X"
        # print self.x
        # print "STATION RANGE"
        # print self._get_station_pixel_range(STARTING_PLAYER)
        # print "WINDOW"
        # print self._get_station_window(STARTING_PLAYER)
        # print "BALL POSITION"
        # print self._get_x_offset(self.x)
        # print (self._get_x_offset(self.x) + self.BALL_SIZE)
        # print ">>>>>>>>>>>>>>>"

        self.i = 0
        self.data = None
        self.direction = None
        self.speed = 0
        self.velocity = 0

        self.last_x = None

    def _get_ball_starting_position(self, station_id):
        start = self._get_middle_pixel(station_id)
        # print start
        return int(start - (self.BALL_SIZE / 2)) + 1

    def _get_middle_pixel(self, station_id):
        start, end = self._get_station_pixel_range(station_id)
        # print "get middle range"
        # print start
        # print end
        return int((end - start) / 2 + start)

    def _get_station_pixel_range(self, station_id):
        columns_per_station = (COLUMNS / STATIONS)
        if station_id == 0:
            return 0, columns_per_station
        # print columns_per_station

        return int(columns_per_station *
                   station_id), int((columns_per_station * station_id) + columns_per_station)

# 44 45 46 47 48 49 50 51 52 53 54
#             X  X  X
#          X  X  X  X  X  X

    def reset_state(self, osc_data):
        # type: (StoredOSCData) -> None
        """Resets the state for on, off, buttons, and timer"""
        # self.on = []
        # self.off = [c for c in self.all_combos]
        # self.next_button = None
        # self.flash_timer = 0
        for station in STATE.stations:
            station.buttons.set_all(on=False)
            station.buttons[1] = 1
            station.buttons[3] = 1
            # print station.buttons
        # self.pick_next(osc_data=osc_data)
        # def before_rendering(self, pixels, t, collaboration_state, osc_data):
        # MultiEffect.before_rendering(self, pixels, t, collaboration_state, osc_data)
        # for s in range(STATE.layout.sections):
        #     if osc_data.stations[s].button_presses:
        #         print osc_data.stations[s].button_presses
        # self.launch_effect(t, s)

    def scene_starting(self, now, osc_data):

        self.reset_state(osc_data=osc_data)

    def _button_press_is_valid(self, station_id):
        # self.x
        return True

    def _should_paint_frame(self):
        pass

    def _get_station_window(self, station_id):
        half_window = int(self.station_window_size / 2)
        # print "HALF"
        # print half_window
        # start, end = self._get_station_pixel_range(station_id)
        middle = self._get_middle_pixel(station_id)
        window_start = middle - half_window
        window_end = middle + half_window

        # window_start = start + half_window
        # window_end = end - half_window
        return int(window_start), int(window_end) + 1

    def _station_is_active(self, station_id):
        # 11 12 13 14 15 16 17 18 19 20 21
        #       |                  |
        #                         X  X  X  X  X

        # 11 12 13 14 15 16 17 18 19 20 21
        #       |                  |
        #     X  X

        start, end = self._get_station_window(station_id)

        x_offset = self._get_x_offset(self.x)
        # if x_offset + self.BALL_SIZE > start and x_offset < end:
        #     print start
        #     print end
        return x_offset + self.BALL_SIZE >= start and x_offset <= end

    def _set_active_buttons(self):

        for station_id, station in enumerate(STATE.stations):

            # print "station: %d %s" % (station_id, self._station_is_active(station_id))
            if self._station_is_active(station_id):
                for b in range(5):
                    # hack - setting forces and update, so don't set unless necessary to prevent network traffic
                    if station.buttons[b] != b%2:
                        station.buttons[b] = b%2
            elif station.buttons.get_high_buttons():
                station.buttons.set_all(on=False)

    def _get_x_offset(self, x):
        offset_x = x  #+ 33
        if x > 66:
            offset_x = x % 66

        if x < -66:
            offset_x = x % 66
        return offset_x

    def _set_background_pixels(self, pixels):
        pixels[:, :] = WHITE  #ORANGE
        return pixels

    def _set_bottom_ring_pixels(self, pixels):

        # if self.last_x != self.x:
        # print ">>>>>>>>"
        # print "     BALL: %s, %s" % (self._get_x_offset(self.x), (self._get_x_offset(self.x) + self.BALL_SIZE))
        for station_id in xrange(6):
            # print ">>>>>>"

            start, end = self._get_station_window(station_id)
            # print start
            # print end
            # if self.last_x != self.x:
            # print "STATION %s: %s, %s, %s" % (station_id, start, end, self._station_is_active(station_id))

            end = end
            pixels[0:2, start:end] = PURPLE

        if self.last_x != self.x:
            self.last_x = self.x
        # pixels[0:2, 2:4] = PURPLE
        return pixels

    def _set_tetherball_pixels(self, pixels):
        slope = (self.x_start - self.x) / 216
        x = int(self.x)

        for y in xrange(216):
            # pixels[216 - y - 1:216 - y, int(x):int(x +2)] = GREEN
            offset_x = self._get_x_offset(x)
            pixels[y - 1:y, int(offset_x):int((offset_x + self.BALL_SIZE))] = BLUE

            x = x + slope

            # if self.direction == "right":
            #     self.x += 1
            # if self.direction == "left":
            #     self.x -= 1
            # UNCOMMENT TO REVERSE SPIN DIRECTIONS

        #TODO: Write a better method for handling speeds slower than 1
        # speed = int(self.speed if self.speed >= 1 else 1 if (self.i) % 10 == 0 else 0)
        velocity = self.velocity

        if self.direction == "right":
            if ROTATION_DIRECTION_FORWARDS:
                self.x += velocity
            else:
                self.x -= velocity
        if self.direction == "left":
            if ROTATION_DIRECTION_FORWARDS:
                self.x -= velocity
            else:
                self.x += velocity

    def _calculate_velocity(self):

        # - The ball has an initial burst, then should naturally slow down in most cases
        # - The ball should slow down even more if its getting close to the max # of rotation
        # - Once the ball reaches the max # of rotations, it should reverse directions
        # - If a player hits the ball while it is "unraveling", the ball should be even faster

        # resistance = (float(self.x)/float(self.MAX_ROTATIONS * COLUMNS))

        self.velocity = self.velocity * .98

    def next_frame(self, pixels, t, collaboration_state, osc_data):
        if STATE.verbose:
            print "BALL X: %s  VELOCITY: %s" % (self.x, self.velocity)
        self._calculate_velocity()
        self._set_active_buttons()
        self._set_background_pixels(pixels)
        self._set_tetherball_pixels(pixels)
        self._set_bottom_ring_pixels(pixels)

        for s_id, buttons in osc_data.buttons.items():
            if self._button_press_is_valid(s_id):
                if 3 in buttons:
                    self.direction = "right"
                elif 1 in buttons:  #  Matt - did a small change here with elif
                    self.direction = "left"
                self.velocity += 1.5


        # slope = (0 - self.x)/216
        # slope = .02
        # print slope
        # pixels[215:216,0:2] = GREEN

        # print slope
        # slope = (0 - self.x)/216
        # x = self.x
        # slope = (self.x_start - self.x) / 216
        # x = self.x

        #slope = (0 - self.x) / 216
        #x = self.x

        # for y in xrange(216):
        #     # pixels[216 - y - 1:216 - y, int(x):int(x +2)] = GREEN
        #     offset_x = self._get_x_offset(x)
        #     pixels[y - 1:y, int(offset_x):int(offset_x + self.BALL_SIZE)] = BLUE

        #     x = x + slope

        #     # if self.direction == "right":
        #     #     self.x += 1
        #     # if self.direction == "left":
        #     #     self.x -= 1
        #     # UNCOMMENT TO REVERSE SPIN DIRECTIONS

        # #TODO: Write a better method for handling speeds slower than 1
        # speed = int(self.speed if self.speed >= 1 else 1 if (self.i) % 10 == 0 else 0)

        # if self.direction == "right":
        #     if ROTATION_DIRECTION_FORWARDS:
        #         self.x += speed
        #     else:
        #         self.x -= speed
        # if self.direction == "left":
        #     if ROTATION_DIRECTION_FORWARDS:
        #         self.x -= speed
        #     else:
        #         self.x += speed
        self.i += 1

        # start, end = self._get_station_pixel_range(2)
        # pixels[:, start:end] = GREEN

    def compute_state(self, t, collaboration_state, osc_data):
        pass


# class CollaborationCountBasedBackground(Effect):
#     def __init__(self, color=(0, 255, 0), max_count=6, bottom_row=3, max_row=216):
#         Effect.__init__(self)
#         self.color = color
#         self.bottom_row = bottom_row
#         self.top_row_dict = {
#             i: int(bottom_row + i * (max_row - bottom_row) / max_count)
#             for i in range(1, max_count + 1)
#         }
#         self.current_level = int(bottom_row + (max_row - bottom_row) / max_count)
#         self.target_row = self.current_level

#     def next_frame(self, pixels, t, collaboration_state, osc_data):
#         self.target_row = self.top_row_dict[collaboration_state["count"]]
#         if self.target_row > self.current_level:
#             self.current_level += 1
#         elif self.target_row < self.current_level:
#             self.current_level -= 1

#         for ii in set(
#                 reduce(lambda a, b: a + b,
#                        [STATE.layout.row[i] for i in range(self.bottom_row, self.current_level)])):
#             pixels[ii] = self.color

SCENES = [
    Game(
        "tetherball",
        tags=[Scene.TAG_WIP, Scene.TAG_PRODUCTION],
        collaboration_manager=TetherBall(),
        effects=[]
        # effects=[CollaborationCountBasedBackground()]
    )
]
