import importlib
import sys

import gevent
try:
    import uwsgi
    if hasattr(uwsgi, 'websocket_handshake'):
        _websocket_available = "uwsgi"
    else:
        raise ImportError('uWSGI not running with websocket support')
except ImportError:
    try:
        import geventwebsocket  # noqa
        _websocket_available = "gevent"
    except ImportError:
        _websocket_available = False


class Thread(gevent.Greenlet):  # pragma: no cover
    """
    This wrapper class provides gevent Greenlet interface that is compatible
    with the standard library's Thread class.
    """
    def __init__(self, target, args=[], kwargs={}):
        super(Thread, self).__init__(target, *args, **kwargs)

    def _run(self):
        return self.run()


class GeventWebSocket(object):  # pragma: no cover
    """
    This wrapper class provides a gevent WebSocket interface that is
    compatible with eventlet's implementation.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'wsgi.websocket' not in environ:
            raise RuntimeError('You need to use the gevent-websocket server. '
                               'See the Deployment section of the '
                               'documentation for more information.')
        self._sock = environ['wsgi.websocket']
        self.environ = environ
        self.version = self._sock.version
        self.path = self._sock.path
        self.origin = self._sock.origin
        self.protocol = self._sock.protocol
        return self.app(self)

    def close(self):
        return self._sock.close()

    def send(self, message):
        return self._sock.send(message)

    def wait(self):
        return self._sock.receive()


class uWSGIWebSocket(object):  # pragma: no cover
    """
    This wrapper class provides a uWSGI WebSocket interface that is
    compatible with eventlet's implementation.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if _websocket_available != "uwsgi":
            raise RuntimeError('You need to use the uWSGI server.')
        self.environ = environ
        uwsgi.websocket_handshake()
        return self.app(self) or []

    def close(self):
        uwsgi.close()

    def send(self, message):
        uwsgi.websocket_send(message)

    def wait(self):
        msg = uwsgi.websocket_recv()
        if not msg:
            return None
        return msg.decode()

    def send_and_wait(self, poll_func):
        """Calls poll_func(block=False) regularly and sends the messages
        it returns. Apart from that, it observes the websocket for incoming
        messages. If one arrives, it returns that. After the returned message
        was processed, this function can be called again to continue its work.
        A return of None means that the connection was closed. Afterwards."""
        while True:
            # fetch packets to send and transmit them over the websocket
            try:
                packets = poll_func(block=False)
            except IOError:  # no packets to send
                pass
            else:
                try:
                    for pkt in packets:
                        self.send(pkt.encode(always_bytes=False))
                except:
                    break
            # receive packets available on the websocket
            try:
                msg = uwsgi.websocket_recv_nb()
            except IOError:  # connection closed
                return None
            else:
                if not msg:  # no message available
                    # We can't avoid a delay completely, so make it small
                    # at least.
                    gevent.sleep(0.05)
                else:
                    return msg.decode()


async = {
    'threading': sys.modules[__name__],
    'thread_class': 'Thread',
    'queue': importlib.import_module('gevent.queue'),
    'queue_class': 'JoinableQueue',
    'websocket': sys.modules[__name__] if _websocket_available else None,
    'websocket_class': {'gevent': 'GeventWebSocket', 'uwsgi': 'uWSGIWebSocket',
                        False: None}[_websocket_available],
    'sleep': gevent.sleep
}
