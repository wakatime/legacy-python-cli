# -*- coding: utf-8 -*-

import logging

try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    # Python >= 2.7
    import unittest

class TestCase(unittest.TestCase):

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)
