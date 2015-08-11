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
  an asynchronous server based on `Eventlet <http://eventlet.net/>`_ or
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

The following sections describe a variaty of deployment strategies for
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

    import eventlet
    app = engineio.Middleware(eio)
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

An alternative to running the eventlet WSGI server as above is to use
`gunicorn <gunicorn.org>`_, a fully featured pure Python web server. The
command to launch the application under gunicorn is shown below::

    $ gunicorn -k eventlet -w 1 module:app

It is important to specify that only one worker process is used with gunicorn.
A single worker can handle a large number of clients when using eventlet.

Note that when using gunicorn the WebSocket transport is not available. To make
WebSocket work, eventlet uses its own extensions to the WSGI standard, which
gunicorn does not support.

Note: Eventlet provides a ``monkey_patch()`` function that replaces all the
blocking functions in the standard library with equivalent asynchronous
versions. While python-engineio does not require monkey patching, other
libraries such as database drivers are likely to require it.

Gevent
~~~~~~

`Gevent <http://gevent.org>`_ is another asynchronous framework based on
coroutines, very similar to eventlet. Only the long-polling transport is
currently available when using gevent.

Instances of class ``engineio.Server`` will automatically use gevent for
asynchronous operations if the library is installed and eventlet is not
installed. To request gevent to be selected explicitly, the ``async_mode``
option can be given in the constructor::

    eio = engineio.Server(async_mode='gevent')

A server configured for gevent is deployed as a regular WSGI application,
using the provided ``engineio.Middleware``::

    from gevent import pywsgi
    app = engineio.Middleware(eio)
    pywsgi.WSGIServer(('', 5000), app).serve_forever()

An alternative to running the eventlet WSGI server as above is to use
`gunicorn <gunicorn.org>`_, a fully featured pure Python web server. The
command to launch the application under gunicorn is shown below::

    $ gunicorn -k gevent -w 1 module:app

It is important to specify that only one worker process is used with gunicorn.
A single worker can handle a large number of clients when using gevent.

Note: Gevent provides a ``monkey_patch()`` function that replaces all the
blocking functions in the standard library with equivalent asynchronous
versions. While python-engineio does not require monkey patching, other
libraries such as database drivers are likely to require it.

Standard Threading Library
~~~~~~~~~~~~~~~~~~~~~~~~~~

While not comparable to eventlet and gevent in terms of performance,
python-engineio can also be configured to work with multi-threaded web servers
that use standard Python threads. This is an ideal setup to use with
development servers such as `Werkzeug <http://werkzeug.pocoo.org>`_. Only the
long-polling transport is currently available when using gevent.

Instances of class ``engineio.Server`` will automatically use the threading
mode if eventlet and gevent are not installed. To request the threading
mode explicitly, the ``async_mode`` option can be given in the constructor::

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
can handle concurrent requests using threads, as a client can have up to two
outstanding requests at any given time. The Werkzeug server is single-threaded
by default, so the ``threaded=True`` option must be included.

Multi-process deployments
~~~~~~~~~~~~~~~~~~~~~~~~~

Engine.IO is a stateful protocol, which makes horizontal scaling more
difficult. To deploy a cluster of Engine.IO processes, possibly hosted in
multiple servers, the following conditions must be met:

- Each Engine.IO process must be able to handle multiple requests, either by
  using eventlet, gevent, or standard threads.
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
