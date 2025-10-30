from logging import getLogger

from pytest import mark, warns

from engineio.async_client import AsyncClient
from engineio.async_server import AsyncServer
from engineio.client import Client
from engineio.server import Server


@mark.parametrize(
    ['cls', 'name'],
    [
        (AsyncClient, 'engineio.client'),
        (AsyncServer, 'engineio.server'),
        (Client, 'engineio.client'),
        (Server, 'engineio.server'),
    ],
)
class TestLoggingSetup:
    @mark.parametrize('value', [False, True])
    def test_bool_logger_deprecation_warning(self, cls, name, value):
        with warns(
            DeprecationWarning,
            match=r'The logger parameter as a boolean is deprecated',
        ):
            o = cls(logger=value)
        assert o.logger is getLogger(name)

    def test_custom_logger(self, cls, name):
        logger = getLogger('foo')
        assert cls(logger=logger).logger is logger

    def test_default_logger(self, cls, name):
        assert cls().logger is getLogger(name)
