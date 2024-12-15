The Engine.IO Server
====================

This package contains two Engine.IO servers:

- The :func:`engineio.Server` class creates a server compatible with the
  standard Python library.
- The :func:`engineio.AsyncServer` class creates a server compatible with
  the ``asyncio`` package.

The methods in the two servers are the same, with the only difference that in
the ``asyncio`` server most methods are implemented as coroutines.

Installation
------------

To install the Python Engine.IO server use the following command::

    pip install "python-engineio"

In addition to the server, you will need to select an asynchronous framework
or server to use along with it. The list of supported packages is covered
in the :ref:`deployment-strategies` section.

Creating a Server Instance
--------------------------

An Engine.IO server is an instance of class :class:`engineio.Server`. This
instance can be transformed into a standard WSGI application by wrapping it
with the :class:`engineio.WSGIApp` class::

   import engineio

   # create a Engine.IO server
   eio = engineio.Server()

   # wrap with a WSGI application
   app = engineio.WSGIApp(eio)

For asyncio based servers, the :class:`engineio.AsyncServer` class provides
the same functionality, but in a coroutine friendly format. If desired, The
:class:`engineio.ASGIApp` class can transform the server into a standard
ASGI application::

    # create a Engine.IO server
    eio = engineio.AsyncServer()

    # wrap with ASGI application
    app = engineio.ASGIApp(eio)

These two wrappers can also act as middlewares, forwarding any traffic that is
not intended to the Engine.IO server to another application. This allows
Engine.IO servers to integrate easily into existing WSGI or ASGI applications::

   from wsgi import app  # a Flask, Django, etc. application
   app = engineio.WSGIApp(eio, app)

Serving Static Files
--------------------

The Engine.IO server can be configured to serve static files to clients. This
is particularly useful to deliver HTML, CSS and JavaScript files to clients
when this package is used without a companion web framework.

Static files are configured with a Python dictionary in which each key/value
pair is a static file mapping rule. In its simplest form, this dictionary has
one or more static file URLs as keys, and the corresponding files in the server
as values::

    static_files = {
        '/': 'latency.html',
        '/static/engine.io.js': 'static/engine.io.js',
        '/static/style.css': 'static/style.css',
    }

With this example configuration, when the server receives a request for ``/``
(the root URL) it will return the contents of the file ``latency.html`` in the
current directory, and will assign a content type based on the file extension,
in this case ``text/html``.

Files with the ``.html``, ``.css``, ``.js``, ``.json``, ``.jpg``, ``.png``,
``.gif`` and ``.txt`` file extensions are automatically recognized and
assigned the correct content type. For files with other file extensions or
with no file extension, the ``application/octet-stream`` content type is used
as a default.

If desired, an explicit content type for a static file can be given as follows::

    static_files = {
        '/': {'filename': 'latency.html', 'content_type': 'text/plain'},
    }

It is also possible to configure an entire directory in a single rule, so that all
the files in it are served as static files::

    static_files = {
        '/static': './public',
    }

In this example any files with URLs starting with ``/static`` will be served
directly from the ``public`` folder in the current directory, so for example,
the URL ``/static/index.html`` will return local file ``./public/index.html``
and the URL ``/static/css/styles.css`` will return local file
``./public/css/styles.css``.

If a URL that ends in a ``/`` is requested, then a default filename of
``index.html`` is appended to it. In the previous example, a request for the
``/static/`` URL would return local file ``./public/index.html``. The default
filename to serve for slash-ending URLs can be set in the static files
dictionary with an empty key::

    static_files = {
        '/static': './public',
        '': 'image.gif',
    }

With this configuration, a request for ``/static/`` would return
local file ``./public/image.gif``. A non-standard content type can also be
specified if needed::

    static_files = {
        '/static': './public',
        '': {'filename': 'image.gif', 'content_type': 'text/plain'},
    }

The static file configuration dictionary is given as the ``static_files``
argument to the ``engineio.WSGIApp`` or ``engineio.ASGIApp`` classes::

    # for standard WSGI applications
    eio = engineio.Server()
    app = engineio.WSGIApp(eio, static_files=static_files)

    # for asyncio-based ASGI applications
    eio = engineio.AsyncServer()
    app = engineio.ASGIApp(eio, static_files=static_files)

The routing precedence in these two classes is as follows:

- First, the path is checked against the Engine.IO path.
- Next, the path is checked against the static file configuration, if present.
- If the path did not match the Engine.IO path or any static file, control is
  passed to the secondary application if configured, else a 404 error is
  returned.

Note: static file serving is intended for development use only, and as such
it lacks important features such as caching. Do not use in a production
environment.

Defining Event Handlers
-----------------------

To responds to events triggered by the connection or the client, event Handler
functions must be defined using the ``on`` decorator::

    @eio.on('connect')
    def on_connect(sid):
        print('A client connected!')

    @eio.on('message')
    def on_message(sid, data):
        print('I received a message!')

    @eio.on('disconnect')
    def on_disconnect(sid, reason):
        print('Client disconnected! reason:', reason)

For the ``asyncio`` server, event handlers can be regular functions as above,
or can also be coroutines::

    @eio.on('message')
    async def on_message(sid, data):
        print('I received a message!')

The argument given to the ``on`` decorator is the event name. The events that
are supported are ``connect``, ``message`` and ``disconnect``.

The ``sid`` argument passed into all the event handlers is a connection
identifier for the client. All the events from a client will use the same
``sid`` value.

The ``connect`` handler is the place where the server can perform
authentication. The value returned by this handler is used to determine if the
connection is accepted or rejected. When the handler does not return any value
(which is the same as returning ``None``) or when it returns ``True`` the
connection is accepted. If the handler returns ``False`` or any JSON
compatible data type (string, integer, list or dictionary) the connection is
rejected. A rejected connection triggers a response with a 401 status code.

The ``data`` argument passed to the ``'message'`` event handler contains
application-specific data provided by the client with the event.

The ``disconnect`` handler is invoked for client initiated disconnects,
server initiated disconnects, or accidental disconnects, for example due to
networking failures. The second argument passed to this handler provides the
disconnect reason. Example::

    @eio.on('disconnect')
    def on_disconnect(sid, reason):
        if reason == eio.reason.CLIENT_DISCONNECT:
            print('the client went away')
        elif reason == eio.reason.SERVER_DISCONNECT:
            print('the client was kicked out')
        else:
            print(f'disconnect reason: {reason}')

Sending Messages
----------------

The server can send a message to any client using the ``send()`` method::

    eio.send(sid, {'foo': 'bar'})

Or in the case of ``asyncio``, as a coroutine::

    await eio.send(sid, {'foo': 'bar'})

The first argument provided to the method is the connection identifier for
the recipient client. The second argument is the data that is passed on
to the server. The data can be of type ``str``, ``bytes``, ``dict`` or
``list``. The data included inside dictionaries and lists is also
constrained to these types.

The ``send()`` method can be invoked inside an event handler as a response
to a client event, or in any other part of the application, including in
background tasks.

User Sessions
-------------

The server can maintain application-specific information in a user session
dedicated to each connected client. Applications can use the user session to
write any details about the user that need to be preserved throughout the life
of the connection, such as usernames or user ids.

The ``save_session()`` and ``get_session()`` methods are used to store and
retrieve information in the user session::

    @eio.on('connect')
    def on_connect(sid, environ):
        username = authenticate_user(environ)
        eio.save_session(sid, {'username': username})

    @eio.on('message')
    def on_message(sid, data):
        session = eio.get_session(sid)
        print('message from ', session['username'])

For the ``asyncio`` server, these methods are coroutines::

    @eio.on('connect')
    async def on_connect(sid, environ):
        username = authenticate_user(environ)
        await eio.save_session(sid, {'username': username})

    @eio.on('message')
    async def on_message(sid, data):
        session = await eio.get_session(sid)
        print('message from ', session['username'])

The session can also be manipulated with the `session()` context manager::

    @eio.on('connect')
    def on_connect(sid, environ):
        username = authenticate_user(environ)
        with eio.session(sid) as session:
            session['username'] = username

    @eio.on('message')
    def on_message(sid, data):
        with eio.session(sid) as session:
            print('message from ', session['username'])

For the ``asyncio`` server, an asynchronous context manager is used::

    @eio.on('connect')
    def on_connect(sid, environ):
        username = authenticate_user(environ)
        async with eio.session(sid) as session:
            session['username'] = username

    @eio.on('message')
    def on_message(sid, data):
        async with eio.session(sid) as session:
            print('message from ', session['username'])

Note: the contents of the user session are destroyed when the client
disconnects.

Disconnecting a Client
----------------------

At any time the server can disconnect a client from the server by invoking the
``disconnect()`` method and passing the ``sid`` value assigned to the client::

    eio.disconnect(sid)

For the ``asyncio`` client this is a coroutine::

    await eio.disconnect(sid)

Managing Background Tasks
-------------------------

For the convenience of the application, a helper function is provided to
start a custom background task::

    def my_background_task(my_argument)
        # do some background work here!
        pass

    eio.start_background_task(my_background_task, 123)

The arguments passed to this method are the background function and any
positional or keyword arguments to invoke the function with. 

Here is the ``asyncio`` version::

    async def my_background_task(my_argument)
        # do some background work here!
        pass

    eio.start_background_task(my_background_task, 123)

Note that this function is not a coroutine, since it does not wait for the
background function to end, but the background function is.

The ``sleep()`` method is a second convenience function that is provided for
the benefit of applications working with background tasks of their own::

    eio.sleep(2)

Or for ``asyncio``::

    await eio.sleep(2)

The single argument passed to the method is the number of seconds to sleep
for.

Debugging and Troubleshooting
-----------------------------

To help you debug issues, the server can be configured to output logs to the
terminal::

    import engineio

    # standard Python
    eio = engineio.Server(logger=True)

    # asyncio
    eio = engineio.AsyncServer(logger=True)

The ``logger`` argument can be set to ``True`` to output logs to ``stderr``, or
to an object compatible with Python's ``logging`` package where the logs should
be emitted to. A value of ``False`` disables logging.

Logging can help identify the cause of connection problems, 400 responses,
bad performance and other issues.

.. _deployment-strategies:

Deployment Strategies
---------------------

The following sections describe a variety of deployment strategies for
Engine.IO servers.

Uvicorn, Daphne, and other ASGI servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``engineio.ASGIApp`` class is an ASGI compatible application that can
forward Engine.IO traffic to an ``engineio.AsyncServer`` instance::

   eio = engineio.AsyncServer(async_mode='asgi')
   app = engineio.ASGIApp(eio)

If desired, the ``engineio.ASGIApp`` class can forward any traffic that is not
Engine.IO to another ASGI application, making it possible to deploy a standard
ASGI web application and the Engine.IO server as a bundle::

   eio = engineio.AsyncServer(async_mode='asgi')
   app = engineio.ASGIApp(eio, other_app)

The ``ASGIApp`` instance is a fully complaint ASGI instance that can be
deployed with an ASGI compatible web server.

Aiohttp
~~~~~~~

`aiohttp <http://aiohttp.readthedocs.io/>`_ provides a framework with support
for HTTP and WebSocket, based on asyncio.

Instances of class ``engineio.AsyncServer`` will automatically use aiohttp
for asynchronous operations if the library is installed. To request its use
explicitly, the ``async_mode`` option can be given in the constructor::

    eio = engineio.AsyncServer(async_mode='aiohttp')

A server configured for aiohttp must be attached to an existing application::

    app = web.Application()
    eio.attach(app)

The aiohttp application can define regular routes that will coexist with the
Engine.IO server. A typical pattern is to add routes that serve a client
application and any associated static files.

The aiohttp application is then executed in the usual manner::

    if __name__ == '__main__':
        web.run_app(app)

Tornado
~~~~~~~

`Tornado <http://www.tornadoweb.org//>`_ is a web framework with support
for HTTP and WebSocket. Only Tornado version 5 and newer are supported, thanks
to its tight integration with asyncio.

Instances of class ``engineio.AsyncServer`` will automatically use tornado
for asynchronous operations if the library is installed. To request its use
explicitly, the ``async_mode`` option can be given in the constructor::

    eio = engineio.AsyncServer(async_mode='tornado')

A server configured for tornado must include a request handler for
Engine.IO::

    app = tornado.web.Application(
        [
            (r"/engine.io/", engineio.get_tornado_handler(eio)),
        ],
        # ... other application options
    )

The tornado application can define other routes that will coexist with the
Engine.IO server. A typical pattern is to add routes that serve a client
application and any associated static files.

The tornado application is then executed in the usual manner::

    app.listen(port)
    tornado.ioloop.IOLoop.current().start()

Sanic
~~~~~

Note: Due to some backward incompatible changes introduced in recent versions
of Sanic, it is currently recommended that a Sanic application is deployed with
the ASGI integration instead.

`Sanic <http://sanic.readthedocs.io/>`_ is a very efficient asynchronous web
server for Python.

Instances of class ``engineio.AsyncServer`` will automatically use Sanic for
asynchronous operations if the framework is installed. To request its use
explicitly, the ``async_mode`` option can be given in the constructor::

    eio = engineio.AsyncServer(async_mode='sanic')

A server configured for Sanic must be attached to an existing application::

    app = Sanic()
    eio.attach(app)

The Sanic application can define regular routes that will coexist with the
Engine.IO server. A typical pattern is to add routes that serve a client
application and any associated static files to this application.

The Sanic application is then executed in the usual manner::

    if __name__ == '__main__':
        app.run()

It has been reported that the CORS support provided by the Sanic extension
`sanic-cors <https://github.com/ashleysommer/sanic-cors>`_ is incompatible with
this package's own support for this protocol. To disable CORS support in this
package and let Sanic take full control, initialize the server as follows::

    eio = engineio.AsyncServer(async_mode='sanic', cors_allowed_origins=[])

On the Sanic side you will need to enable the `CORS_SUPPORTS_CREDENTIALS`
setting in addition to any other configuration that you use::

    app.config['CORS_SUPPORTS_CREDENTIALS'] = True

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

A server configured for eventlet is deployed as a regular WSGI application
using the provided ``engineio.WSGIApp``::

    app = engineio.WSGIApp(eio)
    import eventlet
    eventlet.wsgi.server(eventlet.listen(('', 8000)), app)

Eventlet with Gunicorn
~~~~~~~~~~~~~~~~~~~~~~

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
gevent has access to the long-polling and websocket transports.

Instances of class ``engineio.Server`` will automatically use gevent for
asynchronous operations if the library is installed and eventlet is not
installed. To request gevent to be selected explicitly, the ``async_mode``
option can be given in the constructor::

    eio = engineio.Server(async_mode='gevent')

A server configured for gevent is deployed as a regular WSGI application
using the provided ``engineio.WSGIApp``::

    from gevent import pywsgi
    app = engineio.WSGIApp(eio)
    pywsgi.WSGIServer(('', 8000), app).serve_forever()

Gevent with Gunicorn
~~~~~~~~~~~~~~~~~~~~

An alternative to running the gevent WSGI server as above is to use
`gunicorn <gunicorn.org>`_, a fully featured pure Python web server. The
command to launch the application under gunicorn is shown below::

    $ gunicorn -k gevent -w 1 module:app

Same as with eventlet, due to limitations in its load balancing algorithm,
gunicorn can only be used with one worker process, so the ``-w 1`` option is
required. Note that a single gevent worker can handle a large number of
concurrent clients.

Note: Gevent provides a ``monkey_patch()`` function that replaces all the
blocking functions in the standard library with equivalent asynchronous
versions. While python-engineio does not require monkey patching, other
libraries such as database drivers are likely to require it.

uWSGI
~~~~~

When using the uWSGI server in combination with gevent, the Engine.IO server
can take advantage of uWSGI's native WebSocket support.

Instances of class ``engineio.Server`` will automatically use this option for
asynchronous operations if both gevent and uWSGI are installed and eventlet is
not installed. To request this asynchoronous mode explicitly, the
``async_mode`` option can be given in the constructor::

    # gevent with uWSGI
    eio = engineio.Server(async_mode='gevent_uwsgi')

A complete explanation of the configuration and usage of the uWSGI server is
beyond the scope of this documentation. The uWSGI server is a fairly complex
package that provides a large and comprehensive set of options. It must be
compiled with WebSocket and SSL support for the WebSocket transport to be
available. As way of an introduction, the following command starts a uWSGI
server for the ``latency.py`` example on port 5000::

    $ uwsgi --http :5000 --gevent 1000 --http-websockets --master --wsgi-file latency.py --callable app

Standard Threads
~~~~~~~~~~~~~~~~

While not comparable to eventlet and gevent in terms of performance,
the Engine.IO server can also be configured to work with multi-threaded web
servers that use standard Python threads. This is an ideal setup to use with
development servers such as `Werkzeug <http://werkzeug.pocoo.org>`_.

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
    app.wsgi_app = engineio.WSGIApp(eio, app.wsgi_app)

    # ... Engine.IO and Flask handler functions ...

    if __name__ == '__main__':
        app.run()

The example that follows shows how to start an Engine.IO application using
Gunicorn's threaded worker class::

    $ gunicorn -w 1 --threads 100 module:app

With the above configuration the server will be able to handle up to 100
concurrent clients.

When using standard threads, WebSocket is supported through the
`simple-websocket <https://github.com/miguelgrinberg/simple-websocket>`_
package, which must be installed separately. This package provides a
multi-threaded WebSocket server that is compatible with Werkzeug and Gunicorn's
threaded worker. Other multi-threaded web servers are not supported and will
not enable the WebSocket transport.

Scalability Notes
~~~~~~~~~~~~~~~~~

Engine.IO is a stateful protocol, which makes horizontal scaling more
difficult. To deploy a cluster of Engine.IO processes hosted on one or
multiple servers the following conditions must be met:

- Each Engine.IO server process must be able to handle multiple requests
  concurrently. This is required because long-polling clients send two
  requests in parallel. Worker processes that can only handle one request at a
  time are not supported.
- The load balancer must be configured to always forward requests from a client
  to the same process. Load balancers call this *sticky sessions*, or
  *session affinity*.

Cross-Origin Controls
---------------------

For security reasons, this server enforces a same-origin policy by default. In
practical terms, this means the following:

- If an incoming HTTP or WebSocket request includes the ``Origin`` header,
  this header must match the scheme and host of the connection URL. In case
  of a mismatch, a 400 status code response is returned and the connection is
  rejected.
- No restrictions are imposed on incoming requests that do not include the
  ``Origin`` header.

If necessary, the ``cors_allowed_origins`` option can be used to allow other
origins. This argument can be set to a string to set a single allowed origin, or
to a list to allow multiple origins. A special value of ``'*'`` can be used to
instruct the server to allow all origins, but this should be done with care, as
this could make the server vulnerable to Cross-Site Request Forgery (CSRF)
attacks.
