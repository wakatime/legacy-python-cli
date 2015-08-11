# -*- coding: utf-8 -*-


import logging
from wakatime.packages.requests.models import Response

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    # Python >= 2.7
    import unittest

from wakatime.base import main


@patch('wakatime.packages.requests.adapters.HTTPAdapter.send')
class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)

    def test_help_contents(self, mock_requests):
        args = ['', '--help']
        with self.assertRaises(SystemExit):
            retval = main(args)
            self.assertEquals(retval, 0)

    def test_argument_parsing(self, mock_requests):
        response = Response()
        response.status_code = 201
        mock_requests.return_value = response
        args = ['', '--file', 'tests/samples/emptyfile.txt', '--key', '123']
        retval = main(args)
        self.assertEquals(retval, 0)
