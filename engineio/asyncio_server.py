import asyncio

import six
from six.moves import urllib

from .exceptions import EngineIOError
from . import packet
from . import server
from . import asyncio_socket


class AsyncServer(server.Server):
    """An Engine.IO server for asyncio.

    This class implements a fully compliant Engine.IO web server with support
    for websocket and long-polling transports, compatible with the asyncio
    framework on Python 3.5 or newer.

    :param async_mode: The asynchronous model to use. See the Deployment
                       section in the documentation for a description of the
                       available options. Valid async modes are "aiohttp". If
                       this argument is not given, an async mode is chosen
                       based on the installed packages.
    :param ping_timeout: The time in seconds that the client waits for the
                         server to respond before disconnecting.
    :param ping_interval: The interval in seconds at which the client pings
                          the server.
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
    :param async_handlers: If set to ``True``, run message event handlers in
                           non-blocking threads. To run handlers synchronously,
                           set to ``False``. The default is ``True``.
    :param kwargs: Reserved for future extensions, any additional parameters
                   given as keyword arguments will be silently ignored.
    """
    def is_asyncio_based(self):
        return True

    def async_modes(self):
        return ['aiohttp', 'sanic']

    def attach(self, app, engineio_path='engine.io'):
        """Attach the Engine.IO server to an application."""
        engineio_path = engineio_path.strip('/')
        self._async['create_route'](app, self, '/{}/'.format(engineio_path))

    async def send(self, sid, data, binary=None):
        """Send a message to a client.

        :param sid: The session id of the recipient client.
        :param data: The data to send to the client. Data can be of type
                     ``str``, ``bytes``, ``list`` or ``dict``. If a ``list``
                     or ``dict``, the data will be serialized as JSON.
        :param binary: ``True`` to send packet as binary, ``False`` to send
                       as text. If not given, unicode (Python 2) and str
                       (Python 3) are sent as text, and str (Python 2) and
                       bytes (Python 3) are sent as binary.

        Note: this method is a coroutine.
        """
        try:
            socket = self._get_socket(sid)
        except KeyError:
            # the socket is not available
            self.logger.warning('Cannot send to sid %s', sid)
            return
        await socket.send(packet.Packet(packet.MESSAGE, data=data,
                                        binary=binary))

    async def disconnect(self, sid=None):
        """Disconnect a client.

        :param sid: The session id of the client to close. If this parameter
                    is not given, then all clients are closed.

        Note: this method is a coroutine.
        """
        if sid is not None:
            try:
                socket = self._get_socket(sid)
            except KeyError:  # pragma: no cover
                # the socket was already closed or gone
                pass
            else:
                await socket.close()
                del self.sockets[sid]
        else:
            await asyncio.wait([client.close()
                                for client in six.itervalues(self.sockets)])
            self.sockets = {}

    async def handle_request(self, *args, **kwargs):
        """Handle an HTTP request from the client.

        This is the entry point of the Engine.IO application. This function
        returns the HTTP response to deliver to the client.

        Note: this method is a coroutine.
        """
        environ = self._async['translate_request'](*args, **kwargs)
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
                        r = await self._handle_connect(environ, transport,
                                                       b64)
                else:
                    if sid not in self.sockets:
                        self.logger.warning('Invalid session %s', sid)
                        r = self._bad_request()
                    else:
                        socket = self._get_socket(sid)
                        try:
                            packets = await socket.handle_get_request(environ)
                            if isinstance(packets, list):
                                r = self._ok(packets, b64=b64)
                            else:
                                r = packets
                        except EngineIOError:
                            if sid in self.sockets:  # pragma: no cover
                                await self.disconnect(sid)
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
                        await socket.handle_post_request(environ)
                        r = self._ok()
                    except EngineIOError:
                        if sid in self.sockets:  # pragma: no cover
                            await self.disconnect(sid)
                        r = self._bad_request()
                    except:  # pragma: no cover
                        # for any other unexpected errors, we log the error
                        # and keep going
                        self.logger.exception('post request handler error')
                        r = self._ok()
            else:
                self.logger.warning('Method %s not supported', method)
                r = self._method_not_found()
        if not isinstance(r, dict):
            return r if r is not None else []
        if self.http_compression and \
                len(r['response']) >= self.compression_threshold:
            encodings = [e.split(';')[0].strip() for e in
                         environ.get('HTTP_ACCEPT_ENCODING', '').split(',')]
            for encoding in encodings:
                if encoding in self.compression_methods:
                    r['response'] = \
                        getattr(self, '_' + encoding)(r['response'])
                    r['headers'] += [('Content-Encoding', encoding)]
                    break
        cors_headers = self._cors_headers(environ)
        return self._async['make_response'](r['status'],
                                            r['headers'] + cors_headers,
                                            r['response'])

    def start_background_task(self, target, *args, **kwargs):
        """Start a background task using the appropriate async model.

        This is a utility function that applications can use to start a
        background task using the method that is compatible with the
        selected async mode.

        :param target: the target function to execute.
        :param args: arguments to pass to the function.
        :param kwargs: keyword arguments to pass to the function.

        The return value is a ``asyncio.Task`` object.
        """
        return asyncio.ensure_future(target(*args, **kwargs))

    async def sleep(self, seconds=0):
        """Sleep for the requested amount of time using the appropriate async
        model.

        This is a utility function that applications can use to put a task to
        sleep without having to worry about using the correct call for the
        selected async mode.

        Note: this method is a coroutine.
        """
        return await asyncio.sleep(seconds)

    async def _handle_connect(self, environ, transport, b64=False):
        """Handle a client connection request."""
        sid = self._generate_id()
        s = asyncio_socket.AsyncSocket(self, sid)
        self.sockets[sid] = s

        pkt = packet.Packet(
            packet.OPEN, {'sid': sid,
                          'upgrades': self._upgrades(sid, transport),
                          'pingTimeout': int(self.ping_timeout * 1000),
                          'pingInterval': int(self.ping_interval * 1000)})
        await s.send(pkt)

        ret = await self._trigger_event('connect', sid, environ,
                                        run_async=False)
        if ret is False:
            del self.sockets[sid]
            self.logger.warning('Application rejected connection')
            return self._unauthorized()

        if transport == 'websocket':
            ret = await s.handle_get_request(environ)
            if s.closed:
                # websocket connection ended, so we are done
                del self.sockets[sid]
            return ret
        else:
            s.connected = True
            headers = None
            if self.cookie:
                headers = [('Set-Cookie', self.cookie + '=' + sid)]
            return self._ok(await s.poll(), headers=headers, b64=b64)

    async def _trigger_event(self, event, *args, **kwargs):
        """Invoke an event handler."""
        run_async = kwargs.pop('run_async', False)
        ret = None
        if event in self.handlers:
            if asyncio.iscoroutinefunction(self.handlers[event]) is True:
                if run_async:
                    return self.start_background_task(self.handlers[event],
                                                      *args)
                else:
                    try:
                        ret = await self.handlers[event](*args)
                    except asyncio.CancelledError:  # pragma: no cover
                        pass
                    except:
                        self.logger.exception(event + ' async handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
            else:
                if run_async:
                    async def async_handler():
                        return self.handlers[event](*args)

                    return self.start_background_task(async_handler)
                else:
                    try:
                        ret = self.handlers[event](*args)
                    except:
                        self.logger.exception(event + ' handler error')
                        if event == 'connect':
                            # if connect handler raised error we reject the
                            # connection
                            return False
        return ret
