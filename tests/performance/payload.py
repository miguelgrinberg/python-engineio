import time
from engineio import packet, payload


def test():
    p = payload.Payload(
        packets=[packet.Packet(packet.MESSAGE, b'hello world')] * 10)
    start = time.time()
    count = 0
    while True:
        p = payload.Payload(encoded_payload=p.encode())
        count += 1
        if time.time() - start >= 5:
            break
    return count


if __name__ == '__main__':
    count = test()
    print('payload:', count, 'payloads processed.')
