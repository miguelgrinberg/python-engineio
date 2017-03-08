python-engineio
===============

.. image:: https://travis-ci.org/miguelgrinberg/python-engineio.svg?branch=master
    :target: https://travis-ci.org/miguelgrinberg/python-engineio

Python implementation of the `Engine.IO`_ realtime server.

Features
--------

- Fully compatible with the Javascript `engine.io-client`_ library, versions 1.5.0 and up.
- Compatible with Python 2.7 and Python 3.3+.
- Supports large number of clients even on modest hardware when used with an asynchronous server based on `asyncio`_(`sanic`_ or `aiohttp`_), `eventlet`_ or `gevent`_. For development and testing, any WSGI compliant multi-threaded server can be used.
- Includes a WSGI middleware that integrates Engine.IO traffic with standard WSGI applications.
- Uses an event-based architecture implemented with decorators that hides the details of the protocol.
- Implements HTTP long-polling and WebSocket transports.
- Supports XHR2 and XHR browsers as clients.
- Supports text and binary messages.
- Supports gzip and deflate HTTP compression.
- Configurable CORS responses to avoid cross-origin problems with browsers.

Examples
--------

The following application uses the Eventlet asynchronous server, and includes a
small Flask application that serves the HTML/Javascript to the client:


.. code:: python

    import engineio
    import eventlet
    import eventlet.wsgi
    from flask import Flask, render_template

    eio = engineio.Server()
    app = Flask(__name__)

    @app.route('/')
    def index():
        """Serve the client-side application."""
        return render_template('index.html')

    @eio.on('connect')
    def connect(sid, environ):
        print("connect ", sid)

    @eio.on('message')
    def message(sid, data):
        print("message ", data)
        eio.send(sid, 'reply')

    @eio.on('disconnect')
    def disconnect(sid):
        print('disconnect ', sid)

    if __name__ == '__main__':
        # wrap Flask application with engineio's middleware
        app = engineio.Middleware(eio, app)

        # deploy as an eventlet WSGI server
        eventlet.wsgi.server(eventlet.listen(('', 8000)), app)


And below is a similar example, coded for asyncio (Python 3.5+ only) with the
`aiohttp`_ framework:


.. code:: python

    from aiohttp import web
    import engineio

    eio = engineio.AsyncServer()
    app = web.Application()
    eio.attach(app)

    async def index(request):
        """Serve the client-side application."""
        with open('index.html') as f:
            return web.Response(text=f.read(), content_type='text/html')

    @eio.on('connect')
    def connect(sid, environ):
        print("connect ", sid)

    @eio.on('message')
    async def message(sid, data):
        print("message ", data)
        await eio.send(sid, 'reply')

    @eio.on('disconnect')
    def disconnect(sid):
        print('disconnect ', sid)

    app.router.add_static('/static', 'static')
    app.router.add_get('/', index)

    if __name__ == '__main__':
        web.run_app(app)

Resources
---------

-  `Documentation`_
-  `PyPI`_

.. _Engine.IO: https://github.com/Automattic/engine.io
.. _engine.io-client: https://github.com/Automattic/engine.io-client
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _sanic: http://sanic.readthedocs.io/
.. _aiohttp: http://aiohttp.readthedocs.io/
.. _eventlet: http://eventlet.net/
.. _gevent: http://gevent.org/
.. _aiohttp: http://aiohttp.readthedocs.io/
.. _Documentation: http://pythonhosted.org/python-engineio
.. _PyPI: https://pypi.python.org/pypi/python-engineio
