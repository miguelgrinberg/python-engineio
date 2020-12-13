import time
from engineio import packet


def test():
    p = packet.Packet(packet.MESSAGE, b'hello world')
    start = time.time()
    count = 0
    while True:
        p = packet.Packet(encoded_packet=p.encode(b64=True))
        count += 1
        if time.time() - start >= 5:
            break
    return count


if __name__ == '__main__':
    count = test()
    print('binary_b64_packet:', count, 'packets processed.')
