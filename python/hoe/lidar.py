from hoe.animation_framework import Effect
from hoe.state import STATE

from math import ceil
import numpy as np

class DavesAbstractLidarClass(Effect):
    def next_frame(self, pixels, t, collaboration_state, osc_data):
        HEIGHT_SCALE = 30
        DISTANCE_SCALE = 10

        ratio = STATE.layout.columns / (np.pi * 2)
        if osc_data.lidar_objects:
            objects = osc_data.lidar_objects
            lidar_computations = []
            for obj_id, data in objects.iteritems():
                # TODO Probably faster conversion mechanism or at least make a helper method
                apothem = np.sqrt(data.pose_x**2 + data.pose_y**2)
                central_theta = np.arctan2(data.pose_y, data.pose_x)
                half_angle = abs(np.arctan2(data.width / 2, apothem))

                bottom_row = max(0, int(apothem * DISTANCE_SCALE))
                top_row = min(STATE.layout.BOTTOM_DISC.center,
                              int(bottom_row + 1 + abs(data.height * HEIGHT_SCALE)))
                bottom_row, top_row = min(bottom_row, top_row), max(bottom_row, top_row)

                col_left = int((central_theta - half_angle) * ratio) % STATE.layout.columns
                col_right = int(ceil((central_theta + half_angle) * ratio)) % STATE.layout.columns

                self.render_lidar_input(
                    pixels=pixels,
                    obj_id=obj_id,
                    row_bottom=bottom_row,
                    row_top=top_row,
                    col_left=col_left,
                    col_right=col_right)

    def get_default_slices(self, row_bottom, row_top, col_start, col_end):
        """ Return an array of pairwise slices from bottom->top and left->right with column wraparound
        Currently does not support:
            right->left
            top->bottom
            start_col>total columns
            start_col<0
            end_col - start_col>total columns (would light everything)
        """

        row_slice = slice(row_bottom, row_top)
        if col_end < col_start:
            return [(row_slice, slice(0, col_end)), (row_slice, slice(col_start, None))]
        else:
            # print "No wrap"
            return [(row_slice, slice(col_start, col_end))]

    def render_lidar_input(self, pixels, obj_id, row_bottom, row_top, col_left, col_right):
        # TODO: Should this just be a passed in function instead of needing to subclass?
        raise NotImplementedError


class OpaqueLidar(DavesAbstractLidarClass):
    def render_lidar_input(self, pixels, obj_id, row_bottom, row_top, col_left, col_right):
        color = np.asarray((0, 0, 0), np.uint8)
        color[obj_id % 3] = (255 - 30) / 2
        pixels.update_slices(
            additive=True,
            color=color,
            slices=self.get_default_slices(row_bottom, row_top, col_left, col_right))


class SwappingLidar(DavesAbstractLidarClass):
    def render_lidar_input(self, pixels, obj_id, row_bottom, row_top, col_left, col_right):
        if col_left < col_right:
            pixels[row_bottom:row_top, col_left:col_right] = pixels[row_top:row_bottom:-1,
                                                                    col_right:col_left:-1]
        else:
            col_indices = map(lambda x: x % STATE.layout.columns,
                              range(col_right, col_left + STATE.layout.columns))
            reversed_indices = col_indices
            reversed_indices.reverse()
            pixels[row_bottom:row_top, col_indices] = pixels[row_top:row_bottom:-1,
                                                             reversed_indices]

