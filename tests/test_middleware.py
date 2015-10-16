import unittest

import six
if six.PY3:
    from unittest import mock
else:
    import mock

from engineio import middleware


class TestMiddleware(unittest.TestCase):
    def test_wsgi_routing(self):
        mock_wsgi_app = mock.MagicMock()
        mock_eio_app = 'foo'
        m = middleware.Middleware(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/foo'}
        start_response = "foo"
        m(environ, start_response)
        mock_wsgi_app.assert_called_once_with(environ, start_response)

    def test_eio_routing(self):
        mock_wsgi_app = 'foo'
        mock_eio_app = mock.Mock()
        mock_eio_app.handle_request = mock.MagicMock()
        m = middleware.Middleware(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/engine.io/'}
        start_response = "foo"
        m(environ, start_response)
        mock_eio_app.handle_request.assert_called_once_with(environ,
                                                            start_response)

    def test_404(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        m = middleware.Middleware(mock_eio_app, mock_wsgi_app)
        environ = {'PATH_INFO': '/foo/bar'}
        start_response = mock.MagicMock()
        r = m(environ, start_response)
        self.assertEqual(r, ['Not Found'])
        start_response.assert_called_once_with(
            "404 Not Found", [('Content-type', 'text/plain')])

    def test_gunicorn_socket(self):
        mock_wsgi_app = None
        mock_eio_app = mock.Mock()
        m = middleware.Middleware(mock_eio_app, mock_wsgi_app)
        environ = {'gunicorn.socket': 123, 'PATH_INFO': '/foo/bar'}
        start_response = mock.MagicMock()
        m(environ, start_response)
        self.assertIn('eventlet.input', environ)
        self.assertEqual(environ['eventlet.input'].get_socket(), 123)
