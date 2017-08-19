"""Launch the framework and cycle through all the scenes"""
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
    options = houseOfEnlightenment.parse_command_line()
    STATE.stations = stations.Stations()
    # could make a mock opc client too, but I think its slightly
    # better to just have a simple socket server setup
    opc = houseOfEnlightenment.create_opc_client('127.0.0.1:7890')
    try:
        osc = MockOscServer()
        mgr = af.AnimationFramework(osc, opc, None, [])
        try:
            thread = mgr.serve_in_background()
            for scene in mgr.scenes:
                print "====="
                print 'Testing {}'.format(scene)
                mgr.pick_scene(scene)
                time.sleep(1)
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
