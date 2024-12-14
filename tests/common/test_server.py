import gzip
import importlib
import io
import logging
import sys
import time
from unittest import mock
import zlib

import pytest

from engineio import exceptions
from engineio import json
from engineio import packet
from engineio import payload
from engineio import server

original_import_module = importlib.import_module


def _mock_import(module, *args, **kwargs):
    if module.startswith('engineio.'):
        return original_import_module(module, *args, **kwargs)
    return module


class TestServer:
    _mock_async = mock.MagicMock()
    _mock_async._async = {
        'thread': 't',
        'queue': 'q',
        'queue_empty': RuntimeError,
        'websocket': 'w',
    }

    def _get_mock_socket(self):
        mock_socket = mock.MagicMock()
        mock_socket.closed = False
        mock_socket.closing = False
        mock_socket.upgraded = False
        mock_socket.session = {}
        return mock_socket

    @classmethod
    def setup_class(cls):
        server.Server._default_monitor_clients = False

    @classmethod
    def teardown_class(cls):
        server.Server._default_monitor_clients = True

    def setup_method(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def teardown_method(self):
        # restore JSON encoder, in case a test changed it
        packet.Packet.json = json

    def test_is_asyncio_based(self):
        s = server.Server()
        assert not s.is_asyncio_based()

    def test_async_modes(self):
        s = server.Server()
        assert s.async_modes() == [
            'eventlet',
            'gevent_uwsgi',
            'gevent',
            'threading',
        ]

    def test_create(self):
        kwargs = {
            'ping_timeout': 1,
            'ping_interval': 2,
            'max_http_buffer_size': 3,
            'allow_upgrades': False,
            'http_compression': False,
            'compression_threshold': 4,
            'cookie': 'foo',
            'cors_allowed_origins': ['foo', 'bar', 'baz'],
            'cors_credentials': False,
            'async_handlers': False,
        }
        s = server.Server(**kwargs)
        for arg in kwargs.keys():
            assert getattr(s, arg) == kwargs[arg]
        assert s.ping_interval_grace_period == 0

    def test_create_with_grace_period(self):
        s = server.Server(ping_interval=(1, 2))
        assert s.ping_interval == 1
        assert s.ping_interval_grace_period == 2

    def test_create_ignores_kwargs(self):
        server.Server(foo='bar')  # this should not raise

    def test_async_mode_threading(self):
        sys.modules['simple_websocket'] = mock.MagicMock()
        s = server.Server(async_mode='threading')
        assert s.async_mode == 'threading'

        from engineio.async_drivers import threading as async_threading
        import queue

        assert s._async['thread'] == async_threading.DaemonThread
        assert s._async['queue'] == queue.Queue
        assert s._async['websocket'] == async_threading.SimpleWebSocketWSGI
        del sys.modules['simple_websocket']
        del sys.modules['engineio.async_drivers.threading']

    def test_async_mode_eventlet(self):
        sys.modules['eventlet'] = mock.MagicMock()
        sys.modules['eventlet'].green = mock.MagicMock()
        sys.modules['eventlet.green'] = sys.modules['eventlet'].green
        sys.modules['eventlet.green'].threading = mock.MagicMock()
        sys.modules['eventlet.green.threading'] = \
            sys.modules['eventlet.green'].threading
        sys.modules['eventlet'].websocket = mock.MagicMock()
        sys.modules['eventlet.websocket'] = sys.modules['eventlet'].websocket
        s = server.Server(async_mode='eventlet')
        assert s.async_mode == 'eventlet'

        from eventlet import queue
        from engineio.async_drivers import eventlet as async_eventlet

        assert s._async['thread'] == async_eventlet.EventletThread
        assert s._async['queue'] == queue.Queue
        assert s._async['websocket'] == async_eventlet.WebSocketWSGI
        del sys.modules['eventlet']
        del sys.modules['eventlet.green']
        del sys.modules['eventlet.green.threading']
        del sys.modules['eventlet.websocket']
        del sys.modules['engineio.async_drivers.eventlet']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['gevent'].queue = mock.MagicMock()
        sys.modules['gevent.queue'] = sys.modules['gevent'].queue
        sys.modules['gevent.queue'].JoinableQueue = 'foo'
        sys.modules['gevent.queue'].Empty = RuntimeError
        sys.modules['gevent.event'] = mock.MagicMock()
        sys.modules['gevent.event'].Event = 'bar'
        sys.modules['uwsgi'] = mock.MagicMock()
        s = server.Server(async_mode='gevent_uwsgi')
        assert s.async_mode == 'gevent_uwsgi'

        from engineio.async_drivers import gevent_uwsgi as async_gevent_uwsgi

        assert s._async['thread'] == async_gevent_uwsgi.Thread
        assert s._async['queue'] == 'foo'
        assert s._async['queue_empty'] == RuntimeError
        assert s._async['event'] == 'bar'
        assert s._async['websocket'] == async_gevent_uwsgi.uWSGIWebSocket
        del sys.modules['gevent']
        del sys.modules['gevent.queue']
        del sys.modules['gevent.event']
        del sys.modules['uwsgi']
        del sys.modules['engineio.async_drivers.gevent_uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi_without_uwsgi(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['gevent'].queue = mock.MagicMock()
        sys.modules['gevent.queue'] = sys.modules['gevent'].queue
        sys.modules['gevent.queue'].JoinableQueue = 'foo'
        sys.modules['gevent.queue'].Empty = RuntimeError
        sys.modules['gevent.event'] = mock.MagicMock()
        sys.modules['gevent.event'].Event = 'bar'
        sys.modules['uwsgi'] = None
        with pytest.raises(ValueError):
            server.Server(async_mode='gevent_uwsgi')
        del sys.modules['gevent']
        del sys.modules['gevent.queue']
        del sys.modules['gevent.event']
        del sys.modules['uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent_uwsgi_without_websocket(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['gevent'].queue = mock.MagicMock()
        sys.modules['gevent.queue'] = sys.modules['gevent'].queue
        sys.modules['gevent.queue'].JoinableQueue = 'foo'
        sys.modules['gevent.queue'].Empty = RuntimeError
        sys.modules['gevent.event'] = mock.MagicMock()
        sys.modules['gevent.event'].Event = 'bar'
        sys.modules['uwsgi'] = mock.MagicMock()
        del sys.modules['uwsgi'].websocket_handshake
        s = server.Server(async_mode='gevent_uwsgi')
        assert s.async_mode == 'gevent_uwsgi'

        from engineio.async_drivers import gevent_uwsgi as async_gevent_uwsgi

        assert s._async['thread'] == async_gevent_uwsgi.Thread
        assert s._async['queue'] == 'foo'
        assert s._async['queue_empty'] == RuntimeError
        assert s._async['event'] == 'bar'
        assert s._async['websocket'] is None
        del sys.modules['gevent']
        del sys.modules['gevent.queue']
        del sys.modules['gevent.event']
        del sys.modules['uwsgi']
        del sys.modules['engineio.async_drivers.gevent_uwsgi']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_gevent(self, import_module):
        sys.modules['gevent'] = mock.MagicMock()
        sys.modules['gevent'].queue = mock.MagicMock()
        sys.modules['gevent.queue'] = sys.modules['gevent'].queue
        sys.modules['gevent.queue'].JoinableQueue = 'foo'
        sys.modules['gevent.queue'].Empty = RuntimeError
        sys.modules['gevent.event'] = mock.MagicMock()
        sys.modules['gevent.event'].Event = 'bar'
        sys.modules['geventwebsocket'] = 'geventwebsocket'
        s = server.Server(async_mode='gevent')
        assert s.async_mode == 'gevent'

        from engineio.async_drivers import gevent as async_gevent

        assert s._async['thread'] == async_gevent.Thread
        assert s._async['queue'] == 'foo'
        assert s._async['queue_empty'] == RuntimeError
        assert s._async['event'] == 'bar'
        assert s._async['websocket'] == async_gevent.WebSocketWSGI
        del sys.modules['gevent']
        del sys.modules['gevent.queue']
        del sys.modules['gevent.event']
        del sys.modules['geventwebsocket']
        del sys.modules['engineio.async_drivers.gevent']

    @mock.patch('importlib.import_module', side_effect=_mock_import)
    def test_async_mode_aiohttp(self, import_module):
        sys.modules['aiohttp'] = mock.MagicMock()
        with pytest.raises(ValueError):
            server.Server(async_mode='aiohttp')

    @mock.patch('importlib.import_module', side_effect=[ImportError])
    def test_async_mode_invalid(self, import_module):
        with pytest.raises(ValueError):
            server.Server(async_mode='foo')

    @mock.patch(
        'importlib.import_module',
        side_effect=[_mock_async],
    )
    def test_async_mode_auto_eventlet(self, import_module):
        s = server.Server()
        assert s.async_mode == 'eventlet'

    @mock.patch(
        'importlib.import_module', side_effect=[ImportError, _mock_async]
    )
    def test_async_mode_auto_gevent_uwsgi(self, import_module):
        s = server.Server()
        assert s.async_mode == 'gevent_uwsgi'

    @mock.patch(
        'importlib.import_module',
        side_effect=[ImportError, ImportError, _mock_async],
    )
    def test_async_mode_auto_gevent(self, import_module):
        s = server.Server()
        assert s.async_mode == 'gevent'

    @mock.patch(
        'importlib.import_module',
        side_effect=[ImportError, ImportError, ImportError, _mock_async],
    )
    def test_async_mode_auto_threading(self, import_module):
        s = server.Server()
        assert s.async_mode == 'threading'

    def test_generate_id(self):
        s = server.Server()
        assert s.generate_id() != s.generate_id()

    def test_on_event(self):
        s = server.Server()

        @s.on('connect')
        def foo():
            pass

        s.on('disconnect', foo)

        assert s.handlers['connect'] == foo
        assert s.handlers['disconnect'] == foo

    def test_on_event_invalid(self):
        s = server.Server()
        with pytest.raises(ValueError):
            s.on('invalid')

    def test_trigger_event(self):
        s = server.Server(async_mode='threading')
        f = {}

        @s.on('connect')
        def foo(sid, environ):
            return sid + environ

        @s.on('message')
        def bar(sid, data):
            f['bar'] = sid + data
            return 'bar'

        @s.on('disconnect')
        def baz(sid, reason):
            return sid + reason

        r = s._trigger_event('connect', 1, 2, run_async=False)
        assert r == 3
        r = s._trigger_event('message', 3, 4, run_async=True)
        r.join()
        assert f['bar'] == 7
        r = s._trigger_event('message', 5, 6)
        assert r == 'bar'
        r = s._trigger_event('disconnect', 'foo', 'bar')
        assert r == 'foobar'

    def test_trigger_legacy_disconnect_event(self):
        s = server.Server(async_mode='threading')

        @s.on('disconnect')
        def baz(sid):
            return sid

        r = s._trigger_event('disconnect', 'foo', 'bar')
        assert r == 'foo'

    def test_trigger_event_error(self):
        s = server.Server()

        @s.on('connect')
        def foo(sid, environ):
            return 1 / 0

        @s.on('message')
        def bar(sid, data):
            return 1 / 0

        r = s._trigger_event('connect', 1, 2, run_async=False)
        assert not r
        r = s._trigger_event('message', 3, 4, run_async=False)
        assert r is None

    def test_session(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        s.sockets['foo'] = mock_socket
        with s.session('foo') as session:
            assert session == {}
            session['username'] = 'bar'
        assert s.get_session('foo') == {'username': 'bar'}

    def test_close_one_socket(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        s.sockets['foo'] = mock_socket
        s.disconnect('foo')
        assert mock_socket.close.call_count == 1
        assert 'foo' not in s.sockets

    def test_close_all_sockets(self):
        s = server.Server()
        mock_sockets = {}
        for sid in ['foo', 'bar', 'baz']:
            mock_sockets[sid] = self._get_mock_socket()
            s.sockets[sid] = mock_sockets[sid]
        s.disconnect()
        for socket in mock_sockets.values():
            assert socket.close.call_count == 1
        assert s.sockets == {}

    def test_upgrades(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        assert s._upgrades('foo', 'polling') == ['websocket']
        assert s._upgrades('foo', 'websocket') == []
        s.sockets['foo'].upgraded = True
        assert s._upgrades('foo', 'polling') == []
        assert s._upgrades('foo', 'websocket') == []
        s.allow_upgrades = False
        s.sockets['foo'].upgraded = True
        assert s._upgrades('foo', 'polling') == []
        assert s._upgrades('foo', 'websocket') == []

    def test_transport(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        s.sockets['foo'].upgraded = False
        s.sockets['bar'] = self._get_mock_socket()
        s.sockets['bar'].upgraded = True
        assert s.transport('foo') == 'polling'
        assert s.transport('bar') == 'websocket'

    def test_bad_session(self):
        s = server.Server()
        s.sockets['foo'] = 'client'
        with pytest.raises(KeyError):
            s._get_socket('bar')

    def test_closed_socket(self):
        s = server.Server()
        s.sockets['foo'] = self._get_mock_socket()
        s.sockets['foo'].closed = True
        with pytest.raises(KeyError):
            s._get_socket('foo')

    def test_jsonp_with_bad_index(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&j=abc'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_jsonp_index(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&j=233'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        assert r[0].startswith(b'___eio[233]("')
        assert r[0].endswith(b'");')

    def test_connect(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert len(s.sockets) == 1
        assert start_response.call_count == 1
        assert start_response.call_args[0][0] == '200 OK'
        assert (
            'Content-Type',
            'text/plain; charset=UTF-8',
        ) in start_response.call_args[0][1]
        assert len(r) == 1
        packets = payload.Payload(encoded_payload=r[0].decode('utf-8')).packets
        assert len(packets) == 1
        assert packets[0].packet_type == packet.OPEN
        assert 'upgrades' in packets[0].data
        assert packets[0].data['upgrades'] == ['websocket']
        assert 'sid' in packets[0].data
        assert packets[0].data['pingTimeout'] == 20000
        assert packets[0].data['pingInterval'] == 25000
        assert packets[0].data['maxPayload'] == 1000000

    def test_connect_no_upgrades(self):
        s = server.Server(allow_upgrades=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0].decode('utf-8')).packets
        assert packets[0].data['upgrades'] == []

    def test_connect_bad_eio_version(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=1'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert start_response.call_args[0][0], '400 BAD REQUEST'
        assert b'unsupported version' in r[0]

    def test_connect_custom_ping_times(self):
        s = server.Server(ping_timeout=123, ping_interval=456,
                          max_http_buffer_size=12345678)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0].decode('utf-8')).packets
        assert packets[0].data['pingTimeout'] == 123000
        assert packets[0].data['pingInterval'] == 456000
        assert packets[0].data['maxPayload'] == 12345678

    @mock.patch(
        'engineio.socket.Socket.poll', side_effect=exceptions.QueueEmpty
    )
    def test_connect_bad_poll(self, poll):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    @mock.patch(
        'engineio.socket.Socket',
        return_value=mock.MagicMock(connected=False, closed=False),
    )
    def test_connect_transport_websocket(self, Socket):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&transport=websocket',
            'HTTP_UPGRADE': 'websocket',
        }
        start_response = mock.MagicMock()
        # force socket to stay open, so that we can check it later
        Socket().closed = False
        s.handle_request(environ, start_response)
        assert s.sockets['123'].send.call_args[0][0].packet_type == packet.OPEN

    @mock.patch(
        'engineio.socket.Socket',
        return_value=mock.MagicMock(connected=False, closed=False),
    )
    def test_http_upgrade_case_insensitive(self, Socket):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&transport=websocket',
            'HTTP_UPGRADE': 'WebSocket',
        }
        start_response = mock.MagicMock()
        # force socket to stay open, so that we can check it later
        Socket().closed = False
        s.handle_request(environ, start_response)
        assert s.sockets['123'].send.call_args[0][0].packet_type == packet.OPEN

    @mock.patch(
        'engineio.socket.Socket',
        return_value=mock.MagicMock(connected=False, closed=False),
    )
    def test_connect_transport_websocket_closed(self, Socket):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&transport=websocket',
            'HTTP_UPGRADE': 'websocket',
        }
        start_response = mock.MagicMock()

        def mock_handle(environ, start_response):
            s.sockets['123'].closed = True

        Socket().handle_get_request = mock_handle
        s.handle_request(environ, start_response)
        assert '123' not in s.sockets

    def test_connect_transport_invalid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': 'EIO=4&transport=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_connect_transport_websocket_without_upgrade(self):
        s = server.Server()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&transport=websocket',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_connect_cors_headers(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    def test_connect_cors_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'b',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'b') in headers

    def test_connect_cors_allowed_origin_with_callable(self):
        def cors(origin):
            return origin == 'a'

        s = server.Server(cors_allowed_origins=cors)
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'a',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'a') in headers

        environ['HTTP_ORIGIN'] = 'b'
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_connect_cors_not_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'c',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'c') not in headers
        assert ('Access-Control-Allow-Origin', '*') not in headers

    def test_connect_cors_headers_all_origins(self):
        s = server.Server(cors_allowed_origins='*')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'foo',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'foo') in headers
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    def test_connect_cors_headers_one_origin(self):
        s = server.Server(cors_allowed_origins='a')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'a',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'a') in headers
        assert ('Access-Control-Allow-Credentials', 'true') in headers

    def test_connect_cors_headers_one_origin_not_allowed(self):
        s = server.Server(cors_allowed_origins='a')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'b',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'b') not in headers
        assert ('Access-Control-Allow-Origin', '*') not in headers

    def test_connect_cors_headers_default_origin(self):
        s = server.Server()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'foo',
            'HTTP_ORIGIN': 'http://foo',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'http://foo') in headers

    def test_connect_cors_headers_default_origin_proxy_server(self):
        s = server.Server()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'foo',
            'HTTP_ORIGIN': 'https://foo',
            'HTTP_X_FORWARDED_PROTO': 'https, ftp',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'https://foo') in headers

    def test_connect_cors_headers_default_origin_proxy_server2(self):
        s = server.Server()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'wsgi.url_scheme': 'http',
            'HTTP_HOST': 'foo',
            'HTTP_ORIGIN': 'https://bar',
            'HTTP_X_FORWARDED_PROTO': 'https, ftp',
            'HTTP_X_FORWARDED_HOST': 'bar , baz',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Origin', 'https://bar') in headers

    def test_connect_cors_no_credentials(self):
        s = server.Server(cors_credentials=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Credentials', 'true') not in headers

    def test_cors_options(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'OPTIONS', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert (
            'Access-Control-Allow-Methods',
            'OPTIONS, GET, POST',
        ) in headers

    def test_cors_request_headers(self):
        s = server.Server()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ACCESS_CONTROL_REQUEST_HEADERS': 'Foo, Bar',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        assert ('Access-Control-Allow-Headers', 'Foo, Bar') in headers

    def test_connect_cors_disabled(self):
        s = server.Server(cors_allowed_origins=[])
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4',
            'HTTP_ORIGIN': 'http://foo',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        headers = start_response.call_args[0][1]
        for header in headers:
            assert not header[0].startswith('Access-Control-')

    def test_connect_cors_default_no_origin(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    def test_connect_cors_all_no_origin(self):
        s = server.Server(cors_allowed_origins='*')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    def test_connect_cors_disabled_no_origin(self):
        s = server.Server(cors_allowed_origins=[])
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        for header in headers:
            assert header[0] != 'Access-Control-Allow-Origin'

    def test_connect_event(self):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock(return_value=None)
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        mock_event.assert_called_once_with('123', environ)
        assert len(s.sockets) == 1

    def test_connect_event_rejects(self):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock(return_value=False)
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        ret = s.handle_request(environ, start_response)
        assert len(s.sockets) == 0
        assert start_response.call_args[0][0] == '401 UNAUTHORIZED'
        assert ret == [b'"Unauthorized"']

    def test_connect_event_rejects_with_message(self):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock(return_value='not allowed')
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        ret = s.handle_request(environ, start_response)
        assert len(s.sockets) == 0
        assert start_response.call_args[0][0] == '401 UNAUTHORIZED'
        assert ret == [b'"not allowed"']

    def test_method_not_found(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'PUT', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '405 METHOD NOT FOUND'

    def test_get_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_post_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_send(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        s.sockets['foo'] = mock_socket
        s.send('foo', 'hello')
        assert mock_socket.send.call_count == 1
        assert mock_socket.send.call_args[0][0].packet_type == packet.MESSAGE
        assert mock_socket.send.call_args[0][0].data == 'hello'

    def test_send_unknown_socket(self):
        s = server.Server()
        # just ensure no exceptions are raised
        s.send('foo', 'hello')

    def test_get_request(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'
        assert len(r) == 1
        packets = payload.Payload(encoded_payload=r[0].decode('utf-8')).packets
        assert len(packets) == 1
        assert packets[0].packet_type == packet.MESSAGE

    def test_get_request_custom_response(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(side_effect=['resp'])
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        assert s.handle_request(environ, start_response) == 'resp'

    def test_get_request_closes_socket(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()

        def mock_get_request(*args, **kwargs):
            mock_socket.closed = True
            return 'resp'

        mock_socket.handle_get_request = mock_get_request
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        assert s.handle_request(environ, start_response) == 'resp'
        assert 'foo' not in s.sockets

    def test_get_request_error(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            side_effect=[exceptions.QueueEmpty]
        )
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'
        assert len(s.sockets) == 0

    def test_get_request_bad_websocket_transport(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.upgraded = False
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': 'EIO=4&transport=websocket&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_get_request_bad_polling_transport(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.upgraded = True
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET',
                   'QUERY_STRING': 'EIO=4&transport=polling&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'

    def test_post_request(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_post_request = mock.MagicMock()
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '200 OK'

    def test_post_request_error(self):
        s = server.Server()
        mock_socket = self._get_mock_socket()
        mock_socket.handle_post_request = mock.MagicMock(
            side_effect=[exceptions.EngineIOError]
        )
        s.sockets['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'EIO=4&sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'
        assert 'foo' not in s.sockets

    @staticmethod
    def _gzip_decompress(b):
        bytesio = io.BytesIO(b)
        with gzip.GzipFile(fileobj=bytesio, mode='r') as gz:
            return gz.read()

    def test_gzip_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': 'gzip,deflate',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert ('Content-Encoding', 'gzip') in start_response.call_args[0][1]
        self._gzip_decompress(r[0])

    def test_deflate_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': 'deflate;q=1,gzip',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        assert ('Content-Encoding', 'deflate') in start_response.call_args[0][
            1
        ]
        zlib.decompress(r[0])

    def test_gzip_compression_threshold(self):
        s = server.Server(compression_threshold=1000)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': 'gzip',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(r[0])

    def test_compression_disabled(self):
        s = server.Server(http_compression=False, compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': 'gzip',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(r[0])

    def test_compression_unknown(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': 'rar',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(r[0])

    def test_compression_no_encoding(self):
        s = server.Server(compression_threshold=0)
        mock_socket = self._get_mock_socket()
        mock_socket.handle_get_request = mock.MagicMock(
            return_value=[packet.Packet(packet.MESSAGE, data='hello')]
        )
        s.sockets['foo'] = mock_socket
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'EIO=4&sid=foo',
            'HTTP_ACCEPT_ENCODING': '',
        }
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            assert header != 'Content-Encoding'
        with pytest.raises(IOError):
            self._gzip_decompress(r[0])

    def test_cookie(self):
        s = server.Server(cookie='sid')
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert ('Set-Cookie', 'sid=123; path=/; SameSite=Lax') \
            in start_response.call_args[0][1]

    def test_cookie_dict(self):
        def get_path():
            return '/a'

        s = server.Server(cookie={
            'name': 'test',
            'path': get_path,
            'SameSite': 'None',
            'Secure': True,
            'HttpOnly': True
        })
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert ('Set-Cookie', 'test=123; path=/a; SameSite=None; Secure; '
                'HttpOnly') in start_response.call_args[0][1]

    def test_no_cookie(self):
        s = server.Server(cookie=None)
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            assert header != 'Set-Cookie'

    def test_logger(self):
        s = server.Server(logger=False)
        assert s.logger.getEffectiveLevel() == logging.ERROR
        s.logger.setLevel(logging.NOTSET)
        s = server.Server(logger=True)
        assert s.logger.getEffectiveLevel() == logging.INFO
        s.logger.setLevel(logging.WARNING)
        s = server.Server(logger=True)
        assert s.logger.getEffectiveLevel() == logging.WARNING
        s.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        s = server.Server(logger=my_logger)
        assert s.logger == my_logger

    def test_custom_json(self):
        # Warning: this test cannot run in parallel with other tests, as it
        # changes the JSON encoding/decoding functions

        class CustomJSON:
            @staticmethod
            def dumps(*args, **kwargs):
                return '*** encoded ***'

            @staticmethod
            def loads(*args, **kwargs):
                return '+++ decoded +++'

        server.Server(json=CustomJSON)
        pkt = packet.Packet(packet.MESSAGE, data={'foo': 'bar'})
        assert pkt.encode() == '4*** encoded ***'
        pkt2 = packet.Packet(encoded_packet=pkt.encode())
        assert pkt2.data == '+++ decoded +++'

        # restore the default JSON module
        packet.Packet.json = json

    def test_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        s = server.Server(async_mode='threading')
        task = s.start_background_task(bg_task)
        task.join()
        assert 'task' in flag
        assert flag['task']

    def test_sleep(self):
        s = server.Server()
        t = time.time()
        s.sleep(0.1)
        assert time.time() - t > 0.1

    def test_create_queue(self):
        s = server.Server()
        q = s.create_queue()
        empty = s.get_queue_empty_exception()
        with pytest.raises(empty):
            q.get(timeout=0.01)

    def test_create_event(self):
        s = server.Server()
        e = s.create_event()
        assert not e.is_set()
        e.set()
        assert e.is_set()

    def test_log_error_once(self):
        s = server.Server(logger=mock.MagicMock())
        s._log_error_once('foo', 'foo-key')
        s._log_error_once('foo', 'foo-key')
        s.logger.error.assert_called_with(
            'foo (further occurrences of this error will be logged with '
            'level INFO)')
        s.logger.info.assert_called_with('foo')

    def test_service_task_started(self):
        s = server.Server(async_mode='threading', monitor_clients=True)
        s._service_task = mock.MagicMock()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        for _ in range(3):
            if s._service_task.call_count > 0:
                break
            time.sleep(0.05)
        s._service_task.assert_called_once_with()

    def test_shutdown(self):
        s = server.Server(async_mode='threading', monitor_clients=True)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'EIO=4'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert s.service_task_handle is not None
        s.shutdown()
        assert s.service_task_handle is None

    def test_transports_invalid(self):
        with pytest.raises(ValueError):
            server.Server(transports='invalid')
        with pytest.raises(ValueError):
            server.Server(transports=['invalid', 'foo'])

    def test_transports_disallowed(self):
        s = server.Server(transports='websocket')
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'transport=polling',
        }
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        assert start_response.call_args[0][0] == '400 BAD REQUEST'
