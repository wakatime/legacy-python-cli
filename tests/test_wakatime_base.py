# -*- coding: utf-8 -*-


import sys
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from wakatime.base import main


@patch('wakatime.packages.requests.adapters.HTTPAdapter.send')
class BaseTestCase(utils.TestCase):

    def test_help_contents(self, mock_requests):
        args = ['--help']
        with self.assertRaises(SystemExit):
            main(args)
        expected_stdout = open('tests/samples/output/test_help_contents').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')

    def test_argument_parsing(self, mock_requests):
        response = Response()
        response.status_code = 201
        mock_requests.return_value = response
        args = ['--file', 'tests/samples/twolinefile.txt', '--key', '123', '--config', 'foo']
        retval = main(args)
        self.assertEquals(retval, 0)
        expected_stdout = u("Error: Could not read from config file foo\n")
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), '')

    def test_missing_config_file(self, mock_requests):
        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'foo']
        with self.assertRaises(SystemExit):
            main(args)
        expected_stdout = u("Error: Could not read from config file foo\n")
        expected_stderr = open('tests/samples/output/test_missing_config_file').read()
        self.assertEquals(sys.stdout.getvalue(), expected_stdout)
        self.assertEquals(sys.stderr.getvalue(), expected_stderr)

    def test_config_file(self, mock_requests):
        response = Response()
        response.status_code = 201
        mock_requests.return_value = response
        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'tests/samples/sample.cfg']
        retval = main(args)
        self.assertEquals(retval, 0)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

    def test_bad_config_file(self, mock_requests):
        args = ['--file', 'tests/samples/emptyfile.txt', '--config', 'tests/samples/bad_config.cfg']
        retval = main(args)
        self.assertEquals(retval, 103)
        self.assertIn('ParsingError', sys.stdout.getvalue())
        self.assertEquals(sys.stderr.getvalue(), '')
