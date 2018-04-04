# -*- coding: utf-8 -*-


from wakatime.utils import format_file_path

import os
from .utils import TestCase, mock


class UtilsTestCase(TestCase):

    def test_format_file_path_forces_forward_slashes(self):
        path = 'some\\path////to\\\\\\a\\file.txt'
        expected = os.path.realpath('some/path/to/a/file.txt')
        result = format_file_path(path)
        self.assertEquals(expected, result)

    def test_format_file_path_uppercase_windows_drive(self):
        path = 'c:\\some\\path////to\\\\\\a\\file.txt'
        expected = 'C:/some/path/to/a/file.txt'

        with mock.patch('os.path.realpath') as mock_realpath:
            mock_realpath.return_value = path
            with mock.patch('os.path.abspath') as mock_abspath:
                mock_abspath.return_value = path

                result = format_file_path(path)
                self.assertEquals(expected, result)

    def test_format_file_path_handles_exceptions(self):
        path = 'c:\\some\\path////to\\\\\\a\\file.txt'
        expected = path

        with mock.patch('os.path.abspath') as mock_abspath:
            mock_abspath.side_effect = Exception('foobar')

            result = format_file_path(path)
            self.assertEquals(expected, result)
