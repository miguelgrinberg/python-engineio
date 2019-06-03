import os
import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

import engineio


class TestWSGIApp(unittest.TestCase):
    def test_wsgi_routing(self):
        mock_wsgi_app = mock.MagicMock()
        mock_eio_app = 'foo'
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/foo'}
        start_response = "foo"
        m(environ, start_response)
        mock_wsgi_app.assert_called_once_with(environ, start_response)

    def test_eio_routing(self):
        mock_wsgi_app = 'foo'
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/engine.io/'}
        start_response = "foo"
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_static_files(self):
        root_dir = os.path.dirname(__file__)
        m = engineio.WSGIApp('foo', None, static_files={
            '/': root_dir + '/index.html',
            '/foo': {'content_type': 'text/plain',
                     'filename': root_dir + '/index.html'},
            '/static': root_dir,
            '/static/test/': root_dir + '/',
        })

        def check_path(path, status_code, content_type, body):
            environ = {'PATH_INFO': path}
            start_response = mock.MagicMock()
            r = m(environ, start_response)
            self.assertEqual(r, [body.encode('utf-8')])
            start_response.assert_called_once_with(
                status_code, [('Content-Type', content_type)])

        check_path('/', '200 OK', 'text/html', '<html></html>\n')
        check_path('/foo', '200 OK', 'text/plain', '<html></html>\n')
        check_path('/static/index.html', '200 OK', 'text/html',
                   '<html></html>\n')
        check_path('/static/foo.bar', '404 Not Found', 'text/plain',
                   'Not Found')
        check_path('/static/test/index.html', '200 OK', 'text/html',
                   '<html></html>\n')
        check_path('/static/test/', '200 OK', 'text/html', '<html></html>\n')
        check_path('/bar/foo', '404 Not Found', 'text/plain', 'Not Found')
        check_path('', '404 Not Found', 'text/plain', 'Not Found')

        m.static_files[''] = 'index.html'
        check_path('/static/test/', '200 OK', 'text/html',
                   '<html></html>\n')

        m.static_files[''] = {'filename': 'index.html'}
        check_path('/static/test/', '200 OK', 'text/html',
                   '<html></html>\n')

        m.static_files[''] = {'filename': 'index.html',
                              'content_type': 'image/gif'}
        check_path('/static/test/', '200 OK', 'image/gif',
                   '<html></html>\n')

        m.static_files[''] = {'filename': 'test.gif'}
        check_path('/static/test/', '404 Not Found', 'text/plain',
                   'Not Found')

        m.static_files = {}
        check_path('/static/test/index.html', '404 Not Found', 'text/plain',
                   'Not Found')

    def test_404(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/foo/bar'}
        start_response = mock.MagicMock()
        r = m(environ, start_response)
        self.assertEqual(r, [b'Not Found'])
        start_response.assert_called_once_with(
            "404 Not Found", [('Content-Type', 'text/plain')])

    def test_custom_eio_path(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app, engineio_path='foo')
        environ = {'PATH_INFO': '/engine.io/'}
        start_response = mock.MagicMock()
        r = m(environ, start_response)
        self.assertEqual(r, [b'Not Found'])
        start_response.assert_called_once_with(
            "404 Not Found", [('Content-Type', 'text/plain')])

        environ = {'PATH_INFO': '/foo/'}
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_custom_eio_path_slashes(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app,
                             engineio_path='/foo/')
        environ = {'PATH_INFO': '/foo/'}
        start_response = mock.MagicMock()
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_custom_eio_path_leading_slash(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app, engineio_path='/foo')
        environ = {'PATH_INFO': '/foo/'}
        start_response = mock.MagicMock()
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_custom_eio_path_trailing_slash(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app, engineio_path='foo/')
        environ = {'PATH_INFO': '/foo/'}
        start_response = mock.MagicMock()
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_gunicorn_socket(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        m = engineio.WSGIApp(mock_eio_app, mock_wsgi_app)
        environ = {'gunicorn.socket': 123, 'PATH_INFO': '/foo/bar'}
        start_response = mock.MagicMock()
        m(environ, start_response)
        self.assertIn('eventlet.input', environ)
        self.assertEqual(environ['eventlet.input'].get_socket(), 123)

    def test_legacy_middleware_class(self):
        m = engineio.Middleware('eio', 'wsgi', 'eio_path')
        self.assertEqual(m.engineio_app, 'eio')
        self.assertEqual(m.wsgi_app, 'wsgi')
        self.assertEqual(m.static_files, {})
        self.assertEqual(m.engineio_path, 'eio_path')
