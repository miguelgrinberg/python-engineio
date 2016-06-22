import gzip
import importlib
import logging
import uuid
import zlib

import six
from six.moves import urllib

from . import packet
from . import payload
from . import socket


class Server(object):
    """An Engine.IO server.

    This class implements a fully compliant Engine.IO web server with support
    for websocket and long-polling transports.

    :param async_mode: The library used for asynchronous operations. Valid
                       options are "threading", "eventlet" and "gevent". If
                       this argument is not given, "eventlet" is tried first,
                       then "gevent", and finally "threading". The websocket
                       transport is only supported in "eventlet" mode.
    :param ping_timeout: The time in seconds that the client waits for the
                         server to respond before disconnecting.
    :param ping_interval: The interval in seconds at which the client pings
                          the server.
    :param ping_holdtime: The time in which the server considers the client as 
                          timeout. (Recommended 3 times of ping_interval)
    :param max_http_buffer_size: The maximum size of a message when using the
                                 polling transport.
    :param allow_upgrades: Whether to allow transport upgrades or not.
    :param http_compression: Whether to compress packages when using the
                             polling transport.
    :param compression_threshold: Only compress messages when their byte size
                                  is greater than this value.
    :param cookie: Name of the HTTP cookie that contains the client session
                   id. If set to ``None``, a cookie is not sent to the client.
    :param cors_allowed_origins: List of origins that are allowed to connect
                                 to this server. All origins are allowed by
                                 default.
    :param cors_credentials: Whether credentials (cookies, authentication) are
                             allowed in requests to this server.
    :param logger: To enable logging set to ``True`` or pass a logger object to
                   use. To disable logging set to ``False``.
    :param json: An alternative json module to use for encoding and decoding
                 packets. Custom json modules must have ``dumps`` and ``loads``
                 functions that are compatible with the standard library
                 versions.
    :param kwargs: Reserved for future extensions, any additional parameters
                   given as keyword arguments will be silently ignored.
    """
    compression_methods = ['gzip', 'deflate']
    event_names = ['connect', 'disconnect', 'message']

    def __init__(self, async_mode=None, ping_timeout=60, ping_interval=25,
                 max_http_buffer_size=100000000, allow_upgrades=True,
                 http_compression=True, compression_threshold=1024,
                 cookie='io', cors_allowed_origins=None,
                 cors_credentials=True, logger=False, json=None, 
                 ping_holdtime=75,
                 **kwargs):
        self.ping_timeout = ping_timeout
        self.ping_interval = ping_interval
        self.ping_holdtime = ping_holdtime
        self.max_http_buffer_size = max_http_buffer_size
        self.allow_upgrades = allow_upgrades
        self.http_compression = http_compression
        self.compression_threshold = compression_threshold
        self.cookie = cookie
        self.cors_allowed_origins = cors_allowed_origins
        self.cors_credentials = cors_credentials
        self.sockets = {}
        self.handlers = {}
        if json is not None:
            packet.Packet.json = json
        if not isinstance(logger, bool):
            self.logger = logger
        else:
            self.logger = logging.getLogger('engineio')
            if not logging.root.handlers and \
                    self.logger.level == logging.NOTSET:
                if logger:
                    self.logger.setLevel(logging.INFO)
                else:
                    self.logger.setLevel(logging.ERROR)
                self.logger.addHandler(logging.StreamHandler())
        if async_mode is None:
            modes = ['eventlet', 'gevent', 'threading']
        else:
            modes = [async_mode]
        self.async = None
        self.async_mode = None
        for mode in modes:
            try:
                self.async = importlib.import_module(
                    'engineio.async_' + mode).async
                self.async_mode = mode
                break
            except ImportError:
                pass
        if self.async_mode is None:
            raise ValueError('Invalid async_mode specified')
        self.logger.info('Server initialized for %s.', self.async_mode)

    def on(self, event, handler=None):
        """Register an event handler.

        :param event: The event name. Can be ``'connect'``, ``'message'`` or
                      ``'disconnect'``.
        :param handler: The function that should be invoked to handle the
                        event. When this parameter is not given, the method
                        acts as a decorator for the handler function.

        Example usage::

            # as a decorator:
            @eio.on('connect')
            def connect_handler(sid, environ):
                print('Connection request')
                if environ['REMOTE_ADDR'] in blacklisted:
                    return False  # reject

            # as a method:
            def message_handler(sid, msg):
                print('Received message: ', msg)
                eio.send(sid, 'response')
            eio.on('message', message_handler)

        The handler function receives the ``sid`` (session ID) for the
        client as first argument. The ``'connect'`` event handler receives the
        WSGI environment as a second argument, and can return ``False`` to
        reject the connection. The ``'message'`` handler receives the message
        payload as a second argument. The ``'disconnect'`` handler does not
        take a second argument.
        """
        if event not in self.event_names:
            raise ValueError('Invalid event')

        def set_handler(handler):
            self.handlers[event] = handler
            return handler

        if handler is None:
            return set_handler
        set_handler(handler)

    def send(self, sid, data, binary=None):
        """Send a message to a client.

        :param sid: The session id of the recipient client.
        :param data: The data to send to the client. Data can be of type
                     ``str``, ``bytes``, ``list`` or ``dict``. If a ``list``
                     or ``dict``, the data will be serialized as JSON.
        :param binary: ``True`` to send packet as binary, ``False`` to send
                       as text. If not given, unicode (Python 2) and str
                       (Python 3) are sent as text, and str (Python 2) and
                       bytes (Python 3) are sent as binary.
        """
        try:
            socket = self._get_socket(sid)
        except KeyError:
            # the socket is not available
            self.logger.warning('Cannot send to sid %s', sid)
            return
        socket.send(packet.Packet(packet.MESSAGE, data=data, binary=binary))

    def disconnect(self, sid=None):
        """Disconnect a client.

        :param sid: The session id of the client to close. If this parameter
                    is not given, then all clients are closed.
        """
        if sid is not None:
            self._get_socket(sid).close()
            del self.sockets[sid]
        else:
            for client in six.itervalues(self.sockets):
                client.close()
            self.sockets = {}

    def transport(self, sid):
        """Return the name of the transport used by the client.

        The two possible values returned by this function are ``'polling'``
        and ``'websocket'``.

        :param sid: The session of the client.
        """
        return 'websocket' if self._get_socket(sid).upgraded else 'polling'

    def handle_request(self, environ, start_response):
        """Handle an HTTP request from the client.

        This is the entry point of the Engine.IO application, using the same
        interface as a WSGI application. For the typical usage, this function
        is invoked by the :class:`Middleware` instance, but it can be invoked
        directly when the middleware is not used.

        :param environ: The WSGI environment.
        :param start_response: The WSGI ``start_response`` function.

        This function returns the HTTP response body to deliver to the client
        as a byte sequence.
        """
        method = environ['REQUEST_METHOD']
        query = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))
        if 'j' in query:
            self.logger.warning('JSONP requests are not supported')
            r = self._bad_request()
        else:
            sid = query['sid'][0] if 'sid' in query else None
            b64 = False
            if 'b64' in query:
                if query['b64'][0] == "1" or query['b64'][0].lower() == "true":
                    b64 = True
            if method == 'GET':
                if sid is None:
                    transport = query.get('transport', ['polling'])[0]
                    if transport != 'polling' and transport != 'websocket':
                        self.logger.warning('Invalid transport %s', transport)
                        r = self._bad_request()
                    else:
                        r = self._handle_connect(environ, start_response,
                                                 transport, b64)
                else:
                    if sid not in self.sockets:
                        self.logger.warning('Invalid session %s', sid)
                        r = self._bad_request()
                    else:
                        socket = self._get_socket(sid)
                        try:
                            packets = socket.handle_get_request(
                                environ, start_response)
                            if isinstance(packets, list):
                                r = self._ok(packets, b64=b64)
                            else:
                                r = packets
                        except IOError:
                            if sid in self.sockets:  # pragma: no cover
                                del self.sockets[sid]
                            r = self._bad_request()
                        if sid in self.sockets and self.sockets[sid].closed:
                            del self.sockets[sid]
            elif method == 'POST':
                if sid is None or sid not in self.sockets:
                    self.logger.warning('Invalid session %s', sid)
                    r = self._bad_request()
                else:
                    socket = self._get_socket(sid)
                    try:
                        socket.handle_post_request(environ)
                        r = self._ok()
                    except ValueError:
                        r = self._bad_request()
            else:
                self.logger.warning('Method %s not supported', method)
                r = self._method_not_found()
        if not isinstance(r, dict):
            return r
        if self.http_compression and \
                len(r['response']) >= self.compression_threshold:
            encodings = [e.split(';')[0].strip() for e in
                         environ.get('ACCEPT_ENCODING', '').split(',')]
            for encoding in encodings:
                if encoding in self.compression_methods:
                    r['response'] = \
                        getattr(self, '_' + encoding)(r['response'])
                    r['headers'] += [('Content-Encoding', encoding)]
                    break
        cors_headers = self._cors_headers(environ)
        start_response(r['status'], r['headers'] + cors_headers)
        return [r['response']]

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task using the appropriate async model.

        This is a utility function that applications can use to start a
        background task using the method that is compatible with the
        selected async mode.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        This function returns an object compatible with the `Thread` class in
        the Python standard library. The `start()` method on this object is
        already called by this function.
        """
        th = getattr(self.async['threading'],
                     self.async['thread_class'])(target=target, args=args,
                                                 kwargs=kwargs)
        th.start()
        return th  # pragma: no cover

    def _generate_id(self):
        """Generate a unique session id."""
        return uuid.uuid4().hex

    def _handle_connect(self, environ, start_response, transport, b64=False):
        """Handle a client connection request."""
        sid = self._generate_id()
        s = socket.Socket(self, sid)
        self.sockets[sid] = s

        pkt = packet.Packet(
            packet.OPEN, {'sid': sid,
                          'upgrades': self._upgrades(sid, transport),
                          'pingTimeout': int(self.ping_timeout * 1000),
                          'pingInterval': int(self.ping_interval * 1000)})
        s.send(pkt)

        if self._trigger_event('connect', sid, environ) is False:
            self.logger.warning('Application rejected connection')
            del self.sockets[sid]
            return self._unauthorized()

        if transport == 'websocket':
            return s.handle_get_request(environ, start_response)
        else:
            s.connected = True
            headers = None
            if self.cookie:
                headers = [('Set-Cookie', self.cookie + '=' + sid)]
            return self._ok(s.poll(), headers=headers, b64=b64)

    def _upgrades(self, sid, transport):
        """Return the list of possible upgrades for a client connection."""
        if not self.allow_upgrades or self._get_socket(sid).upgraded or \
                self.async['websocket_class'] is None or \
                transport == 'websocket':
            return []
        return ['websocket']

    def _trigger_event(self, event, *args):
        """Invoke an event handler."""
        if event in self.handlers:
            return self.handlers[event](*args)

    def _get_socket(self, sid):
        """Return the socket object for a given session."""
        try:
            s = self.sockets[sid]
        except KeyError:
            raise KeyError('Session not found')
        if s.closed:
            del self.sockets[sid]
            raise KeyError('Session is disconnected')
        return s

    def _ok(self, packets=None, headers=None, b64=False):
        """Generate a successful HTTP response."""
        if packets is not None:
            if headers is None:
                headers = []
            headers += [('Content-Type', 'application/octet-stream')]
            return {'status': '200 OK',
                    'headers': headers,
                    'response': payload.Payload(packets=packets).encode(b64)}
        else:
            return {'status': '200 OK',
                    'headers': [('Content-Type', 'text/plain')],
                    'response': b'OK'}

    def _bad_request(self):
        """Generate a bad request HTTP error response."""
        return {'status': '400 BAD REQUEST',
                'headers': [('Content-Type', 'text/plain')],
                'response': b'Bad Request'}

    def _method_not_found(self):
        """Generate a method not found HTTP error response."""
        return {'status': '405 METHOD NOT FOUND',
                'headers': [('Content-Type', 'text/plain')],
                'response': b'Method Not Found'}

    def _unauthorized(self):
        """Generate a unauthorized HTTP error response."""
        return {'status': '401 UNAUTHORIZED',
                'headers': [('Content-Type', 'text/plain')],
                'response': b'Unauthorized'}

    def _cors_headers(self, environ):
        """Return the cross-origin-resource-sharing headers."""
        if self.cors_allowed_origins is not None and \
                environ.get('HTTP_ORIGIN', '') not in \
                self.cors_allowed_origins:
            return []
        if 'HTTP_ORIGIN' in environ:
            headers = [('Access-Control-Allow-Origin', environ['HTTP_ORIGIN'])]
        else:
            headers = [('Access-Control-Allow-Origin', '*')]
        if self.cors_credentials:
            headers += [('Access-Control-Allow-Credentials', 'true')]
        return headers

    def _gzip(self, response):
        """Apply gzip compression to a response."""
        bytesio = six.BytesIO()
        with gzip.GzipFile(fileobj=bytesio, mode='w') as gz:
            gz.write(response)
        return bytesio.getvalue()

    def _deflate(self, response):
        """Apply deflate compression to a response."""
        return zlib.compress(response)
