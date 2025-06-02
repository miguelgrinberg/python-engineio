#!/usr/bin/env python
import gevent.monkey
gevent.monkey.patch_all()

import pytest
import sys

if __name__ == "__main__":
    sys.exit(pytest.main([
        '-p', 'no:logging',
        '--cov=engineio', 
        '--cov-branch', 
        '--cov-report=term-missing', 
        '--cov-report=xml',
        # Skip tests containing 'gevent' in tests/common/test_server.py
        # as these are all stub tests and conflict with monkey patching.
        '-k', 'not (gevent and test_server)',
    ]))