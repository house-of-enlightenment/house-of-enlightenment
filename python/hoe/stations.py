import time
import socket

from hoe.osc_utils import update_buttons

class StationClient(object):
    def __init__(self, s_id, host, port):
        self.s_id = s_id  # Not currently in use but could be useful in the future
        self.host = host
        self.port = port
        self.socket = None

    def _ensure_connected(self):
        if self.socket:
            return

        # TODO - Error handling!
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send(self, buttons):
        self._ensure_connected()
        self.socket.send(reduce(lambda x,y: str(x)+str(y), buttons))

        # TODO handle connection/disconnect


class StationButtons(object):
    BUTTON_OFF = 0
    BUTTON_ON = 1
    BUTTON_TOGGLE = 'toggle'

    def __init__(self, station_id, client, initial_state=BUTTON_ON):
        self.station_id = station_id
        self._remote_client = client
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

    def send_button_light_update(self, force=False):
        if force or self._last_change_timestamp > self._last_update_timestamp:
            self._last_update_timestamp = time.time()
            self._remote_client.send(self._buttons)
            # update_buttons(self._remote_client, self.station_id, self._buttons)
            # TODO: MAJOR - Send buttons to arduino controllers


class OscStationClient(object):
    def __init__(self, station_id, client):
        self.station_id = station_id
        self.client = client

    def send(self, buttons):
        update_buttons(self.client, self.station_id, buttons)