#!/usr/bin/env python

"""A demo client for Open Pixel Control
http://github.com/zestyping/openpixelcontrol

Sends all pixels as red to the address

"""

import time
import random
import opc

ADDRESS = '127.0.0.1:7890'
num_strips=66
pixels_per_strip=216


numPixels = num_strips*pixels_per_strip

# Create a client object
client = opc.Client(ADDRESS)

# Test if it can connect
if client.can_connect():
    print 'connected to %s' % ADDRESS
else:
    # We could exit here, but instead let's just print a warning
    # and then keep trying to send pixels in case the server
    # appears later
    print 'WARNING: could not connect to %s' % ADDRESS

#my_pixels = [(255,0,0)] +([(0,0,0)] * 113)


my_pixels = [(255,0,0)] * numPixels

# Send pixels forever
while True:
    if client.put_pixels(my_pixels, channel=0):
        print 'sent'
    else:
        print 'not connected'
    time.sleep(1)



    # for a in range(0,numPixels):
    #     #my_pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255)] + ( a * bufferPixels)
    #     my_pixels =  [(255,0,0)] * a
    #  #   random.shuffle(bufferPixels)
    #     if client.put_pixels(my_pixels, channel=0):
    #         print 'sent', a
    #     else:
    #         print 'not connected'
    #     time.sleep(0.01)

