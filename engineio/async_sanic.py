import sys
from urllib.parse import urlsplit

from sanic.response import HTTPResponse


def create_route(app, engineio_server, engineio_endpoint):
    """This function sets up the engine.io endpoint as a route for the
    application.

    Note that both GET and POST requests must be hooked up on the engine.io
    endpoint.
    """
    app.add_route(engineio_server.handle_request, engineio_endpoint,
                  methods=['GET', 'POST'])


def translate_request(request):
    """This function takes the arguments passed to the request handler and
    uses them to generate a WSGI compatible environ dictionary.
    """
    class AwaitablePayload(object):
        def __init__(self, payload):
            self.payload = payload or b''

        async def read(self, length=None):
            if length is None:
                r = self.payload
                self.payload = b''
            else:
                r = self.payload[:length]
                self.payload = self.payload[length:]
            return r

    url = request.url + ('?' + request.query_string
                         if request.query_string else '')
    uri_parts = urlsplit(url)
    environ = {
        'wsgi.input': AwaitablePayload(request.body),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.async': True,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'SERVER_SOFTWARE': 'sanic',
        'REQUEST_METHOD': request.method,
        'QUERY_STRING': uri_parts.query or '',
        'RAW_URI': url,
        'SERVER_PROTOCOL': 'HTTP/' + request.version,
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '0',
        'SERVER_NAME': 'sanic',
        'SERVER_PORT': '0',
        'sanic.request': request
    }

    for hdr_name, hdr_value in request.headers.items():
        hdr_name = hdr_name.upper()
        if hdr_name == 'CONTENT-TYPE':
            environ['CONTENT_TYPE'] = hdr_value
            continue
        elif hdr_name == 'CONTENT-LENGTH':
            environ['CONTENT_LENGTH'] = hdr_value
            continue

        key = 'HTTP_%s' % hdr_name.replace('-', '_')
        if key in environ:
            hdr_value = '%s,%s' % (environ[key], hdr_value)

        environ[key] = hdr_value

    environ['wsgi.url_scheme'] = environ.get('HTTP_X_FORWARDED_PROTO', 'http')

    path_info = uri_parts.path

    environ['PATH_INFO'] = path_info
    environ['SCRIPT_NAME'] = ''

    return environ


def make_response(status, headers, payload):
    """This function generates an appropriate response object for this async
    mode.
    """
    headers_dict = {}
    content_type = None
    for h in headers:
        if h[0].lower() == 'content-type':
            content_type = h[1]
        else:
            headers_dict[h[0]] = h[1]
    return HTTPResponse(body_bytes=payload, content_type=content_type,
                        status=int(status.split()[0]), headers=headers_dict)


async = {
    'asyncio': True,
    'create_route': create_route,
    'translate_request': translate_request,
    'make_response': make_response,
    # sanic does not have a websocket implementation yet :(
    'websocket': None,
    'websocket_class': None
}
