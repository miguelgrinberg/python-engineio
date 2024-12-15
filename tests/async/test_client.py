import asyncio
import ssl
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


class TestAsyncClient:
    async def test_is_asyncio_based(self):
        c = async_client.AsyncClient()
        assert c.is_asyncio_based()

    async def test_already_connected(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        with pytest.raises(ValueError):
            await c.connect('http://foo')

    async def test_invalid_transports(self):
        c = async_client.AsyncClient()
        with pytest.raises(ValueError):
            await c.connect('http://foo', transports=['foo', 'bar'])

    async def test_some_invalid_transports(self):
        c = async_client.AsyncClient()
        c._connect_websocket = mock.AsyncMock()
        await c.connect('http://foo', transports=['foo', 'websocket', 'bar'])
        assert c.transports == ['websocket']

    async def test_connect_polling(self):
        c = async_client.AsyncClient()
        c._connect_polling = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo') == 'foo'
        c._connect_polling.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_polling = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo', transports=['polling']) == 'foo'
        c._connect_polling.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_polling = mock.AsyncMock(return_value='foo')
        assert (
            await c.connect('http://foo', transports=['polling', 'websocket'])
            == 'foo'
        )
        c._connect_polling.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )

    async def test_connect_websocket(self):
        c = async_client.AsyncClient()
        c._connect_websocket = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo', transports=['websocket']) == 'foo'
        c._connect_websocket.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = async_client.AsyncClient()
        c._connect_websocket = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo', transports='websocket') == 'foo'
        c._connect_websocket.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )

    async def test_connect_query_string(self):
        c = async_client.AsyncClient()
        c._connect_polling = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo?bar=baz') == 'foo'
        c._connect_polling.assert_awaited_once_with(
            'http://foo?bar=baz', {}, 'engine.io'
        )

    async def test_connect_custom_headers(self):
        c = async_client.AsyncClient()
        c._connect_polling = mock.AsyncMock(return_value='foo')
        assert await c.connect('http://foo', headers={'Foo': 'Bar'}) == 'foo'
        c._connect_polling.assert_awaited_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io'
        )

    async def test_wait(self):
        c = async_client.AsyncClient()
        done = []

        async def fake_read_look_task():
            done.append(True)

        c.read_loop_task = fake_read_look_task()
        await c.wait()
        assert done == [True]

    async def test_wait_no_task(self):
        c = async_client.AsyncClient()
        c.read_loop_task = None
        await c.wait()

    async def test_send(self):
        c = async_client.AsyncClient()
        saved_packets = []

        async def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        await c.send('foo')
        await c.send('foo')
        await c.send(b'foo')
        assert saved_packets[0].packet_type == packet.MESSAGE
        assert saved_packets[0].data == 'foo'
        assert not saved_packets[0].binary
        assert saved_packets[1].packet_type == packet.MESSAGE
        assert saved_packets[1].data == 'foo'
        assert not saved_packets[1].binary
        assert saved_packets[2].packet_type == packet.MESSAGE
        assert saved_packets[2].data == b'foo'
        assert saved_packets[2].binary

    async def test_disconnect_not_connected(self):
        c = async_client.AsyncClient()
        c.state = 'foo'
        c.sid = 'bar'
        await c.disconnect()
        assert c.state == 'disconnected'
        assert c.sid is None

    async def test_disconnect_polling(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.queue.join = mock.AsyncMock()
        c.read_loop_task = mock.AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = mock.AsyncMock()
        c._trigger_event = mock.AsyncMock()
        await c.disconnect()
        c.ws.close.assert_not_awaited()
        assert c not in base_client.connected_clients
        c._trigger_event.assert_awaited_once_with(
            'disconnect', c.reason.CLIENT_DISCONNECT, run_async=False
        )

    async def test_disconnect_websocket(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.queue.join = mock.AsyncMock()
        c.read_loop_task = mock.AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = mock.AsyncMock()
        c._trigger_event = mock.AsyncMock()
        await c.disconnect()
        c.ws.close.assert_awaited_once_with()
        assert c not in base_client.connected_clients
        c._trigger_event.assert_awaited_once_with(
            'disconnect', c.reason.CLIENT_DISCONNECT, run_async=False
        )

    async def test_disconnect_polling_abort(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.queue.join = mock.AsyncMock()
        c.read_loop_task = mock.AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = mock.AsyncMock()
        await c.disconnect(abort=True)
        c.queue.join.assert_not_awaited()
        c.ws.close.assert_not_awaited()
        assert c not in base_client.connected_clients

    async def test_disconnect_websocket_abort(self):
        c = async_client.AsyncClient()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.queue.join = mock.AsyncMock()
        c.read_loop_task = mock.AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = mock.AsyncMock()
        await c.disconnect(abort=True)
        c.queue.join.assert_not_awaited()
        c.ws.assert_not_called()
        assert c not in base_client.connected_clients

    async def test_background_tasks(self):
        r = []

        async def foo(arg):
            r.append(arg)

        c = async_client.AsyncClient()
        await c.start_background_task(foo, 'bar')
        assert r == ['bar']

    async def test_sleep(self):
        c = async_client.AsyncClient()
        await c.sleep(0)

    async def test_create_queue(self):
        c = async_client.AsyncClient()
        q = c.create_queue()
        with pytest.raises(q.Empty):
            q.get_nowait()

    async def test_create_event(self):
        c = async_client.AsyncClient()
        e = c.create_event()
        assert not e.is_set()
        e.set()
        assert e.is_set()

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_polling_connection_failed(self, _time):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock(return_value=None)
        with pytest.raises(exceptions.ConnectionError):
            await c.connect('http://foo', headers={'Foo': 'Bar'})
        c._send_request.assert_awaited_once_with(
            'GET',
            'http://foo/engine.io/?transport=polling&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5,
        )

    async def test_polling_connection_404(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 404
        c._send_request.return_value.json = mock.AsyncMock(
            return_value={'foo': 'bar'}
        )
        try:
            await c.connect('http://foo')
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] == {'foo': 'bar'}

    async def test_polling_connection_404_no_json(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 404
        c._send_request.return_value.json = mock.AsyncMock(
            side_effect=aiohttp.ContentTypeError('foo', 'bar')
        )
        try:
            await c.connect('http://foo')
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] is None

    async def test_polling_connection_invalid_packet(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(return_value=b'foo')
        with pytest.raises(exceptions.ConnectionError):
            await c.connect('http://foo')

    async def test_polling_connection_no_open_packet(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
            await c.connect('http://foo')

    async def test_polling_connection_successful(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.AsyncMock()
        c.on('connect', on_connect)
        await c.connect('http://foo')

        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_awaited_once_with()
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

    async def test_polling_https_noverify_connection_successful(self):
        c = async_client.AsyncClient(ssl_verify=False)
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.AsyncMock()
        c.on('connect', on_connect)
        await c.connect('https://foo')

        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_awaited_once_with()
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

    async def test_polling_connection_with_more_packets(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        c._receive_packet = mock.AsyncMock()
        on_connect = mock.AsyncMock()
        c.on('connect', on_connect)
        await c.connect('http://foo')
        assert c._receive_packet.await_count == 1
        assert (
            c._receive_packet.await_args_list[0][0][0].packet_type
            == packet.NOOP
        )

    async def test_polling_connection_upgraded(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
        c._connect_websocket = mock.AsyncMock(return_value=True)
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect('http://foo')

        c._connect_websocket.assert_awaited_once_with(
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

    async def test_polling_connection_not_upgraded(self):
        c = async_client.AsyncClient()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(
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
        c._connect_websocket = mock.AsyncMock(return_value=False)
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect('http://foo')

        c._connect_websocket.assert_awaited_once_with(
            'http://foo', {}, 'engine.io'
        )
        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_failed(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        with pytest.raises(exceptions.ConnectionError):
            await c.connect(
                'http://foo',
                transports=['websocket'],
                headers={'Foo': 'Bar'},
            )
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_extra(self, _time):
        c = async_client.AsyncClient(websocket_extra_options={
            'headers': {'Baz': 'Qux'},
            'timeout': 10
        })
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        with pytest.raises(exceptions.ConnectionError):
            await c.connect(
                'http://foo',
                transports=['websocket'],
                headers={'Foo': 'Bar'},
            )
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar', 'Baz': 'Qux'},
            timeout=10,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_upgrade_failed(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock(
            side_effect=[aiohttp.client_exceptions.ServerConnectionError()]
        )
        c.sid = '123'
        assert not await c.connect('http://foo', transports=['websocket'])
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&sid=123&t=123.456',
            headers={},
            timeout=5,
        )

    async def test_websocket_connection_no_open_packet(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.CLOSE
        ).encode()
        with pytest.raises(exceptions.ConnectionError):
            await c.connect('http://foo', transports=['websocket'])

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_successful(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect('ws://foo', transports=['websocket'])

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients
        assert c.base_url == 'ws://foo/engine.io/?transport=websocket&EIO=4'
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'websocket'
        assert c.ws == ws
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_https_noverify_connection_successful(self, _time):
        c = async_client.AsyncClient(ssl_verify=False)
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect('wss://foo', transports=['websocket'])

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients
        assert c.base_url == 'wss://foo/engine.io/?transport=websocket&EIO=4'
        assert c.sid == '123'
        assert c.ping_interval == 1
        assert c.ping_timeout == 2
        assert c.upgrades == []
        assert c.transport() == 'websocket'
        assert c.ws == ws
        _, kwargs = c.http.ws_connect.await_args
        assert 'ssl' in kwargs
        assert isinstance(kwargs['ssl'], ssl.SSLContext)
        assert kwargs['ssl'].verify_mode == ssl.CERT_NONE

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_with_cookies(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
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
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect('ws://foo', transports=['websocket'])
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_with_cookie_header(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c.http._cookie_jar = []
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect(
            'ws://foo',
            headers={'Cookie': 'key=value; key2=value2; key3="value3="'},
            transports=['websocket'],
        )
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={},
            timeout=5,
        )
        c.http.cookie_jar.update_cookies.assert_called_once_with(
            {'key': 'value', 'key2': 'value2', 'key3': '"value3="'}
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_websocket_connection_with_cookies_and_headers(self, _time):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
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
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        await c.connect(
            'ws://foo',
            headers={'Foo': 'Bar', 'Cookie': 'key3=value3'},
            transports=['websocket'],
        )
        c.http.ws_connect.assert_awaited_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5,
        )
        c.http.cookie_jar.update_cookies.assert_called_once_with(
            {'key3': 'value3'}
        )

    async def test_websocket_upgrade_no_pong(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        ws.send_str = mock.AsyncMock()
        c.sid = '123'
        c.current_transport = 'polling'
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert not await c.connect('ws://foo', transports=['websocket'])

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_not_called()
        on_connect.assert_not_called()
        assert c.transport() == 'polling'
        ws.send_str.assert_awaited_once_with('2probe')

    async def test_websocket_upgrade_successful(self):
        c = async_client.AsyncClient()
        c.http = mock.MagicMock(closed=False)
        c.http.ws_connect = mock.AsyncMock()
        ws = c.http.ws_connect.return_value
        ws.receive = mock.AsyncMock()
        ws.receive.return_value.data = packet.Packet(
            packet.PONG, 'probe'
        ).encode()
        ws.send_str = mock.AsyncMock()
        c.sid = '123'
        c.base_url = 'http://foo'
        c.current_transport = 'polling'
        c._read_loop_polling = mock.AsyncMock()
        c._read_loop_websocket = mock.AsyncMock()
        c._write_loop = mock.AsyncMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert await c.connect('ws://foo', transports=['websocket'])

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
        on_connect.assert_not_called()  # was called by polling
        assert c not in base_client.connected_clients  # was added by polling
        assert c.base_url == 'http://foo'  # not changed
        assert c.sid == '123'  # not changed
        assert c.transport() == 'websocket'
        assert c.ws == ws
        assert ws.send_str.await_args_list[0] == (('2probe',),)  # ping
        assert ws.send_str.await_args_list[1] == (('5',),)  # upgrade

    async def test_receive_unknown_packet(self):
        c = async_client.AsyncClient()
        await c._receive_packet(packet.Packet(encoded_packet='9'))
        # should be ignored

    async def test_receive_noop_packet(self):
        c = async_client.AsyncClient()
        await c._receive_packet(packet.Packet(packet.NOOP))
        # should be ignored

    async def test_receive_ping_packet(self):
        c = async_client.AsyncClient()
        c._send_packet = mock.AsyncMock()
        await c._receive_packet(packet.Packet(packet.PING))
        assert c._send_packet.await_args_list[0][0][0].encode() == '3'

    async def test_receive_message_packet(self):
        c = async_client.AsyncClient()
        c._trigger_event = mock.AsyncMock()
        await c._receive_packet(packet.Packet(packet.MESSAGE, {'foo': 'bar'}))
        c._trigger_event.assert_awaited_once_with(
            'message', {'foo': 'bar'}, run_async=True
        )

    async def test_receive_close_packet(self):
        c = async_client.AsyncClient()
        c.disconnect = mock.AsyncMock()
        await c._receive_packet(packet.Packet(packet.CLOSE))
        c.disconnect.assert_awaited_once_with(
            abort=True, reason=c.reason.SERVER_DISCONNECT)

    async def test_send_packet_disconnected(self):
        c = async_client.AsyncClient()
        c.queue = c.create_queue()
        c.state = 'disconnected'
        await c._send_packet(packet.Packet(packet.NOOP))
        assert c.queue.empty()

    async def test_send_packet(self):
        c = async_client.AsyncClient()
        c.queue = c.create_queue()
        c.state = 'connected'
        await c._send_packet(packet.Packet(packet.NOOP))
        assert not c.queue.empty()
        pkt = await c.queue.get()
        assert pkt.packet_type == packet.NOOP

    async def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        await c._trigger_event('message', 'bar')
        assert result == ['ok', 'bar']

    async def test_trigger_event_coroutine(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        await c._trigger_event('message', 'bar')
        assert result == ['ok', 'bar']

    async def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        assert not await c._trigger_event('connect', '123')
        assert await c._trigger_event('message', 'bar') is None

    async def test_trigger_event_coroutine_error(self):
        async def connect_handler(arg):
            return 1 / 0

        async def foo_handler(arg):
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        assert not await c._trigger_event('connect', '123')
        assert await c._trigger_event('message', 'bar') is None

    async def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = await c._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['ok', 'bar']

    async def test_trigger_event_coroutine_async(self):
        result = []

        async def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = await c._trigger_event('message', 'bar', run_async=True)
        await fut
        assert result == ['ok', 'bar']

    async def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = await c._trigger_event('message', 'bar', run_async=True)
        with pytest.raises(ZeroDivisionError):
            await fut
        assert result == ['bar']

    async def test_trigger_event_coroutine_async_error(self):
        result = []

        async def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = async_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = await c._trigger_event('message', 'bar', run_async=True)
        with pytest.raises(ZeroDivisionError):
            await fut
        assert result == ['bar']

    async def test_trigger_unknown_event(self):
        c = async_client.AsyncClient()
        await c._trigger_event('connect', run_async=False)
        await c._trigger_event('message', 123, run_async=True)
        # should do nothing

    async def test_trigger_legacy_disconnect_event(self):
        c = async_client.AsyncClient()

        @c.on('disconnect')
        def baz():
            return 'baz'

        r = await c._trigger_event('disconnect', 'foo')
        assert r == 'baz'

    async def test_trigger_legacy_disconnect_event_async(self):
        c = async_client.AsyncClient()

        @c.on('disconnect')
        async def baz():
            return 'baz'

        r = await c._trigger_event('disconnect', 'foo')
        assert r == 'baz'

    async def test_read_loop_polling_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        c._trigger_event = mock.AsyncMock()
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_polling()
        c._trigger_event.assert_not_awaited()
        # should not block

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_read_loop_polling_no_response(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c._send_request = mock.AsyncMock(return_value=None)
        c._trigger_event = mock.AsyncMock()
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)
        c._send_request.assert_awaited_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )
        c._trigger_event.assert_awaited_once_with(
            'disconnect', c.reason.TRANSPORT_ERROR, run_async=False
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_read_loop_polling_bad_status(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 400
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)
        c._send_request.assert_awaited_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    async def test_read_loop_polling_bad_packet(self, _time):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 60
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        c._send_request.return_value.read = mock.AsyncMock(return_value=b'foo')
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)
        c._send_request.assert_awaited_once_with(
            'GET', 'http://foo&t=123.456', timeout=65
        )

    async def test_read_loop_polling(self):
        c = async_client.AsyncClient()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c._send_request = mock.AsyncMock()
        c._send_request.side_effect = [
            mock.MagicMock(
                status=200,
                read=mock.AsyncMock(
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
        c.write_loop_task = mock.AsyncMock()()
        c._receive_packet = mock.AsyncMock()
        await c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)
        assert c._send_request.await_count == 2
        assert c._receive_packet.await_count == 2
        assert c._receive_packet.await_args_list[0][0][0].encode() == '2'
        assert c._receive_packet.await_args_list[1][0][0].encode() == '6'

    async def test_read_loop_websocket_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_websocket()
        # should not block

    async def test_read_loop_websocket_timeout(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = mock.AsyncMock(side_effect=asyncio.TimeoutError())
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)

    async def test_read_loop_websocket_no_response(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = mock.AsyncMock(
            side_effect=aiohttp.client_exceptions.ServerDisconnectedError()
        )
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)

    async def test_read_loop_websocket_unexpected_error(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = mock.AsyncMock(side_effect=ValueError)
        c.write_loop_task = mock.AsyncMock()()
        await c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_awaited_once_with(None)

    async def test_read_loop_websocket(self):
        c = async_client.AsyncClient()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.base_url = 'ws://foo'
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.queue.put = mock.AsyncMock()
        c.ws = mock.MagicMock()
        c.ws.receive = mock.AsyncMock(
            side_effect=[
                mock.MagicMock(data=packet.Packet(packet.PING).encode()),
                ValueError,
            ]
        )
        c.write_loop_task = mock.AsyncMock()()
        c._receive_packet = mock.AsyncMock()
        await c._read_loop_websocket()
        assert c.state == 'disconnected'
        assert c._receive_packet.await_args_list[0][0][0].encode() == '2'
        c.queue.put.assert_awaited_once_with(None)

    async def test_write_loop_disconnected(self):
        c = async_client.AsyncClient()
        c.state = 'disconnected'
        await c._write_loop()
        # should not block

    async def test_write_loop_no_packets(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.get = mock.AsyncMock(return_value=None)
        await c._write_loop()
        c.queue.task_done.assert_called_once_with()
        c.queue.get.assert_awaited_once_with()

    async def test_write_loop_empty_queue(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(side_effect=RuntimeError)
        await c._write_loop()
        c.queue.get.assert_awaited_once_with()

    async def test_write_loop_polling_one_packet(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=RuntimeError)
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        await c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_awaited_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    async def test_write_loop_polling_three_packets(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
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
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        await c._write_loop()
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP),
            ]
        )
        c._send_request.assert_awaited_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    async def test_write_loop_polling_two_packets_done(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(
            side_effect=[packet.Packet(packet.PING), None]
        )
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 200
        await c._write_loop()
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
            ]
        )
        c._send_request.assert_awaited_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    async def test_write_loop_polling_bad_connection(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c._send_request = mock.AsyncMock(return_value=None)
        await c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_awaited_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    async def test_write_loop_polling_bad_status(self):
        c = async_client.AsyncClient()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c._send_request = mock.AsyncMock()
        c._send_request.return_value.status = 500
        await c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_awaited_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'
        assert c.write_loop_task is None

    async def test_write_loop_websocket_one_packet(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_str = mock.AsyncMock()
        await c._write_loop()
        assert c.queue.task_done.call_count == 1
        assert c.ws.send_str.await_count == 1
        c.ws.send_str.assert_awaited_once_with('4{"foo":"bar"}')

    async def test_write_loop_websocket_three_packets(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
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
        c.ws.send_str = mock.AsyncMock()
        await c._write_loop()
        assert c.queue.task_done.call_count == 3
        assert c.ws.send_str.await_count == 3
        assert c.ws.send_str.await_args_list[0][0][0] == '4{"foo":"bar"}'
        assert c.ws.send_str.await_args_list[1][0][0] == '2'
        assert c.ws.send_str.await_args_list[2][0][0] == '6'

    async def test_write_loop_websocket_one_packet_binary(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[packet.Packet(packet.MESSAGE, b'foo'), RuntimeError]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_bytes = mock.AsyncMock()
        await c._write_loop()
        assert c.queue.task_done.call_count == 1
        assert c.ws.send_bytes.await_count == 1
        c.ws.send_bytes.assert_awaited_once_with(b'foo')

    async def test_write_loop_websocket_bad_connection(self):
        c = async_client.AsyncClient()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get = mock.AsyncMock(
            side_effect=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                RuntimeError,
            ]
        )
        c.queue.get_nowait = mock.MagicMock(side_effect=[RuntimeError])
        c.ws = mock.MagicMock()
        c.ws.send_str = mock.AsyncMock(
            side_effect=aiohttp.client_exceptions.ServerDisconnectedError()
        )
        await c._write_loop()
        assert c.state == 'connected'

    @mock.patch('engineio.base_client.original_signal_handler')
    async def test_signal_handler(self, original_handler):
        clients = [mock.MagicMock(), mock.MagicMock()]
        base_client.connected_clients = clients[:]
        base_client.connected_clients[0].is_asyncio_based.return_value = False
        base_client.connected_clients[1].is_asyncio_based.return_value = True
        base_client.connected_clients[1].disconnect = mock.AsyncMock()

        async_client.async_signal_handler()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(0)

        clients[0].disconnect.assert_not_called()
        clients[1].disconnect.assert_called_once_with()
