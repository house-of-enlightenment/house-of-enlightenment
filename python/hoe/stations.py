from itertools import chain
import logging
import socket
import time

import osc_utils

from hoe.osc_utils import update_buttons
from hoe.state import STATE


logger = logging.getLogger(__name__)

id_to_color_names = {
    0: "YELLOW",
    1: "GREEN",
    2: "WHITE",
    3: "RED",
    4: "BLUE",
}

colors_to_id = {v: k for v, k in id_to_color_names.items()}
# TODO - Color scale?
colors_to_rgb = {
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (200, 200, 0),
    "WHITE": (255, 255, 255),
    "ORANGE": (255,165,0),
    "PURPLE": (186,85,211)
}

N_BUTTONS = 5
BUTTON_COLORS = [colors_to_rgb[id_to_color_names[i]] for i in range(N_BUTTONS)]


class Stations(object):
    def __init__(self):
        self._clients = _init_station_clients()
        self._stations = [Station(client=client) for client in self._clients]

    def __getitem__(self, key):
        """Easy get access. Note that set is not specified - stations should not be re-set"""
        return self._stations[key]

    def __setitem__(self, key, value):
        raise Exception('Stations are readonly')

    def send_button_updates(self, force=False):
        # TODO: Asych
        for station in self._stations:
            station.buttons.send_button_light_update(station.client, force)

    def shutdown(self):
        for client in self._clients:
            try:
                client.disconnect()
            except:
                logger.exception("Error shutting down client: %s", client)

    def change_client_status(self, enabled=True, station_id=None, client_type="*"):
        stations = [self._stations[station_id]] if station_id is not None else self._stations
        for station in stations:
            if isinstance(station.client, MultiReceiverStationClient):
                if client_type is None or client_type == "*":
                    station.client.change_client_status(
                        arduino_enabled=enabled, simulator_enabled=enabled)
                elif client_type is "arduino":
                    station.client.change_client_status(arduino_enabled=enabled)
                elif client_type is "simulator":
                    station.client.change_client_status(arduino_enabled=enabled)
            else:
                logger.debug("Enable/disabling client %s", station.client)
                station.client.enabled = enabled

    def get_buttons_code(self):
        # TODO: Cache this and update on presses?
        return get_code_as_int([station.buttons.as_array() for station in self._stations])

    def last_interaction(self):
        return max(map(lambda s: s.buttons.get_last_interaction_time(), self._stations))


class Station(object):
    def __init__(self, client, buttons=None):
        self.client = client
        self.buttons = buttons if buttons else StationButtons()
        self.fader_value = 50

    def set_button_values(self, values):
        for i, v in enumerate(values):
            self.buttons[i] = v

class StationButtons(object):
    BUTTON_OFF = 0
    BUTTON_ON = 1
    BUTTON_TOGGLE = 'toggle'

    def __init__(self, initial_state=BUTTON_ON):
        self._buttons = [initial_state] * 5
        self._last_change_timestamp = time.time()
        self._last_update_timestamp = 0

    def __str__(self):
        return str(self.as_array())

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

    def get_high_buttons(self):
        return [i for i, val in enumerate(self._buttons) if val]

    def send_button_light_update(self, remote_client, force=False):
        if force or self._last_change_timestamp > self._last_update_timestamp:
            self._last_update_timestamp = time.time()
            remote_client.send(self._buttons)
            # update_buttons(self._remote_client, self.station_id, self._buttons)
            # TODO: MAJOR - Send buttons to arduino controllers

    def set_all(self, on=True):
        self._buttons = [1 if on else 0] * 5
        self._last_change_timestamp = time.time()

    def as_array(self):
        return [b for b in self._buttons]  # TODO performance concerns

    def get_last_interaction_time(self):
        return self._last_change_timestamp


class StationClient(object):
    def __init__(self, s_id, host, port, timeout=0.5):
        self.s_id = s_id  # Not currently in use but could be useful in the future
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket = None
        self.enabled = True

    def _ensure_connected(self):
        """Set up a connection if one doesn't already exist.

        Return True on success or False on failure.

        """
        if self._socket:
            logger.debug('_ensure_connected: already connected, doing nothing')
            return True

        try:
            logger.debug('_ensure_connected: trying to connect to %s:%s', self.host, self.port)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
            logger.debug('_ensure_connected:    ...success')
            return True
        except socket.error:
            logger.debug('_ensure_connected:    ...failure')
            self._socket = None
            return False

    def disconnect(self):
        """Drop the connection to the server, if there is one."""
        logger.debug('disconnecting')
        if self._socket:
            self._socket.close()
        self._socket = None

    def send(self, buttons):
        if not self.enabled:
            logger.debug('Client currently disabled. Not sending')
            return

        is_connected = self._ensure_connected()
        if not is_connected:
            logger.debug('send: not connected.  ignoring these pixels.')
            return False

        data = reduce(lambda x, y: str(x) + str(y), buttons)
        logger.debug("Sending data %s to %s" % (data, self._socket))
        try:
            self._socket.send(data)
        except socket.error:
            logger.debug('send: connection lost.  could not send button data.')
            self._socket = None
            return False

        return True


class MultiReceiverStationClient(object):
    def __init__(self, simulator_client, arduino_client):
        self.simulator_client = simulator_client
        self.arduino_client = arduino_client

    def send(self, buttons):
        self.arduino_client.send(buttons)
        self.simulator_client.send(buttons)

    def disconnect(self):
        self.arduino_client.disconnect()
        self.simulator_client.disconnect()

    def change_client_status(self, arduino_enabled=None, simulator_enabled=None):
        if arduino_enabled is not None:
            self.arduino_client.enabled = arduino_enabled
        if simulator_enabled is not None:
            self.simulator_client.enabled = simulator_enabled


def _init_station_clients():
    assert ("remote" in STATE.servers) and ("station_controls" in STATE.servers["remote"]), \
        "remote/station_controls not specified"
    servers = STATE.servers["remote"]["station_controls"]

    assert ("protocol" not in servers) or (servers["protocol"] == "tcp"), \
        "Unknown protocol %s" % servers["protocol"]
    logger.info("Establishing TCP socket connection to stations")
    simulator_clients, arduino_clients = None, None
    if "simulator" in servers:
        assert len(
            servers["simulator"]) == STATE.layout.sections, "Wrong number of servers specified"
        simulator_clients = [
            StationClient(s_id=s_id, host=server["host"], port=int(server["port"]))
            for s_id, server in enumerate(servers["simulator"])
        ]
    if "arduinos" in servers:
        assert len(
            servers["arduinos"]) == STATE.layout.sections, "Wrong number of servers specified"
        arduino_clients = [
            StationClient(s_id=s_id, host=server["host"], port=int(server["port"]))
            for s_id, server in enumerate(servers["arduinos"])
        ]
    assert simulator_clients or arduino_clients, "Could not find simulator or arduino clients"
    if simulator_clients and arduino_clients:
        return [
            MultiReceiverStationClient(simulator, arduino)
            for simulator, arduino in zip(simulator_clients, arduino_clients)
        ]
    elif simulator_clients:
        return simulator_clients
    else:
        return arduino_clients


def get_code_as_int(code_array):
    out = 0
    for bit in chain.from_iterable(code_array):
        out = (out << 1) | bit
    return out


class Codes(object):
    def __init__(self, json):
        self.station_colors_to_station_id = {k: int(v) for k, v in json["station_map"].items()}
        self.station_ids_to_station_colors = {
            v: k
            for k, v in self.station_colors_to_station_id.items()
        }
        self.scenes_to_codes = {
            s: self.create_code_string_for_scene(s, codes)
            for s, codes in json["book"].items()
        }
        self.codes_to_scenes = {v: k for k, v in self.scenes_to_codes.items()}

    def create_code_string_for_scene(self, scene, scene_code_array):
        assert len(scene_code_array) == 6, "Not enough codes"

        stations = [0] * 6
        for color in self.station_colors_to_station_id.keys():
            assert color in scene_code_array, \
                "Station color {} not specified for scene {}".format(color, scene)
            station_id = self.station_colors_to_station_id[color]
            stations[station_id] = [
                id_to_color_names[i] in scene_code_array[color] for i in range(5)]
        return get_code_as_int(stations)

    def get_station_rgb_color(self, station_id):
        return colors_to_rgb[self.station_ids_to_station_colors[station_id]]