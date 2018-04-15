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
from wakatime.arguments import parse_arguments
from wakatime.compat import u, is_py3
from wakatime.constants import (
    API_ERROR,
    AUTH_ERROR,
    SUCCESS,
)
from wakatime.packages.requests.exceptions import RequestException
from wakatime.packages.requests.models import Response
from wakatime.utils import get_user_agent
from .utils import mock, json, ANY, CustomResponse, TemporaryDirectory, TestCase, NamedTemporaryFile


class ArgumentsTestCase(TestCase):
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

    @log_capture()
    def test_help_contents(self, logs):
        logging.disable(logging.NOTSET)
        args = ['--help']
        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), 0)
        expected_stdout = open('tests/samples/output/test_help_contents').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')
        self.assertNothingLogged(logs)

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    @log_capture()
    def test_argument_parsing(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            key = str(uuid.uuid4())
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--key', key, '--config', config]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    @log_capture()
    def test_argument_parsing_strips_quotes(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/python.py'
        plugin = '"abc plugin\\"with quotes"'
        args = ['--file', '"' + entity + '"', '--config', config, '--time', now, '--plugin', plugin]

        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

        ua = get_user_agent().replace('Unknown/0', 'abc plugin"with quotes')
        heartbeat = {
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'branch': ANY,
            'time': float(now),
            'type': 'file',
            'cursorpos': None,
            'dependencies': ['sqlalchemy', 'jinja', 'simplejson', 'flask', 'app', 'django', 'pygments', 'unittest', 'mock'],
            'language': u('Python'),
            'lineno': None,
            'lines': 37,
            'is_write': False,
            'user_agent': ua,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    @log_capture()
    def test_lineno_and_cursorpos(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))
        heartbeat = {
            'language': 'Text only',
            'lines': 2,
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'cursorpos': '4',
            'lineno': '3',
            'branch': ANY,
            'time': float(now),
            'is_write': False,
            'type': 'file',
            'dependencies': [],
            'user_agent': ANY,
        }

        args = ['--entity', entity, '--config', config, '--time', now, '--lineno', '3', '--cursorpos', '4', '--verbose']
        retval = execute(args)

        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        self.assertIn('WakaTime DEBUG Sending heartbeats to api', actual)

        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    @log_capture()
    def test_invalid_timeout_passed_via_command_line(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            args = ['--file', entity, '--key', key, '--config', config, '--timeout', 'abc']

            with self.assertRaises(SystemExit) as e:
                execute(args)

            self.assertNothingLogged(logs)
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

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        entity = 'tests/samples/codefiles/missingfile.txt'

        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--verbose']
        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        expected = 'WakaTime DEBUG File does not exist; ignoring this heartbeat.'
        self.assertIn(expected, actual)

        self.assertHeartbeatNotSent()

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheUntouched()

    @log_capture()
    def test_missing_entity_argument(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        config = 'tests/samples/configs/missing_api_key.cfg'
        args = ['--config', config]

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: Missing api key. Find your api key from wakatime.com/settings/api-key.'
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

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        key = 'an-invalid-key'
        args = ['--key', key]

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: Invalid api key. Find your api key from wakatime.com/settings/api-key.'
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

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            filename = list(filter(lambda x: x.endswith('.txt'), os.listdir(u('tests/samples/codefiles/unicode'))))[0]
            entity = os.path.join('tests/samples/codefiles/unicode', filename)
            shutil.copy(entity, os.path.join(tempdir, filename))
            entity = os.path.realpath(os.path.join(tempdir, filename))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--time', now, '--config', 'fake-foobar']

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': None,
                'time': float(now),
                'type': 'file',
                'cursorpos': None,
                'dependencies': [],
                'lineno': None,
                'is_write': False,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_proxy_argument(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'localhost:1337'

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=True)

    @log_capture()
    def test_disable_ssl_verify_argument(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--no-ssl-verify']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies=ANY, stream=False, timeout=60, verify=False)

    @log_capture()
    def test_write_argument(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity,
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': True,
                'dependencies': [],
                'user_agent': ANY,
            }

            args = ['--file', entity, '--key', key, '--write', '--verbose',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            self.assertIn('WakaTime DEBUG Sending heartbeats to api', actual)

            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_entity_type_domain(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        entity = 'google.com'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entity-type', 'domain', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

        heartbeat = {
            'entity': u(entity),
            'time': float(now),
            'type': 'domain',
            'cursorpos': None,
            'language': None,
            'lineno': None,
            'lines': None,
            'is_write': False,
            'dependencies': [],
            'user_agent': ANY,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    @log_capture()
    def test_entity_type_app(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        entity = 'Firefox'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--entity-type', 'app', '--config', config, '--time', now]
        retval = execute(args)

        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

        heartbeat = {
            'entity': u(entity),
            'time': float(now),
            'type': 'app',
            'cursorpos': None,
            'dependencies': [],
            'language': None,
            'lineno': None,
            'lines': None,
            'is_write': False,
            'user_agent': ANY,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    @log_capture()
    def test_valid_categories(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:

            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            now = u(int(time.time()))

            valid_categories = [
                'coding',
                'building',
                'indexing',
                'debugging',
                'running tests',
                'manual testing',
                'browsing',
                'code reviewing',
                'designing',
            ]

            for category in valid_categories:
                args = ['--entity', entity, '--category', category, '--config', config, '--time', now]

                self.resetMocks()
                retval = execute(args)

                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()
                self.assertNothingLogged(logs)

                heartbeat = {
                    'entity': u(entity),
                    'time': float(now),
                    'type': 'file',
                    'category': category,
                    'cursorpos': None,
                    'language': 'Text only',
                    'lines': 0,
                    'is_write': False,
                    'dependencies': [],
                    'user_agent': ANY,
                }
                self.assertHeartbeatSent(heartbeat)

                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    @log_capture()
    def test_invalid_category(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:

            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            now = u(int(time.time()))
            category = 'foobar'

            args = ['--entity', entity, '--category', category, '--config', config, '--time', now]
            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'entity': u(entity),
                'time': float(now),
                'type': 'file',
                'category': None,
                'cursorpos': None,
                'language': 'Text only',
                'lines': 0,
                'is_write': False,
                'dependencies': [],
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_old_alternate_language_argument_still_supported(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        language = 'Java'
        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/python.py'
        args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', language.upper()]

        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

        heartbeat = {
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'branch': ANY,
            'time': float(now),
            'type': 'file',
            'cursorpos': None,
            'dependencies': [],
            'language': u(language),
            'lineno': None,
            'lines': 37,
            'is_write': False,
            'user_agent': ANY,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_alternate_project_not_used(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now1 = u(int(time.time()))
        project1 = os.path.basename(os.path.abspath('.'))
        project_not_used = 'xyz'
        entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
        entity2 = os.path.abspath('tests/samples/codefiles/twolinefile.txt')
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats']

        with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
            now2 = int(time.time())
            heartbeats = json.dumps([{
                'timestamp': now2,
                'entity': entity2,
                'entity_type': 'file',
                'alternate_project': project_not_used,
                'is_write': True,
            }])
            mock_stdin.readline.return_value = heartbeats

            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity1,
                'project': project1,
                'branch': ANY,
                'time': float(now1),
                'is_write': False,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }
            extra_heartbeats = [{
                'language': 'Text only',
                'lines': 2,
                'entity': entity2,
                'project': project1,
                'branch': ANY,
                'time': float(now2),
                'is_write': True,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }]
            self.assertHeartbeatSent(heartbeat, extra_heartbeats=extra_heartbeats)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_using_project_from_editor(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now1 = u(int(time.time()))
        project1 = os.path.basename(os.path.abspath('.'))
        project2 = 'xyz'
        entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
        entity2 = os.path.abspath('tests/samples/codefiles/twolinefile.txt')
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats']

        with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
            now2 = int(time.time())
            heartbeats = json.dumps([{
                'timestamp': now2,
                'entity': entity2,
                'entity_type': 'file',
                'project': project2,
                'is_write': True,
            }])
            mock_stdin.readline.return_value = heartbeats

            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity1,
                'project': project1,
                'branch': ANY,
                'time': float(now1),
                'is_write': False,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }
            extra_heartbeats = [{
                'language': 'Text only',
                'lines': 2,
                'entity': entity2,
                'project': project2,
                'branch': ANY,
                'time': float(now2),
                'is_write': True,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }]
            self.assertHeartbeatSent(heartbeat, extra_heartbeats=extra_heartbeats)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_when_project_not_detected(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))

            now1 = u(int(time.time()))
            project1 = os.path.basename(os.path.abspath('.'))
            entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
            entity2 = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats']

            with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
                now2 = int(time.time())
                heartbeats = json.dumps([{
                    'timestamp': now2,
                    'entity': entity2,
                    'entity_type': 'file',
                    'is_write': True,
                }])
                mock_stdin.readline.return_value = heartbeats

                retval = execute(args)

                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()
                self.assertNothingLogged(logs)

                heartbeat = {
                    'language': 'Text only',
                    'lines': 0,
                    'entity': entity1,
                    'project': project1,
                    'branch': ANY,
                    'time': float(now1),
                    'is_write': False,
                    'type': 'file',
                    'dependencies': [],
                    'user_agent': ANY,
                }
                extra_heartbeats = [{
                    'language': 'Text only',
                    'lines': 2,
                    'entity': entity2,
                    'project': None,
                    'time': float(now2),
                    'is_write': True,
                    'type': 'file',
                    'dependencies': [],
                    'user_agent': ANY,
                }]
                self.assertHeartbeatSent(heartbeat, extra_heartbeats=extra_heartbeats)

                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_when_project_not_detected_alternate_project_used(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))

            now1 = u(int(time.time()))
            project1 = os.path.basename(os.path.abspath('.'))
            project2 = 'xyz'
            entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
            entity2 = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats']

            with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
                now2 = int(time.time())
                heartbeats = json.dumps([{
                    'timestamp': now2,
                    'entity': entity2,
                    'alternate_project': project2,
                    'entity_type': 'file',
                    'is_write': True,
                }])
                mock_stdin.readline.return_value = heartbeats

                retval = execute(args)

                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()
                self.assertNothingLogged(logs)

                heartbeat = {
                    'language': 'Text only',
                    'lines': 0,
                    'entity': entity1,
                    'project': project1,
                    'branch': ANY,
                    'time': float(now1),
                    'is_write': False,
                    'type': 'file',
                    'dependencies': [],
                    'user_agent': ANY,
                }
                extra_heartbeats = [{
                    'language': 'Text only',
                    'lines': 2,
                    'entity': entity2,
                    'project': project2,
                    'time': float(now2),
                    'is_write': True,
                    'type': 'file',
                    'dependencies': [],
                    'user_agent': ANY,
                }]
                self.assertHeartbeatSent(heartbeat, extra_heartbeats=extra_heartbeats)

                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_with_malformed_json(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))

            entity = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--extra-heartbeats']

            with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
                heartbeats = '[{foobar}]'
                mock_stdin.readline.return_value = heartbeats

                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()
                actual = self.getLogOutput(logs)
                self.assertIn('WakaTime WARNING Malformed extra heartbeats json', actual)

                self.assertHeartbeatSent()

                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_with_null_heartbeat(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now1 = u(int(time.time()))
        project1 = os.path.basename(os.path.abspath('.'))
        project_not_used = 'xyz'
        entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
        entity2 = os.path.abspath('tests/samples/codefiles/twolinefile.txt')
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats']

        with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
            now2 = int(time.time())
            heartbeats = json.dumps([
                None,
                {
                    'timestamp': now2,
                    'entity': entity2,
                    'entity_type': 'file',
                    'alternate_project': project_not_used,
                    'is_write': True,
                },
            ])
            mock_stdin.readline.return_value = heartbeats

            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity1,
                'project': project1,
                'branch': ANY,
                'time': float(now1),
                'is_write': False,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }
            extra_heartbeats = [{
                'language': 'Text only',
                'lines': 2,
                'entity': entity2,
                'project': ANY,
                'branch': ANY,
                'time': float(now2),
                'is_write': True,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }]
            self.assertHeartbeatSent(heartbeat, extra_heartbeats=extra_heartbeats)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_extra_heartbeats_with_skipped_heartbeat(self, logs):
        logging.disable(logging.NOTSET)

        response = CustomResponse()
        response.response_text = '{"responses": [[null, 201], [null,201]]}'
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now1 = u(int(time.time()))
        project_not_used = 'xyz'
        entity1 = os.path.abspath('tests/samples/codefiles/emptyfile.txt')
        entity2 = os.path.abspath('tests/samples/codefiles/twolinefile.txt')
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--time', now1, '--file', entity1, '--config', config, '--extra-heartbeats', '--exclude', 'twoline']

        with mock.patch('wakatime.main.sys.stdin') as mock_stdin:
            now2 = int(time.time())
            heartbeats = json.dumps([
                {
                    'timestamp': now2,
                    'entity': entity2,
                    'entity_type': 'file',
                    'alternate_project': project_not_used,
                    'is_write': True,
                },
            ])
            mock_stdin.readline.return_value = heartbeats

            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'WakaTime WARNING Results from api not matching heartbeats sent.'
            self.assertIn(expected, actual)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity1,
                'project': ANY,
                'branch': ANY,
                'time': float(now1),
                'is_write': False,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_exclude_unknown_project_arg(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--exclude-unknown-project', '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'WakaTime DEBUG Skipping because project unknown.'
            self.assertEquals(actual, expected)

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    @log_capture()
    def test_uses_wakatime_home_env_variable(self, logs):
        logging.disable(logging.NOTSET)
        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            key = str(uuid.uuid4())
            config = 'tests/samples/configs/good_config.cfg'
            logfile = os.path.realpath(os.path.join(tempdir, '.wakatime.log'))

            args = ['--file', entity, '--key', key, '--config', config]

            with mock.patch.object(sys, 'argv', ['wakatime'] + args):
                args, configs = parse_arguments()
                self.assertEquals(args.log_file, None)

                with mock.patch('os.environ.get') as mock_env:
                    mock_env.return_value = os.path.realpath(tempdir)

                    args, configs = parse_arguments()
                    self.assertEquals(args.log_file, logfile)
                    self.assertNothingPrinted()
                    self.assertNothingLogged(logs)

    @log_capture()
    def test_legacy_disableoffline_arg_supported(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].side_effect = RequestException('requests exception')

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--disableoffline',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = "WakaTime ERROR {'RequestException': u'requests exception'}"
            if is_py3:
                expected = "WakaTime ERROR {'RequestException': 'requests exception'}"
            self.assertEquals(expected, log_output)

            self.assertHeartbeatSent()
            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_legacy_hidefilenames_arg_supported(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--hidefilenames', '--logfile', '~/.wakatime.log', '--alternate-project', project]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Python',
                'lines': None,
                'entity': 'HIDDEN.py',
                'project': project,
                'time': float(now),
                'is_write': False,
                'type': 'file',
                'dependencies': None,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_deprecated_logfile_arg_supported(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with NamedTemporaryFile() as fh:
            now = u(int(time.time()))
            entity = 'tests/samples/codefiles/python.py'
            config = 'tests/samples/configs/good_config.cfg'
            logfile = os.path.realpath(fh.name)
            args = ['--file', entity, '--config', config, '--time', now, '--logfile', logfile]

            execute(args)

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()

            self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
            self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)
            logs.check()
