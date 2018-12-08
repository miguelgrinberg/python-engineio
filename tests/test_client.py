import json
import logging
import time
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import client
from engineio import packet


class TestClient(unittest.TestCase):
    def test_is_asyncio_based(self):
        c = client.Client()
        self.assertEqual(c.is_asyncio_based(), False)

    def test_create(self):
        c = client.Client()
        self.assertEqual(c.handlers, {})
        for attr in ['base_url', 'transports', 'sid', 'upgrades',
                     'ping_interval', 'ping_timeout', 'http', 'ws',
                     'read_loop_task', 'queue', 'queue_empty']:
            self.assertIsNone(getattr(c, attr), attr + ' is not None')
        self.assertTrue(c.pong_received)
        self.assertEqual(c.state, 'disconnected')

    def test_custon_json(self):
        client.Client()
        self.assertEqual(packet.Packet.json, json)
        client.Client(json='foo')
        self.assertEqual(packet.Packet.json, 'foo')
        packet.Packet.json = json

    def test_logger(self):
        c = client.Client(logger=False)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.ERROR)
        c.logger.setLevel(logging.NOTSET)
        c = client.Client(logger=True)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.INFO)
        c.logger.setLevel(logging.WARNING)
        c = client.Client(logger=True)
        self.assertEqual(c.logger.getEffectiveLevel(), logging.WARNING)
        c.logger.setLevel(logging.NOTSET)
        my_logger = logging.Logger('foo')
        c = client.Client(logger=my_logger)
        self.assertEqual(c.logger, my_logger)

    def test_on_event(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            pass
        c.on('disconnect', foo)

        self.assertEqual(c.handlers['connect'], foo)
        self.assertEqual(c.handlers['disconnect'], foo)

    def test_on_event_invalid(self):
        c = client.Client()
        self.assertRaises(ValueError, c.on, 'invalid')

    def test_already_connected(self):
        c = client.Client()
        c.state = 'connected'
        self.assertRaises(ValueError, c.connect, 'http://foo')

    def test_invalid_transports(self):
        c = client.Client()
        self.assertRaises(ValueError, c.connect, 'http://foo',
                          transports=['foo', 'bar'])

    def test_some_invalid_transports(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock()
        c.connect('http://foo', transports=['foo', 'websocket', 'bar'])
        self.assertEqual(c.transports, ['websocket'])

    def test_connect_polling(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo'), 'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports=['polling']),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo',
                                   transports=['polling', 'websocket']),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_websocket(self):
        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports=['websocket']),
                         'foo')
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = client.Client()
        c._connect_websocket = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', transports='websocket'),
                         'foo')
        c._connect_websocket.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_query_string(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo?bar=baz'), 'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io')

    def test_connect_custom_headers(self):
        c = client.Client()
        c._connect_polling = mock.MagicMock(return_value='foo')
        self.assertEqual(c.connect('http://foo', headers={'Foo': 'Bar'}),
                         'foo')
        c._connect_polling.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io')

    def test_wait(self):
        c = client.Client()
        c.read_loop_task = mock.MagicMock()
        c.wait()
        c.read_loop_task.join.assert_called_once_with()

    def test_send(self):
        c = client.Client()
        saved_packets = []

        def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        c.send('foo')
        c.send('foo', binary=False)
        c.send(b'foo', binary=True)
        self.assertEqual(saved_packets[0].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[0].data, 'foo')
        self.assertEqual(saved_packets[0].binary,
                         False if six.PY3 else True)
        self.assertEqual(saved_packets[1].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[1].data, 'foo')
        self.assertEqual(saved_packets[1].binary, False)
        self.assertEqual(saved_packets[2].packet_type, packet.MESSAGE)
        self.assertEqual(saved_packets[2].data, b'foo')
        self.assertEqual(saved_packets[2].binary, True)

    def test_disconnect_not_connected(self):
        c = client.Client()
        c.state = 'foo'
        c.disconnect()
        self.assertEqual(c.state, 'disconnected')

    def test_disconnect_polling(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect()
        c.queue.join.assert_called_once_with()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_disconnect_websocket(self):
        c = client.Client()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.read_loop_task = mock.MagicMock()
        c.ws = mock.MagicMock()
        c.disconnect()
        c.queue.join.assert_called_once_with()
        c.read_loop_task.join.assert_called_once_with()
        c.ws.close.assert_called_once_with()
        self.assertNotIn(c, client.connected_clients)

    def test_current_transport(self):
        c = client.Client()
        c.current_transport = 'foo'
        self.assertEqual(c.transport(), 'foo')

    def test_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        c = client.Client()
        task = c.start_background_task(bg_task)
        task.join()
        self.assertIn('task', flag)
        self.assertTrue(flag['task'])
        self.assertEqual(task.daemon, False)

    def test_daemon_background_tasks(self):
        flag = {}

        def bg_task():
            flag['task'] = True

        c = client.Client()
        task = c.start_background_task(bg_task, _daemon=True)
        task.join()
        self.assertIn('task', flag)
        self.assertTrue(flag['task'])
        self.assertEqual(task.daemon, True)

    def test_sleep(self):
        c = client.Client()
        t = time.time()
        c.sleep(0.1)
        self.assertTrue(time.time() - t > 0.1)

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

        r = c._trigger_event('connect', run_async=False)
        self.assertEqual(r, 'foo')
        r = c._trigger_event('message', 123, run_async=True)
        r.join()
        self.assertEqual(f['bar'], 123)
        r = c._trigger_event('message', 321)
        self.assertEqual(r, 'bar')

    def test_trigger_event_error(self):
        c = client.Client()

        @c.on('connect')
        def foo():
            return 1 / 0

        @c.on('message')
        def bar(data):
            return 1 / 0

        r = c._trigger_event('connect', run_async=False)
        self.assertEqual(r, None)
        r = c._trigger_event('message', 123, run_async=False)
        self.assertEqual(r, None)
