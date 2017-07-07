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

    python_clients/spatial_stripes_new.py --layout layouts/wall.json

"""

from __future__ import division
import time
import sys
import optparse
try:
    import json
except ImportError:
    import simplejson as json

import opc
import osc
import sceneManager
import color_utils

#TODO: remove these
globalParams = {}
globalParams["effectCount"] = 5
globalParams["effectIndex"] = 0
globalParams["xPos"] = 0
globalParams["yPos"] = 0
globalParams["colorR"] = 0
globalParams["colorG"] = 0
globalParams["colorB"] = 0

#-------------------------------------------------------------------------------
# command line
def parseCommandLine():
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

    options.layout = parseLayout(options.raw_layout)

    return options

#-------------------------------------------------------------------------------
# parse layout file.
# TODO: groups, strips, clients, channels
def parseLayout(layout):
    print
    print '    parsing layout file'
    print

    coordinates = []
    for item in json.load(open(layout)):
        if 'point' in item:
            coordinates.append(tuple(item['point']))

    return coordinates

#-------------------------------------------------------------------------------
def initOSC(server):
    controller = osc.Controller()
    controller.connect()
    #TODO: registration
    return controller


#-------------------------------------------------------------------------------
# connect to OPC server
def initOPC(server):
    client = opc.Client(server)
    if client.can_connect():
        print '    connected to %s' % server
    else:
        # can't connect, but keep running in case the server appears later
        print '    WARNING: could not connect to %s' % server
    print
    return client

def initSceneManager(osc, opc, config):
    return sceneManager.SceneManager(osc, opc, config.layout, config.fps)


#-------------------------------------------------------------------------------
def launch():
    config = parseCommandLine()
    osc = initOSC
    opc = initOPC(config.server)
    scene = initSceneManager(osc, opc, config)
    scene.start() #run forever

if __name__=='__main__':
    launch();

#-------------------------------------------------------------------------------
# handlers for OSC

#TODO: marked for removal
def nextEffect(args):
    print "next effect message received"
    if globalParams["effectIndex"] >= globalParams["effectCount"]:
        globalParams["effectIndex"] = 0
    else:
        globalParams["effectIndex"] += 1
    print "effect index is ", globalParams["effectIndex"]

def toggleHandler(args):
    print "toggle " + args

def buttonHandler(addr, args):
	print "Button pressed", addr

def faderHandler(addr, args):
    if addr[0] == "xy":
        globalParams["xPos"] = args[0] * 30
        globalParams["yPos"] = args[1] * 16
    if addr[0] == "fader1":
        globalParams["colorR"] = args[0]
    if addr[0] == "fader2":
        globalParams["colorG"] = args[0]
    if addr[0] == "fader3":
        globalParams["colorB"] = args[0]

    print "fader", addr, args

# globalParams["xPos"]
# globalParams["xPos"]
# globalParams["color"]


def user_callback(path, tags, args, source):
    # which user will be determined by path:e
    # we just throw away all slashes and join together what's left
    user = ''.join(path.split("/"))
    # tags will contain 'fff'
    # args is a OSCMessage with data
    # source is where the message came from (in case you need to reply)
    print ("Now do something with", user,args[2],args[0],1-args[1])

"""
#-------------------------------------------------------------------------------
# Create OSC listener for timeline/effects control
if osc_support:

    def default_handler(path, tags, args, source):
        #print path, tags, args, source
        addr = path.split("/")
        #print "address 1 is" , addr[1]
        if addr[1] == "button":
            addr2 = addr[2:]
            buttonHandler(addr2, args)
            return
        if addr[1] =="fader":
            addr2 = addr[2:]
            faderHandler(addr2, args)

        #print "address is ", addr
        print path, tags, args, source


    def next_effect_handler(path, tags, args, source):
    	if args[0] > 0:
    		nextEffect(args)

    def toggle_handler(path, tags, args, source):
        toggleHandler(args)

    def button_handler(path, tags, args, source):
    	if args[0] > 0:
    		print "This is the button handler"
        print path, tags, args, source
        return

    server = ThreadingOSCServer( ("0.0.0.0", 7000) )

    server.addMsgHandler("/nextEffect", next_effect_handler)
    #server.addMsgHandler("/toggle", toggle_handler)
    #server.addMsgHandler("/button", button_handler)
    server.addMsgHandler("default", default_handler)




    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    print "Listening for OSC messages on port 7000"
"""