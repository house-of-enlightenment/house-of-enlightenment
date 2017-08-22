#!/usr/bin/env python

from __future__ import division
import argparse
import json
import logging
from multiprocessing import Process
import os
import traceback
import sys
from threading import Thread
from time import sleep

from hoe import animation_framework as AF
from hoe.layout import Layout
from hoe import opc
from hoe import osc_utils
from hoe.play_lidar import play_lidar
from hoe.state import STATE
from hoe.stations import Stations, Codes
from hoe import utils

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# command line
def parse_command_line():
    root_dir = find_root()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-l',
        '--layout',
        dest='layout_file',
        default=os.path.join(root_dir, 'layout', 'hoeLayout.json'),
        action='store',
        type=str,
        help='layout file')
    parser.add_argument(
        '-s',
        '--servers',
        dest='servers',
        default=os.path.join(root_dir, 'layout', 'servers_local.json'),
        action='store',
        type=str,
        help='json file for server addresses')
    parser.add_argument(
        '-f', '--fps', dest='fps', default=30, action='store', type=int, help='frames per second')
    parser.add_argument(
        '-n',
        '--scene',
        dest='scene',
        default=None,
        action='store',
        type=str,
        help='First scene to display')
    parser.add_argument('-t', '--tags', dest='tags', action='append')
    parser.add_argument('-v', '--verbose', dest='verbose', default=False, action='store_true')

    options = parser.parse_args()

    log_level = 'DEBUG' if options.verbose else 'INFO'
    utils.configure_logging(level=log_level)

    if not options.layout_file:
        parser.print_help()
        print
        print('ERROR: you must specify a layout file using '
              '--layout or use default (../layout/hoeLayout.json)')
        print
        sys.exit(1)

    STATE.layout = Layout(parse_json_file(options.layout_file))
    STATE.servers = parse_json_file(options.servers)
    STATE.fps = options.fps
    STATE.verbose = options.verbose
    STATE.codes = Codes(parse_json_file(os.path.join(root_dir, "layout", "codes.json")))
    return options


def find_root(start_dirs=[], look_for=set(["layout", "python"])):
    # type: ([str], set([str])) -> str
    """
    Find the root directory of the project by looking for some common directories
    :return: the root directory
    """
    # Handle symlinks
    start_dirs = [] + [
        os.path.dirname(os.path.abspath(__file__)),
        os.path.dirname(os.path.realpath(__file__))
    ]
    for curr_dir in start_dirs:
        while curr_dir != os.path.dirname(curr_dir):
            curr_dir = os.path.dirname(curr_dir)
            if look_for.issubset(os.listdir(curr_dir)):
                print "    Found root directory of", curr_dir
                return curr_dir
    print "Could not find %s in parent dirs of %s. Root will be none" % (look_for, start_dirs)


def parse_json_file(filename):
    with open(filename) as f:
        return json.load(f)


def create_opc_client(server, verbose=False):
    client = opc.Client(server_ip_port=server, verbose=False)
    if client.can_connect():
        print '    connected to %s' % server
    else:
        # can't connect, but keep running in case the server appears later
        print '    WARNING: could not connect to %s' % server
    print
    return client


def init_animation_framework(osc_server, opc_client, first_scene=None, tags=[]):
    # type: (OSCServer, Client, [OSCClient], str) -> AnimationFramework
    mgr = AF.AnimationFramework(
        osc_server=osc_server, opc_client=opc_client, first_scene=first_scene, tags=tags)
    return mgr


def listen_for_keyboard(scene):
    # SceneManager -> None
    osc_client = osc_utils.get_osc_client()
    keep_running = True
    while keep_running:
        try:
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
            elif key_lower.startswith("lidar "):
                args = key_lower.split(" ", 1)
                filename = args[1]
                thread = Process(target=play_lidar, args=(filename, ))
                thread.daemon = True
                print "Running lidar thread"
                thread.start()
                print "Started lidar thread"
            elif key_lower.startswith("disable ") or key.startswith("enable "):
                # Accepts disable (simulator|arduino|*) [b_id]
                args = key_lower.split(" ", 2)
                enabled = args[0] == "enable"
                if len(args) == 3:
                    STATE.stations.change_client_status(
                        enabled=enabled, client_type=args[1], station_id=int(args[2]))
                elif len(args) == 2:
                    STATE.stations.change_client_status(enabled=enabled, client_type=args[1])
            else:
                args = key.split(" ")
                if len(args) == 1:
                    osc_utils.send_simple_message(osc_client, args[0])
                elif len(args) >= 2:
                    osc_utils.send_simple_message(osc_client, args[0], args[1:])
        except:
            traceback.print_exc()

        sleep(.1)


def build_opc_client(verbose):
    if 'opc_server' in STATE.servers['remote']:
        return create_opc_client(server=STATE.servers["remote"]["opc_server"], verbose=verbose)
    else:
        clients = {}
        opc_servers = STATE.servers['remote']['opc_servers']
        if 'layout' in opc_servers:
            for server_ip_port in opc_servers['layout']:
                cl = create_opc_client(server_ip_port, verbose=verbose)
                clients[cl] = STATE.layout.address[cl.ip]  # pylint: disable=no-member
        if 'all' in opc_servers:
            client = create_opc_client(opc_servers['all'][0], verbose)
            clients[client] = range(STATE.layout.n_pixels)
        return opc.MultiClient(clients)


def launch():
    config = parse_command_line()
    osc_server = osc_utils.create_osc_server(
        host=STATE.servers["hosting"]["osc_server"]["host"],
        port=int(STATE.servers["hosting"]["osc_server"]["port"]))
    opc_client = build_opc_client(config.verbose)
    # stations = create_osc_station_clients(servers=STATE.servers["remote"]["osc_controls"])
    # STATE.station_osc_clients = stations
    # STATE.buttons = [StationButtons(client=client) for s_id, client in enumerate(stations)]
    STATE.stations = Stations()
    framework = init_animation_framework(osc_server, opc_client, config.scene, config.tags)

    keyboard_thread = Thread(
        target=listen_for_keyboard, args=(framework, ), name="KeyboardListeningThread")
    keyboard_thread.setDaemon(True)
    keyboard_thread.start()

    try:
        framework.serve_forever()
    except KeyboardInterrupt:
        print "Received interrupt. Stopping..."
    finally:
        framework.shutdown()
        opc_client.disconnect()
        STATE.stations.shutdown()
    # TODO: This was deadlocking
    # osc_server.shutdown()


if __name__ == '__main__':
    launch()
