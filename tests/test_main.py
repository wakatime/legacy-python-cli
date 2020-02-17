# -*- coding: utf-8 -*-


from wakatime.main import execute
import requests

import os
import time
import shutil
import uuid
from wakatime.compat import u
from wakatime.constants import (
    API_ERROR,
    AUTH_ERROR,
    MAX_FILE_SIZE_SUPPORTED,
    SUCCESS,
)
import tzlocal
from requests.exceptions import RequestException
from requests.models import Response
from . import utils
from .utils import ANY, CustomResponse


class MainTestCase(utils.TestCase):
    patch_these = [
        'time.sleep',
        'requests.adapters.HTTPAdapter.send',
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
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'entity': 'HIDDEN.txt',
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
            }

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()
            self.assertHeartbeatSent(heartbeat)
            self.assertHeartbeatSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_400_response(self):
        response = Response()
        response.status_code = 400
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'entity': 'HIDDEN.txt',
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
            }

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()
            self.assertHeartbeatSent(heartbeat)
            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_401_response(self):
        response = Response()
        response.status_code = 401
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': None,
                'entity': 'HIDDEN.txt',
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
            }

            args = ['--file', entity, '--key', key,
                    '--config', 'tests/samples/configs/paranoid.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, AUTH_ERROR)
            self.assertNothingPrinted()
            self.assertHeartbeatSent(heartbeat)
            self.assertHeartbeatSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_500_response_without_offline_logging(self):
        response = Response()
        response.status_code = 500
        response._content = 'fake content'.encode('utf8')
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': 2,
                'entity': entity,
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
                'dependencies': [],
            }

            args = ['--file', entity, '--key', key, '--disable-offline',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()

            log_output = self.getLogOutput()
            expected = "'response_code': 500"
            assert expected in log_output
            expected = "'response_content': 'fake content'"
            assert expected in log_output

            self.assertHeartbeatSent(heartbeat)
            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_requests_exception(self):
        self.patched['requests.adapters.HTTPAdapter.send'].side_effect = RequestException('requests exception')

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': 2,
                'entity': entity,
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
                'dependencies': [],
            }

            args = ['--file', entity, '--key', key, '--verbose',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()

            actual = self.getLogOutput()
            expected = 'Parsing dependencies not supported for special.TextParser'
            assert expected in actual
            expected = 'Sending heartbeats to api at https://api.wakatime.com/api/v1/users/current/heartbeats.bulk'
            assert expected in actual
            expected = "RequestException': 'requests exception'"
            assert expected in actual

            self.assertHeartbeatSent(heartbeat)
            self.assertHeartbeatSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_requests_exception_without_offline_logging(self):
        self.patched['requests.adapters.HTTPAdapter.send'].side_effect = RequestException('requests exception')

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/twolinefile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'twolinefile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'twolinefile.txt'))
            now = u(int(time.time()))
            key = str(uuid.uuid4())

            args = ['--file', entity, '--key', key, '--disable-offline',
                    '--config', 'tests/samples/configs/good_config.cfg', '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()

            expected = "{'RequestException': 'requests exception'}"
            assert expected in self.getLogOutput()

            self.assertHeartbeatSent()
            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_invalid_api_key(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        config = 'tests/samples/configs/missing_api_key.cfg'
        args = ['--config', config, '--key', 'invalid-api-key']

        retval = execute(args)
        assert retval == AUTH_ERROR

        captured = self._capsys.readouterr()

        assert captured.out == ''
        expected = 'error: Invalid api key. Find your api key from wakatime.com/settings/api-key.'
        assert expected in captured.err

        self.assertNothingLogged()

        self.assertHeartbeatNotSent()
        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsNotSynced()
        self.assertSessionCacheUntouched()

    def test_nonascii_hostname(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            hostname = 'test汉语'
            with utils.mock.patch('socket.gethostname') as mock_gethostname:
                mock_gethostname.return_value = hostname
                self.assertEquals(type(hostname).__name__, 'str')

                config = 'tests/samples/configs/good_config.cfg'
                args = ['--file', entity, '--config', config]
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()

                headers = {
                    'X-Machine-Name': hostname.encode('utf-8'),
                }
                self.assertHeartbeatSent(headers=headers)
                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    def test_nonascii_timezone(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            class TZ(object):
                @property
                def zone(self):
                    return 'tz汉语'
            timezone = TZ()

            with utils.mock.patch('tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.return_value = timezone

                config = 'tests/samples/configs/has_everything.cfg'
                timeout = 15
                args = ['--file', entity, '--config', config, '--timeout', u(timeout)]
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()

                headers = {
                    'TimeZone': u(timezone.zone).encode('utf-8'),
                }
                self.assertHeartbeatSent(headers=headers, proxies=ANY, timeout=timeout)
                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    def test_timezone_with_invalid_encoding(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            class TZ(object):
                @property
                def zone(self):
                    return bytes('\xab', 'utf-16')
            timezone = TZ()

            with self.assertRaises(UnicodeDecodeError):
                timezone.zone.decode('utf8')

            with utils.mock.patch('tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.return_value = timezone

                timeout = 15
                config = 'tests/samples/configs/has_everything.cfg'
                args = ['--file', entity, '--config', config, '--timeout', u(timeout)]
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()

                headers = {
                    'TimeZone': u(bytes('\xab', 'utf-16')).encode('utf-8'),
                }
                self.assertHeartbeatSent(headers=headers, proxies=ANY, timeout=timeout)
                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    def test_tzlocal_exception(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            with utils.mock.patch('tzlocal.get_localzone') as mock_getlocalzone:
                mock_getlocalzone.side_effect = Exception('tzlocal exception')

                timeout = 15
                config = 'tests/samples/configs/has_everything.cfg'
                args = ['--file', entity, '--config', config, '--timeout', u(timeout)]
                retval = execute(args)
                self.assertEquals(retval, SUCCESS)
                self.assertNothingPrinted()

                headers = {
                    'TimeZone': None,
                }
                self.assertHeartbeatSent(headers=headers, proxies=ANY, timeout=timeout)
                self.assertHeartbeatNotSavedOffline()
                self.assertOfflineHeartbeatsSynced()
                self.assertSessionCacheSaved()

    def test_timezone_header(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))

            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config]
            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()

            timezone = tzlocal.get_localzone()
            headers = {
                'TimeZone': u(timezone.zone).encode('utf-8'),
            }
            self.assertHeartbeatSent(headers=headers)
            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_nonascii_filename(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        with utils.TemporaryDirectory() as tempdir:
            filename = list(filter(lambda x: x.endswith('.txt'), os.listdir(u('tests/samples/codefiles/unicode'))))[0]
            entity = os.path.join('tests/samples/codefiles/unicode', filename)
            shutil.copy(entity, os.path.join(tempdir, filename))
            entity = os.path.realpath(os.path.join(tempdir, filename))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
                'dependencies': [],
            }

            args = ['--file', entity, '--key', key, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, SUCCESS)
            self.assertNothingPrinted()
            self.assertNothingLogged()

            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsSynced()
            self.assertSessionCacheSaved()

    def test_nonascii_filename_saved_when_offline(self):
        response = Response()
        response.status_code = 500
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            filename = list(filter(lambda x: x.endswith('.txt'), os.listdir(u('tests/samples/codefiles/unicode'))))[0]
            entity = os.path.join('tests/samples/codefiles/unicode', filename)
            shutil.copy(entity, os.path.join(tempdir, filename))
            entity = os.path.realpath(os.path.join(tempdir, filename))
            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())
            heartbeat = {
                'language': 'Text only',
                'lines': 0,
                'entity': os.path.realpath(entity),
                'project': None,
                'time': float(now),
                'type': 'file',
                'is_write': False,
                'user_agent': ANY,
                'dependencies': [],
            }

            args = ['--file', entity, '--key', key, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()
            self.assertNothingLogged()

            self.assertHeartbeatSent(heartbeat)

            self.assertHeartbeatSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheDeleted()

    def test_unhandled_exception(self):
        with utils.mock.patch('wakatime.main.send_heartbeats') as mock_send:
            ex_msg = 'testing unhandled exception'
            mock_send.side_effect = RuntimeError(ex_msg)

            entity = 'tests/samples/codefiles/twolinefile.txt'
            config = 'tests/samples/configs/good_config.cfg'
            key = str(uuid.uuid4())

            args = ['--entity', entity, '--key', key, '--config', config]

            execute(args)

            captured = self._capsys.readouterr()

            assert ex_msg in captured.out
            assert captured.err == ''
            assert ex_msg in self.getLogOutput()

            self.assertHeartbeatNotSent()

            self.assertHeartbeatNotSavedOffline()
            self.assertOfflineHeartbeatsNotSynced()
            self.assertSessionCacheUntouched()

    def test_large_file_skips_lines_count(self):
        response = Response()
        response.status_code = 0
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        now = u(int(time.time()))
        heartbeat = {
            'language': 'Text only',
            'lines': None,
            'entity': os.path.realpath(entity),
            'project': os.path.basename(os.path.abspath('.')),
            'cursorpos': None,
            'lineno': None,
            'branch': ANY,
            'time': float(now),
            'type': 'file',
            'is_write': False,
            'user_agent': ANY,
            'dependencies': [],
        }

        args = ['--entity', entity, '--config', config, '--time', now]

        with utils.mock.patch('os.path.getsize') as mock_getsize:
            mock_getsize.return_value = MAX_FILE_SIZE_SUPPORTED + 1

            retval = execute(args)
            self.assertEquals(retval, API_ERROR)
            self.assertNothingPrinted()

        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatSavedOffline()
        self.assertOfflineHeartbeatsNotSynced()
        self.assertSessionCacheDeleted()
