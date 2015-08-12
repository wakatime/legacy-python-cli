# -*- coding: utf-8 -*-

import logging

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

class TestCase(unittest.TestCase):
    patch_these = []

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)

        self.patched = {}
        if hasattr(self, 'patch_these'):
            for patch_this in self.patch_these:
                namespace = patch_this[0] if isinstance(patch_this, (list, set)) else patch_this

                patcher = patch(namespace)
                mocked = patcher.start()
                self.patched[namespace] = mocked

                if isinstance(patch_this, (list, set)) and len(patch_this) > 0:
                    retval = patch_this[1]
                    if callable(retval):
                        retval = retval()
                    mocked.return_value = retval

    def tearDown(self):
        patch.stopall()
