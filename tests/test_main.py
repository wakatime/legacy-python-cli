# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import os
import time
import sys
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils

try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json
try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY


class BaseTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    def test_help_contents(self):
        args = ['--help']
        with self.assertRaises(SystemExit):
            execute(args)
        expected_stdout = open('tests/samples/output/test_help_contents').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_argument_parsing(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--key', '123', '--config', config]

        retval = execute(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_config_file_not_passed_in_command_line_args(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.main.open') as mock_open:
            mock_open.side_effect = IOError('')

            config = os.path.join(os.path.expanduser('~'), '.wakatime.cfg')
            entity = 'tests/samples/codefiles/emptyfile.txt'
            args = ['--file', entity]

            with self.assertRaises(SystemExit):
                execute(args)
            expected_stdout = u("Error: Could not read from config file {0}\n").format(u(config))
            expected_stderr = open('tests/samples/output/test_missing_config_file').read()
            self.assertEquals(sys.stdout.getvalue(), expected_stdout)
            self.assertEquals(sys.stderr.getvalue(), expected_stderr)
            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_missing_config_file(self):
        config = 'foo'
        entity = 'tests/samples/codefiles/emptyfile.txt'
        args = ['--file', entity, '--config', config]
        with self.assertRaises(SystemExit):
            execute(args)
        expected_stdout = u("Error: Could not read from config file foo\n")
        expected_stderr = open('tests/samples/output/test_missing_config_file').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_good_config_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/emptyfile.txt'
        config = 'tests/samples/configs/has_everything.cfg'
        args = ['--file', entity, '--config', config]
        retval = execute(args)
        self.assertEquals(retval, 0)
        expected_stdout = open('tests/samples/output/main_test_good_config_file').read()
        traceback_file = os.path.realpath('wakatime/main.py')
        self.assertEquals(sys.stdout.getvalue(), expected_stdout.format(file=traceback_file))
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_api_key_without_underscore_accepted(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/emptyfile.txt'
        config = 'tests/samples/configs/sample_alternate_apikey.cfg'
        args = ['--file', entity, '--config', config]
        retval = execute(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_bad_config_file(self):
        entity = 'tests/samples/codefiles/emptyfile.txt'
        config = 'tests/samples/configs/bad_config.cfg'
        args = ['--file', entity, '--config', config]
        retval = execute(args)
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
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--key', '123', '--config', config, '--time', now]

        retval = execute(args)
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
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_hidden_filename(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/paranoid.cfg'

        args = ['--file', entity, '--key', '123', '--config', config, '--time', now]

        retval = execute(args)
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
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_500_response(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        args = ['--file', 'tests/samples/codefiles/twolinefile.txt', '--key', '123',
                '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]


        retval = execute(args)
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
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_400_response(self):
        response = Response()
        response.status_code = 400
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        args = ['--file', 'tests/samples/codefiles/twolinefile.txt', '--key', '123',
                '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]


        retval = execute(args)
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
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--alternate-project', 'xyz', '--config', config, '--time', now]

        retval = execute(args)
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
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_set_project_from_command_line(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--project', 'xyz', '--config', config, '--time', now]

        retval = execute(args)
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
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_missing_entity_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/missingfile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config]
        retval = execute(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_proxy_argument(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--proxy', 'localhost:1234']
        retval = execute(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': 'localhost:1234'}, stream=False, timeout=30, verify=True)

    def test_domain_heartbeat(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'google.com'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entitytype', 'domain', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'entity': u(entity),
            'time': float(now),
            'type': 'domain',
        }
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): None,
            u('lineno'): None,
            u('lines'): None,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_app_heartbeat(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'Firefox'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entitytype', 'app', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'entity': u(entity),
            'time': float(now),
            'type': 'app',
        }
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): None,
            u('lineno'): None,
            u('lines'): None,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
