import asyncio
import os
import unittest
from unittest import mock

from engineio.async_drivers import asgi as async_asgi


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


class AsgiTests(unittest.TestCase):
    def test_create_app(self):
        app = async_asgi.ASGIApp(
            'eio',
            'other_app',
            static_files='static_files',
            engineio_path='/foo/',
        )
        assert app.engineio_server == 'eio'
        assert app.other_asgi_app == 'other_app'
        assert app.static_files == 'static_files'
        assert app.engineio_path == '/foo/'

    def test_engineio_routing(self):
        mock_server = mock.MagicMock()
        mock_server.handle_request = AsyncMock()
        app = async_asgi.ASGIApp(mock_server)
        scope = {'type': 'http', 'path': '/engine.io/'}
        _run(app(scope, 'receive', 'send'))
        mock_server.handle_request.mock.assert_called_once_with(
            scope, 'receive', 'send'
        )

    def test_other_app_routing(self):
        other_app = AsyncMock()
        app = async_asgi.ASGIApp('eio', other_app)
        scope = {'type': 'http', 'path': '/foo'}
        _run(app(scope, 'receive', 'send'))
        other_app.mock.assert_called_once_with(scope, 'receive', 'send')

    def test_other_app_lifespan_routing(self):
        other_app = AsyncMock()
        app = async_asgi.ASGIApp('eio', other_app)
        scope = {'type': 'lifespan'}
        _run(app(scope, 'receive', 'send'))
        other_app.mock.assert_called_once_with(scope, 'receive', 'send')

    def test_static_file_routing(self):
        root_dir = os.path.dirname(__file__)
        app = async_asgi.ASGIApp(
            'eio',
            static_files={
                '/': root_dir + '/index.html',
                '/foo': {
                    'content_type': 'text/plain',
                    'filename': root_dir + '/index.html',
                },
                '/static': root_dir,
                '/static/test/': root_dir + '/',
                '/static2/test/': {'filename': root_dir + '/',
                                   'content_type': 'image/gif'},
            },
        )

        def check_path(path, status_code, content_type, body):
            scope = {'type': 'http', 'path': path}
            receive = AsyncMock(return_value={'type': 'http.request'})
            send = AsyncMock()
            _run(app(scope, receive, send))
            send.mock.assert_any_call(
                {
                    'type': 'http.response.start',
                    'status': status_code,
                    'headers': [
                        (b'Content-Type', content_type.encode('utf-8'))
                    ],
                }
            )
            send.mock.assert_any_call(
                {'type': 'http.response.body', 'body': body.encode('utf-8')}
            )

        check_path('/', 200, 'text/html', '<html></html>\n')
        check_path('/foo', 200, 'text/plain', '<html></html>\n')
        check_path('/foo/bar', 404, 'text/plain', 'Not Found')
        check_path('/static/index.html', 200, 'text/html', '<html></html>\n')
        check_path('/static/foo.bar', 404, 'text/plain', 'Not Found')
        check_path(
            '/static/test/index.html', 200, 'text/html', '<html></html>\n'
        )
        check_path('/static/test/index.html', 200, 'text/html',
                   '<html></html>\n')
        check_path('/static/test/files/', 200, 'text/html',
                   '<html>file</html>\n')
        check_path('/static/test/files/file.txt', 200, 'text/plain',
                   'file\n')
        check_path('/static/test/files/x.html', 404, 'text/plain',
                   'Not Found')
        check_path('/static2/test/', 200, 'image/gif', '<html></html>\n')
        check_path('/static2/test/index.html', 200, 'image/gif',
                   '<html></html>\n')
        check_path('/static2/test/files/', 200, 'image/gif',
                   '<html>file</html>\n')
        check_path('/static2/test/files/file.txt', 200, 'image/gif',
                   'file\n')
        check_path('/static2/test/files/x.html', 404, 'text/plain',
                   'Not Found')
        check_path('/bar/foo', 404, 'text/plain', 'Not Found')
        check_path('', 404, 'text/plain', 'Not Found')

        app.static_files[''] = 'index.html'
        check_path('/static/test/', 200, 'text/html', '<html></html>\n')

        app.static_files[''] = {'filename': 'index.html'}
        check_path('/static/test/', 200, 'text/html', '<html></html>\n')

        app.static_files[''] = {
            'filename': 'index.html',
            'content_type': 'image/gif',
        }
        check_path('/static/test/', 200, 'image/gif', '<html></html>\n')

        app.static_files[''] = {'filename': 'test.gif'}
        check_path('/static/test/', 404, 'text/plain', 'Not Found')

        app.static_files = {}
        check_path('/static/test/index.html', 404, 'text/plain', 'Not Found')

    def test_lifespan_startup(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                         {'type': 'lifespan.shutdown'}])
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_any_call(
            {'type': 'lifespan.startup.complete'}
        )

    def test_lifespan_startup_sync_function(self):
        up = False

        def startup():
            nonlocal up
            up = True

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                         {'type': 'lifespan.shutdown'}])
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_any_call(
            {'type': 'lifespan.startup.complete'}
        )
        assert up

    def test_lifespan_startup_async_function(self):
        up = False

        async def startup():
            nonlocal up
            up = True

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                         {'type': 'lifespan.shutdown'}])
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_any_call(
            {'type': 'lifespan.startup.complete'}
        )
        assert up

    def test_lifespan_startup_function_exception(self):
        up = False

        def startup():
            raise Exception

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(side_effect=[{'type': 'lifespan.startup'}])
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with({'type': 'lifespan.startup.failed'})
        assert not up

    def test_lifespan_shutdown(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )

    def test_lifespan_shutdown_sync_function(self):
        down = False

        def shutdown():
            nonlocal down
            down = True

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )
        assert down

    def test_lifespan_shutdown_async_function(self):
        down = False

        async def shutdown():
            nonlocal down
            down = True

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )
        assert down

    def test_lifespan_shutdown_function_exception(self):
        down = False

        def shutdown():
            raise Exception

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with({'type': 'lifespan.shutdown.failed'})
        assert not down

    def test_lifespan_invalid(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = AsyncMock(side_effect=[{'type': 'lifespan.foo'},
                                         {'type': 'lifespan.shutdown'}])
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_called_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )

    def test_not_found(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'http', 'path': '/foo'}
        receive = AsyncMock(return_value={'type': 'http.request'})
        send = AsyncMock()
        _run(app(scope, receive, send))
        send.mock.assert_any_call(
            {
                'type': 'http.response.start',
                'status': 404,
                'headers': [(b'Content-Type', b'text/plain')],
            }
        )
        send.mock.assert_any_call(
            {'type': 'http.response.body', 'body': b'Not Found'}
        )

    def test_translate_request(self):
        receive = AsyncMock(
            return_value={'type': 'http.request', 'body': b'hello world'}
        )
        send = AsyncMock()
        environ = _run(
            async_asgi.translate_request(
                {
                    'type': 'http',
                    'method': 'PUT',
                    'headers': [
                        (b'a', b'b'),
                        (b'c-c', b'd'),
                        (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123'),
                    ],
                    'path': '/foo/bar',
                    'query_string': b'baz=1',
                },
                receive,
                send,
            )
        )
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send,
        }
        for k, v in expected_environ.items():
            assert v == environ[k]
        assert environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d'
        body = _run(environ['wsgi.input'].read())
        assert body == b'hello world'

    def test_translate_request_no_query_string(self):
        receive = AsyncMock(
            return_value={'type': 'http.request', 'body': b'hello world'}
        )
        send = AsyncMock()
        environ = _run(
            async_asgi.translate_request(
                {
                    'type': 'http',
                    'method': 'PUT',
                    'headers': [
                        (b'a', b'b'),
                        (b'c-c', b'd'),
                        (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123'),
                    ],
                    'path': '/foo/bar',
                },
                receive,
                send,
            )
        )
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send,
        }
        for k, v in expected_environ.items():
            assert v == environ[k]
        assert environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d'
        body = _run(environ['wsgi.input'].read())
        assert body == b'hello world'

    def test_translate_request_with_large_body(self):
        receive = AsyncMock(
            side_effect=[
                {'type': 'http.request', 'body': b'hello ', 'more_body': True},
                {'type': 'http.request', 'body': b'world', 'more_body': True},
                {'type': 'foo.bar'},  # should stop parsing here
                {'type': 'http.request', 'body': b'!!!'},
            ]
        )
        send = AsyncMock()
        environ = _run(
            async_asgi.translate_request(
                {
                    'type': 'http',
                    'method': 'PUT',
                    'headers': [
                        (b'a', b'b'),
                        (b'c-c', b'd'),
                        (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123'),
                    ],
                    'path': '/foo/bar',
                    'query_string': b'baz=1',
                },
                receive,
                send,
            )
        )
        expected_environ = {
            'REQUEST_METHOD': 'PUT',
            'PATH_INFO': '/foo/bar',
            'QUERY_STRING': 'baz=1',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '123',
            'HTTP_A': 'b',
            # 'HTTP_C_C': 'd,e',
            'RAW_URI': '/foo/bar?baz=1',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'asgi.receive': receive,
            'asgi.send': send,
        }
        for k, v in expected_environ.items():
            assert v == environ[k]
        assert environ['HTTP_C_C'] == 'd,e' or environ['HTTP_C_C'] == 'e,d'
        body = _run(environ['wsgi.input'].read())
        assert body == b'hello world'

    def test_translate_websocket_request(self):
        receive = AsyncMock(return_value={'type': 'websocket.connect'})
        send = AsyncMock()
        _run(
            async_asgi.translate_request(
                {
                    'type': 'websocket',
                    'headers': [
                        (b'a', b'b'),
                        (b'c-c', b'd'),
                        (b'c_c', b'e'),
                        (b'content-type', b'application/json'),
                        (b'content-length', b'123'),
                    ],
                    'path': '/foo/bar',
                    'query_string': b'baz=1',
                },
                receive,
                send,
            )
        )
        send.mock.assert_not_called()

    def test_translate_unknown_request(self):
        receive = AsyncMock(return_value={'type': 'http.foo'})
        send = AsyncMock()
        environ = _run(
            async_asgi.translate_request(
                {'type': 'http', 'path': '/foo/bar', 'query_string': b'baz=1'},
                receive,
                send,
            )
        )
        assert environ == {}

    def test_make_response(self):
        environ = {'asgi.send': AsyncMock(), 'asgi.scope': {'type': 'http'}}
        _run(
            async_asgi.make_response(
                '202 ACCEPTED', [('foo', 'bar')], b'payload', environ
            )
        )
        environ['asgi.send'].mock.assert_any_call(
            {
                'type': 'http.response.start',
                'status': 202,
                'headers': [(b'foo', b'bar')],
            }
        )
        environ['asgi.send'].mock.assert_any_call(
            {'type': 'http.response.body', 'body': b'payload'}
        )

    def test_make_response_websocket_accept(self):
        environ = {
            'asgi.send': AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        _run(
            async_asgi.make_response(
                '200 OK', [('foo', 'bar')], b'payload', environ
            )
        )
        environ['asgi.send'].mock.assert_called_with(
            {'type': 'websocket.accept', 'headers': [(b'foo', b'bar')]}
        )

    def test_make_response_websocket_reject(self):
        environ = {
            'asgi.send': AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        _run(
            async_asgi.make_response(
                '401 UNAUTHORIZED', [('foo', 'bar')], b'payload', environ
            )
        )
        environ['asgi.send'].mock.assert_called_with(
            {'type': 'websocket.close', 'reason': 'payload'}
        )

    def test_make_response_websocket_reject_no_payload(self):
        environ = {
            'asgi.send': AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        _run(
            async_asgi.make_response(
                '401 UNAUTHORIZED', [('foo', 'bar')], None, environ
            )
        )
        environ['asgi.send'].mock.assert_called_with(
            {'type': 'websocket.close'}
        )
