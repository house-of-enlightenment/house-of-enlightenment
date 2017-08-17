import time
import socket

from hoe.osc_utils import update_buttons
import osc_utils
from hoe.state import STATE


class Stations(object):
    def __init__(self):
        self._clients = _init_station_clients()
        self._stations = [Station(client=client) for client in self._clients]

    def __getitem__(self, key):
        """Easy get access. Note that set is not specified - stations should not be re-set"""
        return self._stations[key]

    def send_button_updates(self, force=False):
        for station in self._stations:
            station.buttons.send_button_light_update(station.client, force)


class Station(object):
    def __init__(self, client, buttons=None):
        self.client = client
        self.buttons = buttons if buttons else StationButtons()
        # TODO fader


class StationButtons(object):
    BUTTON_OFF = 0
    BUTTON_ON = 1
    BUTTON_TOGGLE = 'toggle'

    def __init__(self, initial_state=BUTTON_ON):
        self._buttons = [initial_state]*5
        self._last_change_timestamp = time.time()
        self._last_update_timestamp = 0

    def __getitem__(self, key):
        return self._buttons[key]

    def __setitem__(self, key, value):
        if value == StationButtons.BUTTON_TOGGLE:
            self._buttons[key] = (self._buttons[key] + 1) % 2
        else:
            self._buttons[key] = value
        self._last_change_timestamp = time.time()

    def __len__(self):
        return len(self._buttons)

    def send_button_light_update(self, remote_client, force=False):
        if force or self._last_change_timestamp > self._last_update_timestamp:
            self._last_update_timestamp = time.time()
            remote_client.send(self._buttons)
            # update_buttons(self._remote_client, self.station_id, self._buttons)
            # TODO: MAJOR - Send buttons to arduino controllers

    def set_all(self, on=True):
        self._buttons = [1 if on else 0] * 5
        self._last_change_timestamp = time.time()

class StationClient(object):
    def __init__(self, s_id, host, port, timeout=0.5):
        self.s_id = s_id  # Not currently in use but could be useful in the future
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = None

    def _ensure_connected(self):
        """Set up a connection if one doesn't already exist.

        Return True on success or False on failure.

        """
        if self._socket:
            self._debug('_ensure_connected: already connected, doing nothing')
            return True

        try:
            self._debug('_ensure_connected: trying to connect to {}:{}', self.host, self.port)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
            self._debug('_ensure_connected:    ...success')
            return True
        except socket.error:
            self._debug('_ensure_connected:    ...failure')
            self._socket = None
            return False

    def disconnect(self):
        """Drop the connection to the server, if there is one."""
        self._debug('disconnecting')
        if self._socket:
            self._socket.close()
        self._socket = None

    def _debug(self, msg, *args):
        # TODO  Move verbose to state and IF on that, or something similar
        if STATE.verbose:
            print msg.format(*args)

    def send(self, buttons):
        is_connected = self._ensure_connected()
        if not is_connected:
            self._debug('send: not connected.  ignoring these pixels.')
            return False

        data = reduce(lambda x, y: str(x) + str(y), buttons)
        self._debug("Sending data %s to %s" % (data, self._socket))
        try:
            self._socket.send(data)
        except socket.error:
            self._debug('send: connection lost.  could not send button data.')
            self._socket = None
            return False

        return True


        # TODO handle connection/disconnect


class OscStationClient(object):
    def __init__(self, station_id, client):
        self.station_id = station_id
        self.client = client

    def send(self, buttons):
        update_buttons(self.client, self.station_id, buttons)

    def disconnect(self):
        # No-Op? This class is temporary anyway
        pass

class MultiReceiverStationClient(object):
    def __init__(self, simulator_client, arduino_client):
        self.simulator_client = simulator_client
        self.arduino_client = arduino_client
        # TODO disable/enable clients

    def send(self, buttons):
        self.arduino_client.send(buttons)
        self.simulator_client.send(buttons)

    def disconnect(self):
        self.arduino_client.disconnect()
        self.simulator_client.disconnect()


def _init_station_clients():
    assert "remote" in STATE.servers and "station_controls" in STATE.servers["remote"], "remote/station_controls not specified"
    servers = STATE.servers["remote"]["station_controls"]

    assert "protocol" not in servers or servers["protocol"] == "tcp", "Unknown protocol %s" % servers["protocol"]
    print "Establishing TCP socket connection to stations"
    simulator_clients, arduino_clients = None, None
    if "simulator" in servers:
        assert len(servers["simulator"]) == STATE.layout.sections, "Wrong number of servers specified"
        simulator_clients = [StationClient(s_id=s_id, host=server["host"], port=int(server["port"]))
                                for s_id, server in enumerate(servers["simulator"])]
    if "arduinos" in servers:
        assert len(servers["arduinos"]) == STATE.layout.sections, "Wrong number of servers specified"
        arduino_clients = [StationClient(s_id=s_id, host=server["host"], port=int(server["port"]))
                                for s_id, server in enumerate(servers["arduinos"])]
    assert simulator_clients or arduino_clients, "Could not find simulator or arduino clients"
    if simulator_clients and arduino_clients:
        return [MultiReceiverStationClient(simulator, arduino) for simulator,arduino in zip(simulator_clients, arduino_clients)]
    elif simulator_clients:
        return simulator_clients
    else:
        return arduino_clients
