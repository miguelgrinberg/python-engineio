import unittest

import six

from engineio import packet


class TestPacket(unittest.TestCase):
    def test_encode_default_packet(self):
        pkt = packet.Packet()
        assert pkt.packet_type == packet.NOOP
        assert pkt.data is None
        assert not pkt.binary
        assert pkt.encode() == b'6'

    def test_decode_default_packet(self):
        pkt = packet.Packet(encoded_packet=b'6')
        assert pkt.encode(), b'6'

    def test_encode_text_packet(self):
        data = six.text_type('text')
        pkt = packet.Packet(packet.MESSAGE, data=data)
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == data
        assert not pkt.binary
        assert pkt.encode() == b'4text'

    def test_decode_text_packet(self):
        pkt = packet.Packet(encoded_packet=b'4text')
        assert pkt.encode() == b'4text'

    def test_encode_binary_packet(self):
        pkt = packet.Packet(packet.MESSAGE, data=b'\x01\x02\x03', binary=True)
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == b'\x01\x02\x03'
        assert pkt.binary
        assert pkt.encode() == b'\x04\x01\x02\x03'

    def test_encode_binary_bytearray_packet(self):
        pkt = packet.Packet(
            packet.MESSAGE, data=bytearray(b'\x01\x02\x03'), binary=True
        )
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == b'\x01\x02\x03'
        assert pkt.binary
        assert pkt.encode() == b'\x04\x01\x02\x03'

    def test_encode_binary_b64_packet(self):
        pkt = packet.Packet(
            packet.MESSAGE, data=b'\x01\x02\x03\x04', binary=True
        )
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == b'\x01\x02\x03\x04'
        assert pkt.binary
        assert pkt.encode(b64=True) == b'b4AQIDBA=='

    def test_encode_binary_packet_py3(self):
        pkt = packet.Packet(packet.MESSAGE, data=b'\x01\x02\x03')
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == b'\x01\x02\x03'
        assert pkt.binary
        assert pkt.encode() == b'\x04\x01\x02\x03'

    def test_decode_binary_packet(self):
        pkt = packet.Packet(encoded_packet=b'\x04\x01\x02\x03')
        assert pkt.encode(), b'\x04\x01\x02\x03'

    def test_decode_binary_bytearray_packet(self):
        pkt = packet.Packet(encoded_packet=bytearray(b'\x04\x01\x02\x03'))
        assert pkt.encode(), b'\x04\x01\x02\x03'

    def test_decode_binary_b64_packet(self):
        pkt = packet.Packet(encoded_packet=b'b4AAEC')
        assert pkt.encode(), b'\x04\x01\x02\x03'

    def test_encode_json_packet(self):
        pkt = packet.Packet(packet.MESSAGE, data={'a': 123, 'b': '456'})
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == {'a': 123, 'b': '456'}
        assert not pkt.binary
        assert pkt.encode() in [
            b'4{"a":123,"b":"456"}',
            b'4{"b":"456","a":123}',
        ]

    def test_decode_json_packet(self):
        pkt = packet.Packet(encoded_packet=b'4{"a":123,"b":"456"}')
        assert pkt.encode() in [
            b'4{"a":123,"b":"456"}',
            b'4{"b":"456","a":123}',
        ]

    def test_encode_number_packet(self):
        pkt = packet.Packet(packet.MESSAGE, data=123)
        assert pkt.packet_type == packet.MESSAGE
        assert pkt.data == 123
        assert not pkt.binary
        assert pkt.encode() == b'4123'

    def test_decode_number_packet(self):
        pkt = packet.Packet(encoded_packet=b'4123')
        assert pkt.packet_type == packet.MESSAGE
        # integer payloads are parsed as strings, see
        # https://github.com/miguelgrinberg/python-engineio/issues/75
        # for background on this decision
        assert pkt.data == '123'
        assert not pkt.binary
        assert pkt.encode() == b'4123'
