The Engine.IO Client
====================

This package contains two Engine.IO clients:

- The :func:`engineio.Client` class creates a client compatible with the
  standard Python library.
- The :func:`engineio.AsyncClient` class creates a client compatible with
  the ``asyncio`` package.

The methods in the two clients are the same, with the only difference that in
the ``asyncio`` client most methods are implemented as coroutines.

Installation
------------

To install the standard Python client along with its dependencies, use the
following command::

    pip install "python-engineio[client]"

If instead you plan on using the ``asyncio`` client, then use this::

    pip install "python-engineio[asyncio_client]"

Creating a Client Instance
--------------------------

To instantiate an Engine.IO client, simply create an instance of the
appropriate client class::

    import engineio

    # standard Python
    eio = engineio.Client()

    # asyncio
    eio = engineio.AsyncClient()

Defining Event Handlers
-----------------------

To responds to events triggered by the connection or the server, event Handler
functions must be defined using the ``on`` decorator::

    @eio.on('connect')
    def on_connect():
        print('I'm connected!')

    @eio.on('message')
    def on_message(data):
        print('I received a message!')

    @eio.on('disconnect')
    def on_disconnect(reason):
        print('I'm disconnected! reason:', reason)

For the ``asyncio`` server, event handlers can be regular functions as above,
or can also be coroutines::

    @eio.on('message')
    async def on_message(data):
        print('I received a message!')

The argument given to the ``on`` decorator is the event name. The events that
are supported are ``connect``, ``message`` and ``disconnect``.

The ``data`` argument passed to the ``'message'`` event handler contains
application-specific data provided by the server with the event.

The ``disconnect`` handler is invoked for client initiated disconnects, server
initiated disconnects, or accidental disconnects, for example due to
networking failures. The argument passed to this handler provides the
disconnect reason. Example::

    @eio.on('disconnect')
    def on_disconnect(reason):
        if reason == eio.reason.CLIENT_DISCONNECT:
            print('client disconnection')
        elif reason == eio.reason.SERVER_DISCONNECT:
            print('the server kicked me out')
        else:
            print(f'disconnect reason: {reason}')

Connecting to a Server
----------------------

The connection to a server is established by calling the ``connect()``
method::

    eio.connect('http://localhost:5000')

In the case of the ``asyncio`` client, the method is a coroutine::

    await eio.connect('http://localhost:5000')

Upon connection, the server assigns the client a unique session identifier.
The applicaction can find this identifier in the ``sid`` attribute::

    print('my sid is', eio.sid)

Sending Messages
----------------

The client can send a message to the server using the ``send()`` method::

    eio.send({'foo': 'bar'})

Or in the case of ``asyncio``, as a coroutine::

    await eio.send({'foo': 'bar'})

The single argument provided to the method is the data that is passed on
to the server. The data can be of type ``str``, ``bytes``, ``dict`` or
``list``. The data included inside dictionaries and lists is also
constrained to these types.

The ``send()`` method can be invoked inside an event handler as a response
to a server event, or in any other part of the application, including in
background tasks.

Disconnecting from the Server
-----------------------------

At any time the client can request to be disconnected from the server by
invoking the ``disconnect()`` method::

    eio.disconnect()

For the ``asyncio`` client this is a coroutine::

    await eio.disconnect()

Managing Background Tasks
-------------------------

When a client connection to the server is established, a few background
tasks will be spawned to keep the connection alive and handle incoming
events. The application running on the main thread is free to do any
work, as this is not going to prevent the functioning of the Engine.IO
client.

If the application does not have anything to do in the main thread and
just wants to wait until the connection ends, it can call the ``wait()``
method::

    eio.wait()

Or in the ``asyncio`` version::

    await eio.wait()

For the convenience of the application, a helper function is
provided to start a custom background task::

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

To help you debug issues, the client can be configured to output logs to the
terminal::

    import engineio

    # standard Python
    eio = engineio.Client(logger=True)

    # asyncio
    eio = engineio.AsyncClient(logger=True)

The ``logger`` argument can be set to ``True`` to output logs to ``stderr``, or
to an object compatible with Python's ``logging`` package where the logs should
be emitted to. A value of ``False`` disables logging.

Logging can help identify the cause of connection problems, unexpected
disconnections and other issues.
