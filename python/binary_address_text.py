#!/usr/bin/env python

# Show the strip indexes on all outputs by lighting the first six pixels in binary

import time
import random
import opc
import optparse

parser = optparse.OptionParser()
parser.add_option('-s', '--server', dest='server', default='127.0.0.1:7890',
                    action='store', type='string',
                    help='ip and port of server')
parser.add_option('-n', '--num', dest='num_strips', default='66',
                    action='store', type='int',
                    help='length of each strip (single strip length supported right now')
parser.add_option('-l', '--length', dest='strip_length', default='216',
                    action='store', type='int',
                    help='length of each strip (single strip length supported right now')
options, args = parser.parse_args()

# Create a client object
client = opc.Client(options.server)

# Test if it can connect
if client.can_connect():
    print 'connected to %s' % options.server
else:
    # We could exit here, but instead let's just print a warning
    # and then keep trying to send pixels in case the server
    # appears later
    print 'WARNING: could not connect to %s' % options.server

# Send pixels forever
while True:
    pixels = []
    for strip in range(options.num_strips):
        #pixels = pixels + [(0, 0, 0)] * channel 
	#pixels.append((255, 0, 0))
        #pixels = pixels + [(0, 0, 0)] * (46 - channel)
        for bit in range(6):
            pixels.append((255, 0, 0) if strip & 1<<bit else (0, 0, 60))
        pixels = pixels + [(0, 0, 0)] * (options.strip_length- 6)
    client.put_pixels(pixels, channel=0)
    time.sleep(0.2)

