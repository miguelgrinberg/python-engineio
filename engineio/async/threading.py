from __future__ import absolute_import

import threading

try:
    import queue
except ImportError:  # pragma: no cover
    import Queue as queue
Queue = queue.Queue
QueueEmpty = queue.Empty
has_websocket = False


def thread(target):
    return threading.Thread(target=target)


def wrap_websocket(app):
    raise RuntimeError("Websocket support is not available")
