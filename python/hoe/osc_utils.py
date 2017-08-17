from OSC import ThreadingOSCServer
from OSC import OSCClient
from OSC import OSCMessage
from OSC import OSCBundle
from threading import Thread
import atexit

defaults = {'address': '0.0.0.0', 'port': 7000}
button_path = "/button"
BUTTON_OFF = 0
BUTTON_ON = 1
BUTTON_TOGGLE = 2


def create_osc_server(host=defaults['address'], port=defaults['port']):
    # String, int -> OSCServer

    server = ThreadingOSCServer((host, port))
    thread = Thread(target=server.serve_forever)
    thread.setDaemon(True)
    thread.start()

    # TODO: atexit.register(self.disconnect())
    return server


def get_osc_client(host='localhost', port=defaults['port'], say_hello=False):
    # String, int -> OSCClient

    client = OSCClient()
    client.connect((host, port))

    # TODO Make this work
    if say_hello:
        send_simple_message(client, "/hello", timeout=None)

    return client


def send_simple_message(client, path, data=[], timeout=None):
    # OSCClient, String, String, int -> None
    msg = OSCMessage(path)
    for d in data:
        msg.append(d)
    client.send(msg, timeout)


def update_buttons(client, station_id, updates, timeout=None):
    """Given a feedback client, update buttons.

    Update should be a button id mapped to one of [0,1,2] where:

    0: Turn off
    1: Turn on
    2: Toggle

    However, it is recommended you use BUTTON_ON, BUTTON_OFF, BUTTON_TOGGLE
    """
    if not updates:
        return

    if isinstance(updates, type([])):
        updates = {idx: updates[idx] for idx in range(len(updates))}

    if len(updates) == 1:
        client.send(
            create_button_update_msg(
                station=station_id, id=updates.items()[0][0], update=updates.items()[0][1]))
    else:
        bundle = OSCBundle()
        for id, up in updates.items():
            bundle.append(create_button_update_msg(station=station_id, id=id, update=up))
        client.send(msg=bundle, timeout=timeout)


def create_button_update_msg(station, id, update):
    msg = OSCMessage(button_path)
    msg.append(station)
    msg.append(id)
    msg.append(update)
    return msg
