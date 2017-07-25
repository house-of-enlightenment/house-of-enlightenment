from OSC import ThreadingOSCServer
from OSC import OSCClient
from OSC import OSCMessage
from threading import Thread
import atexit

defaults = {'address': '0.0.0.0', 'port': 7000}


def create_osc_server(host=defaults['address'], port=defaults['port']):
    # String, int -> OSCServer

    server = ThreadingOSCServer((host, port))
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()

    # TODO: atexit.register(self.disconnect())
    return server


def get_osc_client(host='localhost', port=defaults['port']):
    # String, int -> OSCClient

    client = OSCClient()
    client.connect((host, port))
    return client


def send_simple_message(client, path, data=[], timeout=None):
    # OSCClient, String, String, int -> None
    msg = OSCMessage(path)
    for d in data:
        msg.append(d)
    client.send(msg, timeout)
