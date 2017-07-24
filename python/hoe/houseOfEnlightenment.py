#!/usr/bin/env python

from __future__ import division
import json
import optparse
import sys
from threading import Thread
from time import sleep

from hoe import opc
from hoe import osc_utils
from hoe import animation_framework as AF


# -------------------------------------------------------------------------------
# command line
def parse_command_line():
    parser = optparse.OptionParser()
    parser.add_option(
        '-l',
        '--layout',
        dest='raw_layout',
        default='../layout/hoeLayout.json',
        action='store',
        type='string',
        help='layout file')
    parser.add_option(
        '-s',
        '--server',
        dest='server',
        default='127.0.0.1:7890',
        action='store',
        type='string',
        help='ip and port of server')
    parser.add_option(
        '-f', '--fps', dest='fps', default=20, action='store', type='int', help='frames per second')

    options, args = parser.parse_args()

    if not options.raw_layout:
        parser.print_help()
        print
        print('ERROR: you must specify a layout file using '
              '--layout or use default (../layout/hoeLayout.json)')
        print
        sys.exit(1)

    options.layout = parse_layout(options.raw_layout)

    return options


# -------------------------------------------------------------------------------


# parse layout file.
# TODO: groups, strips, clients, channels
def parse_layout(layout):

    print
    print '    parsing layout file'
    print
    """
    Old:
    coordinates = []
    for item in json.load(open(layout)):
        if 'point' in item:
            coordinates.append(tuple(item['point']))

    return coordinates
    """

    # Just use a dictionary as loaded
    return json.load(open(layout))


# -------------------------------------------------------------------------------
# connect to OPC server


def start_opc(server):
    client = opc.Client(server)
    if client.can_connect():
        print '    connected to %s' % server
    else:
        # can't connect, but keep running in case the server appears later
        print '    WARNING: could not connect to %s' % server
    print
    return client


def init_animation_framework(osc_server, opc_client, config):
    # OSCServer, Client, dict -> SceneManager, Thread
    mgr = AF.AnimationFramework(osc_server, opc_client, config.layout, config.fps)
    init_osc_inputs(mgr)
    return mgr


def init_osc_inputs(mgr):
    # SceneManager -> None
    """
    DEVELOPERS - Add inputs you need for testing. They will be finalized later
    """

    # Add "stations"
    for s in range(6):
        for i in range(6):
            # TODO : Can we send to a single input each time with args data?
            mgr.add_button("s%s.b%s" % (s, i), "/input/station/%s/button/%s" % (s, i))
            mgr.add_fader("s%s.f%s" % (s, i), "/input/station/%s/fader/%s" % (s, i), 0)

    # ----------- Developers - add buttons/faders here for testing ------------

    # Good and easy faders for sharing across testing
    mgr.add_fader("r", default=50)
    mgr.add_fader("g", default=50)
    mgr.add_fader("b", default=255)

    # A fader for example_spatial_stripes.AdjustableFillFromBottom
    mgr.add_fader("bottom_fill", default=25)

    #A button for stop_the_light example
    mgr.add_button("b0")

    print 'Registered OSC Inputs\n'


def listen_for_keyboard(scene):
    # SceneManager -> None
    osc_client = osc_utils.get_osc_client()
    keep_running = True
    while keep_running:
        key = raw_input("Send a keyboard command: ")
        if not key:
            continue
        key_lower = key.lower()
        if ("quit" == key_lower):
            # TODO: We should really use atexit for all this. This is
            # a short-term fix to not take down the simulator with us
            print "Received shutdown command. Exiting now"
            scene.shutdown()
            keep_running = False
        elif key_lower.startswith("next "):
            # Increment one or more scenes
            args = key_lower.split(" ")
            if len(args)>1:
                osc_utils.send_simple_message(osc_client, "/scene/next", args[1])
            else:
                osc_utils.send_simple_message(osc_client, "/scene/next")
        elif key_lower.startswith("scene "):
            args = key_lower.split(" ", 1)
            osc_utils.send_simple_message(osc_client, "/scene/select", args[1])
        else:
            args = key.split(" ", 1)
            if (len(args) == 1):
                osc_utils.send_simple_message(osc_client, args[0])
            elif (len(args) == 2):
                osc_utils.send_simple_message(osc_client, args[0], args[1])

        sleep(.1)


def launch():
    config = parse_command_line()
    osc_server = osc_utils.create_osc_server()

    opc = start_opc(config.server)
    framework = init_animation_framework(osc_server, opc, config)

    osc_server.addMsgHandler("/scene/next", framework.next_scene_handler)
    osc_server.addMsgHandler("/scene/select", framework.select_scene_handler)

    keyboard_thread = Thread(
        target=listen_for_keyboard, args=(framework, ), name="KeyboardListeningThread")
    keyboard_thread.setDaemon(True)
    keyboard_thread.start()

    framework.serve_forever()

    # TODO: This was deadlocking
    # osc_server.shutdown()

    opc.disconnect()


if __name__ == '__main__':
    launch()
