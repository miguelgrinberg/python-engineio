import six

from . import packet


class Payload(object):
    """Engine.IO payload."""
    def __init__(self, packets=None, encoded_payload=None):
        self.packets = packets or []
        if encoded_payload is not None:
            self.decode(encoded_payload)

    def encode(self, b64=False):
        """Encode the payload for transmission."""
        encoded_payload = b''
        for pkt in self.packets:
            encoded_packet = pkt.encode(b64=b64)
            packet_len = len(encoded_packet)
            if b64:
                encoded_payload += str(packet_len).encode('utf-8') + b':' + \
                    encoded_packet
            else:
                binary_len = b''
                while packet_len != 0:
                    binary_len = six.int2byte(packet_len % 10) + binary_len
                    packet_len = int(packet_len / 10)
                if not pkt.binary:
                    encoded_payload += b'\0'
                else:
                    encoded_payload += b'\1'
                encoded_payload += binary_len + b'\xff' + encoded_packet
        return encoded_payload

    def decode(self, encoded_payload):
        """Decode a transmitted payload."""
        fixed_double_encode = False
        self.packets = []
        while encoded_payload:
            if six.byte2int(encoded_payload[0:1]) <= 1:
                packet_len = 0
                i = 1
                while six.byte2int(encoded_payload[i:i + 1]) != 255:
                    packet_len = packet_len * 10 + six.byte2int(
                        encoded_payload[i:i + 1])
                    i += 1
                self.packets.append(packet.Packet(
                    encoded_packet=encoded_payload[i + 1:i + 1 + packet_len]))
            else:
                i = encoded_payload.find(b':')
                if i == -1:
                    raise ValueError('invalid payload')
                packet_len = int(encoded_payload[0:i])
                if not fixed_double_encode:
                    # the engine.io javascript client sends text payloads with
                    # a double UTF-8 encoding. Here we try to fix that mess and
                    # restore the original packet
                    try:
                        # first we remove one UTF-8 encoding layer
                        fixed_payload = encoded_payload.decode(
                            'utf-8').encode('raw_unicode_escape')

                        # then we make sure the result can be decoded a second
                        # time (this will raise an exception if not)
                        fixed_payload.decode('utf-8')

                        # if a second utf-8 decode worked, then this appears to
                        # be a double encoded packet, so here we keep the
                        # packet after a single decode, since the packet class
                        # will perform a decode as well
                        encoded_payload = fixed_payload
                    except:
                        # if we couldn't apply a double utf-8 decode then
                        # the packet must have been correct, so keep going
                        pass
                    fixed_double_encode = True
                pkt = encoded_payload[i + 1: i + 1 + packet_len]
                self.packets.append(packet.Packet(encoded_packet=pkt))
            encoded_payload = encoded_payload[i + 1 + packet_len:]
