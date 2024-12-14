import os
from unittest import mock

from engineio.async_drivers import asgi as async_asgi


class TestAsgi:
    async def test_create_app(self):
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

    async def test_engineio_routing(self):
        mock_server = mock.MagicMock()
        mock_server.handle_request = mock.AsyncMock()

        app = async_asgi.ASGIApp(mock_server)
        scope = {'type': 'http', 'path': '/engine.io/'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/engine.io/'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/engine.iofoo/'}
        await app(scope, 'receive', mock.AsyncMock())
        mock_server.handle_request.assert_not_awaited()

        app = async_asgi.ASGIApp(mock_server, engineio_path=None)
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/foo'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )

        app = async_asgi.ASGIApp(mock_server, engineio_path='mysocket.io')
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/mysocket.io'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/mysocket.io/'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/mysocket.io/foo'}
        await app(scope, 'receive', 'send')
        mock_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send'
        )
        mock_server.handle_request.reset_mock()
        scope = {'type': 'http', 'path': '/mysocket.iofoo'}
        await app(scope, 'receive', mock.AsyncMock())
        mock_server.handle_request.assert_not_awaited()

    async def test_other_app_routing(self):
        other_app = mock.AsyncMock()
        app = async_asgi.ASGIApp('eio', other_app)
        scope = {'type': 'http', 'path': '/foo'}
        await app(scope, 'receive', 'send')
        other_app.assert_awaited_once_with(scope, 'receive', 'send')

    async def test_other_app_lifespan_routing(self):
        other_app = mock.AsyncMock()
        app = async_asgi.ASGIApp('eio', other_app)
        scope = {'type': 'lifespan'}
        await app(scope, 'receive', 'send')
        other_app.assert_awaited_once_with(scope, 'receive', 'send')

    async def test_static_file_routing(self):
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

        async def check_path(path, status_code, content_type, body):
            scope = {'type': 'http', 'path': path}
            receive = mock.AsyncMock(return_value={'type': 'http.request'})
            send = mock.AsyncMock()
            await app(scope, receive, send)
            send.assert_any_await(
                {
                    'type': 'http.response.start',
                    'status': status_code,
                    'headers': [
                        (b'Content-Type', content_type.encode('utf-8'))
                    ],
                }
            )
            send.assert_any_await(
                {'type': 'http.response.body', 'body': body.encode('utf-8')}
            )

        await check_path('/', 200, 'text/html', '<html></html>\n')
        await check_path('/foo', 200, 'text/plain', '<html></html>\n')
        await check_path('/foo/bar', 404, 'text/plain', 'Not Found')
        await check_path('/static/index.html', 200, 'text/html',
                         '<html></html>\n')
        await check_path('/static/foo.bar', 404, 'text/plain', 'Not Found')
        await check_path(
            '/static/test/index.html', 200, 'text/html', '<html></html>\n'
        )
        await check_path('/static/test/index.html', 200, 'text/html',
                         '<html></html>\n')
        await check_path('/static/test/files/', 200, 'text/html',
                         '<html>file</html>\n')
        await check_path('/static/test/files/file.txt', 200, 'text/plain',
                         'file\n')
        await check_path('/static/test/files/x.html', 404, 'text/plain',
                         'Not Found')
        await check_path('/static2/test/', 200, 'image/gif', '<html></html>\n')
        await check_path('/static2/test/index.html', 200, 'image/gif',
                         '<html></html>\n')
        await check_path('/static2/test/files/', 200, 'image/gif',
                         '<html>file</html>\n')
        await check_path('/static2/test/files/file.txt', 200, 'image/gif',
                         'file\n')
        await check_path('/static2/test/files/x.html', 404, 'text/plain',
                         'Not Found')
        await check_path('/bar/foo', 404, 'text/plain', 'Not Found')
        await check_path('', 404, 'text/plain', 'Not Found')

        app.static_files[''] = 'index.html'
        await check_path('/static/test/', 200, 'text/html', '<html></html>\n')

        app.static_files[''] = {'filename': 'index.html'}
        await check_path('/static/test/', 200, 'text/html', '<html></html>\n')

        app.static_files[''] = {
            'filename': 'index.html',
            'content_type': 'image/gif',
        }
        await check_path('/static/test/', 200, 'image/gif', '<html></html>\n')

        app.static_files[''] = {'filename': 'test.gif'}
        await check_path('/static/test/', 404, 'text/plain', 'Not Found')

        app.static_files = {}
        await check_path('/static/test/index.html', 404, 'text/plain',
                         'Not Found')

    async def test_lifespan_startup(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                              {'type': 'lifespan.shutdown'}])
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_any_await(
            {'type': 'lifespan.startup.complete'}
        )

    async def test_lifespan_startup_sync_function(self):
        up = False

        def startup():
            nonlocal up
            up = True

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                              {'type': 'lifespan.shutdown'}])
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_any_await(
            {'type': 'lifespan.startup.complete'}
        )
        assert up

    async def test_lifespan_startup_async_function(self):
        up = False

        async def startup():
            nonlocal up
            up = True

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(side_effect=[{'type': 'lifespan.startup'},
                                              {'type': 'lifespan.shutdown'}])
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_any_await(
            {'type': 'lifespan.startup.complete'}
        )
        assert up

    async def test_lifespan_startup_function_exception(self):
        up = False

        def startup():
            raise Exception

        app = async_asgi.ASGIApp('eio', on_startup=startup)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(side_effect=[{'type': 'lifespan.startup'}])
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with({'type': 'lifespan.startup.failed'})
        assert not up

    async def test_lifespan_shutdown(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )

    async def test_lifespan_shutdown_sync_function(self):
        down = False

        def shutdown():
            nonlocal down
            down = True

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )
        assert down

    async def test_lifespan_shutdown_async_function(self):
        down = False

        async def shutdown():
            nonlocal down
            down = True

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )
        assert down

    async def test_lifespan_shutdown_function_exception(self):
        down = False

        def shutdown():
            raise Exception

        app = async_asgi.ASGIApp('eio', on_shutdown=shutdown)
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(return_value={'type': 'lifespan.shutdown'})
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with({'type': 'lifespan.shutdown.failed'})
        assert not down

    async def test_lifespan_invalid(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'lifespan'}
        receive = mock.AsyncMock(side_effect=[{'type': 'lifespan.foo'},
                                              {'type': 'lifespan.shutdown'}])
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_awaited_once_with(
            {'type': 'lifespan.shutdown.complete'}
        )

    async def test_not_found(self):
        app = async_asgi.ASGIApp('eio')
        scope = {'type': 'http', 'path': '/foo'}
        receive = mock.AsyncMock(return_value={'type': 'http.request'})
        send = mock.AsyncMock()
        await app(scope, receive, send)
        send.assert_any_await(
            {
                'type': 'http.response.start',
                'status': 404,
                'headers': [(b'Content-Type', b'text/plain')],
            }
        )
        send.assert_any_await(
            {'type': 'http.response.body', 'body': b'Not Found'}
        )

    async def test_translate_request(self):
        receive = mock.AsyncMock(
            return_value={'type': 'http.request', 'body': b'hello world'}
        )
        send = mock.AsyncMock()
        environ = await async_asgi.translate_request(
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
        body = await environ['wsgi.input'].read()
        assert body == b'hello world'

    async def test_translate_request_no_query_string(self):
        receive = mock.AsyncMock(
            return_value={'type': 'http.request', 'body': b'hello world'}
        )
        send = mock.AsyncMock()
        environ = await async_asgi.translate_request(
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
        body = await environ['wsgi.input'].read()
        assert body == b'hello world'

    async def test_translate_request_with_large_body(self):
        receive = mock.AsyncMock(
            side_effect=[
                {'type': 'http.request', 'body': b'hello ', 'more_body': True},
                {'type': 'http.request', 'body': b'world', 'more_body': True},
                {'type': 'foo.bar'},  # should stop parsing here
                {'type': 'http.request', 'body': b'!!!'},
            ]
        )
        send = mock.AsyncMock()
        environ = await async_asgi.translate_request(
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
        body = await environ['wsgi.input'].read()
        assert body == b'hello world'

    async def test_translate_websocket_request(self):
        receive = mock.AsyncMock(return_value={'type': 'websocket.connect'})
        send = mock.AsyncMock()
        await async_asgi.translate_request(
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
        send.assert_not_awaited()

    async def test_translate_unknown_request(self):
        receive = mock.AsyncMock(return_value={'type': 'http.foo'})
        send = mock.AsyncMock()
        environ = await async_asgi.translate_request(
            {'type': 'http', 'path': '/foo/bar', 'query_string': b'baz=1'},
            receive,
            send,
        )
        assert environ == {}

    async def test_translate_request_bad_unicode(self):
        receive = mock.AsyncMock(return_value={'type': 'http.request',
                                               'body': b'foo'})
        send = mock.AsyncMock()
        environ = await async_asgi.translate_request(
            {
                'type': 'http.request',
                'headers': [
                    (b'a', b'b'),
                    (b'c', b'\xa0'),
                    (b'e', b'f'),
                ],
                'path': '/foo/bar',
                'query_string': b'baz=1&bad=\xa0',
            },
            receive,
            send,
        )
        assert environ['HTTP_A'] == 'b'
        assert environ['HTTP_E'] == 'f'
        assert 'HTTP_C' not in environ
        assert environ['QUERY_STRING'] == ''
        assert environ['RAW_URI'] == '/foo/bar'

    async def test_make_response(self):
        environ = {'asgi.send': mock.AsyncMock(),
                   'asgi.scope': {'type': 'http'}}
        await async_asgi.make_response(
            '202 ACCEPTED', [('foo', 'bar')], b'payload', environ
        )
        environ['asgi.send'].assert_any_await(
            {
                'type': 'http.response.start',
                'status': 202,
                'headers': [(b'foo', b'bar')],
            }
        )
        environ['asgi.send'].assert_any_await(
            {'type': 'http.response.body', 'body': b'payload'}
        )

    async def test_make_response_websocket_accept(self):
        environ = {
            'asgi.send': mock.AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        await async_asgi.make_response(
            '200 OK', [('foo', 'bar')], b'payload', environ
        )
        environ['asgi.send'].assert_awaited_with(
            {'type': 'websocket.accept', 'headers': [(b'foo', b'bar')]}
        )

    async def test_make_response_websocket_reject(self):
        environ = {
            'asgi.send': mock.AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        await async_asgi.make_response(
            '401 UNAUTHORIZED', [('foo', 'bar')], b'payload', environ
        )
        environ['asgi.send'].assert_awaited_with(
            {'type': 'websocket.close', 'reason': 'payload'}
        )

    async def test_make_response_websocket_reject_no_payload(self):
        environ = {
            'asgi.send': mock.AsyncMock(),
            'asgi.scope': {'type': 'websocket'},
        }
        await async_asgi.make_response(
            '401 UNAUTHORIZED', [('foo', 'bar')], None, environ
        )
        environ['asgi.send'].assert_awaited_with(
            {'type': 'websocket.close'}
        )

    async def test_sub_app_routing(self):

        class ASGIDispatcher:
            def __init__(self, routes):
                self.routes = routes

            async def __call__(self, scope, receive, send):
                path = scope['path']
                for prefix, app in self.routes.items():
                    if path.startswith(prefix):
                        await app(scope, receive, send)
                        return
                assert False, 'No route found'

        other_app = mock.AsyncMock()
        mock_server = mock.MagicMock()
        mock_server.handle_request = mock.AsyncMock()
        eio_app = async_asgi.ASGIApp(mock_server, engineio_path=None)
        root_app = ASGIDispatcher({'/foo': other_app, '/eio': eio_app})
        scope = {'type': 'http', 'path': '/foo/bar'}
        await root_app(scope, 'receive', 'send')
        other_app.assert_awaited_once_with(scope, 'receive', 'send')
        scope = {'type': 'http', 'path': '/eio/'}
        await root_app(scope, 'receive', 'send')
        eio_app.engineio_server.handle_request.assert_awaited_once_with(
            scope, 'receive', 'send')
