from __future__ import absolute_import

import gevent
import gevent.queue
try:
    import geventwebsocket
    assert geventwebsocket  # silence flakes8
    has_websocket = True
except ImportError:
    has_websocket = False

Queue = gevent.queue.JoinableQueue
QueueEmpty = gevent.queue.Empty


def thread(target):
    return gevent.Greenlet(target)


class WebSocket(object):
    """
    An abstract wrapper that tries to unify minor API differences
    between gevent and eventlet's Websocket classes.
    """
    def __init__(self, sock):
        self._sock = sock
        self.environ = sock.environ
        self.version = sock.version
        self.path = sock.path
        self.origin = sock.origin
        self.protocol = sock.protocol

    def close(self):
        return self._sock.close()

    def send(self, message):
        return self._sock.send(message)

    def wait(self):
        return self._sock.receive()


def wrap_websocket(app):
    """
    Given a callable that accepts a single argument - the websocket object,
    make gevent-websocket's approach compatible with eventlet's.
    """
    def __wrapper(environ, start_response):
        ws = WebSocket(environ["wsgi.websocket"])
        return app(ws)
    return __wrapper
