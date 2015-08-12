# -*- coding: utf-8 -*-


from wakatime.base import main
from wakatime.packages import requests

import os
import time
import sys
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils

try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY


class LanguagesTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_python_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefile.py'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Python',
            'lines': 26,
            'entity': os.path.abspath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'dependencies': ['wakatime', 'os', 'mock', 'simplejson', 'django'],
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": ["wakatime", "os", "mock", "simplejson", "django"], "lines": 26, "lineno": null, "language": "Python"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
