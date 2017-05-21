# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import logging
import os
import time
import shutil
import sys
import uuid
from testfixtures import log_capture
from wakatime.compat import u
from wakatime.constants import (
    API_ERROR,
    AUTH_ERROR,
    SUCCESS,
    MALFORMED_HEARTBEAT_ERROR,
)
from wakatime.packages.requests.models import Response
from . import utils

try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json
try:
    from mock import ANY, call
except ImportError:
    from unittest.mock import ANY, call


class ArgumentsTestCase(utils.TestCase):
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
        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), 0)
        expected_stdout = open('tests/samples/output/test_help_contents').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_argument_parsing(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            key = str(uuid.uuid4())
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--key', key, '--config', config]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_lineno_and_cursorpos(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--config', config, '--time', now, '--lineno', '3', '--cursorpos', '4', '--verbose']
        retval = execute(args)

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.assertEquals(retval, API_ERROR)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'cursorpos': '4',
            'lineno': '3',
            'branch': 'master',
            'time': float(now),
            'type': 'file',
        }
        stats = {
            u('cursorpos'): '4',
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): '3',
            u('lines'): 2,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
        for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
            self.assertEquals(heartbeat[key], val)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_invalid_timeout_passed_via_command_line(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            args = ['--file', entity, '--key', key, '--config', config, '--timeout', 'abc']

            with self.assertRaises(SystemExit) as e:
                execute(args)

            self.assertEquals(int(str(e.exception)), 2)
            self.assertEquals(sys.stdout.getvalue(), '')
            expected_stderr = open('tests/samples/output/main_test_timeout_passed_via_command_line').read()
            self.assertEquals(sys.stderr.getvalue(), expected_stderr)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    @log_capture()
    def test_missing_entity_file(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/missingfile.txt'

        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--verbose']
        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = 'WakaTime DEBUG File does not exist; ignoring this heartbeat.'
        self.assertEquals(log_output, expected)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    @log_capture()
    def test_missing_entity_argument(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        config = 'tests/samples/configs/good_config.cfg'
        args = ['--config', config]

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), 2)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: argument --entity is required'
        self.assertIn(expected, sys.stderr.getvalue())

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = ''
        self.assertEquals(log_output, expected)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    @log_capture()
    def test_missing_api_key(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        config = 'tests/samples/configs/missing_api_key.cfg'
        args = ['--config', config]

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: Missing api key. Find your api key from wakatime.com/settings.'
        self.assertIn(expected, sys.stderr.getvalue())

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = ''
        self.assertEquals(log_output, expected)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    @log_capture()
    def test_invalid_api_key(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        key = 'an-invalid-key'
        args = ['--key', key]

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: Invalid api key. Find your api key from wakatime.com/settings.'
        self.assertIn(expected, sys.stderr.getvalue())

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = ''
        self.assertEquals(log_output, expected)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    @log_capture()
    def test_api_key_passed_via_command_line(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            filename = list(filter(lambda x: x.endswith('.txt'), os.listdir(u('tests/samples/codefiles/unicode'))))[0]
            entity = os.path.join('tests/samples/codefiles/unicode', filename)
            shutil.copy(entity, os.path.join(tempdir, filename))
            entity = os.path.realpath(os.path.join(tempdir, filename))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--time', now, '--config', 'fake-foobar']

            retval = execute(args)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            self.assertEquals(log_output, '')

            self.assertEquals(retval, API_ERROR)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 0,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_proxy_argument(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'localhost:1337'

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=True)

    def test_disable_ssl_verify_argument(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--no-ssl-verify']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies=ANY, stream=False, timeout=60, verify=False)

    def test_write_argument(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--write', '--verbose',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity,
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
                'is_write': True,
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 0,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_entity_type_domain(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'google.com'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entity-type', 'domain', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, API_ERROR)
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

    def test_entity_type_app(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'Firefox'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entity-type', 'app', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, API_ERROR)
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

    def test_old_alternate_language_argument_still_supported(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/python.py'
        args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'JAVA']

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('Java')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_extra_heartbeats_argument(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))

            project1 = os.path.basename(os.path.abspath('.'))
            project2 = 'xyz'
            entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
            entity2 = os.path.abspath('tests/samples/codefiles/twolinefile.txt')
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity1, '--config', config, '--extra-heartbeats']

            with utils.mock.patch('wakatime.main.sys.stdin') as mock_stdin:
                now = int(time.time())
                heartbeats = json.dumps([{
                    'timestamp': now,
                    'entity': entity2,
                    'entity_type': 'file',
                    'project': project2,
                    'is_write': True,
                }])
                mock_stdin.readline.return_value = heartbeats

                retval = execute(args)

                self.assertEquals(retval, SUCCESS)
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')

                self.patched['wakatime.session_cache.SessionCache.get'].assert_has_calls([call(), call()])
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_has_calls([call(ANY), call(ANY)])

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

                calls = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args_list

                body = calls[0][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), entity1)
                self.assertEquals(data.get('project'), project1)

                body = calls[1][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), entity2)
                self.assertEquals(data.get('project'), project2)

    @log_capture()
    def test_extra_heartbeats_with_malformed_json(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))

            entity = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--extra-heartbeats']

            with utils.mock.patch('wakatime.main.sys.stdin') as mock_stdin:
                heartbeats = '[{foobar}]'
                mock_stdin.readline.return_value = heartbeats

                retval = execute(args)

                self.assertEquals(retval, MALFORMED_HEARTBEAT_ERROR)
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')

                log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
                self.assertEquals(log_output, '')

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
