.. engineio documentation master file, created by
   sphinx-quickstart on Sat Jun 13 23:41:23 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

engineio documentation
======================

:ref:`genindex` | :ref:`modindex` | :ref:`search`

This project implements an Engine.IO server that can run standalone or
integrated with a Python WSGI application. The following are some of its
features:

- Fully compatible with the Javascript
  `engine.io-client <https://github.com/Automattic/engine.io-client>`_ library.
- Compatible with Python 2.7 and Python 3.3+.
- Based on `Eventlet <http://eventlet.net/>`_, enabling large number of
  clients even on modest hardware.
- Includes a WSGI middleware that integrates Engine.IO traffic with standard
  WSGI applications.
- Uses an event-based architecture implemented with decorators that hides the
  details of the protocol.
- Implements HTTP long-polling and WebSocket transports.
- Supports XHR2 and XHR browsers as clients.
- Supports text and binary messages.
- Supports gzip and deflate HTTP compression.
- Configurable CORS responses to avoid cross-origin problems with browsers.

What is Engine.IO?
------------------

Engine.IO is a lightweight transport protocol that enables real-time
bidirectional event-based communication between clients (typically web
browsers) and a server. The official implementations of the client and
server components are written in JavaScript.

The protocol is extremely simple. The example that follows shows the
client-side Javascript code required to setup an Engine.IO connection to
a server::

    var socket = eio('http://chat.example.com');
    socket.on('open', function() {
       alert('connected');
       socket.on('message', function(data) { alert(data); });
       socket.on('close', function() { alert('disconnected'); });
    });

Getting Started
---------------

The following is a basic example of an Engine.IO server that uses Flask to
deploy the client code to the browser::

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

The client-side application must include the
`engine.io-client <https://github.com/Automattic/engine.io-client>`_ library
(versions 1.5.0 or newer recommended).

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
``bytes`` or ``dict`` (JSON encoded).

API Reference
-------------

.. toctree::
   :maxdepth: 2

.. module:: engineio

.. autoclass:: Middleware
   :members:

.. autoclass:: Server
   :members:
