.. engineio documentation master file, created by
   sphinx-quickstart on Sat Jun 13 23:41:23 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Getting Started
===============

What is Engine.IO?
------------------

Engine.IO is a lightweight transport protocol that enables real-time
bidirectional event-based communication between clients (typically, though
not always, web browsers) and a server. The official implementations of the
client and server components are written in JavaScript. This package provides
Python implementations of both, each with standard and ``asyncio`` variants.

The Engine.IO protocol is extremely simple. Once a connection between a client
and a server is established, either side can send "messages" to the other
side. Event handlers provided by the applications on both ends are invoked
when a message is received, or when a connection is established or dropped.

Client Examples
---------------

The example that follows shows a simple Python client::

    import engineio

    eio = engineio.Client()

    @eio.on('connect')
    def on_connect():
        print('connection established')

    @eio.on('message')
    def on_message(data):
        print('message received with ', data)
        eio.send({'response': 'my response'})
    
    @eio.on('disconnect')
    def on_disconnect():
        print('disconnected from server')
    
    eio.connect('http://localhost:5000')
    eio.wait()

And here is a similar client written using the official Engine.IO Javascript
client::

    <script src="/path/to/engine.io.js"></script>
    <script>
        var socket = eio('http://localhost:5000');
        socket.on('open', function() { console.log('connection established'); });
        socket.on('message', function(data) {
            console.log('message received with ' + data);
            socket.send({response: 'my response'});
        });
        socket.on('close', function() { console.log('disconnected from server'); });
    </script>

Client Features
---------------

- Can connect to other Engine.IO complaint servers besides the one in this package.
- Compatible with Python 3.6+.
- Two versions of the client, one for standard Python and another for ``asyncio``.
- Uses an event-based architecture implemented with decorators that hides the
  details of the protocol.
- Implements HTTP long-polling and WebSocket transports.

Server Examples
---------------

The following application is a basic example that uses the Eventlet
asynchronous server::

    import engineio
    import eventlet

    eio = engineio.Server()
    app = engineio.WSGIApp(eio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })

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
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)

Below is a similar application, coded for asyncio and the Uvicorn web server::

    import engineio
    import uvicorn

    eio = engineio.AsyncServer()
    app = engineio.ASGIApp(eio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })

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

    if __name__ == '__main__':
        uvicorn.run('127.0.0.1', 5000)

Server Features
---------------

- Can accept clients running other complaint Engine.IO clients besides the one in this
  package.
- Compatible with Python 3.6+.
- Two versions of the server, one for standard Python and another for ``asyncio``.
- Supports large number of clients even on modest hardware due to being
  asynchronous.
- Can be hosted on any `WSGI <https://wsgi.readthedocs.io/en/latest/index.html>`_ and
  `ASGI <https://asgi.readthedocs.io/en/latest/>`_ web servers includind
  `Gunicorn <https://gunicorn.org/>`_, `Uvicorn <https://github.com/encode/uvicorn>`_,
  `eventlet <http://eventlet.net/>`_ and `gevent <http://gevent.org>`_.
- Can be integrated with WSGI applications written in frameworks such as Flask, Django,
  etc.
- Can be integrated with `aiohttp <http://aiohttp.readthedocs.io/>`_,
  `sanic <http://sanic.readthedocs.io/>`_ and `tornado <http://www.tornadoweb.org/>`_
  ``asyncio`` applications.
- Uses an event-based architecture implemented with decorators that hides the
  details of the protocol.
- Implements HTTP long-polling and WebSocket transports.
- Supports XHR2 and XHR browsers as clients.
- Supports text and binary messages.
- Supports gzip and deflate HTTP compression.
- Configurable CORS responses to avoid cross-origin problems with browsers.
