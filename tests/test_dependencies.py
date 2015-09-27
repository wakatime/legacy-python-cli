# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import os
import time
import sys
from wakatime.compat import u
from wakatime.exceptions import NotYetImplemented
from wakatime.dependencies import TokenParser
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


class DependenciesTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_token_parser(self):
        with self.assertRaises(NotYetImplemented):
            source_file = 'tests/samples/codefiles/see.h'
            parser = TokenParser(source_file)
            parser.parse()

        with utils.mock.patch('wakatime.dependencies.TokenParser._extract_tokens') as mock_extract_tokens:
            source_file = 'tests/samples/codefiles/see.h'
            parser = TokenParser(source_file)
            parser.tokens
            mock_extract_tokens.assert_called_once_with()

    def test_python_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
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
            'lines': 36,
            'entity': os.path.realpath(entity),
            'project': u(os.path.basename(os.path.realpath('.'))),
            'dependencies': ANY,
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = {
            u('cursorpos'): None,
            u('dependencies'): ANY,
            u('language'): u('Python'),
            u('lineno'): None,
            u('lines'): 36,
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
            'sys',
            'unittest',
        ]

        def normalize(items):
            return sorted([u(x) for x in items])

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
        self.assertEquals(normalize(dependencies), normalize(expected_dependencies))
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_bower_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/bower.json'
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
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
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

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        for dep in expected_dependencies:
            self.assertIn(dep, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies'])
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_java_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/java.java'
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
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
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
            'googlecode.javacv',
            'colorfulwolf.webcamapplet',
            'foobar',
        ]

        def normalize(items):
            return sorted([u(x) for x in items])

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
        self.assertEquals(normalize(dependencies), normalize(expected_dependencies))
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_c_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/see.c'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        {'project': 'wakatime-cli', 'language': 'C', 'time': 1443295423.0, 'type': 'file', 'lines': 7, 'entity': '/Users/alanhamlett/git/wakatime-cli/tests/samples/codefiles/see.c'}
        {'language': 'C', 'lines': 7, 'entity': '/Users/alanhamlett/git/wakatime-cli/tests/samples/codefiles/see.c', 'project': u'wakatime-cli', 'time': 1443295423.0, 'type': 'file'}

        heartbeat = {
            'language': u('C'),
            'lines': 8,
            'entity': os.path.realpath(entity),
            'project': u(os.path.basename(os.path.realpath('.'))),
            'dependencies': ANY,
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
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

        def normalize(items):
            return sorted([u(x) for x in items])

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
        self.assertEquals(normalize(dependencies), normalize(expected_dependencies))
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_cpp_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/seeplusplus.cpp'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        {'project': 'wakatime-cli', 'language': 'C', 'time': 1443295423.0, 'type': 'file', 'lines': 7, 'entity': '/Users/alanhamlett/git/wakatime-cli/tests/samples/codefiles/see.c'}
        {'language': 'C', 'lines': 7, 'entity': '/Users/alanhamlett/git/wakatime-cli/tests/samples/codefiles/see.c', 'project': u'wakatime-cli', 'time': 1443295423.0, 'type': 'file'}

        heartbeat = {
            'language': u('C++'),
            'lines': 8,
            'entity': os.path.realpath(entity),
            'project': u(os.path.basename(os.path.realpath('.'))),
            'dependencies': ANY,
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
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

        def normalize(items):
            return sorted([u(x) for x in items])

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        dependencies = self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies']
        self.assertEquals(normalize(dependencies), normalize(expected_dependencies))
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()
