# -*- coding: utf-8 -*-


from wakatime.compat import u
from wakatime.main import execute
import requests
from requests.models import Response

import logging
import os
import platform
import time
import shutil
import unittest
from . import utils


class LoggingTestCase(utils.TestCase):
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

    def test_default_log_file_used(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/has_regex_errors.cfg'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertNothingPrinted()

        self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
        logfile = os.path.realpath(os.path.expanduser('~/.wakatime.log'))
        self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)

        expected = 'Regex error (unbalanced parenthesis at position 15) for include pattern: \\(invalid regex)'
        assert expected in self.getLogOutput()

    def test_log_file_location_can_be_changed(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.NamedTemporaryFile() as fh:
            now = u(int(time.time()))
            entity = 'tests/samples/codefiles/python.py'
            config = 'tests/samples/configs/good_config.cfg'
            logfile = os.path.realpath(fh.name)
            args = ['--file', entity, '--config', config, '--time', now, '--log-file', logfile]

            execute(args)

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()

            self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
            self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)

            self.assertNothingLogged()

    @unittest.skipIf(platform.system() == 'Windows', 'Windows file issue')
    def test_log_file_location_can_be_set_from_env_variable(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            config = 'tests/samples/configs/good_config.cfg'
            shutil.copy(config, os.path.join(tempdir, '.wakatime.cfg'))
            config = os.path.realpath(os.path.join(tempdir, '.wakatime.cfg'))
            expected_logfile = os.path.realpath(os.path.join(tempdir, '.wakatime.log'))

            with utils.mock.patch('wakatime.configs.os.environ.get') as mock_env:
                mock_env.return_value = tempdir

                args = ['--file', entity, '--config', config, '--time', now]

                execute(args)

                retval = execute(args)
                self.assertEquals(retval, 102)
                self.assertNothingPrinted()

                self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
                logfile = os.path.realpath(logging.getLogger('WakaTime').handlers[0].baseFilename)
                self.assertEquals(logfile, expected_logfile)

                self.assertNothingLogged()

    def test_verbose_flag_enables_verbose_logging(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/has_regex_errors.cfg'
        args = ['--file', entity, '--config', config, '--time', now, '--verbose']

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertNothingPrinted()

        self.assertEquals(logging.DEBUG, logging.getLogger('WakaTime').level)
        logfile = os.path.realpath(os.path.expanduser('~/.wakatime.log'))
        self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)

        log_output = self.getLogOutput()
        expected = 'Regex error (unbalanced parenthesis at position 15) for include pattern: \\(invalid regex)'
        assert expected in log_output
        expected = 'Sending heartbeats to api at https://api.wakatime.com/api/v1/users/current/heartbeats.bulk'
        assert expected in log_output
        assert 'Python' in log_output
        assert 'response_code' in log_output

    def test_exception_traceback_logged_in_debug_mode(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--time', now, '--verbose']

        with utils.mock.patch('wakatime.stats.open') as mock_open:
            mock_open.side_effect = Exception('FooBar')

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()

            log_output = self.getLogOutput()
            assert 'Traceback (most recent call last):' in log_output
            assert 'Exception: FooBar' in log_output

    def test_exception_traceback_not_logged_normally(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.stats.open') as mock_open:
            mock_open.side_effect = Exception('FooBar')

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()
            self.assertNothingLogged()

    def test_can_log_invalid_utf8(self):
        data = bytes('\xab', 'utf-16')

        with self.assertRaises(UnicodeDecodeError):
            data.decode('utf8')

        logger = logging.getLogger('WakaTime')
        logger.error(data)

        assert u(data) in self.getLogOutput()
