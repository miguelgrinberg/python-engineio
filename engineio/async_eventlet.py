import importlib

async = {
    'threading': importlib.import_module('eventlet.green.threading'),
    'thread_class': 'Thread',
    'queue': importlib.import_module('eventlet.queue'),
    'queue_class': 'Queue',
    'websocket': importlib.import_module('eventlet.websocket'),
    'websocket_class': 'WebSocketWSGI'
}
