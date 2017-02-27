# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import logging
import os
import time
import shutil
import sys
from testfixtures import log_capture
from wakatime.compat import u
from wakatime.exceptions import NotYetImplemented
from wakatime.dependencies import DependencyParser, TokenParser
from wakatime.packages.pygments.lexers import ClassNotFound, PythonLexer
from wakatime.packages.requests.models import Response
from wakatime.stats import get_lexer_by_name
from . import utils

try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json
try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY


class DependenciesTestCase(utils.TestCase):
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

    def test_token_parser(self):
        with self.assertRaises(NotYetImplemented):
            source_file = 'tests/samples/codefiles/c_only/non_empty.h'
            parser = TokenParser(source_file)
            parser.parse()

        with utils.mock.patch('wakatime.dependencies.TokenParser._extract_tokens') as mock_extract_tokens:
            source_file = 'tests/samples/codefiles/see.h'
            parser = TokenParser(source_file)
            parser.tokens
            mock_extract_tokens.assert_called_once_with()

        parser = TokenParser(None)
        parser.append('one.two.three', truncate=True, truncate_to=1)
        parser.append('one.two.three', truncate=True, truncate_to=2)
        parser.append('one.two.three', truncate=True, truncate_to=3)
        parser.append('one.two.three', truncate=True, truncate_to=4)

        expected = [
            'one',
            'one.two',
            'one.two.three',
            'one.two.three',
        ]
        self.assertEquals(parser.dependencies, expected)

    @log_capture()
    def test_dependency_parser(self, logs):
        logging.disable(logging.NOTSET)

        lexer = PythonLexer
        lexer.__class__.__name__ = 'FooClass'
        parser = DependencyParser(None, lexer)

        dependencies = parser.parse()

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        self.assertEquals(log_output, '')

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        expected = []
        self.assertEquals(dependencies, expected)

    @log_capture()
    def test_missing_dependency_parser_in_debug_mode(self, logs):
        logging.disable(logging.NOTSET)

        # turn on debug mode
        log = logging.getLogger('WakaTime')
        log.setLevel(logging.DEBUG)

        lexer = PythonLexer
        lexer.__class__.__name__ = 'FooClass'
        parser = DependencyParser(None, lexer)

        # parse dependencies
        dependencies = parser.parse()

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = 'WakaTime DEBUG Parsing dependencies not supported for python.FooClass'
        self.assertEquals(log_output, expected)

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        expected = []
        self.assertEquals(dependencies, expected)

    @log_capture()
    def test_missing_dependency_parser_importerror_in_debug_mode(self, logs):
        logging.disable(logging.NOTSET)

        # turn on debug mode
        log = logging.getLogger('WakaTime')
        log.setLevel(logging.DEBUG)

        with utils.mock.patch('wakatime.dependencies.import_module') as mock_import:
            mock_import.side_effect = ImportError('foo')

            lexer = PythonLexer
            lexer.__class__.__name__ = 'FooClass'
            parser = DependencyParser(None, lexer)

            # parse dependencies
            dependencies = parser.parse()

        log_output = u("\n").join([u(' ').join(x) for x in logs.actual()])
        expected = 'WakaTime DEBUG Parsing dependencies not supported for python.FooClass'
        self.assertEquals(log_output, expected)

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        expected = []
        self.assertEquals(dependencies, expected)

    def test_io_error_suppressed_when_parsing_dependencies(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            with utils.mock.patch('wakatime.dependencies.open') as mock_open:
                mock_open.side_effect = IOError('')
                retval = execute(args)

            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('Python'),
                'lines': 37,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): [],
                u('language'): u('Python'),
                u('lineno'): None,
                u('lines'): 37,
            }
            expected_dependencies = []

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('dependencies', [])
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_classnotfound_error_raised_when_passing_none_to_pygments(self):
        with self.assertRaises(ClassNotFound):
            get_lexer_by_name(None)

    def test_classnotfound_error_suppressed_when_parsing_dependencies(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            with utils.mock.patch('wakatime.stats.guess_lexer_using_filename') as mock_guess:
                mock_guess.return_value = (None, None)

                with utils.mock.patch('wakatime.stats.get_filetype_from_buffer') as mock_filetype:
                    mock_filetype.return_value = 'foo'
                    retval = execute(args)

            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': None,
                'lines': 37,
                'dependencies': [],
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('language'): None,
                u('lineno'): None,
                u('lines'): 37,
                u('dependencies'): [],
            }

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_python_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('Python'),
                'lines': 37,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('Python'),
                u('lineno'): None,
                u('lines'): 37,
            }
            expected_dependencies = [
                'app',
                'django',
                'flask',
                'jinja',
                'mock',
                'pygments',
                'simplejson',
                'sqlalchemy',
                'unittest',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_bower_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/bower.json'
            shutil.copy(entity, os.path.join(tempdir, 'bower.json'))
            entity = os.path.realpath(os.path.join(tempdir, 'bower.json'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')
            self.assertEquals(retval, 102)

            heartbeat = {
                'language': u('JSON'),
                'lines': 11,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('JSON'),
                u('lineno'): None,
                u('lines'): 11,
            }
            expected_dependencies = ['animate.css', 'moment', 'moment-timezone']

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            for dep in expected_dependencies:
                self.assertIn(dep, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies'])
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_grunt_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/Gruntfile'
            shutil.copy(entity, os.path.join(tempdir, 'Gruntfile'))
            entity = os.path.realpath(os.path.join(tempdir, 'Gruntfile'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')
            self.assertEquals(retval, 102)

            heartbeat = {
                'language': None,
                'lines': 23,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): None,
                u('lineno'): None,
                u('lines'): 23,
            }
            expected_dependencies = ['grunt']

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            for dep in expected_dependencies:
                self.assertIn(dep, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies'])
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_java_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/java.java'
            shutil.copy(entity, os.path.join(tempdir, 'java.java'))
            entity = os.path.realpath(os.path.join(tempdir, 'java.java'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('Java'),
                'lines': 20,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('Java'),
                u('lineno'): None,
                u('lines'): 20,
            }
            expected_dependencies = [
                'colorfulwolf.webcamapplet',
                'foobar',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_c_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/c_only/non_empty.c'
            shutil.copy(entity, os.path.join(tempdir, 'see.c'))
            entity = os.path.realpath(os.path.join(tempdir, 'see.c'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('C'),
                'lines': 8,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('C'),
                u('lineno'): None,
                u('lines'): 8,
            }
            expected_dependencies = [
                'openssl',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_cpp_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/c_and_cpp/non_empty.cpp'
            shutil.copy(entity, os.path.join(tempdir, 'non_empty.cpp'))
            entity = os.path.realpath(os.path.join(tempdir, 'non_empty.cpp'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('C++'),
                'lines': 8,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('C++'),
                u('lineno'): None,
                u('lines'): 8,
            }
            expected_dependencies = [
                'openssl',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_csharp_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/csharp/seesharp.cs'
            shutil.copy(entity, os.path.join(tempdir, 'seesharp.cs'))
            entity = os.path.realpath(os.path.join(tempdir, 'seesharp.cs'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('C#'),
                'lines': 18,
                'entity': os.path.realpath(entity),
                'dependencies': ANY,
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('C#'),
                u('lineno'): None,
                u('lines'): 18,
            }
            expected_dependencies = [
                'Proper',
                'Fart',
                'Math',
                'WakaTime',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_php_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/php.php'
            shutil.copy(entity, os.path.join(tempdir, 'php.php'))
            entity = os.path.realpath(os.path.join(tempdir, 'php.php'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('PHP'),
                'lines': ANY,
                'entity': os.path.realpath(entity),
                'dependencies': ANY,
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('PHP'),
                u('lineno'): None,
                u('lines'): ANY,
            }
            expected_dependencies = [
                'Interop',
                'FooBarOne',
                'FooBarTwo',
                'FooBarThree',
                'FooBarFour',
                'FooBarSeven',
                'FooBarEight',
                'ArrayObject',
                "'ServiceLocator.php'",
                "'ServiceLocatorTwo.php'",
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_php_in_html_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/html-with-php.html'
            shutil.copy(entity, os.path.join(tempdir, 'html-with-php.html'))
            entity = os.path.realpath(os.path.join(tempdir, 'html-with-php.html'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('HTML+PHP'),
                'lines': ANY,
                'dependencies': ANY,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('HTML+PHP'),
                u('lineno'): None,
                u('lines'): ANY,
            }
            expected_dependencies = [
                '"https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_html_django_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/html-django.html'
            shutil.copy(entity, os.path.join(tempdir, 'html-django.html'))
            entity = os.path.realpath(os.path.join(tempdir, 'html-django.html'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('HTML+Django/Jinja'),
                'lines': ANY,
                'dependencies': ANY,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('HTML+Django/Jinja'),
                u('lineno'): None,
                u('lines'): ANY,
            }
            expected_dependencies = [
                '"libs/json2.js"',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_go_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/go.go'
            shutil.copy(entity, os.path.join(tempdir, 'go.go'))
            entity = os.path.realpath(os.path.join(tempdir, 'go.go'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            retval = execute(args)
            self.assertEquals(retval, 102)
            self.assertEquals(sys.stdout.getvalue(), '')
            self.assertEquals(sys.stderr.getvalue(), '')

            self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
            self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

            heartbeat = {
                'language': u('Go'),
                'lines': 24,
                'entity': os.path.realpath(entity),
                'project': u(os.path.basename(os.path.realpath('.'))),
                'dependencies': ANY,
                'time': float(now),
                'type': 'file',
            }
            stats = {
                u('cursorpos'): None,
                u('dependencies'): ANY,
                u('language'): u('Go'),
                u('lineno'): None,
                u('lines'): 24,
            }
            expected_dependencies = [
                '"compress/gzip"',
                '"direct"',
                '"foobar"',
                '"github.com/golang/example/stringutil"',
                '"image/gif"',
                '"log"',
                '"math"',
                '"oldname"',
                '"os"',
                '"supress"',
            ]

            self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
            for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                self.assertEquals(heartbeat[key], val)
            dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
            self.assertListsEqual(dependencies, expected_dependencies)
            self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
            self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_dependencies_still_detected_when_alternate_language_used(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/python.py'
            shutil.copy(entity, os.path.join(tempdir, 'python.py'))
            entity = os.path.realpath(os.path.join(tempdir, 'python.py'))

            now = u(int(time.time()))
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now, '--alternate-language', 'PYTHON']

            with utils.mock.patch('wakatime.stats.smart_guess_lexer') as mock_guess_lexer:
                mock_guess_lexer.return_value = None

                retval = execute(args)

                self.assertEquals(retval, 102)
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

                heartbeat = {
                    'language': u('Python'),
                    'lines': 37,
                    'entity': os.path.realpath(entity),
                    'project': u(os.path.basename(os.path.realpath('.'))),
                    'dependencies': ANY,
                    'time': float(now),
                    'type': 'file',
                }
                stats = {
                    u('cursorpos'): None,
                    u('dependencies'): ANY,
                    u('language'): u('Python'),
                    u('lineno'): None,
                    u('lines'): 37,
                }
                expected_dependencies = [
                    'app',
                    'django',
                    'flask',
                    'jinja',
                    'mock',
                    'pygments',
                    'simplejson',
                    'sqlalchemy',
                    'unittest',
                ]

                self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(ANY, ANY, None)
                for key, val in self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].items():
                    self.assertEquals(heartbeat[key], val)
                dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
                self.assertListsEqual(dependencies, expected_dependencies)
                self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
                self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
