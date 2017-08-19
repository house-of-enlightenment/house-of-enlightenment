import OSC
import time

count = 0


def handler(addr, tags, data, client_address):
    txt = "OSCMessage '%s' from %s: " % (addr, client_address)
    txt += str(data)
    print(txt)


def countHandler(addr, tags, data, client_address):
    global count
    count += int(data[0])
    print count


def default_handler(path, tags, args, source):
    print "Path is: ", path, " Tags is: ", tags, " Args are: ", args, " Source is: ", source


s = OSC.OSCServer(('0.0.0.0', 7000))  # listen on localhost, port 57120
s.addMsgHandler('/startup',
                handler)  # call handler() for OSC messages received with the /startup address
s.addMsgHandler('/count', countHandler)
s.addMsgHandler("default", default_handler)
s.serve_forever()

while True:
    time.sleep(1)
