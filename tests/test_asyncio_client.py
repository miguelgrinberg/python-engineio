import sys
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import client
from engineio import packet
if sys.version_info >= (3, 5):
    import asyncio
    from asyncio import coroutine
    from engineio import asyncio_client
else:
    # mock coroutine so that Python 2 doesn't complain
    def coroutine(f):
        return f


def AsyncMock(*args, **kwargs):
    """Return a mock asynchronous function."""
    m = mock.MagicMock(*args, **kwargs)

    @coroutine
    def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TestAsyncClient(unittest.TestCase):
    def test_is_asyncio_based(self):
        c = asyncio_client.AsyncClient()
        self.assertEqual(c.is_asyncio_based(), True)

    def test_already_connected(self):
        c = asyncio_client.AsyncClient()
        c.state = 'connected'
        self.assertRaises(ValueError, _run, c.connect('http://foo'))

    def test_invalid_transports(self):
        c = asyncio_client.AsyncClient()
        self.assertRaises(ValueError, _run, c.connect(
            'http://foo', transports=['foo', 'bar']))

    def test_some_invalid_transports(self):
        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock()
        _run(c.connect('http://foo', transports=['foo', 'websocket', 'bar']))
        self.assertEqual(c.transports, ['websocket'])

    def test_connect_polling(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(_run(c.connect('http://foo')), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['polling'])), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['polling',
                                                     'websocket'])),
            'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_websocket(self):
        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports=['websocket'])),
            'foo')
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

        c = asyncio_client.AsyncClient()
        c._connect_websocket = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', transports='websocket')),
            'foo')
        c._connect_websocket.mock.assert_called_once_with(
            'http://foo', {}, 'engine.io')

    def test_connect_query_string(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(_run(c.connect('http://foo?bar=baz')), 'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo?bar=baz', {}, 'engine.io')

    def test_connect_custom_headers(self):
        c = asyncio_client.AsyncClient()
        c._connect_polling = AsyncMock(return_value='foo')
        self.assertEqual(
            _run(c.connect('http://foo', headers={'Foo': 'Bar'})),
            'foo')
        c._connect_polling.mock.assert_called_once_with(
            'http://foo', {'Foo': 'Bar'}, 'engine.io')

    def test_wait(self):
        c = asyncio_client.AsyncClient()
        done = []

        @coroutine
        def fake_read_look_task():
            done.append(True)

        c.read_loop_task = fake_read_look_task()
        _run(c.wait())
        self.assertEqual(done, [True])

    def test_send(self):
        c = asyncio_client.AsyncClient()
        saved_packets = []

        @coroutine
        def fake_send_packet(pkt):
            saved_packets.append(pkt)

        c._send_packet = fake_send_packet
        _run(c.send('foo'))
        _run(c.send('foo', binary=False))
        _run(c.send(b'foo', binary=True))
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
        c = asyncio_client.AsyncClient()
        c.state = 'foo'
        _run(c.disconnect())
        self.assertEqual(c.state, 'disconnected')

    def test_disconnect_polling(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'polling'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect())
        c.queue.join.mock.assert_called_once_with()
        c.ws.close.mock.assert_not_called()
        self.assertNotIn(c, client.connected_clients)

    def test_disconnect_websocket(self):
        c = asyncio_client.AsyncClient()
        client.connected_clients.append(c)
        c.state = 'connected'
        c.current_transport = 'websocket'
        c.queue = mock.MagicMock()
        c.queue.put = AsyncMock()
        c.queue.join = AsyncMock()
        c.read_loop_task = AsyncMock()()
        c.ws = mock.MagicMock()
        c.ws.close = AsyncMock()
        _run(c.disconnect())
        c.queue.join.mock.assert_called_once_with()
        c.ws.close.mock.assert_called_once_with()
        self.assertNotIn(c, client.connected_clients)

    def test_background_tasks(self):
        r = []

        @coroutine
        def foo(arg):
            r.append(arg)

        c = asyncio_client.AsyncClient()
        c.start_background_task(foo, 'bar')
        pending = asyncio.Task.all_tasks()
        asyncio.get_event_loop().run_until_complete(asyncio.wait(pending))
        self.assertEqual(r, ['bar'])

    def test_sleep(self):
        c = asyncio_client.AsyncClient()
        _run(c.sleep(0))

    def test_trigger_event_function(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        _run(c._trigger_event('message', 'bar'))
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_error(self):
        def connect_handler(arg):
            return 1 / 0

        def foo_handler(arg):
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        self.assertFalse(_run(c._trigger_event('connect', '123')))
        self.assertIsNone(_run(c._trigger_event('message', 'bar')))

    def test_trigger_event_coroutine_error(self):
        @coroutine
        def connect_handler(arg):
            return 1 / 0

        @coroutine
        def foo_handler(arg):
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('connect', handler=connect_handler)
        c.on('message', handler=foo_handler)
        self.assertFalse(_run(c._trigger_event('connect', '123')))
        self.assertIsNone(_run(c._trigger_event('message', 'bar')))

    def test_trigger_event_function_async(self):
        result = []

        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_coroutine_async(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append('ok')
            result.append(arg)

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        asyncio.get_event_loop().run_until_complete(fut)
        self.assertEqual(result, ['ok', 'bar'])

    def test_trigger_event_function_async_error(self):
        result = []

        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        self.assertRaises(
            ZeroDivisionError, asyncio.get_event_loop().run_until_complete,
            fut)
        self.assertEqual(result, ['bar'])

    def test_trigger_event_coroutine_async_error(self):
        result = []

        @coroutine
        def foo_handler(arg):
            result.append(arg)
            return 1 / 0

        c = asyncio_client.AsyncClient()
        c.on('message', handler=foo_handler)
        fut = _run(c._trigger_event('message', 'bar', run_async=True))
        self.assertRaises(
            ZeroDivisionError, asyncio.get_event_loop().run_until_complete,
            fut)
        self.assertEqual(result, ['bar'])
