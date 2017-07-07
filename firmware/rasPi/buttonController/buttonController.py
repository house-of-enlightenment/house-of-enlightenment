#!/usr/bin/env python2.7  
# script by Alex Eames http://RasPi.tv  
# http://RasPi.tv/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3  
import RPi.GPIO as GPIO  
import time
from time import gmtime, strftime
from OSC import *
GPIO.setmode(GPIO.BCM)  

# wait for lights to start
time.sleep(5)
  
# GPIO 23 & 17 set up as inputs, pulled up to avoid false detection.  
# Both ports are wired to connect to GND on button press.  
# So we'll be setting up falling edge detection for both  

inputButtons = [(22, 1, 1), 
                (23, 1, 2),
                ( 4, 1, 3),
                (14, 1, 4),
                (15, 2, 1 ),
                (18, 2, 2),
                (17, 2, 3),
                (27, 2, 4)]


for b in inputButtons:
    #print "input is" , b[0]
    GPIO.setup(b[0], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
   
globalParams = {}  

c = OSCClient()
c.connect( ("localhost", 7000) )

def sendButton(channel):  
    print "received button press on channel ", channel , " at ", strftime("%Y-%m-%d %H:%M:%S", gmtime())
    

    for b in inputButtons:
        if b[0] == channel:
            m = OSCMessage("/button" +  "/" + str(b[1]) + "/" + str(b[2]))
            m.append(1.0)
            c.send(m)
            # m.append(b[1])
            # m.append("/")
            # m.append(b[2])
            
         

 
# when a falling edge is detected on port 23, regardless of whatever   
# else is happening in the program, the function my_callback2 will be run  
# 'bouncetime=300' includes the bounce control written into interrupts2a.py

for b in inputButtons:
    GPIO.add_event_detect(b[0], GPIO.FALLING, callback=sendButton, bouncetime=500)  
  

try:
    while True:
        time.sleep(0.05)

except KeyboardInterrupt:  
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
GPIO.cleanup()           # clean up GPIO on normal exit  
