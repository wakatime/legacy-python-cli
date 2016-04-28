# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import time
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from wakatime.stats import guess_language
from . import utils


class LanguagesTestCase(utils.TestCase):
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

    def test_language_detected_for_header_file(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/see.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

        entity = 'tests/samples/codefiles/seeplusplus.h'
        args[1] = entity

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C++')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_c_language_detected_for_header_with_c_files_in_folder(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/c_only/see.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_cpp_language_detected_for_header_with_c_and_cpp_files_in_folder(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/c_and_cpp/empty.h'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C++')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_guess_language(self):
        with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None
            source_file = 'tests/samples/codefiles/python.py'
            result = guess_language(source_file)
            mock_guess_lexer.assert_called_once_with(source_file)
            self.assertEquals(result, (None, None))

    def test_guess_language_from_vim_modeline(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/python_without_extension'
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('Python')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_alternate_language_not_used_when_guessed(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/configs/good_config.cfg'
        entity = 'tests/samples/codefiles/python.py'
        args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'java']

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('Python')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_alternate_language_is_used_when_not_guessed(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            entity = 'tests/samples/codefiles/python.py'
            args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'Java']

            retval = execute(args)
            self.assertEquals(retval, 102)

            language = u('Java')
            self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_vim_alternate_language_is_used_when_not_guessed(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            entity = 'tests/samples/codefiles/python.py'
            args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'java', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']

            retval = execute(args)
            self.assertEquals(retval, 102)

            language = u('Java')
            self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_alternate_language_not_used_when_invalid(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'
            entity = 'tests/samples/codefiles/python.py'
            args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'foo', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']

            retval = execute(args)
            self.assertEquals(retval, 102)

            language = None
            self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)

    def test_error_reading_alternate_language_json_map_file(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            with utils.mock.patch('wakatime.stats.open') as mock_open:
                mock_open.side_effect = IOError('')

                now = u(int(time.time()))
                config = 'tests/samples/configs/good_config.cfg'
                entity = 'tests/samples/codefiles/python.py'
                args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'foo', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']

                retval = execute(args)
                self.assertEquals(retval, 102)

                language = None
                self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('language'), language)
