# -*- coding: utf-8 -*-


from wakatime.main import execute
import requests

import base64
import logging
import os
import time
import re
import shutil
import uuid
from wakatime.compat import u
from wakatime.constants import (
    AUTH_ERROR,
    CONFIG_FILE_PARSE_ERROR,
    SUCCESS,
)
from requests.models import Response
from .utils import mock, ANY, CustomResponse, TemporaryDirectory, TestCase


class ConfigsTestCase(TestCase):
    patch_these = [
        'requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    def test_config_file_not_passed_in_command_line_args(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            args = ['--file', entity, '--log-file', '~/.wakatime.log']

            with mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = None

                with mock.patch('wakatime.configs.open') as mock_open:
                    mock_open.side_effect = IOError('')

                    retval = execute(args)
                    assert retval == AUTH_ERROR

        captured = self._capsys.readouterr()
        assert captured.out == ''
        expected_stderr = open('tests/samples/output/common_usage_header').read()
        expected_stderr += open('tests/samples/output/configs_test_config_file_not_passed_in_command_line_args').read()
        assert captured.err == expected_stderr

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_config_file_from_env(self):
        logging.disable(logging.NOTSET)

        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
                assert retval == SUCCESS

                captured = self._capsys.readouterr()
                expected_stdout = open('tests/samples/output/configs_test_good_config_file').read()
                traceback_file = os.path.realpath('wakatime/arguments.py')
                lineno = int(re.search(r' line (\d+),', captured.out).group(1))
                self.assertEquals(captured.out, expected_stdout.format(file=traceback_file, lineno=lineno))
                self.assertEquals(captured.err, '')

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
            retval = execute(args)

        self.assertEquals(retval, AUTH_ERROR)

        captured = self._capsys.readouterr()
        expected_stdout = u('')
        expected_stderr = open('tests/samples/output/common_usage_header').read()
        expected_stderr += open('tests/samples/output/configs_test_missing_config_file').read()
        assert captured.out == expected_stdout
        assert captured.err == expected_stderr

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_good_config_file(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/has_everything.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']
            retval = execute(args)
            assert retval == SUCCESS

            captured = self._capsys.readouterr()
            expected_stdout = open('tests/samples/output/configs_test_good_config_file').read()
            traceback_file = os.path.realpath('wakatime/arguments.py')
            lineno = int(re.search(r' line (\d+),', captured.out).group(1))
            assert captured.out == expected_stdout.format(file=traceback_file, lineno=lineno)
            assert captured.err == ''

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_api_key_setting_without_underscore_accepted(self):
        """Api key in wakatime.cfg should also work without an underscore:
            apikey = XXX
        """

        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/sample_alternate_apikey.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']
            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_bad_config_file(self):
        logging.disable(logging.NOTSET)

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/bad_config.cfg'
            args = ['--file', entity, '--config', config, '--log-file', '~/.wakatime.log']

            retval = execute(args)
            assert retval == CONFIG_FILE_PARSE_ERROR

            captured = self._capsys.readouterr()
            assert 'ParsingError' in captured.out
            assert captured.err == ''

            self.assertNothingLogged()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

    def test_non_hidden_filename(self):
        logging.disable(logging.NOTSET)

        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
            self.assertNothingLogged()

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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
                'Authorization': u('Basic {0}').format(u(base64.b64encode(str.encode(key)))),
            }
            self.assertHeartbeatSent(heartbeat, headers=headers)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_does_not_hide_unmatching_filenames(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names_not_python.cfg'
            key = u(uuid.uuid4())
            dependencies = ['sqlalchemy', 'jinja', 'simplejson', 'flask', 'app', 'django', 'pygments', 'unittest', 'mock', 'first', 'second']
            project = 'abcxyz'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log', '--alternate-project', project]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Python',
                'lines': 38,
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

    def test_does_not_hide_file_names_from_invalid_regex(self):
        logging.disable(logging.NOTSET)

        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/invalid_hide_file_names.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            expected = 'Regex error (missing ), unterminated subpattern at position 7) for hide_file_names pattern: invalid(regex'
            assert expected in self.getLogOutput()

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

    def test_hide_matching_filenames_showing_branch_names(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
            shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
            entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names_showing_branch_name.cfg'
            key = u(uuid.uuid4())
            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Text only',
                'lines': None,
                'entity': 'HIDDEN.txt',
                'project': 'git',
                'branch': 'master',
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

    def test_obfuscte_project_names(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
            shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
            entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
            now = u(int(time.time()))
            config = 'tests/samples/configs/paranoid_projects.cfg'
            key = u(uuid.uuid4())
            generated_proj = 'Icy Bridge 42'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            with mock.patch('wakatime.project.generate_project_name') as mock_proj:
                mock_proj.return_value = generated_proj

                retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Text only',
                'lines': None,
                'entity': os.path.realpath(entity),
                'project': generated_proj,
                'branch': None,
                'time': float(now),
                'is_write': False,
                'type': 'file',
                'dependencies': None,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            detected_proj = open(os.path.join(tempdir, 'git', '.wakatime-project')).read()
            self.assertEquals(detected_proj, generated_proj)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_obfuscate_project_names_showing_branch_names(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
            shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
            entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
            now = u(int(time.time()))
            config = 'tests/samples/configs/paranoid_projects_showing_branch_names.cfg'
            key = u(uuid.uuid4())
            generated_proj = 'Icy Bridge 42'

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--log-file', '~/.wakatime.log']

            with mock.patch('wakatime.project.generate_project_name') as mock_proj:
                mock_proj.return_value = generated_proj

                retval = execute(args)

            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            heartbeat = {
                'language': 'Text only',
                'lines': None,
                'entity': os.path.realpath(entity),
                'project': generated_proj,
                'branch': 'master',
                'time': float(now),
                'is_write': False,
                'type': 'file',
                'dependencies': None,
                'user_agent': ANY,
            }
            self.assertHeartbeatSent(heartbeat)

            detected_proj = open(os.path.join(tempdir, 'git', '.wakatime-project')).read()
            self.assertEquals(detected_proj, generated_proj)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_exclude_file(self):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--exclude', 'empty', '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            actual = self.getLogOutput()
            expected = 'Skipping because matches exclude pattern: empty'
            assert expected in actual

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    def test_exclude_file_without_project_file(self):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/include_only_with_project_file.cfg'

            args = ['--file', entity, '--config', config, '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            actual = self.getLogOutput()
            expected = 'Skipping because missing .wakatime-project file in parent path.'
            assert expected in actual

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    def test_exclude_file_because_project_unknown(self):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/exclude_unknown_project.cfg'

            args = ['--file', entity, '--config', config, '--verbose', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            actual = self.getLogOutput()
            expected = 'Skipping because project unknown.'
            assert expected in actual

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheUntouched()

    def test_include_file_with_project_file(self):
        logging.disable(logging.NOTSET)

        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

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
                'X-Machine-Name': hostname.encode('utf-8'),
            }
            self.assertHeartbeatSent(headers=headers, proxies=ANY, timeout=15)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_no_ssl_verify_from_config_file(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/ssl_verify_disabled.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            self.assertHeartbeatSent(proxies=ANY, timeout=15, verify=False)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_ssl_custom_ca_certs_file(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/ssl_custom_certfile.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--log-file', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            self.assertHeartbeatSent(proxies=ANY, timeout=15, verify='/fake/ca/certs/bundle.pem')

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()
