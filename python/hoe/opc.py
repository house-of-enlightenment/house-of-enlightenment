#!/usr/bin/env python
"""Python Client library for Open Pixel Control
http://github.com/zestyping/openpixelcontrol

Sends pixel values to an Open Pixel Control server to be displayed.
http://openpixelcontrol.org/

Recommended use:

    import opc

    # Create a client object
    client = opc.Client('localhost:7890')

    # Test if it can connect (optional)
    if client.can_connect():
        print 'connected to %s' % ADDRESS
    else:
        # We could exit here, but instead let's just print a warning
        # and then keep trying to send pixels in case the server
        # appears later
        print 'WARNING: could not connect to %s' % ADDRESS

    # Send pixels forever at 30 frames per second
    while True:
        my_pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        if client.put_pixels(my_pixels, channel=0):
            print '...'
        else:
            print 'not connected'
        time.sleep(1/30.0)

"""

import socket
import struct

import numpy as np

from hoe import color_utils

kinet_data = [0x0401dc4a, 0x0100, 0x0101, 0x00000000, 0x00, 0x00, 0x0000, 0xffffffff, 0x00]
kinet_header = struct.pack(">IHHIBBHIB", *kinet_data)
kinet_maxpixels = 170
opc_maxpixels = 120 * 48
max_channels = 16


class Client(object):
    def __init__(self, server_ip_port, long_connection=True, verbose=False, protocol="opc"):
        """Create an OPC client object which sends pixels to an OPC server.

        server_ip_port should be an ip:port or hostname:port as a single string.
        For example: '127.0.0.1:7890' or 'localhost:7890'

        There are two connection modes:
        * In long connection mode, we try to maintain a single long-lived
          connection to the server.  If that connection is lost we will try to
          create a new one whenever put_pixels is called.  This mode is best
          when there's high latency or very high framerates.
        * In short connection mode, we open a connection when it's needed and
          close it immediately after.  This means creating a connection for each
          call to put_pixels. Keeping the connection usually closed makes it
          possible for others to also connect to the server.

        A connection is not established during __init__.  To check if a
        connection will succeed, use can_connect().

        If verbose is True, the client will print debugging info to the console.

        """
        self.verbose = verbose
        self.address = server_ip_port
        self._long_connection = long_connection

        self.ip, self.port = server_ip_port.split(':')
        self.port = int(self.port)

        self._socket = None  # will be None when we're not connected
        # TODO: if you want a different protocol, make a different class
        assert protocol == 'opc'
        self.protocol = protocol
        self.socket_type = socket.SOCK_STREAM
        self.header = bytearray(4)
        self.message = bytearray()

    def _debug(self, m):
        if self.verbose:
            print '    %s' % str(m)

    def _ensure_connected(self):
        """Set up a connection if one doesn't already exist.

        Return True on success or False on failure.

        """
        if self._socket:
            self._debug('_ensure_connected: already connected, doing nothing')
            return True

        try:
            self._debug('_ensure_connected: trying to connect to ' + self.ip + ' using protocol ' +
                        self.protocol + '...')
            self._socket = socket.socket(socket.AF_INET, self.socket_type)
            self._socket.settimeout(0.5)
            self._socket.connect((self.ip, self.port))
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

    def can_connect(self):
        """Try to connect to the server.

        Return True on success or False on failure.

        If in long connection mode, this connection will be kept and re-used for
        subsequent put_pixels calls.

        """
        success = self._ensure_connected()
        if not self._long_connection:
            self.disconnect()
        return success

    def put_pixels(self, pixels, channel=0):
        """Send the list of pixel colors to the OPC server on the given channel.

        channel: Which strand of lights to send the pixel colors to.
            Must be an int in the range 0-255 inclusive.
            0 is a special value which means "all channels".

        pixels: A list of 3-tuples representing rgb colors.
            Each value in the tuple should be in the range 0-255 inclusive.
            For example: [(255, 255, 255), (0, 0, 0), (127, 0, 0)]
            Floats will be rounded down to integers.
            Values outside the legal range will be clamped.

        Will establish a connection to the server as needed.

        On successful transmission of pixels, return True.
        On failure (bad connection), return False.

        The list of pixel colors will be applied to the LED string starting
        with the first LED.  It's not possible to send a color just to one
        LED at a time (unless it's the first one).

        """
        # ledscape OPC ignores the channel parameter
        # https://github.com/Yona-Appletree/LEDscape/blob/master/opc-server.c#L1996
        assert channel == 0
        self._debug('put_pixels: connecting')
        is_connected = self._ensure_connected()
        if not is_connected:
            self._debug('put_pixels: not connected.  ignoring these pixels.')
            return False

        if isinstance(pixels, np.ndarray):
            header = self.get_opc_header(channel, pixels)
            self.message = header + pixels.tobytes()
        else:
            self.allocate_message(pixels)
            # build OPC message
            if (self.protocol == "opc"):
                self.header = self.get_opc_header(channel, pixels)
            self.headerl = len(self.header)
            self.copy_header_into_message()
            self.copy_pixels_into_message(pixels)
        if not self._send_message():
            return False
        if not self._long_connection:
            self._debug('put_pixels: disconnecting')
            self.disconnect()
        return True

    def allocate_message(self, pixels):
        if (len(self.message) != len(pixels) * 3 + len(self.header)):
            self.message = bytearray(len(pixels) * 3 + len(self.header))

    def get_opc_header(self, channel, pixels):
        data_size = len(pixels) * 3
        len_hi_byte = data_size // 256
        len_lo_byte = data_size % 256
        return struct.pack('BBBB', channel, 0, len_hi_byte, len_lo_byte)

    def copy_header_into_message(self):
        for index, b in enumerate(self.header):
            self.message[index] = b

    def copy_pixels_into_message(self, pixels):
        for index, pixel in enumerate(pixels):
            self.set_pixel(index, pixel)

    def set_pixel(self, index, pixel):
        assert len(pixel) == 3
        for i, color_value in enumerate(pixel):
            self.message[self.headerl + index * 3 + i] = to_byte(color_value)

    def _send_message(self):
        self._debug('put_pixels: sending pixels to server')
        try:
            # 42772 is the length if we're sending to the simulator
            # assert len(self.message) == 42772, len(self.message)
            self._socket.send(self.message)
        except socket.error:
            self._debug('put_pixels: connection lost.  could not send pixels.')
            self._socket = None
            raise
            return False


def to_byte(num):
    return int(min(255, max(0, num)))


class MultiClient(object):
    """Opc client that splits messsages across multiple opc lients.

    The pixels are broken into parts, as determined by the address field
    of the pixel in the layout file

    Attributes:
        clients_map: a map from client to index values corresponding to pixels that client
            needs to send data too
    """

    def __init__(self, clients_map):
        self.clients_map = clients_map

    @property
    def clients(self):
        return list(self.clients_map.keys())

    def put_pixels(self, pixels, channel=0):
        pixels = np.array(pixels)
        # pixels = color_utils.color_correct(pixels)
        for client in self.clients:
            client.put_pixels(pixels[self.clients_map[client]])

    def disconnect(self):
        return all([c.disconnect() for c in self.clients])

    def can_connect(self):
        return all([c.can_connect() for c in self.clients])

    def remove_client(self, client=None, ip_address=None):
        assert client or ip_address
        assert not (client and ip_address)
        for my_client in self.clients:
            if client and my_client == client:
                self.clients_map.pop(client)
            if ip_address and my_client.ip == ip_address:
                self.clients_map.pop(client)

    @classmethod
    def fromlayout(cls, clients, layout):
        """Generate a client to pixel map from the layout

        Args:
            clients: a list of opc clients
            layout: layout object used to allocate pixels to clients
        """
        mapping = map_clients(clients, layout)
        return cls(mapping)


def map_clients(clients, layout):
    ips = set(c.ip for c in clients)
    assert ips == set(layout.address.keys()), 'client ips do not match addresses in layout'
    mapping = {c: layout.address[c.ip] for c in clients}
    return mapping
