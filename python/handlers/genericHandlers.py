
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
