import gzip
import logging
import unittest
import zlib

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import packet
from engineio import payload
from engineio import server


class TestServer(unittest.TestCase):
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
            'cors_credentials': False}
        s = server.Server(**kwargs)
        for arg in six.iterkeys(kwargs):
            self.assertEqual(getattr(s, arg), kwargs[arg])

    def test_generate_id(self):
        s = server.Server()
        self.assertNotEqual(s.generate_id(), s.generate_id())

    def test_on_event(self):
        s = server.Server()

        @s.on('connect')
        def foo():
            pass

        self.assertEqual(s.handlers['connect'], foo)

    def test_on_event_invalid(self):
        s = server.Server()
        self.assertRaises(ValueError, s.on, 'invalid')

    def test_close_one_socket(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        s.clients['foo'] = mock_socket
        s.close('foo')
        mock_socket.close.assert_called_once()
        self.assertNotIn('foo', s.clients)

    def test_close_all_sockets(self):
        s = server.Server()
        mock_sockets = {}
        for sid in ['foo', 'bar', 'baz']:
            mock_sockets[sid] = mock.MagicMock()
            s.clients[sid] = mock_sockets[sid]
        s.close()
        for socket in six.itervalues(mock_sockets):
            socket.close.assert_called_once()
        self.assertEqual(s.clients, {})

    def test_upgrades(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        s.clients['foo'] = mock_socket
        mock_socket.upgraded = False
        self.assertEqual(s._upgrades('foo'), ['websocket'])
        mock_socket.upgraded = True
        self.assertEqual(s._upgrades('foo'), [])
        s.allow_upgrades = False
        mock_socket.upgraded = True
        self.assertEqual(s._upgrades('foo'), [])

    def test_bad_session(self):
        s = server.Server()
        s.clients['foo'] = 'client'
        self.assertRaises(KeyError, s._get_socket, 'bar')

    def test_jsonp_not_supported(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'j=abc'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_connect(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertEqual(len(s.clients), 1)
        start_response.assert_called_once()
        self.assertEqual(start_response.call_args[0][0], '200 OK')
        self.assertEqual(len(r), 1)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.OPEN)
        self.assertIn('upgrades', packets[0].data)
        self.assertEqual(packets[0].data['upgrades'], ['websocket'])
        self.assertIn('sid', packets[0].data)

    def test_connect_no_upgrades(self):
        s = server.Server(allow_upgrades=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(packets[0].data['upgrades'], [])

    def test_connect_custom_ping_times(self):
        s = server.Server(ping_timeout=123, ping_interval=456)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(packets[0].data['pingTimeout'], 123000)
        self.assertEqual(packets[0].data['pingInterval'], 456000)

    def test_connect_cors_headers(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', '*'), headers)
        self.assertIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_connect_cors_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'ORIGIN': 'b'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertIn(('Access-Control-Allow-Origin', 'b'), headers)

    def test_connect_cors_not_allowed_origin(self):
        s = server.Server(cors_allowed_origins=['a', 'b'])
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': '', 'ORIGIN': 'c'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Origin', 'c'), headers)

    def test_connect_cors_no_credentials(self):
        s = server.Server(cors_credentials=False)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        headers = start_response.call_args[0][1]
        self.assertNotIn(('Access-Control-Allow-Credentials', 'true'), headers)

    def test_connect_event(self):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock()
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        mock_event.assert_called_once_with('123', environ)
        self.assertEqual(len(s.clients), 1)

    def test_connect_event_rejects(self):
        s = server.Server()
        s.generate_id = mock.MagicMock(return_value='123')
        mock_event = mock.MagicMock(return_value=False)
        s.on('connect')(mock_event)
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(len(s.clients), 0)
        self.assertEqual(start_response.call_args[0][0], '401 UNAUTHORIZED')

    def test_method_not_found(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'PUT', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '405 METHOD NOT FOUND')

    def test_get_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_post_request_with_bad_sid(self):
        s = server.Server()
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    def test_send(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        s.clients['foo'] = mock_socket
        s.send('foo', 'hello')
        mock_socket.send.assert_called_once()
        self.assertEqual(mock_socket.send.call_args[0][0].packet_type,
                         packet.MESSAGE)
        self.assertEqual(mock_socket.send.call_args[0][0].data, 'hello')

    def test_get_request(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '200 OK')
        self.assertEqual(len(r), 1)
        packets = payload.Payload(encoded_payload=r[0]).packets
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0].packet_type, packet.MESSAGE)

    def test_get_request_error(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(side_effect=[IOError])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')
        self.assertEqual(len(s.clients), 0)

    def test_post_request(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        mock_socket.handle_post_request = mock.MagicMock()
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '200 OK')

    def test_post_request_error(self):
        s = server.Server()
        mock_socket = mock.MagicMock()
        mock_socket.handle_post_request = mock.MagicMock(
            side_effect=[ValueError])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'POST', 'QUERY_STRING': 'sid=foo'}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertEqual(start_response.call_args[0][0],
                         '400 BAD REQUEST')

    @staticmethod
    def _gzip_decompress(b):
        bytesio = six.BytesIO(b)
        with gzip.GzipFile(fileobj=bytesio, mode='r') as gz:
            return gz.read()

    def test_gzip_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': 'gzip,deflate'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertIn(('Content-Encoding', 'gzip'),
                      start_response.call_args[0][1])
        self._gzip_decompress(r[0])

    def test_deflate_compression(self):
        s = server.Server(compression_threshold=0)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': 'deflate;q=1,gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        self.assertIn(('Content-Encoding', 'deflate'),
                      start_response.call_args[0][1])
        zlib.decompress(r[0])

    def test_gzip_compression_threshold(self):
        s = server.Server(compression_threshold=1000)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': 'gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_disabled(self):
        s = server.Server(http_compression=False, compression_threshold=0)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': 'gzip'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_unknown(self):
        s = server.Server(http_compression=False, compression_threshold=0)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': 'rar'}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_compression_no_encoding(self):
        s = server.Server(compression_threshold=0)
        mock_socket = mock.MagicMock()
        mock_socket.handle_get_request = mock.MagicMock(return_value=[
            packet.Packet(packet.MESSAGE, data='hello')])
        s.clients['foo'] = mock_socket
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': 'sid=foo',
                   'ACCEPT_ENCODING': ''}
        start_response = mock.MagicMock()
        r = s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Content-Encoding')
        self.assertRaises(IOError, self._gzip_decompress, r[0])

    def test_cookie(self):
        s = server.Server(cookie='sid')
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        self.assertIn(('Set-Cookie', 'sid=123'),
                      start_response.call_args[0][1])

    def test_no_cookie(self):
        s = server.Server(cookie=None)
        s.generate_id = mock.MagicMock(return_value='123')
        environ = {'REQUEST_METHOD': 'GET', 'QUERY_STRING': ''}
        start_response = mock.MagicMock()
        s.handle_request(environ, start_response)
        for header, value in start_response.call_args[0][1]:
            self.assertNotEqual(header, 'Set-Cookie')

    def test_logger(self):
        s = server.Server(logger=False)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.ERROR)
        s = server.Server(logger=True)
        self.assertEqual(s.logger.getEffectiveLevel(), logging.INFO)
        s = server.Server(logger='foo')
        self.assertEqual(s.logger, 'foo')
