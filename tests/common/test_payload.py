import pytest

from engineio import packet
from engineio import payload


class TestPayload:
    def test_encode_empty_payload(self):
        p = payload.Payload()
        assert p.packets == []
        assert p.encode() == ''

    def test_decode_empty_payload(self):
        p = payload.Payload(encoded_payload='')
        assert p.encode() == ''

    def test_encode_payload_text(self):
        pkt = packet.Packet(packet.MESSAGE, data='abc')
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode() == '4abc'

    def test_encode_payload_text_multiple(self):
        pkt = packet.Packet(packet.MESSAGE, data='abc')
        pkt2 = packet.Packet(packet.MESSAGE, data='def')
        p = payload.Payload([pkt, pkt2])
        assert p.packets == [pkt, pkt2]
        assert p.encode() == '4abc\x1e4def'

    def test_encode_payload_binary(self):
        pkt = packet.Packet(packet.MESSAGE, data=b'\x00\x01\x02')
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode() == 'bAAEC'

    def test_encode_payload_binary_multiple(self):
        pkt = packet.Packet(packet.MESSAGE, data=b'\x00\x01\x02')
        pkt2 = packet.Packet(packet.MESSAGE, data=b'\x03\x04\x05\x06')
        p = payload.Payload([pkt, pkt2])
        assert p.packets == [pkt, pkt2]
        assert p.encode() == 'bAAEC\x1ebAwQFBg=='

    def test_encode_payload_text_binary_multiple(self):
        pkt = packet.Packet(packet.MESSAGE, data='abc')
        pkt2 = packet.Packet(packet.MESSAGE, data=b'\x03\x04\x05\x06')
        p = payload.Payload([pkt, pkt2, pkt2, pkt])
        assert p.packets == [pkt, pkt2, pkt2, pkt]
        assert p.encode() == '4abc\x1ebAwQFBg==\x1ebAwQFBg==\x1e4abc'

    def test_encode_jsonp_payload(self):
        pkt = packet.Packet(packet.MESSAGE, data='abc')
        p = payload.Payload([pkt])
        assert p.packets == [pkt]
        assert p.encode(jsonp_index=233) == '___eio[233]("4abc");'

    def test_decode_jsonp_payload(self):
        p = payload.Payload(encoded_payload='d=4abc')
        assert p.encode() == '4abc'

    def test_decode_invalid_payload(self):
        with pytest.raises(ValueError):
            payload.Payload(encoded_payload='bad payload')

    def test_decode_multi_payload_with_too_many_packets(self):
        with pytest.raises(ValueError):
            payload.Payload(encoded_payload='4abc\x1e4def\x1e' * 9 + '6')
