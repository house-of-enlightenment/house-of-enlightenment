#!/usr/bin/env python

"""A demo client for Open Pixel Control
http://github.com/zestyping/openpixelcontrol

Creates moving stripes visualizing the x, y, and z coordinates
mapped to r, g, and b, respectively.  Also draws a moving white
spot which shows the order of the pixels in the layout file.

To run:
First start the gl simulator using, for example, the included "wall" layout

    make
    bin/gl_server layouts/wall.json

Then run this script in another shell to send colors to the simulator

    python_clients/example_spatial_stripes.py --layout layouts/wall.json

"""

from __future__ import division
import sys
import optparse
from time import sleep

try:
    import json
except ImportError:
    import simplejson as json

import opc
import osc_utils
import scene_manager
from threading import Thread

#TODO: remove these
#globalParams = {}
#globalParams["effectCount"] = 5
#globalParams["effectIndex"] = 0

#-------------------------------------------------------------------------------
# command line
def parse_command_line():
    parser = optparse.OptionParser()
    parser.add_option('-l', '--layout', dest='raw_layout',
                        action='store', type='string',
                        help='layout file')
    parser.add_option('-s', '--server', dest='server', default='127.0.0.1:7890',
                        action='store', type='string',
                        help='ip and port of server')
    parser.add_option('-f', '--fps', dest='fps', default=20,
                        action='store', type='int',
                        help='frames per second')

    options, args = parser.parse_args()

    if not options.raw_layout:
        parser.print_help()
        print
        print 'ERROR: you must specify a layout file using --layout'
        print
        sys.exit(1)

    options.layout = parse_layout(options.raw_layout)

    return options

#-------------------------------------------------------------------------------
groups = {}
group_strips = {}
clients = {}


# parse layout file.
# TODO: groups, strips, clients, channels
def parse_layout(layout):
    print
    print '    parsing layout file'
    print

    coordinates = []
    for item in json.load(open(layout)):
        if 'point' in item:
            coordinates.append(tuple(item['point']))
        
        #if 'angle' in item:
        #	coordinates.append()


    return coordinates


#-------------------------------------------------------------------------------
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


def start_scene_manager(osc, opc, config):
    mgr = scene_manager.SceneManager(osc, opc, config.layout, config.fps)
    #Run scene manager in the background
    thread = Thread(target=mgr.serve_forever)
    thread.setName("SceneManager")
    thread.setDaemon(True)
    thread.start()
    print "Started scene manager"
    return mgr, thread


#-------------------------------------------------------------------------------
def launch():
    config = parse_command_line()
    osc_server = osc_utils.create_osc_server()

    opc = start_opc(config.server)
    scene, scene_thread = start_scene_manager(osc_utils, opc, config)
   # scene.start() #run forever

    #TODO: Not ready osc_server.addMsgHandler("/handleKeyboard", osc_utils.keyboard_handler)
    osc_server.addMsgHandler("/nextScene", scene.next_scene_handler)

    from OSC import OSCMessage
    osc_client = osc_utils.get_osc_client()
    keep_running=True
    while keep_running:
        key = raw_input("Send a keyboard command: ")
        key_lower=key.lower()
        if ("quit" == key_lower):
            #TODO: We should really use atexit for all this. This is a short-term fix to not take down the simulator with us
            print "Received shutdown command. Exiting now"
            scene.shutdown()
            print "Waiting up to 10s for scene thread to shutdown"
            scene_thread.join(10000)
            #osc_server.shutdown()
            #TODO: This was deadlocking!
            print "Skipped OSC Server Shutdown"
            opc.disconnect()
            print "OPC Connector Terminated"
            keep_running=False
        if (key_lower in ["next"]):
            osc_utils.send_simple_message(osc_client, "/nextScene")
        else:
            args=key.split(" ",1)
            if(len(args)==1):
                osc_utils.send_simple_message(osc_client, args[0])
            elif(len(args)==2):
                osc_utils.send_simple_message(osc_client, args[0], args[1])

        sleep(.1)

if __name__=='__main__':
    launch();
