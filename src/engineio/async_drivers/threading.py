from __future__ import absolute_import
import queue
import threading
import time

try:
    from simple_websocket import Server, ConnectionClosed
    _websocket_available = True
except ImportError:  # pragma: no cover
    _websocket_available = False


class DaemonThread(threading.Thread):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, daemon=True)


class WebSocketWSGI(object):  # pragma: no cover
    """
    This wrapper class provides a threading WebSocket interface that is
    compatible with eventlet's implementation.
    """
    def __init__(self, handler, server):
        self.app = handler

    def __call__(self, environ, start_response):
        self.ws = Server(environ)
        ret = self.app(self)
        if self.ws.mode == 'gunicorn':
            raise StopIteration()
        return ret

    def close(self):
        if self.ws.connected:
            self.ws.close()

    def send(self, message):
        try:
            return self.ws.send(message)
        except ConnectionClosed:
            raise IOError()

    def wait(self):
        try:
            return self.ws.receive()
        except ConnectionClosed:
            return None


_async = {
    'thread': DaemonThread,
    'queue': queue.Queue,
    'queue_empty': queue.Empty,
    'event': threading.Event,
    'websocket': WebSocketWSGI if _websocket_available else None,
    'sleep': time.sleep,
}
