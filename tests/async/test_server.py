import asyncio
import gzip
import io
import logging
from unittest import mock
import zlib

import pytest

from engineio import async_server
from engineio.async_drivers import aiohttp as async_aiohttp
from engineio import exceptions
from engineio import json
from engineio import packet
from engineio import payload


class TestAsyncServer:
    @staticmethod
    def get_async_mock(environ={'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}):
        if environ.get('QUERY_STRING'):
            if 'EIO=' not in environ['QUERY_STRING']:
                environ['QUERY_STRING'] = 'EIO=4&' + environ['QUERY_STRING']
        else:
            environ['QUERY_STRING'] = 'EIO=4'
        a = mock.MagicMock()
        a._async = {
            'asyncio': True,
            'create_route': mock.MagicMock(),
            'translate_request': mock.MagicMock(),
            'make_response': mock.MagicMock(),
            'websocket': 'w',
        }
        a._async['translate_request'].return_value = environ
        a._async['make_response'].return_value = 'response'
        return a

    def _get_mock_socket(self):
        mock_socket = mock.MagicMock()
        mock_socket.connected = False
        mock_socket.closed = False
        mock_socket.closing = False
        mock_socket.upgraded = False
        mock_socket.send = mock.AsyncMock()
        mock_socket.handle_get_request = mock.AsyncMock()
        mock_socket.handle_post_request = mock.AsyncMock()
        mock_socket.check_ping_timeout = mock.AsyncMock()
        mock_socket.close = mock.AsyncMock()
        mock_socket.session = {}
        return mock_socket

    @classmethod
    def setup_class(cls):
        async_server.AsyncServer._default_monitor_clients = False

    @classmethod
    def teardown_class(cls):
        async_server.AsyncServer._default_monitor_clients = True

    def setup_method(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def teardown_method(self):
        # restore JSON encoder, in case a test changed it
        packet.Packet.json = json

    async def test_is_asyncio_based(self):
        s = async_server.AsyncServer()
        assert s.is_asyncio_based()

    async def test_async_modes(self):
        s = async_server.AsyncServer()
        assert s.async_modes() == ['aiohttp', 'sanic', 'tornado', 'asgi']

    async def test_async_mode_aiohttp(self):
        s = async_server.AsyncServer(async_mode='aiohttp')
        assert s.async_mode == 'aiohttp'
        assert s._async['asyncio']
        assert s._async['create_route'] == async_aiohttp.create_route
        assert s._async['translate_request'] == async_aiohttp.translate_request
        assert s._async['make_response'] == async_aiohttp.make_response
        assert s._async['websocket'].__name__ == 'WebSocket'

    @mock.patch('importlib.import_module')
    async def test_async_mode_auto_aiohttp(self, import_module):
        import_module.side_effect = [self.get_async_mock()]
        s = async_server.AsyncServer()
        assert s.async_mode == 'aiohttp'

    async def test_async_modes_wsgi(self):
        with pytest.raises(ValueError):
            async_server.AsyncServer(async_mode='eventlet')
        with pytest.raises(ValueError):
            async_server.AsyncServer(async_mode='gevent')
        with pytest.raises(ValueError):
            async_server.AsyncServer(async_mode='gevent_uwsgi')
        with pytest.raises(ValueError):
            async_server.AsyncServer(async_mode='threading')

    @mock.patch('importlib.import_module')
    async def test_attach(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.attach('app', engineio_path='abc')
        a._async['create_route'].assert_called_with('app', s, '/abc/')
        s.attach('app', engineio_path='/def/')
        a._async['create_route'].assert_called_with('app', s, '/def/')
        s.attach('app', engineio_path='/ghi')
        a._async['create_route'].assert_called_with('app', s, '/ghi/')
        s.attach('app', engineio_path='jkl/')
        a._async['create_route'].assert_called_with('app', s, '/jkl/')

    async def test_session(self):
        s = async_server.AsyncServer()
        s.sockets['foo'] = self._get_mock_socket()

        async def _func():
            async with s.session('foo') as session:
                await s.sleep(0)
                session['username'] = 'bar'
            assert await s.get_session('foo') == {'username': 'bar'}

        await _func()

    async def test_disconnect(self):
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        await s.disconnect('foo')
        assert mock_socket.close.await_count == 1
        mock_socket.close.assert_awaited_once_with(
            reason=s.reason.SERVER_DISCONNECT)
        assert 'foo' not in s.sockets

    async def test_disconnect_all(self):
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_foo = self._get_mock_socket()
        s.sockets['bar'] = mock_bar = self._get_mock_socket()
        await s.disconnect()
        assert mock_foo.close.await_count == 1
        assert mock_bar.close.await_count == 1
        mock_foo.close.assert_awaited_once_with(
            reason=s.reason.SERVER_DISCONNECT)
        mock_bar.close.assert_awaited_once_with(
            reason=s.reason.SERVER_DISCONNECT)
        assert 'foo' not in s.sockets
        assert 'bar' not in s.sockets

    @mock.patch('importlib.import_module')
    async def test_jsonp_not_supported(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'j=abc'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        response = await s.handle_request('request')
        assert response == 'response'
        a._async['translate_request'].assert_called_once_with('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_jsonp_index(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'j=233'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        response = await s.handle_request('request')
        assert response == 'response'
        a._async['translate_request'].assert_called_once_with('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        assert (
            a._async['make_response']
            .call_args[0][2]
            .startswith(b'___eio[233]("')
        )
        assert a._async['make_response'].call_args[0][2].endswith(b'");')

    @mock.patch('importlib.import_module')
    async def test_connect(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert len(s.sockets) == 1
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        assert ('Content-Type', 'text/plain; charset=UTF-8') in a._async[
            'make_response'
        ].call_args[0][1]
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2].decode(
                'utf-8')).packets
        assert len(packets) == 1
        assert packets[0].packet_type == packet.OPEN
        assert 'upgrades' in packets[0].data
        assert packets[0].data['upgrades'] == ['websocket']
        assert 'sid' in packets[0].data
        assert packets[0].data['pingTimeout'] == 20000
        assert packets[0].data['pingInterval'] == 25000
        assert packets[0].data['maxPayload'] == 1000000

    @mock.patch('importlib.import_module')
    async def test_connect_async_request_response_handlers(
            self, import_module):
        a = self.get_async_mock()
        a._async['translate_request'] = mock.AsyncMock(
            return_value=a._async['translate_request'].return_value
        )
        a._async['make_response'] = mock.AsyncMock(
            return_value=a._async['make_response'].return_value
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert len(s.sockets) == 1
        assert a._async['make_response'].await_count == 1
        assert a._async['make_response'].await_args[0][0] == '200 OK'
        assert ('Content-Type', 'text/plain; charset=UTF-8') in a._async[
            'make_response'
        ].await_args[0][1]
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].await_args[0][
                2].decode('utf-8')).packets
        assert len(packets) == 1
        assert packets[0].packet_type == packet.OPEN
        assert 'upgrades' in packets[0].data
        assert packets[0].data['upgrades'] == ['websocket']
        assert 'sid' in packets[0].data

    @mock.patch('importlib.import_module')
    async def test_connect_no_upgrades(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(allow_upgrades=False)
        await s.handle_request('request')
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2].decode(
                'utf-8')).packets
        assert packets[0].data['upgrades'] == []

    @mock.patch('importlib.import_module')
    async def test_connect_bad_eio_version(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=1'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'
        assert b'unsupported version' in \
            a._async['make_response'].call_args[0][2]

    @mock.patch('importlib.import_module')
    async def test_connect_custom_ping_times(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(ping_timeout=123, ping_interval=456,
                                     max_http_buffer_size=12345678)
        await s.handle_request('request')
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2].decode(
                'utf-8')).packets
        assert packets[0].data['pingTimeout'] == 123000
        assert packets[0].data['pingInterval'] == 456000
        assert packets[0].data['maxPayload'] == 12345678

    @mock.patch('importlib.import_module')
    @mock.patch('engineio.async_server.async_socket.AsyncSocket')
    async def test_connect_bad_poll(self, AsyncSocket, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        AsyncSocket.return_value.poll.side_effect = [exceptions.QueueEmpty]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    @mock.patch('engineio.async_server.async_socket.AsyncSocket')
    async def test_connect_transport_websocket(self, AsyncSocket,
                                               import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'transport=websocket',
                'HTTP_UPGRADE': 'websocket',
            }
        )
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')
        # force socket to stay open, so that we can check it later
        AsyncSocket().closed = False
        await s.handle_request('request')
        assert (
            s.sockets['123'].send.await_args[0][0].packet_type
            == packet.OPEN
        )

    @mock.patch('importlib.import_module')
    @mock.patch('engineio.async_server.async_socket.AsyncSocket')
    async def test_http_upgrade_case_insensitive(self, AsyncSocket,
                                                 import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'transport=websocket',
                'HTTP_UPGRADE': 'WebSocket',
            }
        )
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')
        # force socket to stay open, so that we can check it later
        AsyncSocket().closed = False
        await s.handle_request('request')
        assert (
            s.sockets['123'].send.await_args[0][0].packet_type
            == packet.OPEN
        )

    @mock.patch('importlib.import_module')
    @mock.patch('engineio.async_server.async_socket.AsyncSocket')
    async def test_connect_transport_websocket_closed(
            self, AsyncSocket, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'transport=websocket',
                'HTTP_UPGRADE': 'websocket'
            }
        )
        import_module.side_effect = [a]
        AsyncSocket.return_value = self._get_mock_socket()
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')

        # this mock handler just closes the socket, as it would happen on a
        # real websocket exchange
        async def mock_handle(environ):
            s.sockets['123'].closed = True

        AsyncSocket().handle_get_request = mock_handle
        await s.handle_request('request')
        assert '123' not in s.sockets  # socket should close on its own

    @mock.patch('importlib.import_module')
    async def test_connect_transport_invalid(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'transport=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_connect_transport_websocket_without_upgrade(
            self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'transport=websocket'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_connect_cors_headers(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_allowed_origin(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'b'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=['a', 'b'])
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'b') in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_allowed_origin_with_callable(
            self, import_module):
        def cors(origin):
            return origin == 'a'

        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': '',
            'HTTP_ORIGIN': 'a'
        }
        a = self.get_async_mock(environ)
        import_module.side_effect = [a]

        s = async_server.AsyncServer(cors_allowed_origins=cors)
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'a') in headers

        environ['HTTP_ORIGIN'] = 'b'
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_connect_cors_not_allowed_origin(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'c'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=['a', 'b'])
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'c') not in headers
        assert ('Access-Control-Allow-Origin', '*') not in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_not_allowed_origin_async_response(
        self, import_module
    ):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'c'}
        )
        a._async['make_response'] = mock.AsyncMock(
            return_value=a._async['make_response'].return_value
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=['a', 'b'])
        await s.handle_request('request')
        assert (
            a._async['make_response'].await_args[0][0] == '400 BAD REQUEST'
        )
        headers = a._async['make_response'].await_args[0][1]
        assert ('Access-Control-Allow-Origin', 'c') not in headers
        assert ('Access-Control-Allow-Origin', '*') not in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_all_origins(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins='*')
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'foo') in headers
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_one_origin(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'a'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins='a')
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'a') in headers
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_one_origin_not_allowed(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'HTTP_ORIGIN': 'b'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins='a')
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'b') not in headers
        assert ('Access-Control-Allow-Origin', '*') not in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_headers_default_origin(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': '',
                'wsgi.url_scheme': 'http',
                'HTTP_HOST': 'foo',
                'HTTP_ORIGIN': 'http://foo',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'http://foo') in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_no_credentials(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_credentials=False)
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert ('Access-Control-Allow-Credentials', 'true') not in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_options(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'OPTIONS', 'QUERY_STRING': ''}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_credentials=False)
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        assert (
            'Access-Control-Allow-Methods',
            'OPTIONS, GET, POST',
        ) in headers

    @mock.patch('importlib.import_module')
    async def test_connect_cors_disabled(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': '',
                'HTTP_ORIGIN': 'http://foo',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=[])
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        for header in headers:
            assert not header[0].startswith('Access-Control-')

    @mock.patch('importlib.import_module')
    async def test_connect_cors_default_no_origin(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=[])
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    @mock.patch('importlib.import_module')
    async def test_connect_cors_all_no_origin(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins='*')
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    @mock.patch('importlib.import_module')
    async def test_connect_cors_disabled_no_origin(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cors_allowed_origins=[])
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        headers = a._async['make_response'].call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    @mock.patch('importlib.import_module')
    async def test_connect_event(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')

        def mock_connect(sid, environ):
            return True

        s.on('connect', handler=mock_connect)
        await s.handle_request('request')
        assert len(s.sockets) == 1

    @mock.patch('importlib.import_module')
    async def test_connect_event_rejects(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')

        def mock_connect(sid, environ):
            return False

        s.on('connect')(mock_connect)
        await s.handle_request('request')
        assert len(s.sockets) == 0
        assert a._async['make_response'].call_args[0][0] == '401 UNAUTHORIZED'
        assert a._async['make_response'].call_args[0][2] == b'"Unauthorized"'

    @mock.patch('importlib.import_module')
    async def test_connect_event_rejects_with_message(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.generate_id = mock.MagicMock(return_value='123')

        def mock_connect(sid, environ):
            return {'not': 'allowed'}

        s.on('connect')(mock_connect)
        await s.handle_request('request')
        assert len(s.sockets) == 0
        assert a._async['make_response'].call_args[0][0] == '401 UNAUTHORIZED'
        assert (
            a._async['make_response'].call_args[0][2] == b'{"not": "allowed"}'
        )

    @mock.patch('importlib.import_module')
    async def test_method_not_found(self, import_module):
        a = self.get_async_mock({'REQUEST_METHOD': 'PUT', 'QUERY_STRING': ''})
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert len(s.sockets) == 0
        assert (
            a._async['make_response'].call_args[0][0] == '405 METHOD NOT FOUND'
        )

    @mock.patch('importlib.import_module')
    async def test_get_request_with_bad_sid(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert len(s.sockets) == 0
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_get_request_bad_websocket_transport(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET',
             'QUERY_STRING': 'EIO=4&transport=websocket&sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.upgraded = False
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_get_request_bad_polling_transport(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET',
             'QUERY_STRING': 'EIO=4&transport=polling&sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.upgraded = True
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_post_request_with_bad_sid(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        await s.handle_request('request')
        assert len(s.sockets) == 0
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @mock.patch('importlib.import_module')
    async def test_send(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        await s.send('foo', 'hello')
        assert mock_socket.send.await_count == 1
        assert (
            mock_socket.send.await_args[0][0].packet_type == packet.MESSAGE
        )
        assert mock_socket.send.await_args[0][0].data == 'hello'

    @mock.patch('importlib.import_module')
    async def test_send_unknown_socket(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        # just ensure no exceptions are raised
        await s.send('foo', 'hello')

    @mock.patch('importlib.import_module')
    async def test_get_request(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'
        packets = payload.Payload(
            encoded_payload=a._async['make_response'].call_args[0][2].decode(
                'utf-8')
        ).packets
        assert len(packets) == 1
        assert packets[0].packet_type == packet.MESSAGE

    @mock.patch('importlib.import_module')
    async def test_get_request_custom_response(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = 'resp'
        r = await s.handle_request('request')
        assert r == 'resp'

    @mock.patch('importlib.import_module')
    async def test_get_request_closes_socket(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        async def mock_get_request(*args, **kwargs):
            mock_socket.closed = True
            return 'resp'

        mock_socket.handle_get_request = mock_get_request
        r = await s.handle_request('request')
        assert r == 'resp'
        assert 'foo' not in s.sockets

    @mock.patch('importlib.import_module')
    async def test_get_request_error(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        async def mock_get_request(*args, **kwargs):
            raise exceptions.QueueEmpty()

        mock_socket.handle_get_request = mock_get_request
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'
        assert len(s.sockets) == 0

    @mock.patch('importlib.import_module')
    async def test_post_request(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = self._get_mock_socket()
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '200 OK'

    @mock.patch('importlib.import_module')
    async def test_post_request_error(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()

        async def mock_post_request(*args, **kwargs):
            raise exceptions.ContentTooLongError()

        mock_socket.handle_post_request = mock_post_request
        await s.handle_request('request')
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'

    @staticmethod
    def _gzip_decompress(b):
        bytesio = io.BytesIO(b)
        with gzip.GzipFile(fileobj=bytesio, mode='r') as gz:
            return gz.read()

    @mock.patch('importlib.import_module')
    async def test_gzip_compression(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': 'gzip,deflate',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        assert ('Content-Encoding', 'gzip') in headers
        self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_deflate_compression(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': 'deflate;q=1,gzip',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        assert ('Content-Encoding', 'deflate') in headers
        zlib.decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_gzip_compression_threshold(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': 'gzip',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(compression_threshold=1000)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            print(a._async['make_response'].call_args[0][2])
            self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_compression_disabled(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': 'gzip',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(
            http_compression=False, compression_threshold=0
        )
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_compression_unknown(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': 'rar',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_compression_no_encoding(self, import_module):
        a = self.get_async_mock(
            {
                'REQUEST_METHOD': 'GET',
                'QUERY_STRING': 'sid=foo',
                'HTTP_ACCEPT_ENCODING': '',
            }
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(compression_threshold=0)
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request.return_value = [
            packet.Packet(packet.MESSAGE, data='hello')
        ]
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(a._async['make_response'].call_args[0][2])

    @mock.patch('importlib.import_module')
    async def test_cookie(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cookie='sid')
        s.generate_id = mock.MagicMock(return_value='123')
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        assert ('Set-Cookie', 'sid=123; path=/; SameSite=Lax') in headers

    @mock.patch('importlib.import_module')
    async def test_cookie_dict(self, import_module):
        def get_path():
            return '/a'

        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cookie={
            'name': 'test',
            'path': get_path,
            'SameSite': 'None',
            'Secure': True,
            'HttpOnly': True
        })
        s.generate_id = mock.MagicMock(return_value='123')
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        assert ('Set-Cookie', 'test=123; path=/a; SameSite=None; Secure; '
                'HttpOnly') in headers

    @mock.patch('importlib.import_module')
    async def test_no_cookie(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(cookie=None)
        s.generate_id = mock.MagicMock(return_value='123')
        await s.handle_request('request')
        headers = a._async['make_response'].call_args[0][1]
        for header, value in headers:
            assert header != 'Set-Cookie'

    async def test_logger(self):
        s = async_server.AsyncServer(logger=False)
        assert s.logger.getEffectiveLevel() == logging.ERROR
        s.logger.setLevel(logging.NOTSET)
        s = async_server.AsyncServer(logger=True)
        assert s.logger.getEffectiveLevel() == logging.INFO
        s.logger.setLevel(logging.WARNING)
        s = async_server.AsyncServer(logger=True)
        assert s.logger.getEffectiveLevel() == logging.WARNING
        s.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        s = async_server.AsyncServer(logger=my_logger)
        assert s.logger == my_logger

    async def test_custom_json(self):
        # Warning: this test cannot run in parallel with other tests, as it
        # changes the JSON encoding/decoding functions

        class CustomJSON:
            @staticmethod
            def dumps(*args, **kwargs):
                return '*** encoded ***'

            @staticmethod
            def loads(*args, **kwargs):
                return '+++ decoded +++'

        async_server.AsyncServer(json=CustomJSON)
        pkt = packet.Packet(packet.MESSAGE, data={'foo': 'bar'})
        assert pkt.encode() == '4*** encoded ***'
        pkt2 = packet.Packet(encoded_packet=pkt.encode())
        assert pkt2.data == '+++ decoded +++'

        # restore the default JSON module
        packet.Packet.json = json

    async def test_background_tasks(self):
        r = []

        async def foo(arg):
            r.append(arg)

        async def main():
            s = async_server.AsyncServer()
            task = s.start_background_task(foo, 'bar')
            await task

        await main()
        assert r == ['bar']

    async def test_sleep(self):
        s = async_server.AsyncServer()
        await s.sleep(0)

    async def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        await s._trigger_event('message', 'bar')
        assert result == ['ok', 'bar']

    async def test_trigger_event_coroutine(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        await s._trigger_event('message', 'bar')
        assert result == ['ok', 'bar']

    async def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        s = async_server.AsyncServer()
        s.on('connect', handler=connect_handler)
        s.on('message', handler=foo_handler)
        assert not await s._trigger_event('connect', '123')
        assert await s._trigger_event('message', 'bar') is None

    async def test_trigger_event_coroutine_error(self):
        async def connect_handler(arg):
            return 1 / 0

        async def foo_handler(arg):
            return 1 / 0

        s = async_server.AsyncServer()
        s.on('connect', handler=connect_handler)
        s.on('message', handler=foo_handler)
        assert not await s._trigger_event('connect', '123')
        assert await s._trigger_event('message', 'bar') is None

    async def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = await s._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['ok', 'bar']

    async def test_trigger_event_coroutine_async(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = await s._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['ok', 'bar']

    async def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = await s._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['bar']

    async def test_trigger_event_coroutine_async_error(self):
        result = []

        async def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        s = async_server.AsyncServer()
        s.on('message', handler=foo_handler)
        fut = await s._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['bar']

    async def test_trigger_legacy_disconnect_event(self):
        s = async_server.AsyncServer()

        @s.on('disconnect')
        def baz(sid):
            return sid

        r = await s._trigger_event('disconnect', 'foo', 'bar')
        assert r == 'foo'

    async def test_trigger_legacy_disconnect_event_async(self):
        s = async_server.AsyncServer()

        @s.on('disconnect')
        async def baz(sid):
            return sid

        r = await s._trigger_event('disconnect', 'foo', 'bar')
        assert r == 'foo'

    async def test_create_queue(self):
        s = async_server.AsyncServer()
        q = s.create_queue()
        empty = s.get_queue_empty_exception()
        with pytest.raises(empty):
            q.get_nowait()

    async def test_create_event(self):
        s = async_server.AsyncServer()
        e = s.create_event()
        assert not e.is_set()
        e.set()
        assert e.is_set()

    @mock.patch('importlib.import_module')
    async def test_service_task_started(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(monitor_clients=True)
        s._service_task = mock.AsyncMock()
        await s.handle_request('request')
        await asyncio.sleep(0)
        s._service_task.assert_awaited_once_with()

    @mock.patch('importlib.import_module')
    async def test_shutdown(self, import_module):
        a = self.get_async_mock()
        import_module.side_effect = [a]
        s = async_server.AsyncServer(monitor_clients=True)
        await s.handle_request('request')
        await asyncio.sleep(0)
        assert s.service_task_handle is not None
        await s.shutdown()
        assert s.service_task_handle is None

    @mock.patch('importlib.import_module')
    async def test_transports_disallowed(self, import_module):
        a = self.get_async_mock(
            {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'transport=polling'}
        )
        import_module.side_effect = [a]
        s = async_server.AsyncServer(transports='websocket')
        response = await s.handle_request('request')
        assert response == 'response'
        a._async['translate_request'].assert_called_once_with('request')
        assert a._async['make_response'].call_count == 1
        assert a._async['make_response'].call_args[0][0] == '400 BAD REQUEST'
