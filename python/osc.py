from threading import Thread

host_address="0.0.0.0"
host_port=7000
class Controller(object):

    def __init__(self, verbose=False):
        self.verbose = verbose

        try:
            from OSC import ThreadingOSCServer
        except ImportError:
            print "WARNING: pyOSC not found, remote OSC control will not be available."
            osc_support = False

        self.connected=False
        self.server = ThreadingOSCServer (host_address, host_port)

    def connect(self):
        if self.connected:
            print "Already connected"
            return
        thread = Thread(target=self.server.serve_forever)
        thread.setDaemon(True)
        thread.start()
        self.connected=True
        print "Listening for OSC messages on port 7000"

    def disconnect(self):
        self.server.shutdown()
        print "Disconnected from OSC messages"

    def registerHandler(self, handler, path):
        self.server.addMsgHandler(path, handler)
        #TODO: debug statement

    def unregisterHandler(self, path):
        self.server.delMsgHandler(path)
        #TODO: debug statement, is this correct?