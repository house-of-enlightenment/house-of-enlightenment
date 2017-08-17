import time
import socket

from hoe.osc_utils import update_buttons


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

    def send_button_light_update(self, force=False):
        if force or self._last_change_timestamp > self._last_update_timestamp:
            self._last_update_timestamp = time.time()
            self._remote_client.send(self._buttons)
            # update_buttons(self._remote_client, self.station_id, self._buttons)
            # TODO: MAJOR - Send buttons to arduino controllers


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