import io
import time
from unittest import mock

import pytest

from engineio import exceptions
from engineio import packet
from engineio import payload
from engineio import socket


class TestSocket:
    def setup_method(self):
        self.bg_tasks = []

    def _get_mock_server(self):
        mock_server = mock.Mock()
        mock_server.ping_timeout = 0.2
        mock_server.ping_interval = 0.2
        mock_server.ping_interval_grace_period = 0.001
        mock_server.async_handlers = True
        mock_server.max_http_buffer_size = 128

        try:
            import queue
        except ImportError:
            import Queue as queue
        import threading

        mock_server._async = {
            'threading': threading.Thread,
            'queue': queue.Queue,
            'websocket': None,
        }

        def bg_task(target, *args, **kwargs):
            th = threading.Thread(target=target, args=args, kwargs=kwargs)
            self.bg_tasks.append(th)
            th.start()
            return th

        def create_queue(*args, **kwargs):
            return queue.Queue(*args, **kwargs)

        mock_server.start_background_task = bg_task
        mock_server.create_queue = create_queue
        mock_server.get_queue_empty_exception.return_value = queue.Empty
        return mock_server

    def _join_bg_tasks(self):
        for task in self.bg_tasks:
            task.join()

    def test_create(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        assert s.server == mock_server
        assert s.sid == 'sid'
        assert not s.upgraded
        assert not s.closed
        assert hasattr(s.queue, 'get')
        assert hasattr(s.queue, 'put')
        assert hasattr(s.queue, 'task_done')
        assert hasattr(s.queue, 'join')

    def test_empty_poll(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        with pytest.raises(exceptions.QueueEmpty):
            s.poll()

    def test_poll(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        s.send(pkt1)
        s.send(pkt2)
        assert s.poll() == [pkt1, pkt2]

    def test_poll_none(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.queue.put(None)
        assert s.poll() == []

    def test_poll_none_after_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        pkt = packet.Packet(packet.MESSAGE, data='hello')
        s.send(pkt)
        s.queue.put(None)
        assert s.poll() == [pkt]
        assert s.poll() == []

    def test_schedule_ping(self):
        mock_server = self._get_mock_server()
        mock_server.ping_interval = 0.01
        s = socket.Socket(mock_server, 'sid')
        s.send = mock.MagicMock()
        s.schedule_ping()
        time.sleep(0.05)
        assert s.last_ping is not None
        assert s.send.call_args_list[0][0][0].encode() == '2'

    def test_schedule_ping_closed_socket(self):
        mock_server = self._get_mock_server()
        mock_server.ping_interval = 0.01
        s = socket.Socket(mock_server, 'sid')
        s.send = mock.MagicMock()
        s.closed = True
        s.schedule_ping()
        time.sleep(0.05)
        assert s.last_ping is None
        s.send.assert_not_called()

    def test_pong(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.schedule_ping = mock.MagicMock()
        s.receive(packet.Packet(packet.PONG))
        s.schedule_ping.assert_called_once_with()

    def test_message_async_handler(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.receive(packet.Packet(packet.MESSAGE, data='foo'))
        mock_server._trigger_event.assert_called_once_with(
            'message', 'sid', 'foo', run_async=True
        )

    def test_message_sync_handler(self):
        mock_server = self._get_mock_server()
        mock_server.async_handlers = False
        s = socket.Socket(mock_server, 'sid')
        s.receive(packet.Packet(packet.MESSAGE, data='foo'))
        mock_server._trigger_event.assert_called_once_with(
            'message', 'sid', 'foo', run_async=False
        )

    def test_invalid_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        with pytest.raises(exceptions.UnknownPacketError):
            s.receive(packet.Packet(packet.OPEN))

    def test_timeout(self):
        mock_server = self._get_mock_server()
        mock_server.ping_interval = 6
        mock_server.ping_interval_grace_period = 2
        s = socket.Socket(mock_server, 'sid')
        s.last_ping = time.time() - 9
        s.close = mock.MagicMock()
        s.send('packet')
        s.close.assert_called_once_with(wait=False, abort=False,
                                        reason=mock_server.reason.PING_TIMEOUT)

    def test_polling_read(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'foo')
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        s.send(pkt1)
        s.send(pkt2)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        packets = s.handle_get_request(environ, start_response)
        assert packets == [pkt1, pkt2]

    def test_polling_read_error(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'foo')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        with pytest.raises(exceptions.QueueEmpty):
            s.handle_get_request(environ, start_response)

    def test_polling_write(self):
        mock_server = self._get_mock_server()
        mock_server.max_http_buffer_size = 1000
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        p = payload.Payload(packets=[pkt1, pkt2]).encode().encode('utf-8')
        s = socket.Socket(mock_server, 'foo')
        s.receive = mock.MagicMock()
        environ = {
            'REQUEST_METHOD': 'POST',
            'QUERY_STRING': 'sid=foo',
            'CONTENT_LENGTH': len(p),
            'wsgi.input': io.BytesIO(p),
        }
        s.handle_post_request(environ)
        assert s.receive.call_count == 2

    def test_polling_write_too_large(self):
        mock_server = self._get_mock_server()
        pkt1 = packet.Packet(packet.MESSAGE, data='hello')
        pkt2 = packet.Packet(packet.MESSAGE, data='bye')
        p = payload.Payload(packets=[pkt1, pkt2]).encode().encode('utf-8')
        mock_server.max_http_buffer_size = len(p) - 1
        s = socket.Socket(mock_server, 'foo')
        s.receive = mock.MagicMock()
        environ = {
            'REQUEST_METHOD': 'POST',
            'QUERY_STRING': 'sid=foo',
            'CONTENT_LENGTH': len(p),
            'wsgi.input': io.BytesIO(p),
        }
        with pytest.raises(exceptions.ContentTooLongError):
            s.handle_post_request(environ)

    def test_upgrade_handshake(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'foo')
        s._upgrade_websocket = mock.MagicMock()
        environ = {
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'sid=foo',
            'HTTP_CONNECTION': 'Foo,Upgrade,Bar',
            'HTTP_UPGRADE': 'websocket',
        }
        start_response = mock.MagicMock()
        s.handle_get_request(environ, start_response)
        s._upgrade_websocket.assert_called_once_with(environ, start_response)

    def test_upgrade(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = mock.MagicMock()
        mock_ws = mock.MagicMock()
        mock_server._async['websocket'].return_value = mock_ws
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        environ = "foo"
        start_response = "bar"
        s._upgrade_websocket(environ, start_response)
        mock_server._async['websocket'].assert_called_once_with(
            s._websocket_handler, mock_server
        )
        mock_ws.assert_called_once_with(environ, start_response)

    def test_upgrade_twice(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = mock.MagicMock()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.upgraded = True
        environ = "foo"
        start_response = "bar"
        with pytest.raises(IOError):
            s._upgrade_websocket(environ, start_response)

    def test_upgrade_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.receive(packet.Packet(packet.UPGRADE))
        r = s.poll()
        assert len(r) == 1
        assert r[0].encode() == packet.Packet(packet.NOOP).encode()

    def test_upgrade_no_probe(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        ws = mock.MagicMock()
        ws.wait.return_value = packet.Packet(packet.NOOP).encode()
        s._websocket_handler(ws)
        assert not s.upgraded

    def test_upgrade_no_upgrade_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.queue.join = mock.MagicMock(return_value=None)
        ws = mock.MagicMock()
        probe = 'probe'
        ws.wait.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(),
            packet.Packet(packet.NOOP).encode(),
        ]
        s._websocket_handler(ws)
        ws.send.assert_called_once_with(
            packet.Packet(packet.PONG, data=probe).encode()
        )
        assert s.queue.get().packet_type == packet.NOOP
        assert not s.upgraded

    def test_close_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.close = mock.MagicMock()
        s.receive(packet.Packet(packet.CLOSE))
        s.close.assert_called_once_with(
            wait=False, abort=True,
            reason=mock_server.reason.CLIENT_DISCONNECT)

    def test_invalid_packet_type(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        pkt = packet.Packet(packet_type=99)
        with pytest.raises(exceptions.UnknownPacketError):
            s.receive(pkt)

    def test_upgrade_not_supported(self):
        mock_server = self._get_mock_server()
        mock_server._async['websocket'] = None
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        environ = "foo"
        start_response = "bar"
        s._upgrade_websocket(environ, start_response)
        mock_server._bad_request.assert_called_once_with()

    def test_websocket_read_write(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = False
        s.queue.join = mock.MagicMock(return_value=None)
        foo = 'foo'
        bar = 'bar'
        s.poll = mock.MagicMock(
            side_effect=[
                [packet.Packet(packet.MESSAGE, data=bar)],
                exceptions.QueueEmpty,
            ]
        )
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.MESSAGE, data=foo).encode(),
            None,
        ]
        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.connected
        assert s.upgraded
        assert mock_server._trigger_event.call_count == 2
        mock_server._trigger_event.assert_has_calls(
            [
                mock.call('message', 'sid', 'foo', run_async=True),
                mock.call('disconnect', 'sid',
                          mock_server.reason.TRANSPORT_CLOSE,
                          run_async=False)
            ]
        )
        ws.send.assert_called_with('4bar')

    def test_websocket_upgrade_read_write(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.queue.join = mock.MagicMock(return_value=None)
        foo = 'foo'
        bar = 'bar'
        probe = 'probe'
        s.poll = mock.MagicMock(
            side_effect=[
                [packet.Packet(packet.MESSAGE, data=bar)],
                exceptions.QueueEmpty,
            ]
        )
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(),
            packet.Packet(packet.UPGRADE).encode(),
            packet.Packet(packet.MESSAGE, data=foo).encode(),
            None,
        ]
        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.upgraded
        assert mock_server._trigger_event.call_count == 2
        mock_server._trigger_event.assert_has_calls(
            [
                mock.call('message', 'sid', 'foo', run_async=True),
                mock.call('disconnect', 'sid',
                          mock_server.reason.TRANSPORT_CLOSE,
                          run_async=False)
            ]
        )
        ws.send.assert_called_with('4bar')

    def test_websocket_upgrade_with_payload(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.queue.join = mock.MagicMock(return_value=None)
        probe = 'probe'
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(),
            packet.Packet(packet.UPGRADE, data='2').encode(),
        ]
        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.upgraded

    def test_websocket_upgrade_with_backlog(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.queue.join = mock.MagicMock(return_value=None)
        probe = 'probe'
        foo = 'foo'
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(),
            packet.Packet(packet.UPGRADE, data='2').encode(),
        ]
        s.upgrading = True
        s.send(packet.Packet(packet.MESSAGE, data=foo))
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=sid'}
        start_response = mock.MagicMock()
        packets = s.handle_get_request(environ, start_response)
        assert len(packets) == 1
        assert packets[0].encode() == '6'
        packets = s.poll()
        assert len(packets) == 1
        assert packets[0].encode() == '4foo'

        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.upgraded
        assert not s.upgrading
        packets = s.handle_get_request(environ, start_response)
        assert len(packets) == 1
        assert packets[0].encode() == '6'

    def test_websocket_read_write_wait_fail(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = False
        s.queue.join = mock.MagicMock(return_value=None)
        foo = 'foo'
        bar = 'bar'
        s.poll = mock.MagicMock(
            side_effect=[
                [packet.Packet(packet.MESSAGE, data=bar)],
                [packet.Packet(packet.MESSAGE, data=bar)],
                exceptions.QueueEmpty,
            ]
        )
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.MESSAGE, data=foo).encode(),
            RuntimeError,
        ]
        ws.send.side_effect = [None, RuntimeError]
        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.closed

    def test_websocket_upgrade_with_large_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = True
        s.queue.join = mock.MagicMock(return_value=None)
        probe = 'probe'
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.PING, data=probe).encode(),
            packet.Packet(packet.UPGRADE, data='2' * 128).encode(),
        ]
        with pytest.raises(ValueError):
            s._websocket_handler(ws)
        self._join_bg_tasks()
        assert not s.upgraded

    def test_websocket_ignore_invalid_packet(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.connected = False
        s.queue.join = mock.MagicMock(return_value=None)
        foo = 'foo'
        bar = 'bar'
        s.poll = mock.MagicMock(
            side_effect=[
                [packet.Packet(packet.MESSAGE, data=bar)],
                exceptions.QueueEmpty,
            ]
        )
        ws = mock.MagicMock()
        ws.wait.side_effect = [
            packet.Packet(packet.OPEN).encode(),
            packet.Packet(packet.MESSAGE, data=foo).encode(),
            None,
        ]
        s._websocket_handler(ws)
        self._join_bg_tasks()
        assert s.connected
        assert mock_server._trigger_event.call_count == 2
        mock_server._trigger_event.assert_has_calls(
            [
                mock.call('message', 'sid', foo, run_async=True),
                mock.call('disconnect', 'sid',
                          mock_server.reason.TRANSPORT_CLOSE,
                          run_async=False)
            ]
        )
        ws.send.assert_called_with('4bar')

    def test_send_after_close(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.close(wait=False)
        with pytest.raises(exceptions.SocketIsClosedError):
            s.send(packet.Packet(packet.NOOP))

    def test_close_after_close(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.close(wait=False)
        assert s.closed
        assert mock_server._trigger_event.call_count == 1
        mock_server._trigger_event.assert_called_once_with(
            'disconnect', 'sid', mock_server.reason.SERVER_DISCONNECT,
            run_async=False
        )
        s.close()
        assert mock_server._trigger_event.call_count == 1

    def test_close_and_wait(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.queue = mock.MagicMock()
        s.close(wait=True)
        s.queue.join.assert_called_once_with()

    def test_close_without_wait(self):
        mock_server = self._get_mock_server()
        s = socket.Socket(mock_server, 'sid')
        s.queue = mock.MagicMock()
        s.close(wait=False)
        assert s.queue.join.call_count == 0
