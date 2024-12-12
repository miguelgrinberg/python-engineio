import time
import engineio

eio = engineio.Client()
start_timer = None


def send_ping():
    global start_timer
    start_timer = time.time()
    eio.send('ping')


@eio.on('connect')
def on_connect():
    print('connected to server')
    send_ping()


@eio.on('message')
def on_message(data):
    global start_timer
    latency = time.time() - start_timer
    print(f'latency is {latency * 1000:.2f} ms')
    eio.sleep(1)
    send_ping()


if __name__ == '__main__':
    eio.connect('http://localhost:5000')
    eio.wait()
