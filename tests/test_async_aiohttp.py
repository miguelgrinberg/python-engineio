import sys
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

if sys.version_info >= (3, 5):
    from aiohttp import web
    from engineio import async_aiohttp


@unittest.skipIf(sys.version_info < (3, 5), 'only for Python 3.5+')
class AiohttpTests(unittest.TestCase):
    @mock.patch('aiohttp.web_urldispatcher.UrlDispatcher.add_route')
    def test_create_route(self, add_route):
        app = web.Application()
        mock_server = mock.MagicMock()
        async_aiohttp.create_route(app, mock_server, '/foo')
        add_route.assert_any_call('GET', '/foo', mock_server.handle_request,
                                  name=None)
        add_route.assert_any_call('POST', '/foo', mock_server.handle_request)

    def test_translate_request(self):
        request = mock.MagicMock()
        request._message.method = 'PUT'
        request._message.path = '/foo/bar?baz=1'
        request._message.version = (1, 1)
        request._message.headers = {'a': 'b', 'c-c': 'd', 'c_c': 'e',
                                    'content-type': 'application/json',
                                    'content-length': 123}
        request._payload = b'hello world'
        environ = async_aiohttp.translate_request(request)
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': 123,
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.input': b'hello world',
            'aiohttp.request': request,
        }
        for k, v in expected_environ.items():
            self.assertEqual(v, environ[k])
        self.assertTrue(
            environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d')

    @mock.patch('engineio.async_aiohttp.aiohttp.web.Response')
    def test_make_response(self, Response):
        async_aiohttp.make_response('202 ACCEPTED', 'headers', 'payload')
        Response.assert_called_once_with(body='payload', status=202,
                                         headers='headers')
