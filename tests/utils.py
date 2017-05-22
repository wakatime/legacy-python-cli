# -*- coding: utf-8 -*-

import logging
import os
import sys
import tempfile

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
    def isPy35OrNewer(self):
        if sys.version_info[0] > 3:
            return True
        return (sys.version_info[0] >= 3 and sys.version_info[1] >= 5)


try:
    # Python >= 3
    from tempfile import TemporaryDirectory
except ImportError:
    # Python < 3
    import shutil
    class TemporaryDirectory(object):
        """Context manager for tempfile.mkdtemp().

        Adds the ability to use with a `with` statement.
        """

        def __enter__(self):
            self.name = tempfile.mkdtemp()
            return self.name

        def __exit__(self, exc_type, exc_value, traceback):
            try:
                shutil.rmtree(u(self.name))
            except:
                pass


class NamedTemporaryFile(object):
    """Context manager for a named temporary file compatible with Windows.

    Provides the path to a closed temporary file that is writeable. Deletes the
    temporary file when exiting the context manager. The built-in
    tempfile.NamedTemporaryFile is not writeable on Windows.
    """
    name = None

    def __enter__(self):
        fh = tempfile.NamedTemporaryFile(delete=False)
        self.name = fh.name
        fh.close()
        return self

    def __exit__(self, type, value, traceback):
        try:
            os.unlink(self.name)
        except:
            pass


class DynamicIterable(object):
    def __init__(self, data, max_calls=None, raise_on_calls=None):
        self.called = 0
        self.max_calls = max_calls
        self.raise_on_calls = raise_on_calls
        self.index = 0
        self.data = data
    def __iter__(self):
        return self
    def __next__(self):
        if self.raise_on_calls and self.called < len(self.raise_on_calls) and self.raise_on_calls[self.called]:
            raise self.raise_on_calls[self.called]
        if self.index >= len(self.data):
            self.called += 1
            self.index = 0
            raise StopIteration
        val = self.data[self.index]
        self.index += 1
        if not self.max_calls or self.called <= self.max_calls:
            return val
        return None
    def next(self):
        return self.__next__()
