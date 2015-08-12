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


class BaseTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_help_contents(self):
        args = ['--help']
        with self.assertRaises(SystemExit):
            main(args)
        expected_stdout = open('tests/samples/output/test_help_contents').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_argument_parsing(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        args = ['--file', 'tests/samples/twolinefile.txt', '--key', '123', '--config', 'tests/samples/sample.cfg']

        retval = main(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_missing_config_file(self):
        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'foo']
        with self.assertRaises(SystemExit):
            main(args)
        expected_stdout = u("Error: Could not read from config file foo\n")
        expected_stderr = open('tests/samples/output/test_missing_config_file').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_config_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'tests/samples/sample.cfg']
        retval = main(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_bad_config_file(self):
        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'tests/samples/bad_config.cfg']
        retval = main(args)
        self.assertEquals(retval, 103)
        self.assertIn('ParsingError', sys.stdout.getvalue())
        self.assertEquals(sys.stderr.getvalue(), '')
        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

    def test_non_hidden_filename(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--key', '123', '--config', config, '--time', now]

        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': os.path.abspath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": [], "lines": 2, "lineno": null, "language": "Text only"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_hidden_filename(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/twolinefile.txt'
        config = 'tests/samples/paranoid.cfg'

        args = ['--file', entity, '--key', '123', '--config', config, '--time', now]

        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': 'HIDDEN.txt',
            'project': os.path.basename(os.path.abspath('.')),
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": [], "lines": 2, "lineno": null, "language": "Text only"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_500_response(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        args = ['--file', 'tests/samples/twolinefile.txt', '--key', '123',
                '--config', 'tests/samples/paranoid.cfg', '--time', now]


        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': 'HIDDEN.txt',
            'project': os.path.basename(os.path.abspath('.')),
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": [], "lines": 2, "lineno": null, "language": "Text only"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_400_response(self):
        response = Response()
        response.status_code = 400
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        args = ['--file', 'tests/samples/twolinefile.txt', '--key', '123',
                '--config', 'tests/samples/paranoid.cfg', '--time', now]


        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_alternate_project(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--alternate-project', 'xyz', '--config', config, '--time', now]

        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': os.path.abspath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": [], "lines": 2, "lineno": null, "language": "Text only"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_set_project_from_command_line(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--project', 'xyz', '--config', config, '--time', now]

        retval = main(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': os.path.abspath(entity),
            'project': 'xyz',
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = '{"cursorpos": null, "dependencies": [], "lines": 2, "lineno": null, "language": "Text only"}'

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, stats, None)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
