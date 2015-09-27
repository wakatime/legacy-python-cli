# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import logging
import os
import tempfile
import time
import sys
from testfixtures import log_capture
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils


class LanguagesTestCase(utils.TestCase):
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
        config = 'tests/samples/configs/sample.cfg'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
        logfile = os.path.realpath(os.path.expanduser('~/.wakatime.log'))
        self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)
        output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        self.assertEquals(output, u("WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: \\(invalid regex)\nWakaTime WARNING Regex error (unbalanced parenthesis) for exclude pattern: \\(invalid regex)"))

    @log_capture()
    def test_log_file_location_can_be_changed(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with tempfile.NamedTemporaryFile() as fh:
            now = u(int(time.time()))
            entity = 'tests/samples/codefiles/python.py'
            config = 'tests/samples/configs/good_config.cfg'
            logfile = os.path.realpath(fh.name)
            args = ['--file', entity, '--config', config, '--time', now, '--logfile', logfile]

            execute(args)

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.assertEquals(logging.WARNING, logging.getLogger('WakaTime').level)
            self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)
            logs.check()

    @log_capture()
    def test_verbose_flag_enables_verbose_logging(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/configs/sample.cfg'
        args = ['--file', entity, '--config', config, '--time', now, '--verbose']

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.assertEquals(logging.DEBUG, logging.getLogger('WakaTime').level)
        logfile = os.path.realpath(os.path.expanduser('~/.wakatime.log'))
        self.assertEquals(logfile, logging.getLogger('WakaTime').handlers[0].baseFilename)
        output = [u(' ').join(x) for x in logs.actual()]
        self.assertEquals(output[0], u('WakaTime WARNING Regex error (unbalanced parenthesis) for include pattern: \\(invalid regex)'))
        self.assertEquals(output[1], u('WakaTime WARNING Regex error (unbalanced parenthesis) for exclude pattern: \\(invalid regex)'))
        self.assertEquals(output[2], u('WakaTime DEBUG Sending heartbeat to api at https://wakatime.com/api/v1/heartbeats'))
        self.assertIn('Python', output[3])
        self.assertIn('response_code', output[4])
