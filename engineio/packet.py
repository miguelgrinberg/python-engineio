import base64
import json

import six

(OPEN, CLOSE, PING, PONG, MESSAGE, UPGRADE, NOOP) = (0, 1, 2, 3, 4, 5, 6)
packet_names = ['OPEN', 'CLOSE', 'PING', 'PONG', 'MESSAGE', 'UPGRADE', 'NOOP']


class Packet(object):
    """Engine.IO packet."""

    def __init__(self, packet_type=NOOP, data=None, binary=None,
                 encoded_packet=None):
        self.packet_type = packet_type
        self.data = data
        if binary is not None:
            self.binary = binary
        elif isinstance(data, six.text_type):
            self.binary = False
        elif isinstance(data, six.binary_type):
            self.binary = True
        else:
            self.binary = False
        if encoded_packet:
            self.decode(encoded_packet)

    def encode(self, b64=False, always_bytes=True):
        """Encode the packet for transmission."""
        if self.binary and not b64:
            encoded_packet = six.int2byte(self.packet_type)
        else:
            encoded_packet = six.text_type(self.packet_type)
            if self.binary and b64:
                encoded_packet = 'b' + encoded_packet
        if self.binary:
            if b64:
                encoded_packet += base64.b64encode(self.data).decode('utf-8')
            else:
                encoded_packet += self.data
        elif isinstance(self.data, six.string_types):
            encoded_packet += self.data
        elif isinstance(self.data, dict) or isinstance(self.data, list):
            encoded_packet += json.dumps(self.data,
                                         separators=(',', ':'))
        elif self.data is not None:
            encoded_packet += str(self.data)
        if always_bytes and not isinstance(encoded_packet, six.binary_type):
            encoded_packet = encoded_packet.encode('utf-8')
        return encoded_packet

    def decode(self, encoded_packet):
        """Decode a transmitted package."""
        b64 = False
        self.packet_type = six.byte2int(encoded_packet[0:1])
        if self.packet_type == 98:  # 'b' --> binary base64 encoded packet
            self.binary = True
            encoded_packet = encoded_packet[1:]
            self.packet_type = six.byte2int(encoded_packet[0:1])
            self.packet_type -= 48
            b64 = True
        elif self.packet_type >= 48:
            self.packet_type -= 48
            self.binary = False
        else:
            self.binary = True
        self.data = None
        if len(encoded_packet) > 1:
            if self.binary:
                if b64:
                    self.data = base64.b64decode(encoded_packet[1:])
                else:
                    self.data = encoded_packet[1:]
            else:
                try:
                    self.data = json.loads(encoded_packet[1:].decode('utf-8'))
                except ValueError:
                    self.data = encoded_packet[1:].decode('utf-8')
