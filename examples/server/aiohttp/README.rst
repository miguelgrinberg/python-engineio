Engine.IO Examples
==================

This directory contains example Engine.IO applications that are compatible
with asyncio and the aiohttp framework. These applications require Python 3.5
or later.

simple.py
---------

A basic application in which the client sends messages to the server and the
server responds.

latency.py
----------

A port of the latency application included in the official Engine.IO
Javascript server. In this application the client sends *ping* messages to
the server, which are responded by the server with a *pong*. The client
measures the time it takes for each of these exchanges and plots these in real
time to the page.

This is an ideal application to measure the performance of the different
asynchronous modes supported by the Engine.IO server.

Running the Examples
--------------------

To run these examples, create a virtual environment, install the requirements
and then run::

    $ python simple.py

or::

    $ python latency.py

You can then access the application from your web browser at
``http://localhost:8080``.