import signal
import threading
import engineio

eio = engineio.Client()
exit_event = threading.Event()
original_signal_handler = None


def send_hello():
    message = 'Hello from client side!'
    while not exit_event.is_set():
        print('sending: ' + 'Hello from client side!')
        eio.send(message)
        exit_event.wait(5)
    eio.disconnect()


@eio.on('connect')
def on_connect():
    print('connected to server')
    eio.start_background_task(send_hello)


@eio.on('message')
def on_message(data):
    print('received: ' + str(data))


def signal_handler(sig, frame):
    exit_event.set()
    print('exiting')
    if callable(original_signal_handler):
        original_signal_handler(sig, frame)


if __name__ == '__main__':
    original_signal_handler = signal.signal(signal.SIGINT, signal_handler)
    eio.connect('http://localhost:5000')
    eio.wait()
