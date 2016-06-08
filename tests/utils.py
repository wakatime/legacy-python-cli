# -*- coding: utf-8 -*-

import logging
import sys

from wakatime.compat import u


try:
    import mock
except ImportError:
    import unittest.mock as mock
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

                patcher = mock.patch(namespace)
                mocked = patcher.start()
                mocked.reset_mock()
                self.patched[namespace] = mocked

                if isinstance(patch_this, (list, set)) and len(patch_this) > 0:
                    retval = patch_this[1]
                    if callable(retval):
                        retval = retval()
                    mocked.return_value = retval

    def tearDown(self):
        mock.patch.stopall()

    def normalize_list(self, items):
        return sorted([u(x) for x in items])

    def assertListsEqual(self, first_list, second_list):
        self.assertEquals(self.normalize_list(first_list), self.normalize_list(second_list))

    @property
    def isPy35(self):
        return (sys.version_info[0] == 3 and sys.version_info[1] == 5)


try:
    # Python >= 3
    from tempfile import TemporaryDirectory
except ImportError:
    # Python < 3
    import shutil
    import tempfile
    class TemporaryDirectory(object):
        """Context manager for tempfile.mkdtemp().

        Adds the ability to use with a `with` statement.
        """

        def __enter__(self):
            self.name = tempfile.mkdtemp()
            return self.name

        def __exit__(self, exc_type, exc_value, traceback):
            shutil.rmtree(self.name)
