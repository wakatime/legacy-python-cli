# -*- coding: utf-8 -*-

import logging
import os
import sys
import tempfile

from wakatime.compat import u
from wakatime.packages.requests.models import Response


try:
    import mock
    from mock import ANY
except ImportError:
    import unittest.mock as mock
    from unittest.mock import ANY
try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    # Python >= 2.7
    import unittest
try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json


class TestCase(unittest.TestCase):
    patch_these = []

    def setUp(self):
        # disable logging while testing
        logging.disable(logging.CRITICAL)

        self.maxDiff = 1000

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

    def assertListsEqual(self, first_list, second_list, message=None):
        if isinstance(first_list, list) and isinstance(second_list, list):
            if message:
                self.assertEquals(self.normalize_list(first_list), self.normalize_list(second_list), message)
            else:
                self.assertEquals(self.normalize_list(first_list), self.normalize_list(second_list))
        else:
            if message:
                self.assertEquals(first_list, second_list, message)
            else:
                self.assertEquals(first_list, second_list)

    def assertHeartbeatNotSent(self):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_not_called()

    def assertHeartbeatSent(self, heartbeat=None, extra_heartbeats=[], headers=None, cert=None, proxies={}, stream=False, timeout=60, verify=True):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
            ANY, cert=cert, proxies=proxies, stream=stream, timeout=timeout, verify=verify,
        )

        body = json.loads(self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].body)
        self.assertIsInstance(body, list)

        if headers:
            actual_headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
            for key, val in headers.items():
                self.assertEquals(actual_headers.get(key), val, u('Expected api request to have header {0}={1}, instead {0}={2}').format(u(key), u(actual_headers.get(key)), u(val)))

        if heartbeat:
            keys = list(body[0].keys()) + list(heartbeat.keys())
            for key in keys:
                if isinstance(heartbeat.get(key), list):
                    self.assertListsEqual(heartbeat.get(key), body[0].get(key), u('Expected heartbeat to be sent with {0}={1}, instead {0}={2}').format(u(key), u(heartbeat.get(key)), u(body[0].get(key))))
                else:
                    self.assertEquals(heartbeat.get(key), body[0].get(key), u('Expected heartbeat to be sent with {1} {0}={2}, instead {3} {0}={4}').format(u(key), type(heartbeat.get(key)).__name__, u(heartbeat.get(key)), type(body[0].get(key)).__name__, u(body[0].get(key))))

        if extra_heartbeats:
            for i in range(len(extra_heartbeats)):
                keys = list(body[i + 1].keys()) + list(extra_heartbeats[i].keys())
                for key in keys:
                    if isinstance(extra_heartbeats[i].get(key), list):
                        self.assertListsEqual(extra_heartbeats[i].get(key), body[i + 1].get(key), u('Expected extra heartbeat {3} to be sent with {0}={1}, instead {0}={2}').format(u(key), u(extra_heartbeats[i].get(key)), u(body[i + 1].get(key)), i))
                    else:
                        self.assertEquals(extra_heartbeats[i].get(key), body[i + 1].get(key), u('Expected extra heartbeat {5} to be sent with {1} {0}={2}, instead {3} {0}={4}').format(u(key), type(extra_heartbeats[i].get(key)).__name__, u(extra_heartbeats[i].get(key)), type(body[i + 1].get(key)).__name__, u(body[i + 1].get(key)), i))

    def assertSessionCacheUntouched(self):
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

    def assertSessionCacheDeleted(self):
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

    def assertSessionCacheSaved(self):
        self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)
        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()

    def assertHeartbeatSavedOffline(self):
        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY)
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def assertHeartbeatNotSavedOffline(self):
        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()

    def assertOfflineHeartbeatsSynced(self):
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_called()

    def assertOfflineHeartbeatsNotSynced(self):
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def assertNothingPrinted(self):
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

    def getPrintedOutput(self):
        return sys.stdout.getvalue() or '' + sys.stderr.getvalue() or ''

    def assertNothingLogged(self, logs):
        self.assertEquals(self.getLogOutput(logs), '')

    def getLogOutput(self, logs):
        return u("\n").join([u(' ').join(x) for x in logs.actual()])

    def resetMocks(self):
        for key in self.patched:
            self.patched[key].reset_mock()

    @property
    def isPy35OrNewer(self):
        if sys.version_info[0] > 3:
            return True
        return (sys.version_info[0] >= 3 and sys.version_info[1] >= 5)

    @property
    def isPy33OrNewer(self):
        if sys.version_info[0] > 3:
            return True
        return (sys.version_info[0] >= 3 and sys.version_info[1] >= 3)


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


class CustomResponse(Response):
    response_code = 201
    response_text = '{"responses": [[null,201]]}'
    limit = 0
    second_response_code = 0
    second_response_text = None

    _count = 0

    @property
    def status_code(self):
        if self.limit and self._count > self.limit:
            return self.second_response_code
        self._count += 1
        return self.response_code

    @status_code.setter
    def status_code(self, value):
        pass

    @property
    def text(self):
        if self.limit and self._count > self.limit:
            return self.second_response_text if self.second_response_text is not None else self.response_text
        self._count += 1
        return self.response_text
