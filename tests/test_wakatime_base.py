# -*- coding: utf-8 -*-


import logging
import unittest

try:
    from mock import patch
except:
    from unittest.mock import patch

from wakatime.base import main


@patch('requests.post')
class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)

    def test_help_contents(self, mock_post):
        with self.assertRaises(SystemExit):
            args = ['', '--help']
            retval = main(args)
            self.assertEquals(retval, 0)

    def test_argument_parsing(self, mock_post):
        args = ['', '--file', 'tests/samples/emptyfile.txt']
        retval = main(args)
        self.assertEquals(retval, 0)
