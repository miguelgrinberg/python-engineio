import importlib

async = {
    'threading': importlib.import_module('gevent.threading'),
    'queue': importlib.import_module('gevent.queue'),
    'queue_class': 'Queue',
    'websocket': None,
    'websocket_class': None
}
