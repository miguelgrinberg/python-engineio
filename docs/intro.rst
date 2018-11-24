.. engineio documentation master file, created by
   sphinx-quickstart on Sat Jun 13 23:41:23 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Getting Started
===============

What is Engine.IO?
------------------

Engine.IO is a lightweight transport protocol that enables real-time
bidirectional event-based communication between clients (typically web
browsers) and a server. The official implementations of the client and
server components are written in JavaScript.

The Engine.IO protocol is extremely simple. The example that follows shows the
client-side Javascript code required to setup an Engine.IO connection to
a server::

    var socket = eio('http://chat.example.com');
    socket.on('open', function() { alert('connected'); });
    socket.on('message', function(data) { alert(data); });
    socket.on('close', function() { alert('disconnected'); });
    socket.send('Hello from the client!');

Features
--------

- Fully compatible with the Javascript
  `engine.io-client <https://github.com/Automattic/engine.io-client>`_ library,
  and with other Engine.IO clients.
- Compatible with Python 2.7 and Python 3.3+.
- Supports large number of clients even on modest hardware due to being
  asynchronous.
- Compatible with `aiohttp <http://aiohttp.readthedocs.io/>`_,
  `sanic <http://sanic.readthedocs.io/>`_,
  `tornado <http://www.tornadoweb.org/>`_,
  `eventlet <http://eventlet.net/>`_,
  `gevent <http://gevent.org>`_,
  or any `WSGI <https://wsgi.readthedocs.io/en/latest/index.html>`_ or
  `ASGI <https://asgi.readthedocs.io/en/latest/>`_ compatible server.
- Includes WSGI and ASGI middlewares that integrate Engine.IO traffic with
  other web applications.
- Uses an event-based architecture implemented with decorators that hides the
  details of the protocol.
- Implements HTTP long-polling and WebSocket transports.
- Supports XHR2 and XHR browsers as clients.
- Supports text and binary messages.
- Supports gzip and deflate HTTP compression.
- Configurable CORS responses to avoid cross-origin problems with browsers.

Examples
--------

The following application is a basic example that uses the Eventlet
asynchronous server and includes a small Flask application that serves the
HTML/Javascript to the client::

    import engineio
    import eventlet
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

Below is a similar application, coded for asyncio (Python 3.5+ only) with the
aiohttp framework::

    from aiohttp import web
    import engineio

    eio = engineio.AsyncServer()
    app = web.Application()

    # attach the Engine.IO server to the application
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
        # run the aiohttp application
        web.run_app(app)

The client-side application must include the
`engine.io-client <https://github.com/Automattic/engine.io-client>`_ library
(version 1.5.0 or newer recommended).

Each time a client connects to the server the ``connect`` event handler is
invoked with the ``sid`` (session ID) assigned to the connection and the WSGI
environment dictionary. The server can inspect authentication or other headers
to decide if the client is allowed to connect. To reject a client the handler
must return ``False``.

When the client sends a message to the server the ``message`` event handler is
invoked with the ``sid`` and the message.

Finally, when the connection is broken, the ``disconnect`` event is called,
allowing the application to perform cleanup.

Because Engine.IO is a bidirectional protocol, the server can send messages to
any connected client at any time. The ``engineio.Server.send()`` method takes
the client's ``sid`` and the message payload, which can be of type ``str``,
``bytes``, ``list`` or ``dict`` (the last two are JSON encoded).
