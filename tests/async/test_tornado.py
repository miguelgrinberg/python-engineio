from unittest import mock

try:
    import tornado.web
except ImportError:
    pass

from engineio.async_drivers import tornado as async_tornado


class TestTornado:
    async def test_get_tornado_handler(self):
        mock_server = mock.MagicMock()
        handler = async_tornado.get_tornado_handler(mock_server)
        assert issubclass(handler, tornado.websocket.WebSocketHandler)

    async def test_translate_request(self):
        mock_handler = mock.MagicMock()
        mock_handler.request.method = 'PUT'
        mock_handler.request.path = '/foo/bar'
        mock_handler.request.query = 'baz=1'
        mock_handler.request.version = '1.1'
        mock_handler.request.headers = {
            'a': 'b',
            'c': 'd',
            'content-type': 'application/json',
            'content-length': 123,
        }
        mock_handler.request.body = b'hello world'
        environ = async_tornado.translate_request(mock_handler)
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': 123,
            'HTTP_A': 'b',
            'HTTP_C': 'd',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            # 'wsgi.input': b'hello world',
            'tornado.handler': mock_handler,
        }
        for k, v in expected_environ.items():
            assert v == environ[k]
        payload = await environ['wsgi.input'].read(1)
        payload += await environ['wsgi.input'].read()
        assert payload == b'hello world'

    async def test_make_response(self):
        mock_handler = mock.MagicMock()
        mock_environ = {'tornado.handler': mock_handler}
        async_tornado.make_response(
            '202 ACCEPTED', [('foo', 'bar')], b'payload', mock_environ
        )
        mock_handler.set_status.assert_called_once_with(202)
        mock_handler.set_header.assert_called_once_with('foo', 'bar')
        mock_handler.write.assert_called_once_with(b'payload')
        mock_handler.finish.assert_called_once_with()
