# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

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
    API_ERROR,
    AUTH_ERROR,
    CONFIG_FILE_PARSE_ERROR,
    SUCCESS,
)
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


class ConfigsTestCase(utils.TestCase):
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
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            args = ['--file', entity, '--logfile', '~/.wakatime.log']

            with utils.mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = None

                with utils.mock.patch('wakatime.configs.open') as mock_open:
                    mock_open.side_effect = IOError('')

                    with self.assertRaises(SystemExit) as e:
                        execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        expected_stdout = u('')
        expected_stderr = open('tests/samples/output/configs_test_config_file_not_passed_in_command_line_args').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)
        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_config_file_from_env(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/has_everything.cfg'
            shutil.copy(config, os.path.join(tempdir, '.wakatime.cfg'))
            config = os.path.realpath(os.path.join(tempdir, '.wakatime.cfg'))

            with utils.mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = tempdir

                args = ['--file', entity, '--logfile', '~/.wakatime.log']
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                expected_stdout = open('tests/samples/output/main_test_good_config_file').read()
                traceback_file = os.path.realpath('wakatime/arguments.py')
                lineno = int(re.search(r' line (\d+),', sys.stdout.getvalue()).group(1))
                self.assertEquals(sys.stdout.getvalue(), expected_stdout.format(file=traceback_file, lineno=lineno))
                self.assertEquals(sys.stderr.getvalue(), '')

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_missing_config_file(self):
        config = 'foo'

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            args = ['--file', entity, '--config', config, '--logfile', '~/.wakatime.log']
            with self.assertRaises(SystemExit) as e:
                execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)

        expected_stdout = u('')
        expected_stderr = open('tests/samples/output/configs_test_missing_config_file').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

    def test_good_config_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/has_everything.cfg'
            args = ['--file', entity, '--config', config, '--logfile', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            expected_stdout = open('tests/samples/output/main_test_good_config_file').read()
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

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/sample_alternate_apikey.cfg'
            args = ['--file', entity, '--config', config, '--logfile', '~/.wakatime.log']
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

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/bad_config.cfg'
            args = ['--file', entity, '--config', config, '--logfile', '~/.wakatime.log']

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

    def test_non_hidden_filename(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 2,
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
                u('lines'): 2,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_hide_all_filenames(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/paranoid.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
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

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_hide_all_filenames_from_cli_arg(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--hidefilenames', '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
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

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_hide_matching_filenames(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
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

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_does_not_hide_unmatching_filenames(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/hide_file_names.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity,
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

    @log_capture()
    def test_does_not_hide_filenames_from_invalid_regex(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            now = u(int(time.time()))
            config = 'tests/samples/configs/invalid_hide_file_names.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now, '--logfile', '~/.wakatime.log']

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: invalid(regex')
            if self.isPy35OrNewer:
                expected = 'WakaTime WARNING Regex error (missing ), unterminated subpattern at position 7) for include pattern: invalid(regex'
            self.assertEquals(expected, log_output)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': entity,
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

    @log_capture()
    def test_exclude_file(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--exclude', 'empty', '--verbose', '--logfile', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)

            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = 'WakaTime DEBUG Skipping because matches exclude pattern: empty'
            self.assertEquals(log_output, expected)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

    def test_hostname_set_from_config_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            hostname = 'fromcfgfile'
            config = 'tests/samples/configs/has_everything.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--logfile', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
            self.assertEquals(headers.get('X-Machine-Name'), hostname.encode('utf-8') if is_py3 else hostname)

    def test_no_ssl_verify_from_config_file(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/has_ssl_verify_disabled.cfg'
            args = ['--file', entity, '--config', config, '--timeout', '15', '--logfile', '~/.wakatime.log']
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies=ANY, stream=False, timeout=15, verify=False)
