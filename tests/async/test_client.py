import asyncio
import ssl
import sys
import unittest
from unittest import mock

try:
    import aiohttp
except ImportError:
    aiohttp = None
import pytest

from engineio import async_client
from engineio import base_client
from engineio import exceptions
from engineio import packet
from engineio import payload


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TestAsyncClient(unittest.TestCase):
    def test_is_asyncio_based(self):
        c = async_client.AsyncClient()
        assert c.is_asyncio_based()

    def test_already_connected(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        with pytest.raises(ValueError):
            _run(c.connect('http://foo'))

    def test_invalid_transports(self):
        c = async_client.AsyncClient()
        with pytest.raises(ValueError):
            _run(c.connect('http://foo', transports=['foo', 'bar']))

    def test_some_invalid_transports(self):
        c = async_client.AsyncClient()
        c._connect_websocket = AsyncMock()
        _run(c.connect('http://foo', transports=['foo', 'websocket', 'bar']))
        assert c.transports == ['websocket']

    def test_connect_polling(self):
        c = async_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo')) == 'foo'
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo', transports=['polling'])) == 'foo'
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        assert (
            _run(c.connect('http://foo', transports=['polling', 'websocket']))
            == 'foo'
        )
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

    def test_connect_websocket(self):
        c = async_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo', transports=['websocket'])) == 'foo'
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo', transports='websocket')) == 'foo'
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

    def test_connect_query_string(self):
        c = async_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo?bar=baz')) == 'foo'
        c._connect_polling.mock.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io'
        )

    def test_connect_custom_headers(self):
        c = async_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        assert _run(c.connect('http://foo', headers={'Foo': 'Bar'})) == 'foo'
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io'
        )

    def test_wait(self):
        c = async_client.AsyncClient()
        done = []

        async def fake_read_look_task():
            done.append(True)

        c.read_loop_task = fake_read_look_task()
        _run(c.wait())
        assert done == [True]

    def test_wait_no_task(self):
        c = async_client.AsyncClient()
        c.read_loop_task = None
        _run(c.wait())

    def test_send(self):
        c = async_client.AsyncClient()
        saved_packets = []

        async def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        _run(c.send('foo'))
        _run(c.send('foo'))
        _run(c.send(b'foo'))
        assert saved_packets[0].packet_type == packet.MESSAGE
        assert saved_packets[0].data == 'foo'
        assert not saved_packets[0].binary
        assert saved_packets[1].packet_type == packet.MESSAGE
        assert saved_packets[1].data == 'foo'
        assert not saved_packets[1].binary
        assert saved_packets[2].packet_type == packet.MESSAGE
        assert saved_packets[2].data == b'foo'
        assert saved_packets[2].binary

    def test_disconnect_not_connected(self):
        c = async_client.AsyncClient()
        c.state = 'foo'
        c.sid = 'bar'
        _run(c.disconnect())
        assert c.state == 'disconnected'
        assert c.sid is None

    def test_disconnect_polling(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        c._trigger_event = AsyncMock()
        _run(c.disconnect())
        c.ws.close.mock.assert_not_called()
        assert c not in base_client.connected_clients
        c._trigger_event.mock.assert_called_once_with(
            'disconnect', run_async=False
        )

    def test_disconnect_websocket(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        c._trigger_event = AsyncMock()
        _run(c.disconnect())
        c.ws.close.mock.assert_called_once_with()
        assert c not in base_client.connected_clients
        c._trigger_event.mock.assert_called_once_with(
            'disconnect', run_async=False
        )

    def test_disconnect_polling_abort(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect(abort=True))
        c.queue.join.mock.assert_not_called()
        c.ws.close.mock.assert_not_called()
        assert c not in base_client.connected_clients

    def test_disconnect_websocket_abort(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect(abort=True))
        c.queue.join.mock.assert_not_called()
        c.ws.mock.assert_not_called()
        assert c not in base_client.connected_clients

    def test_background_tasks(self):
        r = []

        async def foo(arg):
            r.append(arg)

        c = async_client.AsyncClient()
        c.start_background_task(foo, 'bar')
        pending = asyncio.all_tasks(loop=asyncio.get_event_loop()) \
            if hasattr(asyncio, 'all_tasks') else asyncio.Task.all_tasks()
        asyncio.get_event_loop().run_until_complete(asyncio.wait(pending))
        assert r == ['bar']

    def test_sleep(self):
        c = async_client.AsyncClient()
        _run(c.sleep(0))

    def test_create_queue(self):
        c = async_client.AsyncClient()
        q = c.create_queue()
        with pytest.raises(q.Empty):
            q.get_nowait()

    def test_create_event(self):
        c = async_client.AsyncClient()
        e = c.create_event()
        assert not e.is_set()
        e.set()
        assert e.is_set()

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_polling_connection_failed(self, _time):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock(return_value=None)
        with pytest.raises(exceptions.ConnectionError):
            _run(c.connect('http://foo', headers={'Foo': 'Bar'}))
        c._send_request.mock.assert_called_once_with(
            'GET',
            'http://foo/engine.io/?transport=polling&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5,
        )

    def test_polling_connection_404(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 404
        c._send_request.mock.return_value.json = AsyncMock(
            return_value={'foo': 'bar'}
        )
        try:
            _run(c.connect('http://foo'))
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] == {'foo': 'bar'}

    def test_polling_connection_404_no_json(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 404
        c._send_request.mock.return_value.json = AsyncMock(
            side_effect=aiohttp.ContentTypeError('foo', 'bar')
        )
        try:
            _run(c.connect('http://foo'))
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] is None

    def test_polling_connection_invalid_packet(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(return_value=b'foo')
        with pytest.raises(exceptions.ConnectionError):
            _run(c.connect('http://foo'))

    def test_polling_connection_no_open_packet(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.CLOSE,
                        {
                            'sid': '123',
                            'upgrades': [],
                            'pingInterval': 10,
                            'pingTimeout': 20,
                        },
                    )
                ]
            ).encode().encode('utf-8')
        )
        with pytest.raises(exceptions.ConnectionError):
            _run(c.connect('http://foo'))

    def test_polling_connection_successful(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.OPEN,
                        {
                            'sid': '123',
                            'upgrades': [],
                            'pingInterval': 1000,
                            'pingTimeout': 2000,
                        },
                    )
                ]
            ).encode().encode('utf-8')
        )
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = AsyncMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))

        c._read_loop_polling.mock.assert_called_once_with()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_called_once_with()
        on_connect.mock.assert_called_once_with()
        assert c in base_client.connected_clients
        assert (
            c.base_url
            == 'http://foo/engine.io/?transport=polling&EIO=4&sid=123'
        )
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'polling'

    def test_polling_https_noverify_connection_successful(self):
        c = async_client.AsyncClient(ssl_verify=False)
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.OPEN,
                        {
                            'sid': '123',
                            'upgrades': [],
                            'pingInterval': 1000,
                            'pingTimeout': 2000,
                        },
                    )
                ]
            ).encode().encode('utf-8')
        )
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = AsyncMock()
        c.on('connect', on_connect)
        _run(c.connect('https://foo'))

        c._read_loop_polling.mock.assert_called_once_with()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_called_once_with()
        on_connect.mock.assert_called_once_with()
        assert c in base_client.connected_clients
        assert (
            c.base_url
            == 'https://foo/engine.io/?transport=polling&EIO=4&sid=123'
        )
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'polling'

    def test_polling_connection_with_more_packets(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.OPEN,
                        {
                            'sid': '123',
                            'upgrades': [],
                            'pingInterval': 1000,
                            'pingTimeout': 2000,
                        },
                    ),
                    packet.Packet(packet.NOOP),
                ]
            ).encode().encode('utf-8')
        )
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        c._receive_packet = AsyncMock()
        on_connect = AsyncMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))
        assert c._receive_packet.mock.call_count == 1
        assert (
            c._receive_packet.mock.call_args_list[0][0][0].packet_type
            == packet.NOOP
        )

    def test_polling_connection_upgraded(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.OPEN,
                        {
                            'sid': '123',
                            'upgrades': ['websocket'],
                            'pingInterval': 1000,
                            'pingTimeout': 2000,
                        },
                    )
                ]
            ).encode().encode('utf-8')
        )
        c._connect_websocket = AsyncMock(return_value=True)
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))

        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients
        assert (
            c.base_url
            == 'http://foo/engine.io/?transport=polling&EIO=4&sid=123'
        )
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == ['websocket']

    def test_polling_connection_not_upgraded(self):
        c = async_client.AsyncClient()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(
            return_value=payload.Payload(
                packets=[
                    packet.Packet(
                        packet.OPEN,
                        {
                            'sid': '123',
                            'upgrades': ['websocket'],
                            'pingInterval': 1000,
                            'pingTimeout': 2000,
                        },
                    )
                ]
            ).encode().encode('utf-8')
        )
        c._connect_websocket = AsyncMock(return_value=False)
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('http://foo'))

        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )
        c._read_loop_polling.mock.assert_called_once_with()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_failed(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        with pytest.raises(exceptions.ConnectionError):
            _run(
                c.connect(
                    'http://foo',
                    transports=['websocket'],
                    headers={'Foo': 'Bar'},
                )
            )
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_extra(self, _time):
        c = async_client.AsyncClient(websocket_extra_options={
            'headers': {'Baz': 'Qux'},
            'timeout': 10
        })
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        with pytest.raises(exceptions.ConnectionError):
            _run(
                c.connect(
                    'http://foo',
                    transports=['websocket'],
                    headers={'Foo': 'Bar'},
                )
            )
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar', 'Baz': 'Qux'},
            timeout=10,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_upgrade_failed(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        c.sid = '123'
        assert not _run(c.connect('http://foo', transports=['websocket']))
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&sid=123&t=123.456',
            headers={},
            timeout=5,
        )

    def test_websocket_connection_no_open_packet(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.CLOSE
        ).encode()
        with pytest.raises(exceptions.ConnectionError):
            _run(c.connect('http://foo', transports=['websocket']))

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_successful(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('ws://foo', transports=['websocket']))

        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_called_once_with()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients
        assert c.base_url == 'ws://foo/engine.io/?transport=websocket&EIO=4'
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'websocket'
        assert c.ws == ws
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_https_noverify_connection_successful(self, _time):
        c = async_client.AsyncClient(ssl_verify=False)
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('wss://foo', transports=['websocket']))

        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_called_once_with()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients
        assert c.base_url == 'wss://foo/engine.io/?transport=websocket&EIO=4'
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'websocket'
        assert c.ws == ws
        _, kwargs = c.http.ws_connect.mock.call_args
        assert 'ssl' in kwargs
        assert isinstance(kwargs['ssl'], ssl.SSLContext)
        assert kwargs['ssl'].verify_mode == ssl.CERT_NONE

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_with_cookies(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c.http._cookie_jar = [mock.MagicMock(), mock.MagicMock()]
        c.http._cookie_jar[0].key = 'key'
        c.http._cookie_jar[0].value = 'value'
        c.http._cookie_jar[1].key = 'key2'
        c.http._cookie_jar[1].value = 'value2'
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(c.connect('ws://foo', transports=['websocket']))
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_with_cookie_header(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c.http._cookie_jar = []
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(
            c.connect(
                'ws://foo',
                headers={'Cookie': 'key=value; key2=value2; key3="value3="'},
                transports=['websocket'],
            )
        )
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )
        c.http.cookie_jar.update_cookies.assert_called_once_with(
            {'key': 'value', 'key2': 'value2', 'key3': '"value3="'}
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_websocket_connection_with_cookies_and_headers(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c.http._cookie_jar = [mock.MagicMock(), mock.MagicMock()]
        c.http._cookie_jar[0].key = 'key'
        c.http._cookie_jar[0].value = 'value'
        c.http._cookie_jar[1].key = 'key2'
        c.http._cookie_jar[1].value = 'value2'
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        _run(
            c.connect(
                'ws://foo',
                headers={'Foo': 'Bar', 'Cookie': 'key3=value3'},
                transports=['websocket'],
            )
        )
        c.http.ws_connect.mock.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5,
        )
        c.http.cookie_jar.update_cookies.assert_called_once_with(
            {'key3': 'value3'}
        )

    def test_websocket_upgrade_no_pong(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        ws.send_str = AsyncMock()
        c.sid = '123'
        c.current_transport = 'polling'
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert not _run(c.connect('ws://foo', transports=['websocket']))

        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_not_called()
        c._write_loop.mock.assert_not_called()
        on_connect.assert_not_called()
        assert c.transport() == 'polling'
        ws.send_str.mock.assert_called_once_with('2probe')

    def test_websocket_upgrade_successful(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = AsyncMock()
        ws = c.http.ws_connect.mock.return_value
        ws.receive = AsyncMock()
        ws.receive.mock.return_value.data = packet.Packet(
            packet.PONG, 'probe'
        ).encode()
        ws.send_str = AsyncMock()
        c.sid = '123'
        c.base_url = 'http://foo'
        c.current_transport = 'polling'
        c._read_loop_polling = AsyncMock()
        c._read_loop_websocket = AsyncMock()
        c._write_loop = AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert _run(c.connect('ws://foo', transports=['websocket']))

        c._read_loop_polling.mock.assert_not_called()
        c._read_loop_websocket.mock.assert_called_once_with()
        c._write_loop.mock.assert_called_once_with()
        on_connect.assert_not_called()  # was called by polling
        assert c not in base_client.connected_clients  # was added by polling
        assert c.base_url == 'http://foo'  # not changed
        assert c.sid == '123'  # not changed
        assert c.transport() == 'websocket'
        assert c.ws == ws
        assert ws.send_str.mock.call_args_list[0] == (('2probe',),)  # ping
        assert ws.send_str.mock.call_args_list[1] == (('5',),)  # upgrade

    def test_receive_unknown_packet(self):
        c = async_client.AsyncClient()
        _run(c._receive_packet(packet.Packet(encoded_packet='9')))
        # should be ignored

    def test_receive_noop_packet(self):
        c = async_client.AsyncClient()
        _run(c._receive_packet(packet.Packet(packet.NOOP)))
        # should be ignored

    def test_receive_ping_packet(self):
        c = async_client.AsyncClient()
        c._send_packet = AsyncMock()
        _run(c._receive_packet(packet.Packet(packet.PING)))
        assert c._send_packet.mock.call_args_list[0][0][0].encode() == '3'

    def test_receive_message_packet(self):
        c = async_client.AsyncClient()
        c._trigger_event = AsyncMock()
        _run(c._receive_packet(packet.Packet(packet.MESSAGE, {'foo': 'bar'})))
        c._trigger_event.mock.assert_called_once_with(
            'message', {'foo': 'bar'}, run_async=True
        )

    def test_receive_close_packet(self):
        c = async_client.AsyncClient()
        c.disconnect = AsyncMock()
        _run(c._receive_packet(packet.Packet(packet.CLOSE)))
        c.disconnect.mock.assert_called_once_with(abort=True)

    def test_send_packet_disconnected(self):
        c = async_client.AsyncClient()
        c.queue = c.create_queue()
        c.state = 'disconnected'
        _run(c._send_packet(packet.Packet(packet.NOOP)))
        assert c.queue.empty()

    def test_send_packet(self):
        c = async_client.AsyncClient()
        c.queue = c.create_queue()
        c.state = 'connected'
        _run(c._send_packet(packet.Packet(packet.NOOP)))
        assert not c.queue.empty()
        pkt = _run(c.queue.get())
        assert pkt.packet_type == packet.NOOP

    def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        assert result == ['ok', 'bar']

    def test_trigger_event_coroutine(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        assert result == ['ok', 'bar']

    def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        assert not _run(c._trigger_event('connect', '123'))
        assert _run(c._trigger_event('message', 'bar')) is None

    def test_trigger_event_coroutine_error(self):
        async def connect_handler(arg):
            return 1 / 0

        async def foo_handler(arg):
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        assert not _run(c._trigger_event('connect', '123'))
        assert _run(c._trigger_event('message', 'bar')) is None

    def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        assert result == ['ok', 'bar']

    def test_trigger_event_coroutine_async(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        assert result == ['ok', 'bar']

    def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        with pytest.raises(ZeroDivisionError):
            asyncio.get_event_loop().run_until_complete(fut)
        assert result == ['bar']

    def test_trigger_event_coroutine_async_error(self):
        result = []

        async def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        with pytest.raises(ZeroDivisionError):
            asyncio.get_event_loop().run_until_complete(fut)
        assert result == ['bar']

    def test_trigger_unknown_event(self):
        c = async_client.AsyncClient()
        _run(c._trigger_event('connect', run_async=False))
        _run(c._trigger_event('message', 123, run_async=True))
        # should do nothing

    def test_read_loop_polling_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        c._trigger_event = AsyncMock()
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        c._trigger_event.mock.assert_not_called()
        # should not block

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_no_response(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock(return_value=None)
        c._trigger_event = AsyncMock()
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )
        c._trigger_event.mock.assert_called_once_with(
            'disconnect', run_async=False
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_status(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 400
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_packet(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 60
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        c._send_request.mock.return_value.read = AsyncMock(return_value=b'foo')
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_polling())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)
        c._send_request.mock.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=65
        )

    def test_read_loop_polling(self):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c._send_request = AsyncMock()
        c._send_request.mock.side_effect = [
            mock.MagicMock(
                status=200,
                read=AsyncMock(
                    return_value=payload.Payload(
                        packets=[
                            packet.Packet(packet.PING),
                            packet.Packet(packet.NOOP),
                        ]
                    ).encode().encode('utf-8')
                ),
            ),
            None,
        ]
        c.write_loop_task = AsyncMock()()
        c._receive_packet = AsyncMock()
        _run(c._read_loop_polling())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)
        assert c._send_request.mock.call_count == 2
        assert c._receive_packet.mock.call_count == 2
        assert c._receive_packet.mock.call_args_list[0][0][0].encode() == '2'
        assert c._receive_packet.mock.call_args_list[1][0][0].encode() == '6'

    def test_read_loop_websocket_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        # should not block

    def test_read_loop_websocket_timeout(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = AsyncMock(side_effect=asyncio.TimeoutError())
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)

    def test_read_loop_websocket_no_response(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = AsyncMock(
            side_effect=aiohttp.client_exceptions.ServerDisconnectedError()
        )
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)

    def test_read_loop_websocket_unexpected_error(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = AsyncMock(side_effect=ValueError)
        c.write_loop_task = AsyncMock()()
        _run(c._read_loop_websocket())
        assert c.state == 'disconnected'
        c.queue.put.mock.assert_called_once_with(None)

    def test_read_loop_websocket(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = AsyncMock(
            side_effect=[
                mock.MagicMock(data=packet.Packet(packet.PING).encode()),
                ValueError,
            ]
        )
        c.write_loop_task = AsyncMock()()
        c._receive_packet = AsyncMock()
        _run(c._read_loop_websocket())
        assert c.state == 'disconnected'
        assert c._receive_packet.mock.call_args_list[0][0][0].encode() == '2'
        c.queue.put.mock.assert_called_once_with(None)

    def test_write_loop_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        _run(c._write_loop())
        # should not block

    def test_write_loop_no_packets(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.get = AsyncMock(return_value=None)
        _run(c._write_loop())
        c.queue.task_done.assert_called_once_with()
        c.queue.get.mock.assert_called_once_with()

    def test_write_loop_empty_queue(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(side_effect=RuntimeError)
        _run(c._write_loop())
        c.queue.get.mock.assert_called_once_with()

    def test_write_loop_polling_one_packet(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=RuntimeError)
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.mock.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    def test_write_loop_polling_three_packets(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(
            side_effect=[
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP),
                RuntimeError,
            ]
        )
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP),
            ]
        )
        c._send_request.mock.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    def test_write_loop_polling_two_packets_done(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(
            side_effect=[packet.Packet(packet.PING), None]
        )
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 200
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
            ]
        )
        c._send_request.mock.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    def test_write_loop_polling_bad_connection(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c._send_request = AsyncMock(return_value=None)
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.mock.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    def test_write_loop_polling_bad_status(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c._send_request = AsyncMock()
        c._send_request.mock.return_value.status = 500
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.mock.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'disconnected'

    def test_write_loop_websocket_one_packet(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_str = AsyncMock()
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 1
        assert c.ws.send_str.mock.call_count == 1
        c.ws.send_str.mock.assert_called_once_with('4{"foo":"bar"}')

    def test_write_loop_websocket_three_packets(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(
            side_effect=[
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP),
                RuntimeError,
            ]
        )
        c.ws = mock.MagicMock()
        c.ws.send_str = AsyncMock()
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 3
        assert c.ws.send_str.mock.call_count == 3
        assert c.ws.send_str.mock.call_args_list[0][0][0] == '4{"foo":"bar"}'
        assert c.ws.send_str.mock.call_args_list[1][0][0] == '2'
        assert c.ws.send_str.mock.call_args_list[2][0][0] == '6'

    def test_write_loop_websocket_one_packet_binary(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, b'foo'), RuntimeError]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_bytes = AsyncMock()
        _run(c._write_loop())
        assert c.queue.task_done.call_count == 1
        assert c.ws.send_bytes.mock.call_count == 1
        c.ws.send_bytes.mock.assert_called_once_with(b'foo')

    def test_write_loop_websocket_bad_connection(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_str = AsyncMock(
            side_effect=aiohttp.client_exceptions.ServerDisconnectedError()
        )
        _run(c._write_loop())
        assert c.state == 'connected'

    @mock.patch('engineio.base_client.original_signal_handler')
    def test_signal_handler(self, original_handler):
        clients = [mock.MagicMock(), mock.MagicMock()]
        base_client.connected_clients = clients[:]
        base_client.connected_clients[0].is_asyncio_based.return_value = False
        base_client.connected_clients[1].is_asyncio_based.return_value = True

        async def test():
            async_client.async_signal_handler()

        asyncio.get_event_loop().run_until_complete(test())
        clients[0].disconnect.assert_not_called()
        clients[1].disconnect.assert_called_once_with()
