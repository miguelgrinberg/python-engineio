import os


class App:
    """A generic ASGI application that serves static files."""
    def __init__(self, files):
        self.files = files

    def __call__(self, scope):
        return self.serve_static_file(scope)

    def serve_static_file(self, scope):
        async def _app(receive, send):
            event = await receive()
            if event['type'] == 'lifespan.startup':
                await send({'type': 'lifespan.startup.complete'})
            elif event['type'] == 'lifespan.shutdown':
                await send({'type': 'lifespan.shutdown.complete'})
            elif event['type'] == 'http.request':
                if scope['path'] in self.files:
                    content_type = self.files[scope['path']]
                    status_code = 200
                    with open(os.path.join('.', scope['path'][1:])) as f:
                        payload = f.read().encode('utf-8')
                else:
                    content_type = b'text/plain'
                    status_code = 404
                    payload = b'not found'
                await send({'type': 'http.response.start',
                            'status': status_code,
                            'headers': [(b'Content-Type', content_type)]})
                await send({'type': 'http.response.body',
                            'body': payload})
        return _app
