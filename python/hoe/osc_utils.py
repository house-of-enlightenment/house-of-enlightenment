from OSC import ThreadingOSCServer
from OSC import OSCClient
from OSC import OSCMessage
from threading import Thread
import atexit

defaults = {}
defaults['address'] = '127.0.0.1'
defaults['port'] = 7000


def create_osc_server(host=defaults['address'], port=defaults['port']):
    # String, int -> OSCServer

    server = ThreadingOSCServer((host, port))
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()
    # TODO: atexit.register(self.disconnect())
    return server


def get_osc_client(host=defaults['address'], port=defaults['port']):
    # String, int -> OSCClient

    client = OSCClient()
    client.connect((host, port))
    return client


def send_simple_message(client, path, data="", timeout=None):
    # OSCClient, String, String, int -> None
    msg = OSCMessage(path)
    msg.append(data)
    client.send(msg, timeout)
