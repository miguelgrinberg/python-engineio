import io
import sys
import time
import engineio


def test(eio_version, payload):
    s = engineio.Server()
    start = time.time()
    count = 0
    s.handle_request({
        'REQUEST_METHOD': 'GET',
        'QUERY_STRING': eio_version,
    }, lambda s, h: None)
    sid = list(s.sockets.keys())[0]
    while True:
        environ = {
            'REQUEST_METHOD': 'POST',
            'QUERY_STRING': eio_version + '&sid=' + sid,
            'CONTENT_LENGTH': '6',
            'wsgi.input': io.BytesIO(payload)
        }
        s.handle_request(environ, lambda s, h: None)
        count += 1
        if time.time() - start >= 5:
            break
    return count


if __name__ == '__main__':
    eio_version = 'EIO=4'
    payload = b'4hello'
    if len(sys.argv) > 1 and sys.argv[1] == '3':
        eio_version = 'EIO=3'
        payload = b'\x00\x06\xff4hello'
    count = test(eio_version, payload)
    print('server_receive:', count, 'packets received.')
