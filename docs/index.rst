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
  `engine.io-client <https://github.com/Automattic/engine.io-client>`_ library,
  versions 1.5.0 and up.
- Compatible with Python 2.7 and Python 3.3+.
- Supports large number of clients even on modest hardware when used with
  an asynchronous server based on `eventlet <http://eventlet.net/>`_ or
  `gevent <http://gevent.org>`_. For development and testing, any WSGI
  compliant multi-threaded server can be used.
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
    socket.on('open', function() { alert('connected'); });
    socket.on('message', function(data) { alert(data); });
    socket.on('close', function() { alert('disconnected'); });
    socket.send('Hello from the client!');

Getting Started
---------------

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

Deployment
----------

The following sections describe a variety of deployment strategies for
Engine.IO servers.

Eventlet
~~~~~~~~

`Eventlet <http://eventlet.net/>`_ is a high performance concurrent networking
library for Python 2 and 3 that uses coroutines, enabling code to be written in
the same style used with the blocking standard library functions. An Engine.IO
server deployed with eventlet has access to the long-polling and WebSocket
transports.

Instances of class ``engineio.Server`` will automatically use eventlet for
asynchronous operations if the library is installed. To request its use
explicitly, the ``async_mode`` option can be given in the constructor::

    eio = engineio.Server(async_mode='eventlet')

A server configured for eventlet is deployed as a regular WSGI application,
using the provided ``engineio.Middleware``::

    app = engineio.Middleware(eio)
    import eventlet
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

An alternative to running the eventlet WSGI server as above is to use
`gunicorn <gunicorn.org>`_, a fully featured pure Python web server. The
command to launch the application under gunicorn is shown below::

    $ gunicorn -k eventlet -w 1 module:app

Due to limitations in its load balancing algorithm, gunicorn can only be used
with one worker process, so the ``-w 1`` option is required. Note that a
single eventlet worker can handle a large number of concurrent clients.

Another limitation when using gunicorn is that the WebSocket transport is not
available, because this transport it requires extensions to the WSGI standard.

Note: Eventlet provides a ``monkey_patch()`` function that replaces all the
blocking functions in the standard library with equivalent asynchronous
versions. While python-engineio does not require monkey patching, other
libraries such as database drivers are likely to require it.

Gevent
~~~~~~

`Gevent <http://gevent.org>`_ is another asynchronous framework based on
coroutines, very similar to eventlet. An Engine.IO server deployed with
gevent has access to the long-polling transport. If project
`gevent-websocket <https://bitbucket.org/Jeffrey/gevent-websocket/>`_ is
installed, the WebSocket transport is also available. Note that when using the
uWSGI server, the native WebSocket implementation of uWSGI can be used instead
of gevent-websocket (see next section for details on this).

Instances of class ``engineio.Server`` will automatically use gevent for
asynchronous operations if the library is installed and eventlet is not
installed. To request gevent to be selected explicitly, the ``async_mode``
option can be given in the constructor::

    # gevent alone or with gevent-websocket
    eio = engineio.Server(async_mode='gevent')

A server configured for gevent is deployed as a regular WSGI application,
using the provided ``engineio.Middleware``::

    from gevent import pywsgi
    app = engineio.Middleware(eio)
    pywsgi.WSGIServer(('', 8000), app).serve_forever()

If the WebSocket transport is installed, then the server must be started as
follows::

    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    app = engineio.Middleware(eio)
    pywsgi.WSGIServer(('', 8000), app,
                      handler_class=WebSocketHandler).serve_forever()

An alternative to running the gevent WSGI server as above is to use
`gunicorn <gunicorn.org>`_, a fully featured pure Python web server. The
command to launch the application under gunicorn is shown below::

    $ gunicorn -k gevent -w 1 module:app

Or to include WebSocket::

    $ gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 module: app

Same as with eventlet, due to limitations in its load balancing algorithm,
gunicorn can only be used with one worker process, so the ``-w 1`` option is
required. Note that a single gevent worker can handle a large number of
concurrent clients.

Note: Gevent provides a ``monkey_patch()`` function that replaces all the
blocking functions in the standard library with equivalent asynchronous
versions. While python-engineio does not require monkey patching, other
libraries such as database drivers are likely to require it.

Gevent with uWSGI
~~~~~~~~~~~~~~~~~

When using the uWSGI server in combination with gevent, the Engine.IO server
can take advantage of uWSGI's native WebSocket support.

Instances of class ``engineio.Server`` will automatically use this option for
asynchronous operations if both gevent and uWSGI are installed and eventlet is
not installed. uWSGI must be compiled with WebSocket and SSL support for the
WebSocket transport to be available. To request this asynchoronous mode
explicitly, the  ``async_mode`` option can be given in the constructor::

    # gevent alone or with gevent-websocket
    eio = engineio.Server(async_mode='gevent_uwsgi')

A complete explanation of the configuration and usage of the uWSGI server is
beyond the scope of this documentation. The uWSGI server is a fairly complex
package that provides a large and comprehensive set of options. As way of an
introduction, the following command starts a uWSGI server for the
``latency.py`` example on port 5000::

    $ uwsgi --http :5000 --gevent 1000 --http-websockets --master --wsgi-file latency.py --callable app

Standard Threading Library
~~~~~~~~~~~~~~~~~~~~~~~~~~

While not comparable to eventlet and gevent in terms of performance,
the Engine.IO server can also be configured to work with multi-threaded web
servers that use standard Python threads. This is an ideal setup to use with
development servers such as `Werkzeug <http://werkzeug.pocoo.org>`_. Only the
long-polling transport is currently available when using standard threads.

Instances of class ``engineio.Server`` will automatically use the threading
mode if neither eventlet nor gevent are not installed. To request the
threading mode explicitly, the ``async_mode`` option can be given in the
constructor::

    eio = engineio.Server(async_mode='threading')

A server configured for threading is deployed as a regular web application,
using any WSGI complaint multi-threaded server. The example below deploys an
Engine.IO application combined with a Flask web application, using Flask's
development web server based on Werkzeug::

    eio = engineio.Server(async_mode='threading')
    app = Flask(__name__)
    app.wsgi_app = engineio.Middleware(eio, app.wsgi_app)

    # ... Engine.IO and Flask handler functions ...

    if __name__ == '__main__':
        app.run(threaded=True)

When using the threading mode, it is important to ensure that the WSGI server
can handle multiple concurrent requests using threads, since a client can have
up to two outstanding requests at any given time. The Werkzeug server is
single-threaded by default, so the ``threaded=True`` option is required.

Note that servers that use worker processes instead of threads, such as
gunicorn, do not support an Engine.IO server configured in threading mode.

Multi-process deployments
~~~~~~~~~~~~~~~~~~~~~~~~~

Engine.IO is a stateful protocol, which makes horizontal scaling more
difficult. To deploy a cluster of Engine.IO processes (hosted on one or
multiple servers), the following conditions must be met:

- Each Engine.IO process must be able to handle multiple requests, either by
  using eventlet, gevent, or standard threads. Worker processes that only
  handle one request at a time are not supported.
- The load balancer must be configured to always forward requests from a client
  to the same process. Load balancers call this *sticky sessions*, or
  *session affinity*.

API Reference
-------------

.. toctree::
   :maxdepth: 2

.. module:: engineio

.. autoclass:: Middleware
   :members:

.. autoclass:: Server
   :members:
