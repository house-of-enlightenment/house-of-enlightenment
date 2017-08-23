"""Launch the framework and cycle through all the scenes"""
import csv
import sys
import time

from hoe import animation_framework as af
from hoe import houseOfEnlightenment
from hoe.state import STATE
from hoe import stations


class MockOscServer(object):
    def addMsgHandler(self, *args, **kwargs):
        pass


class LoggingAnimationFramework(af.AnimationFramework):
    def _log_timings(self, frame_start_time, render_ts, completed_ts, sleep_amount):
        super(LoggingAnimationFramework, self)._log_timings(
            frame_start_time, render_ts, completed_ts, sleep_amount)
        total = completed_ts - frame_start_time
        render = render_ts - frame_start_time
        opc = completed_ts - render_ts
        with open('timing_log.csv', 'a') as f:
            csv.writer(f).writerow((self.curr_scene.name, total, render, opc, sleep_amount))


def main():
    options = houseOfEnlightenment.parse_command_line()
    STATE.stations = stations.Stations()
    # could make a mock opc client too, but I think its slightly
    # better to just have a simple socket server setup
    opc = houseOfEnlightenment.create_opc_client('127.0.0.1:7890')
    with open('timing_log.csv', 'w') as f:
        csv.writer(f).writerow(('scene_name', 'total', 'render', 'opc', 'sleep'))
    try:
        osc = MockOscServer()
        mgr = LoggingAnimationFramework(osc, opc, None, [])
        try:
            thread = mgr.serve_in_background()
            for scene in mgr.scenes:
                print "====="
                print 'Testing {}'.format(scene)
                mgr.pick_scene(scene)
                time.sleep(10)
                if mgr.is_running:
                    print '{} succesfully rendered'.format(scene)
                else:
                    raise Exception('Failed to render {}'.format(scene))
        finally:
            mgr.shutdown()
            while mgr.is_running:
                time.sleep(.1)
    finally:
        opc.disconnect()


if __name__ == '__main__':
    sys.exit(main())
