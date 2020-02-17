# -*- coding: utf-8 -*-


from wakatime.main import execute
import requests

import os
import shutil
from wakatime.constants import API_ERROR, SUCCESS
import certifi
from requests.exceptions import RequestException
from requests.models import Response
from . import utils
from .utils import CustomResponse

try:
    from mock import ANY, call
except ImportError:
    from unittest.mock import ANY, call


class ProxyTestCase(utils.TestCase):
    patch_these = [
        'requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    def test_proxy_without_protocol(self):
        response = CustomResponse()
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'user:pass@localhost:12345'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where())

    def test_https_proxy(self):
        response = CustomResponse()
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'https://user:pass@localhost:12345'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where())

    def test_socks_proxy(self):
        response = CustomResponse()
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'socks5://user:pass@localhost:12345'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == SUCCESS

            self.assertNothingPrinted()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_called_once_with(ANY)

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_called_once_with()

            self.patched['requests.adapters.HTTPAdapter.send'].assert_called_once_with(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where())

    def test_ntlm_proxy_used_after_trying_normal_proxy(self):
        response = Response()
        response.status_code = 400
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'domain\\user:pass'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == API_ERROR

            self.assertNothingPrinted()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_has_calls([call(), call()])
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            expected_calls = [
                call(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where()),
                call(ANY, cert=None, proxies={}, stream=False, timeout=60, verify=certifi.where()),
            ]
            self.patched['requests.adapters.HTTPAdapter.send'].assert_has_calls(expected_calls)

    def test_ntlm_proxy_used_after_normal_proxy_raises_exception(self):
        ex_msg = 'after exception, should still try ntlm proxy'
        self.patched['requests.adapters.HTTPAdapter.send'].side_effect = RuntimeError(ex_msg)

        with utils.TemporaryDirectory() as tempdir:

            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'domain\\user:pass'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == API_ERROR

            self.assertNothingPrinted()

            assert ex_msg in self.getLogOutput()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_has_calls([call(), call()])
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            expected_calls = [
                call(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where()),
                call(ANY, cert=None, proxies={}, stream=False, timeout=60, verify=certifi.where()),
            ]
            self.patched['requests.adapters.HTTPAdapter.send'].assert_has_calls(expected_calls)

    def test_ntlm_proxy_used_after_normal_proxy_raises_requests_exception(self):
        ex_msg = 'after exception, should still try ntlm proxy'
        self.patched['requests.adapters.HTTPAdapter.send'].side_effect = RequestException(ex_msg)

        with utils.TemporaryDirectory() as tempdir:

            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'domain\\user:pass'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == API_ERROR

            self.assertNothingPrinted()
            self.assertNothingLogged()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_has_calls([call(), call()])
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            expected_calls = [
                call(ANY, cert=None, proxies={'https': proxy}, stream=False, timeout=60, verify=certifi.where()),
                call(ANY, cert=None, proxies={}, stream=False, timeout=60, verify=certifi.where()),
            ]
            self.patched['requests.adapters.HTTPAdapter.send'].assert_has_calls(expected_calls)

    def test_invalid_proxy(self):
        response = CustomResponse()
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            proxy = 'invaliddd:proxyarg'
            config = 'tests/samples/configs/good_config.cfg'
            args = ['--file', entity, '--config', config, '--proxy', proxy]

            retval = execute(args)
            assert retval == 2

            captured = self._capsys.readouterr()

            assert captured.out == ''
            expected = 'error: Invalid proxy. Must be in format https://user:pass@host:port or socks5://user:pass@host:port or domain\\user:pass.'
            assert expected in captured.err

            self.assertNothingLogged()

            self.patched['wakatime.session_cache.SessionCache.get'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_not_called()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            self.patched['wakatime.offlinequeue.Queue.push'].assert_not_called()
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

            self.patched['requests.adapters.HTTPAdapter.send'].assert_not_called()
