# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import time
from wakatime.compat import u
from wakatime.exceptions import NotYetImplemented
from wakatime.languages import TokenParser
from wakatime.packages.requests.models import Response
from . import utils


class LanguagesTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_token_parser(self):
        with utils.mock.patch('wakatime.languages.TokenParser._extract_tokens') as mock_extract_tokens:

            with self.assertRaises(NotYetImplemented):
                source_file = 'tests/samples/codefiles/see.h'
                parser = TokenParser(source_file)
                parser.parse()

            mock_extract_tokens.assert_called_once_with()

    def test_language_detected_for_header_file(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/sample.cfg'
        entity = 'tests/samples/codefiles/see.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)

        entity = 'tests/samples/codefiles/seeplusplus.h'
        args[1] = entity

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C++')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)

    def test_c_language_detected_for_header_with_c_files_in_folder(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/sample.cfg'
        entity = 'tests/samples/codefiles/c_only/see.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)

    def test_cpp_language_detected_for_header_with_c_and_cpp_files_in_folder(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/sample.cfg'
        entity = 'tests/samples/codefiles/c_and_cpp/empty.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C++')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)
