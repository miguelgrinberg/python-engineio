from __future__ import absolute_import

import eventlet.green.threading
import eventlet.queue
try:
    import eventlet.websocket
    has_websocket = True
except ImportError:
    has_websocket = False

Queue = eventlet.queue.Queue
QueueEmpty = eventlet.queue.Empty


def thread(target):
    return eventlet.green.threading(target=target)


def wrap_websocket(app):
    return eventlet.websocket.WebSocketWSGI(app)
