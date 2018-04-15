# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import base64
import logging
import os
import time
import re
import shutil
import sys
import uuid
from testfixtures import log_capture
from wakatime.compat import u, is_py3
from wakatime.constants import (
    AUTH_ERROR,
    CONFIG_FILE_PARSE_ERROR,
    SUCCESS,
)
from wakatime.packages.requests.models import Response
from .utils import mock, ANY, CustomResponse, TemporaryDirectory, TestCase


class ConfigsTestCase(TestCase):
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

    def test_config_file_not_passed_in_command_line_args(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            args = ['--file', entity, '--log-file', '~/.wakatime.log']

            with mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = None

                with mock.patch('wakatime.configs.open') as mock_open:
                    mock_open.side_effect = IOError('')

                    with self.assertRaises(SystemExit) as e:
                        execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        expected_stdout = u('')
        expected_stderr = open('tests/samples/output/configs_test_config_file_not_passed_in_command_line_args').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)
        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    @log_capture()
    def test_config_file_from_env(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/has_everything.cfg'
            shutil.copy(config, os.path.join(tempdir, '.wakatime.cfg'))
            config = os.path.realpath(os.path.join(tempdir, '.wakatime.cfg'))

            with mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = tempdir

                args = ['--file', entity, '--log-file', '~/.wakatime.log']
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                expected_stdout = open('tests/samples/output/configs_test_good_config_file').read()
                traceback_file = os.path.realpath('wakatime/arguments.py')
                lineno = int(re.search(r' line (\d+),', sys.stdout.getvalue()).group(1))
                self.assertEquals(sys.stdout.getvalue(), expected_stdout.format(file=traceback_file, lineno=lineno))
                self.assertEquals(sys.stderr.getvalue(), '')

                self.assertHeartbeatSent(proxies=ANY, verify=ANY)

                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    def test_missing_config_file(self):
        config = 'foo'

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']
            with self.assertRaises(SystemExit) as e:
                execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)

        expected_stdout = u('')
        expected_stderr = open('tests/samples/output/configs_test_missing_config_file').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_good_config_file(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/has_everything.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            expected_stdout = open('tests/samples/output/configs_test_good_config_file').read()
            traceback_file = os.path.realpath('wakatime/arguments.py')
            lineno = int(re.search(r' line (\d+),', sys.stdout.getvalue()).group(1))
            self.assertEquals(sys.stdout.getvalue(), expected_stdout.format(file=traceback_file, lineno=lineno))
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_api_key_setting_without_underscore_accepted(self):
        """Api key in wakatime.cfg should also work without an underscore:
            apikey = XXX
        """

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/sample_alternate_apikey.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    @log_capture()
    def test_bad_config_file(self, logs):
        logging.disable(logging.NOTSET)

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/bad_config.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']

            with self.assertRaises(SystemExit) as e:
                execute(args)

            self.assertEquals(int(str(e.exception)), CONFIG_FILE_PARSE_ERROR)
            self.assertIn('ParsingError', sys.stdout.getvalue())
            expected_stderr = ''
            self.assertEquals(sys.stderr.getvalue(), expected_stderr)

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = ''
            self.assertEquals(log_output, expected)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

    @log_capture()
    def test_non_hidden_filename(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

            heartbeat = {
                'entity': os.path.realpath(entity),
                'project': None,
                'branch': None,
                'time': float(now),
                'type': 'file',
                'cursorpos': None,
                'dependencies': [],
                'language': u('Text only'),
                'lineno': None,
                'lines': 2,
                'is_write': False,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_hide_all_filenames(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/paranoid.cfg'
            key = u(uuid.uuid4())
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log', '--alternate-project', project]

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

    def test_legacy_hidefilenames_config_supported(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/paranoid_legacy.cfg'
            key = u(uuid.uuid4())
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log', '--alternate-project', project]

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

    def test_hide_all_filenames_from_cli_arg(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--hide-filenames', '--log-file', '~/.wakatime.log', '--alternate-project', project]

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

    def test_hide_matching_filenames(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names.cfg'
            key = '033c47c9-0441-4eb5-8b3f-b51f27b31049'
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log', '--alternate-project', project]

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
            headers = {
                'Authorization': u('Basic {0}').format(u(base64.b64encode(str.encode(key) if is_py3 else key))),
            }
            self.assertHeartbeatSent(heartbeat, headers=headers)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_does_not_hide_unmatching_filenames(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names_not_python.cfg'
            key = u(uuid.uuid4())
            dependencies = ['sqlalchemy', 'jinja', 'simplejson', 'flask', 'app', 'django', 'pygments', 'unittest', 'mock']
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log', '--alternate-project', project]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Python',
                'lines': 37,
                'entity': entity,
                'project': project,
                'time': float(now),
                'is_write': False,
                'type': 'file',
                'dependencies': dependencies,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    @log_capture()
    def test_does_not_hide_filenames_from_invalid_regex(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/invalid_hide_file_names.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            actual = self.getLogOutput(logs)
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: invalid(regex')
            if self.isPy35OrNewer:
                expected = 'WakaTime WARNING Regex error (missing ), unterminated subpattern at position 7) for include pattern: invalid(regex'
            self.assertEquals(expected, actual)

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': None,
                'cursorpos': None,
                'lineno': None,
                'time': float(now),
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
    def test_exclude_file(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--exclude', 'empty', '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'WakaTime DEBUG Skipping because matches exclude pattern: empty'
            self.assertEquals(actual, expected)

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    @log_capture()
    def test_exclude_file_without_project_file(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/include_only_with_project_file.cfg'

            args = ['--file', entity, '--config', config, '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'WakaTime DEBUG Skipping because missing .wakatime-project file in parent path.'
            self.assertEquals(actual, expected)

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    @log_capture()
    def test_exclude_file_because_project_unknown(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/exclude_unknown_project.cfg'

            args = ['--file', entity, '--config', config, '--verbose', '--log-file', '~/.wakatime.log']
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
    def test_include_file_with_project_file(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/include_only_with_project_file.cfg'
            project = 'abcxyz'
            now = u(int(time.time()))

            with open(os.path.join(tempdir, '.wakatime-project'), 'w'):
                pass

            args = ['--file', entity, '--config', config, '--time', now, '--verbose', '--log-file', '~/.wakatime.log', '--project', project]
            retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': project,
                'branch': ANY,
                'cursorpos': None,
                'lineno': None,
                'time': float(now),
                'is_write': False,
                'type': 'file',
                'dependencies': [],
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_hostname_set_from_config_file(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            hostname = 'fromcfgfile'
            config = 'tests/samples/configs/has_everything.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            headers = {
                'X-Machine-Name': hostname.encode('utf-8') if is_py3 else hostname,
            }
            self.assertHeartbeatSent(headers=headers, proxies=ANY, timeout=15)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_no_ssl_verify_from_config_file(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/has_ssl_verify_disabled.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            self.assertHeartbeatSent(proxies=ANY, timeout=15, verify=False)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()
