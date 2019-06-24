# -*- coding: utf-8 -*-


from wakatime.heartbeat import Heartbeat

import os
import logging
from testfixtures import log_capture
from .utils import DynamicIterable, TestCase, mock


class HeartbeatTestCase(TestCase):

    @log_capture()
    def test_sanitize_removes_sensitive_data(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            exclude = []
            hide_file_names = ['.*']
            hide_project_names = []
            hide_branch_names = None
            include = []
            plugin = None
            include_only_with_project_file = None
            local_file = None

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
    def test_sanitize_removes_sensitive_data_but_still_shows_branch(self, logs):
        logging.disable(logging.NOTSET)

        class Args(object):
            exclude = []
            hide_file_names = ['.*']
            hide_project_names = []
            hide_branch_names = []
            include = []
            plugin = None
            include_only_with_project_file = None
            local_file = None

        data = {
            'entity': os.path.realpath('tests/samples/codefiles/python.py'),
            'type': 'file',
            'project': 'aproject',
            'branch': 'abranch',
        }
        heartbeat = Heartbeat(data, Args(), None)
        sanitized = heartbeat.sanitize()
        self.assertEquals('HIDDEN.py', sanitized.entity)
        self.assertEquals('master', sanitized.branch)
        self.assertEquals('aproject', sanitized.project)
        sensitive = [
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
            hide_file_names = []
            hide_project_names = []
            hide_branch_names = None
            include = []
            plugin = None
            include_only_with_project_file = None
            local_file = None

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
            hide_file_names = ['.*']
            hide_project_names = []
            hide_branch_names = None
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
            hide_file_names = ['.*']
            hide_project_names = []
            hide_branch_names = None
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

    def test_parsing(self):

        class Args(object):
            hide_file_names = ['.*']
            hide_project_names = []
            hide_branch_names = None
            plugin = None

        samples = [
            ('v1', 'C:\\v1\\file.txt', '\\\\vboxsrv\\Projects\\v1\\file.txt'),
            ('v2', 'D:\\stuff\\v2\\file.py', '\\\\192.0.0.1\\work\\stuff\\v2\\file.py'),
        ]
        for sample, filepath, expected in samples:
            with mock.patch('wakatime.heartbeat.Popen') as mock_popen:

                class MockCommunicate(object):
                    pass

                stdout = open('tests/samples/netuse/' + sample).read()
                mock_communicate = MockCommunicate()
                mock_communicate.communicate = mock.MagicMock(return_value=DynamicIterable((stdout, ''), max_calls=1))
                mock_popen.return_value = mock_communicate

                heartbeat = Heartbeat({'user_agent': 'test'}, Args(), None, _clone=True)
                result = heartbeat._to_unc_path(filepath)
                self.assertEquals(expected, result)

        self.assertNothingPrinted()
