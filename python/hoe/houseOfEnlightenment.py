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
from hoe.layout import Layout
from hoe.layout import init_layout


# -------------------------------------------------------------------------------
# command line
def parse_command_line():
    parser = optparse.OptionParser()
    parser.add_option(
        '-l',
        '--layout',
        dest='layout_file',
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
        help='ip and port of target opc server')
    parser.add_option(
        '-b',
        '--feedback_servers',
        dest='feedback_servers',
        default=[],
        action='append',
        nargs=2,
        type='string',
        help='osc feedback server for buttons. Can be specified more than once')

    parser.add_option(
        '-f', '--fps', dest='fps', default=30, action='store', type='int', help='frames per second')
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true')

    options, args = parser.parse_args()

    if not options.layout_file:
        parser.print_help()
        print
        print('ERROR: you must specify a layout file using '
              '--layout or use default (../layout/hoeLayout.json)')
        print
        sys.exit(1)

    init_layout(Layout(parse_layout(options.layout_file)))

    return options


# -------------------------------------------------------------------------------


# parse layout file.
# TODO: groups, strips, clients, channels
def parse_layout(layout_file):

    print
    print '    parsing layout file'
    print

    # Just use a dictionary as loaded
    return json.load(open(layout_file))


# -------------------------------------------------------------------------------
# connect to OPC server


def create_opc_client(server, verbose=False):
    client = opc.Client(server_ip_port=server, verbose=verbose)
    if client.can_connect():
        print '    connected to %s' % server
    else:
        # can't connect, but keep running in case the server appears later
        print '    WARNING: could not connect to %s' % server
    print
    return client


def init_animation_framework(osc_server, opc_client, config, osc_stations):
    # OSCServer, Client, dict -> SceneManager, Thread
    mgr = AF.AnimationFramework(osc_server=osc_server, opc_client=opc_client, osc_station_clients=osc_stations, fps=config.fps)
    return mgr


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
        elif key_lower.startswith("next"):
            # Increment one or more scenes
            args = key_lower.split(" ")
            if len(args) > 1:
                osc_utils.send_simple_message(osc_client, "/scene/next", [args[1]])
            else:
                osc_utils.send_simple_message(osc_client, "/scene/next")
        elif key_lower.startswith("scene "):
            args = key_lower.split(" ", 1)
            osc_utils.send_simple_message(osc_client, "/scene/select", [args[1]])
        else:
            args = key.split(" ")
            if (len(args) == 1):
                osc_utils.send_simple_message(osc_client, args[0])
            elif (len(args) >= 2):
                osc_utils.send_simple_message(osc_client, args[0], args[1:])

        sleep(.1)


def create_osc_stations(servers):
    if servers:
        print "Creating OSC clients to", servers

    return [osc_utils.get_osc_client(host=s, port=int(p), say_hello=True) for s, p in servers]


def launch():
    config = parse_command_line()
    osc_server = osc_utils.create_osc_server()
    opc_client = create_opc_client(config.server, config.verbose)
    stations = create_osc_stations(config.feedback_servers)

    framework = init_animation_framework(osc_server, opc_client, config, stations)

    keyboard_thread = Thread(
        target=listen_for_keyboard, args=(framework, ), name="KeyboardListeningThread")
    keyboard_thread.setDaemon(True)
    keyboard_thread.start()

    framework.serve_forever()

    # TODO: This was deadlocking
    # osc_server.shutdown()

    opc_client.disconnect()


if __name__ == '__main__':
    launch()
