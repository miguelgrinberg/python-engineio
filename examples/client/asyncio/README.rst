Engine.IO Threading Examples
============================

This directory contains example Engine.IO clients that work with the
`threading` package of the Python standard library.

simple_client.py
----------------

A basic application in which the client sends messages to the server and the
server responds.

latency_client.py
-----------------

In this application the client sends *ping* messages to the server, which are
responded by the server with a *pong*. The client measures the time it takes
for each of these exchanges.

This is an ideal application to measure the performance of the different
asynchronous modes supported by the Engine.IO server.

Running the Examples
--------------------

These examples work with the server examples of the same name. First run one
of the `simple.py` or `latency.py` versions from the `examples/server`
directory. On another terminal, then start the corresponding client with one
of the following commands::

    $ python simple_client.py

or::

    $ python latency_client.py
