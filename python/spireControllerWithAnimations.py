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

    python_clients/spatial_stripes.py --layout layouts/wall.json

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
import color_utils

osc_support = True
try:
    from OSC import ThreadingOSCServer
    from threading import Thread
except ImportError:
    print "WARNING: pyOSC not found, remote OSC control will not be available."
    osc_support = False



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

parser = optparse.OptionParser()
parser.add_option('-l', '--layout', dest='layout',
                    action='store', type='string',
                    help='layout file')
parser.add_option('-s', '--server', dest='server', default='127.0.0.1:7890',
                    action='store', type='string',
                    help='ip and port of server')
parser.add_option('-f', '--fps', dest='fps', default=20,
                    action='store', type='int',
                    help='frames per second')

options, args = parser.parse_args()

if not options.layout:
    parser.print_help()
    print
    print 'ERROR: you must specify a layout file using --layout'
    print
    sys.exit(1)


#-------------------------------------------------------------------------------
# parse layout file

print
print '    parsing layout file'
print

coordinates = []
for item in json.load(open(options.layout)):
    if 'point' in item:
        coordinates.append(tuple(item['point']))



#-------------------------------------------------------------------------------
# handlers for OSC


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





#-------------------------------------------------------------------------------
# connect to server

client = opc.Client(options.server)
if client.can_connect():
    print '    connected to %s' % options.server
else:
    # can't connect, but keep running in case the server appears later
    print '    WARNING: could not connect to %s' % options.server
print


#-------------------------------------------------------------------------------
# color function

def spatial_stripes(t, coord, ii, n_pixels):
    """Compute the color of a given pixel.

    t: time in seconds since the program started.
    ii: which pixel this is, starting at 0
    coord: the (x, y, z) position of the pixel as a tuple
    n_pixels: the total number of pixels

    Returns an (r, g, b) tuple in the range 0-255

    """
    # make moving stripes for x, y, and z
    x, y, z = coord
    r = color_utils.scaled_cos(x, offset=t / 4, period=1, minn=0, maxx=0.7)
    g = color_utils.scaled_cos(y, offset=t / 4, period=1, minn=0, maxx=0.7)
    b = color_utils.scaled_cos(z, offset=t / 4, period=1, minn=0, maxx=0.7)
    r, g, b = color_utils.contrast((r, g, b), 0.5, 2)

    # make a moving white dot showing the order of the pixels in the layout file
    spark_ii = (t*80) % n_pixels
    spark_rad = 8
    spark_val = max(0, (spark_rad - color_utils.mod_dist(ii, spark_ii, n_pixels)) / spark_rad)
    spark_val = min(1, spark_val*2)
    r += spark_val
    g += spark_val
    b += spark_val

    # apply gamma curve
    # only do this on live leds, not in the simulator
    #r, g, b = color_utils.gamma((r, g, b), 2.2)

    return (r*256, g*256, b*256)

def clearPixels(pixels):
    pixels=[(0,0,0)] * n_pixels
    return pixels

def gentle_glow(t, coord, ii, n_pixels):
    x, y, z = coord
    g = 0
    b = 0
    r = min(1, (1 - z) + color_utils.cos(x, offset=t / 5, period=2, minn=0, maxx=0.3))

    return (r*256, g*256, b*256)


def colorFader(pixels):
    pixels=[(globalParams["colorR"] * 256, globalParams["colorG"] * 256, globalParams["colorB"] * 256)] * n_pixels

    return pixels



#def pixel_color(t, coord, ii, n_pixels):


# def singlePixelSelector(xPos, yPos, color):
#     pixels=[(0,0,0,)] * n_pixels
#     pixels[(yPos * 30) + xPos] = color



#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print


n_pixels = len(coordinates)
pixels=[(0,0,0,)] * n_pixels
start_time = time.time()

while True:
    t = time.time() - start_time
    if globalParams["effectIndex"] == 0:
        pixels = [spatial_stripes(t, coord, ii, n_pixels) for ii, coord in enumerate(coordinates)]
    if globalParams["effectIndex"] == 1:
        pixels = clearPixels(pixels)
    if globalParams["effectIndex"] == 2:
        pixels = [gentle_glow(t, coord, ii, n_pixels) for ii, coord in enumerate(coordinates)]
    if globalParams["effectIndex"] == 3:
        pixels = colorFader(pixels)
    if globalParams["effectIndex"] == 4:
        pixels = clearPixels(pixels)
    if globalParams["effectIndex"] == 5:
        pixels = clearPixels(pixels)
    client.put_pixels(pixels, channel=0)
    time.sleep(1 / options.fps)

# Orignal animation main loop
# while True:
#     #t = time.time() - start_time
#     #pixels = [pixel_color(t, coord, ii, n_pixels) for ii, coord in enumerate(coordinates)]
#     singlePixelSelector(globalParams["xPos"], globalParams["yPos"], globalParams["color"])
#     client.put_pixels(pixels, channel=0)
#     time.sleep(1 / options.fps)
