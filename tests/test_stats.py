# -*- coding: utf-8 -*-


import logging
import os
import time
import uuid
from testfixtures import log_capture
from .utils import ANY, CustomResponse, NamedTemporaryFile, TestCase, mock

from wakatime.compat import u
from wakatime.constants import SUCCESS
from wakatime.main import execute
from wakatime.packages import requests
from wakatime.stats import number_lines_in_file


class StatsTestCase(TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    @log_capture()
    def test_guess_lexer_using_filename_analyse_text_exception(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with NamedTemporaryFile() as fh:
            with mock.patch('wakatime.offlinequeue.Queue._get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                mock_analyse = mock.MagicMock()
                mock_analyse.analyse_text.side_effect = Exception('foobar')
                with mock.patch('wakatime.stats.custom_pygments_guess_lexer_for_filename') as mock_lexer:
                    mock_lexer.return_value = mock_analyse

                    entity = os.path.realpath('tests/samples/codefiles/python.py')
                    args = ['--file', entity, '--key', str(uuid.uuid4()), '--config', 'tests/samples/configs/good_config.cfg', '--time', u(int(time.time()))]
                    retval = execute(args)
                    self.assertEquals(retval, SUCCESS)

                    self.assertNothingPrinted()
                    self.assertNothingLogged(logs)

                    heartbeat = {
                        'entity': entity,
                        'language': ANY,
                        'lines': ANY,
                        'project': ANY,
                        'branch': ANY,
                        'time': ANY,
                        'type': 'file',
                        'is_write': ANY,
                        'user_agent': ANY,
                        'dependencies': ANY,
                    }
                    self.assertHeartbeatSent(heartbeat)

    @log_capture()
    def test_guess_lexer_using_filename_analyse_text_exception_and_logs_error_when_debugging(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with NamedTemporaryFile() as fh:
            with mock.patch('wakatime.offlinequeue.Queue._get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                mock_analyse = mock.MagicMock()
                mock_analyse.analyse_text.side_effect = Exception('foobar')
                with mock.patch('wakatime.stats.custom_pygments_guess_lexer_for_filename') as mock_lexer:
                    mock_lexer.return_value = mock_analyse

                    entity = os.path.realpath('tests/samples/codefiles/python.py')
                    args = ['--file', entity, '--key', str(uuid.uuid4()), '--config', 'tests/samples/configs/good_config.cfg', '--time', u(int(time.time())), '--verbose']
                    retval = execute(args)
                    self.assertEquals(retval, SUCCESS)

                    self.assertNothingPrinted()
                    actual = self.getLogOutput(logs)
                    expected = 'Exception: foobar'
                    self.assertIn(expected, actual)

                    heartbeat = {
                        'entity': entity,
                        'language': ANY,
                        'lines': ANY,
                        'project': ANY,
                        'branch': ANY,
                        'time': ANY,
                        'type': 'file',
                        'is_write': ANY,
                        'user_agent': ANY,
                        'dependencies': ANY,
                    }
                    self.assertHeartbeatSent(heartbeat)

    @log_capture()
    def test_number_lines_in_file_getsize_os_error(self, logs):
        logging.disable(logging.NOTSET)

        with mock.patch('wakatime.stats.os.path.getsize') as mock_getsize:
            mock_getsize.side_effect = os.error('')

            entity = os.path.realpath('tests/samples/codefiles/java.java')
            result = number_lines_in_file(entity)
            self.assertEquals(result, 22)

            self.assertNothingPrinted()
            self.assertNothingLogged(logs)
