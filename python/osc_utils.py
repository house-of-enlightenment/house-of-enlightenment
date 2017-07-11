from OSC import ThreadingOSCServer
from OSC import OSCClient
from OSC import OSCMessage
from threading import Thread
import atexit



defaults = {}
defaults['address']='127.0.0.1'
defaults['port']=7000


def create_osc_server(host=defaults['address'], port=defaults['port']):
    server = ThreadingOSCServer((host, port))
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    # TODO: atexit.register(self.disconnect())
    return server

def get_osc_client(host=defaults['address'], port=defaults['port']):
    from OSC import OSCClient
    client = OSCClient()
    client.connect((host, port))
    return client

def send_simple_message(client, path, data="", timeout=None):
    msg = OSCMessage(path)
    msg.append(data)
    client.send(msg, timeout)


def keyboard_handler(path, tags, args, source):
    print "Got keyboard via osc", path, tags, args, source
    #TODO: null checks on args?
    text = args[0]
    if("quit"==text.lower()):
        #TODO: cleaner quit
        quit(0)
    pass