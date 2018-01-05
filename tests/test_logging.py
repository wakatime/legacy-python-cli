# -*- coding: utf-8 -*-


from wakatime.compat import is_py3, u
from wakatime.main import execute
from wakatime.packages import requests
from wakatime.packages.requests.models import Response

import logging
import os
import time
import shutil
from testfixtures import log_capture
from . import utils


class LoggingTestCase(utils.TestCase):
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
    def test_default_log_file_used(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

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
        output = [u(' ').join(x) for x in logs.actual()]
        expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: \\(invalid regex)')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis at position 15) for include pattern: \\(invalid regex)')
        self.assertEquals(output[0], expected)
        expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for exclude pattern: \\(invalid regex)')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis at position 15) for exclude pattern: \\(invalid regex)')
        self.assertEquals(output[1], expected)

    @log_capture()
    def test_log_file_location_can_be_changed(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

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
            logs.check()

    @log_capture()
    def test_log_file_location_can_be_set_from_env_variable(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))
            config = 'tests/samples/configs/good_config.cfg'
            shutil.copy(config, os.path.join(tempdir, '.wakatime.cfg'))
            config = os.path.realpath(os.path.join(tempdir, '.wakatime.cfg'))
            expected_logfile = os.path.realpath(os.path.join(tempdir, '.wakatime.log'))

            with utils.mock.patch('wakatime.main.os.environ.get') as mock_env:
                mock_env.return_value = tempdir

                args = ['--file', entity, '--config', config, '--time', now]

                execute(args)

                retval = execute(args)
                self.assertEquals(retval, 102)
                self.assertNothingPrinted()

                self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
                logfile = os.path.realpath(logging.getLogger('WakaTime').handlers[0].baseFilename)
                self.assertEquals(logfile, expected_logfile)
                logs.check()

    @log_capture()
    def test_verbose_flag_enables_verbose_logging(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

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
        output = [u(' ').join(x) for x in logs.actual()]

        expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: \\(invalid regex)')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis at position 15) for include pattern: \\(invalid regex)')
        self.assertEquals(output[0], expected)
        expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for exclude pattern: \\(invalid regex)')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unbalanced parenthesis at position 15) for exclude pattern: \\(invalid regex)')
        self.assertEquals(output[1], expected)
        self.assertEquals(output[2], u('WakaTime DEBUG Sending heartbeats to api at https://api.wakatime.com/api/v1/users/current/heartbeats.bulk'))
        self.assertIn('Python', output[3])
        self.assertIn('response_code', output[4])

    @log_capture()
    def test_exception_traceback_logged_in_debug_mode(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--time', now, '--verbose']

        with utils.mock.patch('wakatime.stats.open') as mock_open:
            mock_open.side_effect = Exception('FooBar')

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            self.assertIn(u('WakaTime DEBUG Traceback (most recent call last):'), log_output)
            self.assertIn(u('Exception: FooBar'), log_output)

    @log_capture()
    def test_exception_traceback_not_logged_normally(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/good_config.cfg'
        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.stats.open') as mock_open:
            mock_open.side_effect = Exception('FooBar')

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertNothingPrinted()

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            self.assertEquals(u(''), log_output)

    @log_capture()
    def test_can_log_invalid_utf8(self, logs):
        logging.disable(logging.NOTSET)

        data = bytes('\xab', 'utf-16') if is_py3 else '\xab'

        with self.assertRaises(UnicodeDecodeError):
            data.decode('utf8')

        logger = logging.getLogger('WakaTime')
        logger.error(data)

        found = False
        for msg in list(logs.actual())[0]:
            if u(msg) == u(data):
                found = True
        self.assertTrue(found)
