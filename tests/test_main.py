# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import logging
import os
import time
import shutil
import sys
import uuid
from testfixtures import log_capture
from wakatime.compat import u, is_py3
from wakatime.constants import (
    API_ERROR,
    AUTH_ERROR,
    MAX_FILE_SIZE_SUPPORTED,
    SUCCESS,
)
from wakatime.packages.requests.exceptions import RequestException
from wakatime.packages.requests.models import Response
from . import utils

try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json
try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY
from wakatime.packages import tzlocal


class MainTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    def test_500_response(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 2,
                'entity': 'HIDDEN.txt',
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 2,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    def test_400_response(self):
        response = Response()
        response.status_code = 400
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    def test_401_response(self):
        response = Response()
        response.status_code = 401
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, AUTH_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 2,
                'entity': 'HIDDEN.txt',
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 2,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    @log_capture()
    def test_500_response_without_offline_logging(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 500
        response._content = 'fake content'
        if is_py3:
            response._content = 'fake content'.encode('utf8')
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--disableoffline',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = "WakaTime ERROR {'response_code': 500, 'response_content': u'fake content'}"
            if log_output[-2] == '0':
                expected = "WakaTime ERROR {'response_content': u'fake content', 'response_code': 500}"
            if is_py3:
                expected = "WakaTime ERROR {'response_code': 500, 'response_content': 'fake content'}"
                if log_output[-2] == '0':
                    expected = "WakaTime ERROR {'response_content': 'fake content', 'response_code': 500}"
            self.assertEquals(expected, log_output)

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    @log_capture()
    def test_requests_exception(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].side_effect = RequestException('requests exception')

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--verbose',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = 'Parsing dependencies not supported for special.TextParser'
            self.assertIn(expected, log_output)
            expected = 'WakaTime DEBUG Sending heartbeat to api at https://api.wakatime.com/api/v1/heartbeats'
            self.assertIn(expected, log_output)
            expected = "RequestException': u'requests exception'"
            if is_py3:
                expected = "RequestException': 'requests exception'"
            self.assertIn(expected, log_output)

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 2,
                'entity': entity,
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 2,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    @log_capture()
    def test_requests_exception_without_offline_logging(self, logs):
        logging.disable(logging.NOTSET)

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].side_effect = RequestException('requests exception')

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--disableoffline',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            expected = "WakaTime ERROR {'RequestException': u'requests exception'}"
            if is_py3:
                expected = "WakaTime ERROR {'RequestException': 'requests exception'}"
            self.assertEquals(expected, log_output)

            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    @log_capture()
    def test_invalid_api_key(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        config = 'tests/samples/configs/missing_api_key.cfg'
        args = ['--config', config, '--key', 'invalid-api-key']

        with self.assertRaises(SystemExit) as e:
            execute(args)

        self.assertEquals(int(str(e.exception)), AUTH_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        expected = 'error: Invalid api key. Find your api key from wakatime.com/settings.'
        self.assertIn(expected, sys.stderr.getvalue())

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = ''
        self.assertEquals(log_output, expected)

        self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_not_called()

    def test_nonascii_hostname(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            hostname = 'test汉语' if is_py3 else 'test\xe6\xb1\x89\xe8\xaf\xad'
            with utils.mock.patch('socket.gethostname') as mock_gethostname:
                mock_gethostname.return_value = hostname
                self.assertEquals(type(hostname).__name__, 'str')

                config = 'tests/samples/configs/good_config.cfg'
                args = ['--file', entity, '--config', config]
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

                headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
                self.assertEquals(headers.get('X-Machine-Name'), hostname.encode('utf-8') if is_py3 else hostname)

    def test_nonascii_timezone(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            class TZ(object):
                @property
                def zone(self):
                    return 'tz汉语' if is_py3 else 'tz\xe6\xb1\x89\xe8\xaf\xad'
            timezone = TZ()

            with utils.mock.patch('wakatime.packages.tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.return_value = timezone

                config = 'tests/samples/configs/has_everything.cfg'
                args = ['--file', entity, '--config', config, '--timeout', '15']
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

                headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
                self.assertEquals(headers.get('TimeZone'), u(timezone.zone).encode('utf-8') if is_py3 else timezone.zone)

    def test_timezone_with_invalid_encoding(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            class TZ(object):
                @property
                def zone(self):
                    return bytes('\xab', 'utf-16') if is_py3 else '\xab'
            timezone = TZ()

            with self.assertRaises(UnicodeDecodeError):
                timezone.zone.decode('utf8')

            with utils.mock.patch('wakatime.packages.tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.return_value = timezone

                config = 'tests/samples/configs/has_everything.cfg'
                args = ['--file', entity, '--config', config, '--timeout', '15']
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

                headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
                expected_tz = u(bytes('\xab', 'utf-16') if is_py3 else '\xab').encode('utf-8')
                self.assertEquals(headers.get('TimeZone'), expected_tz)

    def test_tzlocal_exception(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            with utils.mock.patch('wakatime.packages.tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.side_effect = Exception('tzlocal exception')

                config = 'tests/samples/configs/has_everything.cfg'
                args = ['--file', entity, '--config', config, '--timeout', '15']
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

                self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

                headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
                self.assertEquals(headers.get('TimeZone'), None)

    def test_timezone_header(self):
        response = Response()
        response.status_code = 201
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config]
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            timezone = tzlocal.get_localzone()
            headers = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args[0][0].headers
            self.assertEquals(headers.get('TimeZone'), u(timezone.zone).encode('utf-8') if is_py3 else timezone.zone)

    @log_capture()
    def test_nonascii_filename(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            filename = list(filter(lambda x: x.endswith('.txt'), os.listdir(u('tests/samples/codefiles/unicode'))))[0]
            entity = os.path.join('tests/samples/codefiles/unicode', filename)
            shutil.copy(entity, os.path.join(tempdir, filename))
            entity = os.path.realpath(os.path.join(tempdir, filename))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            self.assertEquals(log_output, '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': os.path.basename(os.path.abspath('.')),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Text only'),
                u('lineno'): None,
                u('lines'): 0,
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
                ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
            )

    @log_capture()
    def test_unhandled_exception(self, logs):
        logging.disable(logging.NOTSET)

        with utils.mock.patch('wakatime.main.process_heartbeat') as mock_process_heartbeat:
            ex_msg = 'testing unhandled exception'
            mock_process_heartbeat.side_effect = RuntimeError(ex_msg)

            entity = 'tests/samples/codefiles/twolinefile.txt'
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--entity', entity, '--key', key, '--config', config]

            execute(args)

            self.assertIn(ex_msg, sys.stdout.getvalue())
            self.assertEquals(sys.stderr.getvalue(), '')

            log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
            self.assertIn(ex_msg, log_output)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()

            self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_not_called()

    def test_large_file_skips_lines_count(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))

        args = ['--entity', entity, '--config', config, '--time', now]

        with utils.mock.patch('os.path.getsize') as mock_getsize:
            mock_getsize.return_value = MAX_FILE_SIZE_SUPPORTED + 1

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)

            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': 'Text only',
            'lines': None,
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'cursorpos': None,
            'lineno': None,
            'branch': 'master',
            'time': float(now),
            'type': 'file',
        }
        stats = {
            u('cursorpos'): None,
            u('dependencies'): [],
            u('language'): u('Text only'),
            u('lineno'): None,
            u('lines'): None,
        }

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
        for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
            self.assertEquals(heartbeat[key], val)
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].assert_called_once_with(
            ANY, cert=None, proxies={}, stream=False, timeout=60, verify=True,
        )
