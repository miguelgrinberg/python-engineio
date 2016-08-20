import importlib
import sys
import six

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

        self._req_ctx = None
        if hasattr(uwsgi, 'request_context'):
            # uWSGI >= 2.1.x with support for api access across-greenlets
            self._req_ctx = uwsgi.request_context()
        else:
            # use event and queue for sending messages
            import gevent.event
            import gevent.queue
            import gevent.select
            self._event = gevent.event.Event()
            self._send_queue = gevent.queue.Queue()

            # spawn a select greenlet
            def select_greenlet_runner(fd, event):
                """Sets event when data becomes available to read on fd."""
                while True:
                    event.set()
                    gevent.select.select([fd], [], [])[0]
            self._select_greenlet = gevent.spawn(
                select_greenlet_runner,
                uwsgi.connection_fd(),
                self._event)

        return self.app(self)

    def close(self):
        """Disconnects uWSGI from the client."""
        uwsgi.disconnect()
        if self._req_ctx is None:
            # better kill it here in case wait() is not called again
            self._select_greenlet.kill()
            self._event.set()

    def _send(self, msg):
        """Transmits message either in binary or UTF-8 text mode,
        depending on its type."""
        kwargs = {}
        if self._req_ctx is not None:
            kwargs['request_context'] = self._req_ctx
        if isinstance(msg, six.binary_type):
            uwsgi.websocket_send_binary(msg, **kwargs)
        else:
            uwsgi.websocket_send(msg, **kwargs)

    def _decode_received(self, msg):
        """Returns either bytes or str, depending on message type."""
        if not isinstance(msg, six.binary_type):
            # already decoded - do nothing
            return msg
        # only decode from utf-8 if message is not binary data
        type = six.byte2int(msg[0:1])
        if type >= 48:  # no binary
            return msg.decode('utf-8')
        # binary message, don't try to decode
        return msg

    def send(self, msg):
        """Queues a message for sending. Real transmission is done in
        wait method.
        Sends directly if uWSGI version is new enough."""
        if self._req_ctx is not None:
            self._send(msg)
        else:
            self._send_queue.put(msg)
            self._event.set()

    def wait(self):
        """Waits and returns received messages.
        If running in compatibility mode for older uWSGI versions,
        it also sends messages that have been queued by send().
        A return value of None means that connection was closed.
        This must be called repeatedly. For uWSGI < 2.1.x it must
        be called from the main greenlet."""
        while True:
            if self._req_ctx is not None:
                try:
                    msg = uwsgi.websocket_recv(request_context=self._req_ctx)
                except IOError:  # connection closed
                    return None
                return self._decode_received(msg)
            else:
                self._event.wait()
                self._event.clear()
                # maybe there is something to send
                msgs = []
                while True:
                    try:
                        msgs.append(self._send_queue.get(block=False))
                    except gevent.queue.Empty:
                        break
                for msg in msgs:
                    self._send(msg)
                # maybe there is something to receive
                try:
                    msg = uwsgi.websocket_recv_nb()
                except IOError:  # connection closed
                    self._select_greenlet.kill()
                    return None
                if msg:  # message available
                    return self._decode_received(msg)


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
