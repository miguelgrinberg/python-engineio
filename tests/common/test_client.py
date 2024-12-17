import logging
import ssl
import time
from unittest import mock

import pytest
import websocket

from engineio import base_client
from engineio import client
from engineio import exceptions
from engineio import json
from engineio import packet
from engineio import payload


class TestClient:
    def test_is_asyncio_based(self):
        c = client.Client()
        assert not c.is_asyncio_based()

    def test_create(self):
        c = client.Client()
        assert c.handlers == {}
        for attr in [
            'base_url',
            'transports',
            'sid',
            'upgrades',
            'ping_interval',
            'ping_timeout',
            'http',
            'ws',
            'read_loop_task',
            'write_loop_task',
            'queue',
        ]:
            assert getattr(c, attr) is None, attr + ' is not None'
        assert c.state == 'disconnected'

    def test_custom_json(self):
        client.Client()
        assert packet.Packet.json == json
        client.Client(json='foo')
        assert packet.Packet.json == 'foo'
        packet.Packet.json = json

    def test_logger(self):
        c = client.Client(logger=False)
        assert c.logger.getEffectiveLevel() == logging.ERROR
        c.logger.setLevel(logging.NOTSET)
        c = client.Client(logger=True)
        assert c.logger.getEffectiveLevel() == logging.INFO
        c.logger.setLevel(logging.WARNING)
        c = client.Client(logger=True)
        assert c.logger.getEffectiveLevel() == logging.WARNING
        c.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        c = client.Client(logger=my_logger)
        assert c.logger == my_logger

    def test_custom_timeout(self):
        c = client.Client()
        assert c.request_timeout == 5
        c = client.Client(request_timeout=27)
        assert c.request_timeout == 27

    def test_timestamp_requests(self):
        c = client.Client()
        assert c.timestamp_requests
        assert c._get_url_timestamp().startswith('&t=')
        c = client.Client(timestamp_requests=False)
        assert not c.timestamp_requests
        assert c._get_url_timestamp() == ''

    def test_on_event(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            pass

        c.on('disconnect', foo)

        assert c.handlers['connect'] == foo
        assert c.handlers['disconnect'] == foo

    def test_on_event_invalid(self):
        c = client.Client()
        with pytest.raises(ValueError):
            c.on('invalid')

    def test_already_connected(self):
        c = client.Client()
        c.state = 'connected'
        with pytest.raises(ValueError):
            c.connect('http://foo')

    def test_invalid_transports(self):
        c = client.Client()
        with pytest.raises(ValueError):
            c.connect('http://foo', transports=['foo', 'bar'])

    def test_some_invalid_transports(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock()
        c.connect('http://foo', transports=['foo', 'websocket', 'bar'])
        assert c.transports == ['websocket']

    def test_connect_polling(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo') == 'foo'
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo', transports=['polling']) == 'foo'
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        assert (
            c.connect('http://foo', transports=['polling', 'websocket'])
            == 'foo'
        )
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

    def test_connect_websocket(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo', transports=['websocket']) == 'foo'
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo', transports='websocket') == 'foo'
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )

    def test_connect_query_string(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo?bar=baz') == 'foo'
        c._connect_polling.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io'
        )

    def test_connect_custom_headers(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        assert c.connect('http://foo', headers={'Foo': 'Bar'}) == 'foo'
        c._connect_polling.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io'
        )

    def test_wait(self):
        c = client.Client()
        c.read_loop_task = mock.MagicMock()
        c.wait()
        c.read_loop_task.join.assert_called_once_with()

    def test_wait_no_task(self):
        c = client.Client()
        c.read_loop_task = None
        c.wait()  # should not block

    def test_send(self):
        c = client.Client()
        saved_packets = []

        def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        c.send('foo')
        c.send('foo')
        c.send(b'foo')
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
        c = client.Client()
        c.state = 'foo'
        c.sid = 'bar'
        c.disconnect()
        assert c.state == 'disconnected'
        assert c.sid is None

    def test_disconnect_polling(self):
        c = client.Client()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c._trigger_event = mock.MagicMock()
        c.disconnect()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.mock.assert_not_called()
        assert c not in base_client.connected_clients
        c._trigger_event.assert_called_once_with(
            'disconnect', c.reason.CLIENT_DISCONNECT, run_async=False)

    def test_disconnect_websocket(self):
        c = client.Client()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c._trigger_event = mock.MagicMock()
        c.disconnect()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.close.assert_called_once_with()
        assert c not in base_client.connected_clients
        c._trigger_event.assert_called_once_with(
            'disconnect', c.reason.CLIENT_DISCONNECT, run_async=False)

    def test_disconnect_polling_abort(self):
        c = client.Client()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect(abort=True)
        c.queue.join.assert_not_called()
        c.read_loop_task.join.assert_not_called()
        c.ws.mock.assert_not_called()
        assert c not in base_client.connected_clients

    def test_disconnect_websocket_abort(self):
        c = client.Client()
        base_client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect(abort=True)
        c.queue.join.assert_not_called()
        c.read_loop_task.join.assert_not_called()
        c.ws.mock.assert_not_called()
        assert c not in base_client.connected_clients

    def test_current_transport(self):
        c = client.Client()
        c.current_transport = 'foo'
        assert c.transport() == 'foo'

    def test_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        c = client.Client()
        task = c.start_background_task(bg_task)
        task.join()
        assert 'task' in flag
        assert flag['task']

    def test_sleep(self):
        c = client.Client()
        t = time.time()
        c.sleep(0.1)
        assert time.time() - t > 0.1

    def test_create_queue(self):
        c = client.Client()
        q = c.create_queue()
        with pytest.raises(q.Empty):
            q.get(timeout=0.01)

    def test_create_event(self):
        c = client.Client()
        e = c.create_event()
        assert not e.is_set()
        e.set()
        assert e.is_set()

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch('engineio.client.Client._send_request', return_value=None)
    def test_polling_connection_failed(self, _send_request, _time):
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect('http://foo', headers={'Foo': 'Bar'})
        _send_request.assert_called_once_with(
            'GET',
            'http://foo/engine.io/?transport=polling&EIO=4&t=123.456',
            headers={'Foo': 'Bar'},
            timeout=5,
        )

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_404(self, _send_request):
        _send_request.return_value.status_code = 404
        _send_request.return_value.json.return_value = {'foo': 'bar'}
        c = client.Client()
        try:
            c.connect('http://foo')
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] == {'foo': 'bar'}

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_404_no_json(self, _send_request):
        _send_request.return_value.status_code = 404
        _send_request.return_value.json.side_effect = json.JSONDecodeError(
            'error', '<html></html>', 0)
        c = client.Client()
        try:
            c.connect('http://foo')
        except exceptions.ConnectionError as exc:
            assert len(exc.args) == 2
            assert (
                exc.args[0] == 'Unexpected status code 404 in server response'
            )
            assert exc.args[1] is None

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_invalid_packet(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = b'foo'
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect('http://foo')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_no_open_packet(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect('http://foo')

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_successful(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)

        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
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

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_https_noverify_connection_successful(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client(ssl_verify=False)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('https://foo')
        time.sleep(0.1)

        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
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

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_with_more_packets(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)
        assert c._receive_packet.call_count == 1
        assert (
            c._receive_packet.call_args_list[0][0][0].packet_type
            == packet.NOOP
        )

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_upgraded(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value=True)
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')

        c._connect_websocket.assert_called_once_with(
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

    @mock.patch('engineio.client.Client._send_request')
    def test_polling_connection_not_upgraded(self, _send_request):
        _send_request.return_value.status_code = 200
        _send_request.return_value.content = payload.Payload(
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
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value=False)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('http://foo')
        time.sleep(0.1)

        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io'
        )
        c._read_loop_polling.assert_called_once_with()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_called_once_with()
        on_connect.assert_called_once_with()
        assert c in base_client.connected_clients

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch(
        'engineio.client.websocket.create_connection',
        side_effect=[ConnectionError],
    )
    def test_websocket_connection_failed(self, create_connection, _time):
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect(
                'http://foo', transports=['websocket'], headers={'Foo': 'Bar'}
            )
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            header={'Foo': 'Bar'},
            cookie=None,
            enable_multithread=True,
            timeout=5
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch(
        'engineio.client.websocket.create_connection',
        side_effect=[ConnectionError],
    )
    def test_websocket_connection_extra(self, create_connection, _time):
        c = client.Client(websocket_extra_options={'header': {'Baz': 'Qux'},
                                                   'timeout': 10})
        with pytest.raises(exceptions.ConnectionError):
            c.connect(
                'http://foo', transports=['websocket'], headers={'Foo': 'Bar'}
            )
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            header={'Foo': 'Bar', 'Baz': 'Qux'},
            cookie=None,
            enable_multithread=True,
            timeout=10
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch(
        'engineio.client.websocket.create_connection',
        side_effect=[websocket.WebSocketException],
    )
    def test_websocket_connection_failed_with_websocket_error(
        self, create_connection, _time
    ):
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect(
                'http://foo', transports=['websocket'], headers={'Foo': 'Bar'}
            )
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&t=123.456',
            header={'Foo': 'Bar'},
            cookie=None,
            enable_multithread=True,
            timeout=5
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    @mock.patch(
        'engineio.client.websocket.create_connection',
        side_effect=[ConnectionError],
    )
    def test_websocket_upgrade_failed(self, create_connection, _time):
        c = client.Client()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.sid = '123'
        assert not c.connect('http://foo', transports=['websocket'])
        create_connection.assert_called_once_with(
            'ws://foo/engine.io/?transport=websocket&EIO=4&sid=123&t=123.456',
            header={},
            cookie=None,
            enable_multithread=True,
            timeout=5
        )

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_no_open_packet(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.CLOSE
        ).encode()
        c = client.Client()
        with pytest.raises(exceptions.ConnectionError):
            c.connect('http://foo', transports=['websocket'])

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_successful(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c = client.Client()
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])
        time.sleep(0.1)

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
        assert c.ws == create_connection.return_value
        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {},
            'cookie': None,
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_https_noverify_connection_successful(
        self, create_connection
    ):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c = client.Client(ssl_verify=False)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('wss://foo', transports=['websocket'])
        time.sleep(0.1)

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
        assert c.ws == create_connection.return_value
        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {},
            'cookie': None,
            'enable_multithread': True,
            'timeout': 5,
            'sslopt': {'cert_reqs': ssl.CERT_NONE},
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_cookies(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = [mock.MagicMock(), mock.MagicMock()]
        http.cookies[0].name = 'key'
        http.cookies[0].value = 'value'
        http.cookies[1].name = 'key2'
        http.cookies[1].value = 'value2'
        http.auth = None
        http.proxies = None
        http.cert = None
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])
        time.sleep(0.1)

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {},
            'cookie': 'key=value; key2=value2',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_cookie_header(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = None
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect(
            'ws://foo',
            headers={'Foo': 'bar', 'Cookie': 'key=value'},
            transports=['websocket'],
        )
        time.sleep(0.1)

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {'Foo': 'bar'},
            'cookie': 'key=value',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_cookies_and_headers(
        self, create_connection
    ):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = [mock.MagicMock(), mock.MagicMock()]
        http.cookies[0].name = 'key'
        http.cookies[0].value = 'value'
        http.cookies[1].name = 'key2'
        http.cookies[1].value = 'value2'
        http.auth = None
        http.proxies = None
        http.cert = None
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect(
            'ws://foo',
            headers={'Cookie': 'key3=value3'},
            transports=['websocket'],
        )
        time.sleep(0.1)

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {},
            'enable_multithread': True,
            'timeout': 5,
            'cookie': 'key=value; key2=value2; key3=value3',
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_auth(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = ('foo', 'bar')
        http.proxies = None
        http.cert = None
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'header': {'Authorization': 'Basic Zm9vOmJhcg=='},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_cert(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = 'foo.crt'
        c = client.Client(http_session=http, ssl_verify=False)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'sslopt': {'cert_reqs': ssl.CERT_NONE, 'certfile': 'foo.crt'},
            'header': {},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_cert_and_key(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = ('foo.crt', 'key.pem')
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'sslopt': {'certfile': 'foo.crt', 'keyfile': 'key.pem'},
            'header': {},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_verify_with_cert_and_key(
        self, create_connection
    ):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = ('foo.crt', 'key.pem')
        http.verify = 'ca-bundle.crt'
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'sslopt': {
                'certfile': 'foo.crt',
                'keyfile': 'key.pem',
                'ca_certs': 'ca-bundle.crt'
            },
            'header': {},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_proxies(self, create_connection):
        all_urls = [
            'ws://foo',
            'ws://foo',
            'ws://foo',
            'ws://foo',
            'ws://foo',
            'wss://foo',
            'wss://foo',
        ]
        all_proxies = [
            {'http': 'foo.com:1234'},
            {'https': 'foo.com:1234'},
            {'http': 'foo.com:1234', 'ws': 'bar.com:4321'},
            {},
            {'http': 'user:pass@foo.com:1234'},
            {'https': 'foo.com:1234'},
            {'https': 'foo.com:1234', 'wss': 'bar.com:4321'},
        ]
        all_results = [
            ('foo.com', 1234, None),
            None,
            ('bar.com', 4321, None),
            None,
            ('foo.com', 1234, ('user', 'pass')),
            ('foo.com', 1234, None),
            ('bar.com', 4321, None),
        ]
        for url, proxies, results in zip(all_urls, all_proxies, all_results):
            create_connection.reset_mock()
            create_connection.return_value.recv.return_value = packet.Packet(
                packet.OPEN,
                {
                    'sid': '123',
                    'upgrades': [],
                    'pingInterval': 1000,
                    'pingTimeout': 2000,
                },
            ).encode()
            http = mock.MagicMock()
            http.cookies = []
            http.auth = None
            http.proxies = proxies
            http.cert = None
            c = client.Client(http_session=http)
            c._read_loop_polling = mock.MagicMock()
            c._read_loop_websocket = mock.MagicMock()
            c._write_loop = mock.MagicMock()
            on_connect = mock.MagicMock()
            c.on('connect', on_connect)
            c.connect(url, transports=['websocket'])

            assert len(create_connection.call_args_list) == 1
            expected_results = {
                'header': {},
                'cookie': '',
                'enable_multithread': True,
                'timeout': 5,
            }
            if results:
                expected_results.update({
                    'http_proxy_host': results[0],
                    'http_proxy_port': results[1],
                    'http_proxy_auth': results[2]})
            assert create_connection.call_args[1] == expected_results

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_without_verify(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = None
        http.verify = False
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'sslopt': {"cert_reqs": ssl.CERT_NONE},
            'header': {},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_connection_with_verify(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        http = mock.MagicMock()
        http.cookies = []
        http.auth = None
        http.proxies = None
        http.cert = None
        http.verify = 'ca-bundle.crt'
        c = client.Client(http_session=http)
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        c.connect('ws://foo', transports=['websocket'])

        assert len(create_connection.call_args_list) == 1
        assert create_connection.call_args[1] == {
            'sslopt': {'ca_certs': 'ca-bundle.crt'},
            'header': {},
            'cookie': '',
            'enable_multithread': True,
            'timeout': 5,
        }

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_upgrade_no_pong(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.OPEN,
            {
                'sid': '123',
                'upgrades': [],
                'pingInterval': 1000,
                'pingTimeout': 2000,
            },
        ).encode()
        c = client.Client()
        c.sid = '123'
        c.current_transport = 'polling'
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert not c.connect('ws://foo', transports=['websocket'])

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_not_called()
        c._write_loop.assert_not_called()
        on_connect.assert_not_called()
        assert c.transport() == 'polling'

    @mock.patch('engineio.client.websocket.create_connection')
    def test_websocket_upgrade_successful(self, create_connection):
        create_connection.return_value.recv.return_value = packet.Packet(
            packet.PONG, 'probe').encode()
        c = client.Client()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.sid = '123'
        c.base_url = 'http://foo'
        c.current_transport = 'polling'
        c._read_loop_polling = mock.MagicMock()
        c._read_loop_websocket = mock.MagicMock()
        c._write_loop = mock.MagicMock()
        on_connect = mock.MagicMock()
        c.on('connect', on_connect)
        assert c.connect('ws://foo', transports=['websocket'])
        time.sleep(0.1)

        c._read_loop_polling.assert_not_called()
        c._read_loop_websocket.assert_called_once_with()
        c._write_loop.assert_called_once_with()
        on_connect.assert_not_called()  # was called by polling
        assert c not in base_client.connected_clients  # was added by polling
        assert c.base_url == 'http://foo'  # not changed
        assert c.sid == '123'  # not changed
        assert c.transport() == 'websocket'
        assert c.ws == create_connection.return_value
        assert create_connection.return_value.send.call_args_list[0] == (
            (packet.Packet(packet.PING, 'probe').encode(),),
        )  # ping
        assert create_connection.return_value.send.call_args_list[1] == (
            (packet.Packet(packet.UPGRADE).encode(),),
        )  # upgrade

    def test_receive_unknown_packet(self):
        c = client.Client()
        c._receive_packet(packet.Packet(encoded_packet='9'))
        # should be ignored

    def test_receive_noop_packet(self):
        c = client.Client()
        c._receive_packet(packet.Packet(packet.NOOP))
        # should be ignored

    def test_receive_ping_packet(self):
        c = client.Client()
        c._send_packet = mock.MagicMock()
        c._receive_packet(packet.Packet(packet.PING))
        assert c._send_packet.call_args_list[0][0][0].encode() == '3'  # PONG

    def test_receive_message_packet(self):
        c = client.Client()
        c._trigger_event = mock.MagicMock()
        c._receive_packet(packet.Packet(packet.MESSAGE, {'foo': 'bar'}))
        c._trigger_event.assert_called_once_with(
            'message', {'foo': 'bar'}, run_async=True
        )

    def test_receive_close_packet(self):
        c = client.Client()
        c.disconnect = mock.MagicMock()
        c._receive_packet(packet.Packet(packet.CLOSE))
        c.disconnect.assert_called_once_with(
            abort=True, reason=c.reason.SERVER_DISCONNECT)

    def test_send_packet_disconnected(self):
        c = client.Client()
        c.queue = c.create_queue()
        c.state = 'disconnected'
        c._send_packet(packet.Packet(packet.NOOP))
        assert c.queue.empty()

    def test_send_packet(self):
        c = client.Client()
        c.queue = c.create_queue()
        c.state = 'connected'
        c._send_packet(packet.Packet(packet.NOOP))
        assert not c.queue.empty()
        pkt = c.queue.get()
        assert pkt.packet_type == packet.NOOP

    def test_trigger_event(self):
        c = client.Client()
        f = {}

        @c.on('connect')
        def foo():
            return 'foo'

        @c.on('message')
        def bar(data):
            f['bar'] = data
            return 'bar'

        @c.on('disconnect')
        def baz(reason):
            return reason

        r = c._trigger_event('connect', run_async=False)
        assert r == 'foo'
        r = c._trigger_event('message', 123, run_async=True)
        r.join()
        assert f['bar'] == 123
        r = c._trigger_event('message', 321)
        assert r == 'bar'
        r = c._trigger_event('disconnect', 'foo')
        assert r == 'foo'

    def test_trigger_legacy_disconnect_event(self):
        c = client.Client()

        @c.on('disconnect')
        def baz():
            return 'baz'

        r = c._trigger_event('disconnect', 'foo')
        assert r == 'baz'

    def test_trigger_unknown_event(self):
        c = client.Client()
        c._trigger_event('connect', run_async=False)
        c._trigger_event('message', 123, run_async=True)
        # should do nothing

    def test_trigger_event_error(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            return 1 / 0

        @c.on('message')
        def bar(data):
            return 1 / 0

        r = c._trigger_event('connect', run_async=False)
        assert r is None
        r = c._trigger_event('message', 123, run_async=False)
        assert r is None

    def test_engineio_url(self):
        c = client.Client()
        assert (
            c._get_engineio_url('http://foo', 'bar', 'polling')
            == 'http://foo/bar/?transport=polling&EIO=4'
        )
        assert (
            c._get_engineio_url('http://foo', 'bar', 'websocket')
            == 'ws://foo/bar/?transport=websocket&EIO=4'
        )
        assert (
            c._get_engineio_url('ws://foo', 'bar', 'polling')
            == 'http://foo/bar/?transport=polling&EIO=4'
        )
        assert (
            c._get_engineio_url('ws://foo', 'bar', 'websocket')
            == 'ws://foo/bar/?transport=websocket&EIO=4'
        )
        assert (
            c._get_engineio_url('https://foo', 'bar', 'polling')
            == 'https://foo/bar/?transport=polling&EIO=4'
        )
        assert (
            c._get_engineio_url('https://foo', 'bar', 'websocket')
            == 'wss://foo/bar/?transport=websocket&EIO=4'
        )
        assert (
            c._get_engineio_url('http://foo?baz=1', 'bar', 'polling')
            == 'http://foo/bar/?baz=1&transport=polling&EIO=4'
        )
        assert (
            c._get_engineio_url('http://foo#baz', 'bar', 'polling')
            == 'http://foo/bar/?transport=polling&EIO=4'
        )

    def test_read_loop_polling_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c._trigger_event = mock.MagicMock()
        c.write_loop_task = mock.MagicMock()
        c._read_loop_polling()
        c.write_loop_task.join.assert_called_once_with()
        c._trigger_event.assert_not_called()

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_no_response(self, _time):
        c = client.Client()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock(return_value=None)
        c._trigger_event = mock.MagicMock()
        c.write_loop_task = mock.MagicMock()
        c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )
        c._trigger_event.assert_called_once_with(
            'disconnect', c.reason.TRANSPORT_ERROR, run_async=False)

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_status(self, _time):
        c = client.Client()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 400
        c.write_loop_task = mock.MagicMock()
        c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=30
        )

    @mock.patch('engineio.client.time.time', return_value=123.456)
    def test_read_loop_polling_bad_packet(self, _time):
        c = client.Client()
        c.ping_interval = 25
        c.ping_timeout = 60
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 200
        c._send_request.return_value.content = b'foo'
        c.write_loop_task = mock.MagicMock()
        c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        c._send_request.assert_called_once_with(
            'GET', 'http://foo&t=123.456', timeout=65
        )

    def test_read_loop_polling(self):
        c = client.Client()
        c.ping_interval = 25
        c.ping_timeout = 5
        c.state = 'connected'
        c.base_url = 'http://foo'
        c.queue = mock.MagicMock()
        c._send_request = mock.MagicMock()
        c._send_request.side_effect = [
            mock.MagicMock(
                status_code=200,
                content=payload.Payload(
                    packets=[
                        packet.Packet(packet.PING),
                        packet.Packet(packet.NOOP),
                    ]
                ).encode().encode('utf-8'),
            ),
            None,
        ]
        c.write_loop_task = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        c._read_loop_polling()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        assert c._send_request.call_count == 2
        assert c._receive_packet.call_count == 2
        assert c._receive_packet.call_args_list[0][0][0].encode() == '2'
        assert c._receive_packet.call_args_list[1][0][0].encode() == '6'

    def test_read_loop_websocket_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c.write_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        c.write_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket_timeout(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = websocket.WebSocketTimeoutException
        c.write_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket_no_response(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = websocket.WebSocketConnectionClosedException
        c.write_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket_unexpected_error(self):
        c = client.Client()
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = ValueError
        c.write_loop_task = mock.MagicMock()
        c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()

    def test_read_loop_websocket(self):
        c = client.Client()
        c.ping_interval = 1
        c.ping_timeout = 2
        c.state = 'connected'
        c.queue = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.ws.recv.side_effect = [
            packet.Packet(packet.PING).encode(),
            ValueError,
        ]
        c.write_loop_task = mock.MagicMock()
        c._receive_packet = mock.MagicMock()
        c._read_loop_websocket()
        assert c.state == 'disconnected'
        c.queue.put.assert_called_once_with(None)
        c.write_loop_task.join.assert_called_once_with()
        assert c._receive_packet.call_args_list[0][0][0].encode() == '2'

    def test_write_loop_disconnected(self):
        c = client.Client()
        c.state = 'disconnected'
        c._write_loop()
        # should not block

    def test_write_loop_no_packets(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.get.return_value = None
        c._write_loop()
        c.queue.task_done.assert_called_once_with()
        c.queue.get.assert_called_once_with(timeout=7)

    def test_write_loop_empty_queue(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = RuntimeError
        c._write_loop()
        c.queue.get.assert_called_once_with(timeout=7)

    def test_write_loop_polling_one_packet(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 200
        c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    def test_write_loop_polling_three_packets(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError,
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 200
        c._write_loop()
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
                packet.Packet(packet.NOOP),
            ]
        )
        c._send_request.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )

    def test_write_loop_polling_two_packets_done(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            None,
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 200
        c._write_loop()
        assert c.queue.task_done.call_count == 3
        p = payload.Payload(
            packets=[
                packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
                packet.Packet(packet.PING),
            ]
        )
        c._send_request.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    def test_write_loop_polling_bad_connection(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value = None
        c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'

    def test_write_loop_polling_bad_status(self):
        c = client.Client()
        c.base_url = 'http://foo'
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
        ]
        c._send_request = mock.MagicMock()
        c._send_request.return_value.status_code = 500
        c._write_loop()
        assert c.queue.task_done.call_count == 1
        p = payload.Payload(
            packets=[packet.Packet(packet.MESSAGE, {'foo': 'bar'})]
        )
        c._send_request.assert_called_once_with(
            'POST',
            'http://foo',
            body=p.encode(),
            headers={'Content-Type': 'text/plain'},
            timeout=5,
        )
        assert c.state == 'connected'
        assert c.write_loop_task is None

    def test_write_loop_websocket_one_packet(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError,
        ]
        c.ws = mock.MagicMock()
        c._write_loop()
        assert c.queue.task_done.call_count == 1
        assert c.ws.send.call_count == 1
        assert c.ws.send_binary.call_count == 0
        c.ws.send.assert_called_once_with('4{"foo":"bar"}')

    def test_write_loop_websocket_three_packets(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            packet.Packet(packet.PING),
            packet.Packet(packet.NOOP),
            RuntimeError,
            RuntimeError,
        ]
        c.ws = mock.MagicMock()
        c._write_loop()
        assert c.queue.task_done.call_count == 3
        assert c.ws.send.call_count == 3
        assert c.ws.send_binary.call_count == 0
        assert c.ws.send.call_args_list[0][0][0] == '4{"foo":"bar"}'
        assert c.ws.send.call_args_list[1][0][0] == '2'
        assert c.ws.send.call_args_list[2][0][0] == '6'

    def test_write_loop_websocket_one_packet_binary(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, b'foo'),
            RuntimeError,
            RuntimeError,
        ]
        c.ws = mock.MagicMock()
        c._write_loop()
        assert c.queue.task_done.call_count == 1
        assert c.ws.send.call_count == 0
        assert c.ws.send_binary.call_count == 1
        c.ws.send_binary.assert_called_once_with(b'foo')

    def test_write_loop_websocket_bad_connection(self):
        c = client.Client()
        c.state = 'connected'
        c.ping_interval = 1
        c.ping_timeout = 2
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.Empty = RuntimeError
        c.queue.get.side_effect = [
            packet.Packet(packet.MESSAGE, {'foo': 'bar'}),
            RuntimeError,
            RuntimeError,
        ]
        c.ws = mock.MagicMock()
        c.ws.send.side_effect = websocket.WebSocketConnectionClosedException
        c._write_loop()
        assert c.state == 'connected'

    @mock.patch('engineio.base_client.original_signal_handler')
    def test_signal_handler(self, original_handler):
        clients = [mock.MagicMock(), mock.MagicMock()]
        base_client.connected_clients = clients[:]
        base_client.connected_clients[0].is_asyncio_based.return_value = False
        base_client.connected_clients[1].is_asyncio_based.return_value = True
        base_client.signal_handler('sig', 'frame')
        clients[0].disconnect.assert_called_once_with()
        clients[1].disconnect.assert_not_called()
