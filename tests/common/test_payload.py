import unittest

import six

from engineio import packet
from engineio import payload
import pytest


class TestPayload(unittest.TestCase):
    def test_encode_empty_payload(self):
        p = payload.Payload()
        assert p.packets == []
        assert p.encode() == b''

    def test_decode_empty_payload(self):
        p = payload.Payload(encoded_payload=b'')
        assert p.encode() == b''

    def test_encode_payload_xhr2(self):
        pkt = packet.Packet(packet.MESSAGE, data=six.text_type('abc'))
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode() == b'\x00\x04\xff4abc'

    def test_decode_payload_xhr2(self):
        p = payload.Payload(encoded_payload=b'\x00\x04\xff4abc')
        assert p.encode() == b'\x00\x04\xff4abc'

    def test_encode_payload_xhr_text(self):
        pkt = packet.Packet(packet.MESSAGE, data=six.text_type('abc'))
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode(b64=True) == b'4:4abc'

    def test_decode_payload_xhr_text(self):
        p = payload.Payload(encoded_payload=b'4:4abc')
        assert p.encode() == b'\x00\x04\xff4abc'

    def test_encode_payload_xhr_binary(self):
        pkt = packet.Packet(packet.MESSAGE, data=b'\x00\x01\x02', binary=True)
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode(b64=True) == b'6:b4AAEC'

    def test_decode_payload_xhr_binary(self):
        p = payload.Payload(encoded_payload=b'6:b4AAEC')
        assert p.encode() == b'\x01\x04\xff\x04\x00\x01\x02'

    def test_encode_jsonp_payload(self):
        pkt = packet.Packet(packet.MESSAGE, data=six.text_type('abc'))
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode(jsonp_index=233) == b'___eio[233]("\x00\x04\xff4abc");'
        assert p.encode(jsonp_index=233, b64=True) == b'___eio[233]("4:4abc");'

    def test_decode_jsonp_payload(self):
        p = payload.Payload(encoded_payload=b'd=4:4abc')
        assert p.encode() == b'\x00\x04\xff4abc'

    def test_decode_invalid_payload(self):
        with pytest.raises(ValueError):
            payload.Payload(encoded_payload=b'bad payload')

    # performance improvements in the payload parser assume packets in a
    # payload are either all binary or all text, so the following test does
    # no work anymore.
    #
    # def test_decode_multi_payload(self):
    #     p = payload.Payload(encoded_payload=b'4:4abc\x00\x04\xff4def')
    #     self.assertEqual(len(p.packets), 2)
    #     self.assertEqual(p.packets[0].data, 'abc')
    #     self.assertEqual(p.packets[1].data, 'def')

    def test_decode_multi_binary_payload(self):
        p = payload.Payload(
            encoded_payload=b'\x00\x04\xff4abc\x00\x04\xff4def'
        )
        assert len(p.packets) == 2
        assert p.packets[0].data == 'abc'
        assert p.packets[1].data == 'def'

    def test_decode_multi_text_payload(self):
        p = payload.Payload(encoded_payload=b'4:4abc4:4def')
        assert len(p.packets) == 2
        assert p.packets[0].data == 'abc'
        assert p.packets[1].data == 'def'

    def test_decode_multi_binary_payload_with_too_many_packets(self):
        with pytest.raises(ValueError):
            payload.Payload(
                encoded_payload=b'\x00\x04\xff4abc\x00\x04\xff4def' * 9
            )

    def test_decode_multi_text_payload_with_too_many_packets(self):
        with pytest.raises(ValueError):
            payload.Payload(encoded_payload=b'4:4abc4:4def' * 9)
