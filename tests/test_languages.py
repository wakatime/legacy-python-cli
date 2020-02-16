# -*- coding: utf-8 -*-


from wakatime.main import execute
import requests

import os
import time
from wakatime.compat import u
from wakatime.constants import SUCCESS
from wakatime.stats import guess_lexer
from . import utils
from .utils import ANY, CustomResponse


class LanguagesTestCase(utils.TestCase):
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

    def shared(self, expected_language='', entity='', entity_type='file', extra_args=[]):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        config = 'tests/samples/configs/good_config.cfg'
        if entity_type == 'file':
            entity = os.path.join('tests/samples/codefiles', entity)

        now = u(int(time.time()))
        args = ['--entity', entity, '--config', config, '--time', now] + extra_args

        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()

        heartbeat = {
            'language': expected_language,
            'lines': ANY,
            'entity': os.path.realpath(entity) if entity_type == 'file' else entity,
            'project': ANY,
            'branch': ANY,
            'dependencies': ANY,
            'time': float(now),
            'type': entity_type,
            'is_write': False,
            'user_agent': ANY,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

    def test_c_language_detected_for_header_with_c_files_in_folder(self):
        self.shared(
            expected_language='C',
            entity='c_only/see.h',
        )

    def test_cpp_language_detected_for_header_with_c_and_cpp_files_in_folder(self):
        self.shared(
            expected_language='C++',
            entity='c_and_cpp/cpp.h',
        )

    def test_cpp_language_detected_for_header_with_c_and_cxx_files_in_folder(self):
        self.shared(
            expected_language='C++',
            entity='c_and_cxx/cpp.h',
        )

    def test_c_not_detected_for_non_header_with_c_files_in_folder(self):
        self.shared(
            expected_language='Python',
            entity='c_and_python/see.py',
        )

    def test_objectivec_language_detected_when_header_files_in_folder(self):
        self.shared(
            expected_language='Objective-C',
            entity='c_and_cpp/empty.m',
        )

    def test_objectivec_language_detected_when_m_files_in_folder(self):
        self.shared(
            expected_language='Objective-C',
            entity='c_and_cpp/objective-c.h',
        )

    def test_objectivecpp_language_detected_when_header_files_in_folder(self):
        self.shared(
            expected_language='Objective-C++',
            entity='c_and_cpp/empty.mm',
        )

    def test_objectivecpp_language_detected_when_m_files_in_folder(self):
        self.shared(
            expected_language='Objective-C++',
            entity='c_and_cpp/objective-cpp.h',
        )

    def test_guess_lexer(self):
        source_file = 'tests/samples/codefiles/python.py'
        local_file = None
        lexer = guess_lexer(source_file, local_file)
        language = u(lexer.name) if lexer else None
        self.assertEquals(language, 'Python')

    def test_guess_lexer_from_vim_modeline(self):
        self.shared(
            expected_language='Python',
            entity='python_without_extension',
        )

    def test_guess_lexer_when_entity_not_exist_but_local_file_exists(self):
        source_file = 'tests/samples/codefiles/does_not_exist.py'
        local_file = 'tests/samples/codefiles/python.py'
        self.assertFalse(os.path.exists(source_file))
        lexer = guess_lexer(source_file, local_file)
        language = u(lexer.name) if lexer else None
        self.assertEquals(language, 'Python')

    def test_language_arg_takes_priority_over_detected_language(self):
        self.shared(
            expected_language='Java',
            entity='python.py',
            extra_args=['--language', 'JAVA'],
        )

    def test_language_arg_is_used_when_not_guessed(self):
        with utils.mock.patch('wakatime.stats.guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            self.shared(
                expected_language='Java',
                entity='python.py',
                extra_args=['--language', 'JAVA']
            )

    def test_language_defaults_to_none_for_entity_type_app(self):
        self.shared(
            expected_language=None,
            entity='not-a-file',
            entity_type='domain',
            extra_args=['--entity-type', 'domain'],
        )

    def test_language_arg_used_for_entity_type_app(self):
        self.shared(
            expected_language='Java',
            entity='not-a-file',
            entity_type='app',
            extra_args=['--entity-type', 'app', '--language', 'JAVA'],
        )

    def test_language_arg_used_for_entity_type_domain(self):
        self.shared(
            expected_language='Java',
            entity='not-a-file',
            entity_type='domain',
            extra_args=['--entity-type', 'domain', '--language', 'JAVA'],
        )

    def test_vim_language_arg_is_used_when_not_guessed(self):
        with utils.mock.patch('wakatime.stats.guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            self.shared(
                expected_language='Java',
                entity='python.py',
                extra_args=['--language', 'java', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']
            )

    def test_alternate_language_not_used_when_invalid(self):
        with utils.mock.patch('wakatime.stats.guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            self.shared(
                expected_language=None,
                entity='python.py',
                extra_args=['--language', 'foo', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']
            )

    def test_error_reading_alternate_language_json_map_file(self):
        with utils.mock.patch('wakatime.stats.guess_lexer') as mock_guess_lexer:
            mock_guess_lexer.return_value = None

            with utils.mock.patch('wakatime.stats.open') as mock_open:
                mock_open.side_effect = IOError('')

                self.shared(
                    expected_language=None,
                    entity='python.py',
                    extra_args=['--language', 'foo', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']
                )

    def test_typescript_detected_over_typoscript(self):
        self.shared(
            expected_language='TypeScript',
            entity='empty.ts',
            extra_args=['--language', 'foo', '--plugin', 'NeoVim/703 vim-wakatime/4.0.9']
        )

    def test_perl_detected_over_prolog(self):
        self.shared(
            expected_language='Perl',
            entity='perl.pl',
        )

    def test_fsharp_detected_over_forth(self):
        self.shared(
            expected_language='F#',
            entity='fsharp.fs',
        )

    def test_matlab_detected(self):
        self.shared(
            expected_language='Matlab',
            entity='matlab/matlab.m',
        )

    def test_matlab_detected_over_objectivec_when_mat_file_in_folder(self):
        self.shared(
            expected_language='Matlab',
            entity='matlab/with_mat_files/empty.m',
        )

    def test_objectivec_detected_over_matlab_with_matching_header(self):
        self.shared(
            expected_language='Objective-C',
            entity='matlab/with_mat_files/objective-c.m',
        )

    def test_objectivec_detected_over_matlab_with_non_maching_headers_present(self):
        self.shared(
            expected_language='Objective-C',
            entity='matlab/with_headers/empty.m',
        )

    def test_matlab_detected_over_objectivec_when_header_in_folder(self):
        self.shared(
            expected_language='Matlab',
            entity='matlab/with_headers/matlab.m',
        )

    def test_heartbeat_skipped_when_matlab_same_accuracy(self):
        self.patched['requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        entity = 'matlab/without_headers/empty.m'

        config = 'tests/samples/configs/good_config.cfg'
        entity = os.path.join('tests/samples/codefiles', entity)

        now = u(int(time.time()))
        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()
        self.assertHeartbeatNotSent()
        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheUntouched()

    def test_mjs_javascript_module_extension_detected(self):
        self.shared(
            expected_language='JavaScript',
            entity='javascript_module.mjs',
        )

    def test_go_mod_detected(self):
        self.shared(
            expected_language='Go',
            entity='go.mod',
        )

    def test_coldfusion_detected(self):
        self.shared(
            expected_language='ColdFusion',
            entity='coldfusion.cfm',
        )

    def test_gas_detected_as_assembly(self):
        self.shared(
            expected_language='Assembly',
            entity='gas.s',
        )
