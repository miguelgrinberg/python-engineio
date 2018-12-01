import sys

from .middleware import WSGIApp, Middleware
from .server import Server
if sys.version_info >= (3, 5):  # pragma: no cover
    from .asyncio_server import AsyncServer
    from .async_tornado import get_tornado_handler
    from .async_asgi import ASGIApp
else:  # pragma: no cover
    AsyncServer = None

__version__ = '3.0.0'

__all__ = ['__version__', 'Server', 'WSGIApp', 'Middleware']
if AsyncServer is not None:  # pragma: no cover
    __all__ += ['AsyncServer', 'ASGIApp', 'get_tornado_handler']
