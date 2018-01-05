# -*- coding: utf-8 -*-


from wakatime.heartbeat import Heartbeat

import os
import logging
from testfixtures import log_capture
from .utils import TestCase


class HeartbeatTestCase(TestCase):

    @log_capture()
    def test_sanitize_removes_sensitive_data(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            exclude = []
            hide_filenames = ['.*']
            include = []
            plugin = None
            include_only_with_project_file = None

        data = {
            'entity': os.path.realpath('tests/samples/codefiles/python.py'),
            'type': 'file',
            'project': 'aproject',
            'branch': 'abranch',
        }
        heartbeat = Heartbeat(data, Args(), None)
        sanitized = heartbeat.sanitize()
        self.assertEquals('HIDDEN.py', sanitized.entity)
        sensitive = [
            'branch',
            'dependencies',
            'lines',
            'lineno',
            'cursorpos',
        ]
        for item in sensitive:
            self.assertIsNone(getattr(sanitized, item))

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_sanitize_does_nothing_when_hidefilenames_false(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            exclude = []
            hide_filenames = []
            include = []
            plugin = None
            include_only_with_project_file = None

        data = {
            'entity': os.path.realpath('tests/samples/codefiles/python.py'),
            'type': 'file',
            'project': 'aproject',
            'branch': 'abranch',
        }
        heartbeat = Heartbeat(data, Args(), None)
        heartbeat.branch = data['branch']
        sanitized = heartbeat.sanitize()
        self.assertEquals(data['branch'], sanitized.branch)

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_sanitize_does_nothing_when_missing_entity(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            hide_filenames = ['.*']
            plugin = None

        branch = 'abc123'
        data = {
            'entity': None,
            'type': 'file',
            'branch': branch,
        }
        heartbeat = Heartbeat(data, Args(), None, _clone=True)
        sanitized = heartbeat.sanitize()
        self.assertEquals(branch, sanitized.branch)

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_sanitize_does_nothing_when_type_not_file(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            hide_filenames = ['.*']
            plugin = None

        branch = 'abc123'
        data = {
            'entity': 'not.a.file',
            'type': 'app',
            'branch': branch,
        }
        heartbeat = Heartbeat(data, Args(), None, _clone=True)
        sanitized = heartbeat.sanitize()
        self.assertEquals(branch, sanitized.branch)

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)
