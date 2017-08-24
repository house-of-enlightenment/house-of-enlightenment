"""Launch the framework and cycle through all the scenes"""
import argparse
import sys
import time

from hoe import animation_framework as af
from hoe import houseOfEnlightenment
from hoe.state import STATE
from hoe import stations


class MockOscServer(object):
    def addMsgHandler(self, *args, **kwargs):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--time-per-scene', default=1, type=int, help='how long to run each scene')
    parser.add_argument(
        '--loops', default=1, type=int,
        help='how many times to loop thru the scenes. 0 => forever')
    args = parser.parse_args()
    # passing in an empty array means that options come back as the defaults
    options = houseOfEnlightenment.parse_command_line([])
    STATE.stations = stations.Stations()
    # could make a mock opc client too, but I think its slightly
    # better to just have a simple socket server setup
    opc = houseOfEnlightenment.create_opc_client('127.0.0.1:7890')
    try:
        osc = MockOscServer()
        mgr = af.AnimationFramework(osc, opc, None, [])
        try:
            thread = mgr.serve_in_background()
            count = 0
            while True:
                for scene in mgr.scenes:
                    print "====="
                    print 'Testing {}'.format(scene)
                    mgr.pick_scene(scene)
                    time.sleep(args.time_per_scene)
                    if mgr.is_running:
                        print '{} succesfully rendered'.format(scene)
                    else:
                        raise Exception('Failed to render {}'.format(scene))
                if args.loops and count >= args.loops:
                    break
        finally:
            mgr.shutdown()
            while mgr.is_running:
                time.sleep(.1)
    finally:
        opc.disconnect()


if __name__ == '__main__':
    sys.exit(main())
