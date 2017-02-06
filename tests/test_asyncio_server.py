import logging
import sys
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import packet
# from engineio import payload
if sys.version_info >= (3, 5):
    import asyncio
    from asyncio import coroutine
    from engineio import asyncio_server
    from engineio import async_aiohttp
else:
    # mock coroutine so that Python 2 doesn't complain
    def coroutine(f):
        return f


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class TestAsyncServer(unittest.TestCase):
    _mock_async = mock.MagicMock()
    _mock_async.async = {
        'asyncio': True,
        'create_route': mock.MagicMock(),
        'translate_request': mock.MagicMock(),
        'make_response': mock.MagicMock(),
        'websocket': 'w',
        'websocket_class': 'wc'
    }

    def _get_mock_socket(self):
        @coroutine
        def mock_coro():
            pass

        mock_socket = mock.MagicMock()
        mock_socket.closed = False
        mock_socket.upgraded = False
        mock_socket.send.return_value = mock_coro()
        mock_socket.close.return_value = mock_coro()
        return mock_socket

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def setUp(self):
        logging.getLogger('engineio').setLevel(logging.NOTSET)

    def tearDown(self):
        pass

    def test_is_asyncio_based(self):
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.is_asyncio_based(), True)

    def test_async_modes(self):
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.async_modes(), ['aiohttp'])

    def test_async_mode_aiohttp(self):
        s = asyncio_server.AsyncServer(async_mode='aiohttp')
        self.assertEqual(s.async_mode, 'aiohttp')
        self.assertEqual(s._async['asyncio'], True)
        self.assertEqual(s._async['create_route'], async_aiohttp.create_route)
        self.assertEqual(s._async['translate_request'],
                         async_aiohttp.translate_request)
        self.assertEqual(s._async['make_response'],
                         async_aiohttp.make_response)
        self.assertEqual(s._async['websocket'], async_aiohttp)
        self.assertEqual(s._async['websocket_class'], 'WebSocket')

    @mock.patch('importlib.import_module', side_effect=[_mock_async])
    def test_async_mode_auto_aiohttp(self, import_module):
        s = asyncio_server.AsyncServer()
        self.assertEqual(s.async_mode, 'aiohttp')

    def test_async_modes_wsgi(self):
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='eventlet')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='gevent')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='gevent_uwsgi')
        self.assertRaises(ValueError, asyncio_server.AsyncServer,
                          async_mode='threading')

    @mock.patch('importlib.import_module', side_effect=[_mock_async])
    def test_attach(self, import_module):
        s = asyncio_server.AsyncServer()
        s.attach('app', engineio_path='path')
        self._mock_async.async['create_route'].assert_called_with('app', s,
                                                                  '/path/')

    def test_send(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = self._get_mock_socket()
        self._run(s.send('foo', 'hello'))
        self.assertEqual(s.sockets['foo'].send.call_count, 1)
        self.assertEqual(s.sockets['foo'].send.call_args[0][0].packet_type,
                         packet.MESSAGE)
        self.assertEqual(s.sockets['foo'].send.call_args[0][0].data, 'hello')

    def test_send_bad_socket(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = self._get_mock_socket()
        self._run(s.send('bar', 'hello'))
        self.assertEqual(s.sockets['foo'].send.call_count, 0)

    def test_disconnect(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_socket = self._get_mock_socket()
        self._run(s.disconnect('foo'))
        self.assertEqual(mock_socket.close.call_count, 1)
        mock_socket.close.assert_called_once_with()
        self.assertNotIn('foo', s.sockets)

    def test_disconnect_all(self):
        s = asyncio_server.AsyncServer()
        s.sockets['foo'] = mock_foo = self._get_mock_socket()
        s.sockets['bar'] = mock_bar = self._get_mock_socket()
        self._run(s.disconnect())
        self.assertEqual(mock_foo.close.call_count, 1)
        self.assertEqual(mock_bar.close.call_count, 1)
        mock_foo.close.assert_called_once_with()
        mock_bar.close.assert_called_once_with()
        self.assertNotIn('foo', s.sockets)
        self.assertNotIn('bar', s.sockets)
