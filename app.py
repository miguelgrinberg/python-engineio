import json

from eventlet import wsgi
import eventlet
from flask import Flask, render_template, abort, request
import six


app = Flask(__name__)
app.debug = True


(OPEN, CLOSE, PING, PONG, MESSAGE, UPGRADE) = (0, 1, 2, 3, 4, 5)


def encode_packet(packet_type, data=None):
    encoded_data = b''
    if isinstance(data, six.string_types):
        encoded_data = data.encode('utf-8')
    elif isinstance(data, dict):
        encoded_data = json.dumps(data, separators=(',', ':')).encode('utf-8')
    else:
        encoded_data = data
    return six.int2byte(packet_type + 48) + encoded_data


def encode_payload(packets=None):
    payload = b''
    for packet in packets:
        packet_len = len(packet)
        binary_len = b''
        while packet_len != 0:
            binary_len = six.int2byte(packet_len % 10) + binary_len
            packet_len = int(packet_len / 10)
        payload += b'\0' + binary_len + b'\xff' + packet
    return payload


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/engine.io/', methods=['GET', 'POST'])
def engine_io():
    if 'sid' not in request.args:
        return encode_payload([encode_packet(OPEN, data={'upgrades':[], 'pingTimeout': 60000, 'pingInterval': 25000, 'sid': '123456'})]), 200, {'Content-Type': 'application/octet-stream', 'Set-Cookie': 'io=123456', 'Access-Control-Allow-Origin': '*'}
    if request.method == 'POST':
        print(request.data)
        return 'ok'
    return 'ok'

if __name__ == '__main__':
    # app.run(debug=True)
    wsgi.server(eventlet.listen(('localhost', 5000)), app)
