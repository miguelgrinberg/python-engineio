python-engineio
===============

.. image:: https://travis-ci.org/miguelgrinberg/python-engineio.svg?branch=master
    :target: https://travis-ci.org/miguelgrinberg/python-engineio

Python implementation of the `Engine.IO`_ realtime server.

Features
--------

- Fully compatible with the Javascript `engine.io-client`_ library, versions 1.5.0 and up.
- Compatible with Python 2.7 and Python 3.3+.
- Supports large number of clients even on modest hardware when used with an asynchronous server based on `eventlet`_ or `gevent`_. For development and testing, any WSGI compliant multi-threaded server can be used.
- Includes a WSGI middleware that integrates Engine.IO traffic with standard WSGI applications.
- Uses an event-based architecture implemented with decorators that hides the details of the protocol.
- Implements HTTP long-polling and WebSocket transports.
- Supports XHR2 and XHR browsers as clients.
- Supports text and binary messages.
- Supports gzip and deflate HTTP compression.
- Configurable CORS responses to avoid cross-origin problems with browsers.

Example
-------

The following application uses the Eventlet asynchronous server, and includes a
small Flask application that serves the HTML/Javascript to the client:

::

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

Resources
---------

-  `Documentation`_
-  `PyPI`_

.. _Engine.IO: https://github.com/Automattic/engine.io
.. _engine.io-client: https://github.com/Automattic/engine.io-client
.. _eventlet: http://eventlet.net/
.. _gevent: http://gevent.org/
.. _Documentation: http://pythonhosted.org/python-engineio
.. _PyPI: https://pypi.python.org/pypi/python-engineio
