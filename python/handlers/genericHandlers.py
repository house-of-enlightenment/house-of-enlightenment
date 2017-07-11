
class FaderHandler(object):
    def __init__(self, type, args):
        self.type=type
        if type[0] == "xy":
            self.xPos = args[0] * 30
            self.yPos = args[1] * 16
        if type[0] == "fader1":
            self.colorR = args[0]
        if type[0] == "fader2":
            self.colorG = args[0]
        if type[0] == "fader3":
            self.colorB = args[0]

        print "fader", type, args

def toggleHandler(args):
    print "toggle " + args

def buttonHandler(addr, args):
	print "Button pressed", addr


def user_callback(path, tags, args, source):
    # which user will be determined by path:e
    # we just throw away all slashes and join together what's left
    user = ''.join(path.split("/"))
    # tags will contain 'fff'
    # args is a OSCMessage with data
    # source is where the message came from (in case you need to reply)
    print ("Now do something with", user, args[2], args[0], 1 - args[1])

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
        FaderHandler(addr2, args)

    #print "address is ", addr
    print path, tags, args, source

