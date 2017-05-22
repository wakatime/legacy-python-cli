# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests
from wakatime.packages.requests.models import Response

import logging
import os
import platform
import shutil
import sys
import tempfile
import time
from testfixtures import log_capture
from wakatime.compat import u
from wakatime.constants import API_ERROR
from wakatime.exceptions import NotYetImplemented
from wakatime.projects.base import BaseProject
from . import utils


class ProjectTestCase(utils.TestCase):
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

    def test_project_base(self):
        path = 'tests/samples/codefiles/see.h'
        project = BaseProject(path)

        with self.assertRaises(NotYetImplemented):
            project.process()

        with self.assertRaises(NotYetImplemented):
            project.name()

        with self.assertRaises(NotYetImplemented):
            project.branch()

    def test_project_argument_overrides_detected_project(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/git/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--project', 'forced-project', '--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('forced-project', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_alternate_project_argument_does_not_override_detected_project(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/git/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'
        project = os.path.basename(os.path.abspath('.'))

        args = ['--alternate-project', 'alt-project', '--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals(project, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_alternate_project_argument_does_not_override_project_argument(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/git/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--project', 'forced-project', '--alternate-project', 'alt-project', '--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('forced-project', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_alternate_project_argument_used_when_project_not_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        tempdir = tempfile.mkdtemp()
        entity = 'tests/samples/projects/git/emptyfile.txt'
        shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))

        now = u(int(time.time()))
        entity = os.path.join(tempdir, 'emptyfile.txt')
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]
        execute(args)

        args = ['--file', entity, '--config', config, '--time', now, '--alternate-project', 'alt-project']
        execute(args)

        calls = self.patched['wakatime.offlinequeue.Queue.push'].call_args_list
        self.assertEquals(None, calls[0][0][0].get('project'))
        self.assertEquals('alt-project', calls[1][0][0]['project'])

    def test_wakatime_project_file(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/wakatime_project_file/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('waka-project-file', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_git_project_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        now = u(int(time.time()))
        entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('git', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
        self.assertEquals('master', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['branch'])

    def test_ioerror_when_reading_git_branch(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        now = u(int(time.time()))
        entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.projects.git.open') as mock_open:
            mock_open.side_effect = IOError('')
            execute(args)

        self.assertEquals('git', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
        self.assertEquals('master', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('branch'))

    def test_git_detached_head_not_used_as_branch(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-detached-head', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        now = u(int(time.time()))
        entity = os.path.join(tempdir, 'git', 'emptyfile.txt')
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('git', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
        self.assertNotIn('branch', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0])

    def test_svn_project_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with utils.mock.patch('wakatime.projects.subversion.Subversion._has_xcode_tools') as mock_has_xcode:
                mock_has_xcode.return_value = True

                with utils.mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_popen:
                    stdout = open('tests/samples/output/svn').read()
                    stderr = ''
                    mock_popen.return_value = utils.DynamicIterable((stdout, stderr), max_calls=1)

                    execute(args)

        expected = None if platform.system() == 'Windows' else 'svn'
        self.assertEquals(expected, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0].get('project'))

    def test_svn_exception_handled(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            now = u(int(time.time()))
            entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            with utils.mock.patch('wakatime.projects.subversion.Subversion._has_xcode_tools') as mock_has_xcode:
                mock_has_xcode.return_value = True

                with utils.mock.patch('wakatime.projects.subversion.Popen') as mock_popen:
                    mock_popen.side_effect = OSError('')

                    with utils.mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_communicate:
                        mock_communicate.side_effect = OSError('')

                        execute(args)

            self.assertNotIn('project', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0])

    def test_svn_on_mac_without_xcode_tools_installed(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with utils.mock.patch('wakatime.projects.subversion.platform.system') as mock_system:
                mock_system.return_value = 'Darwin'

                with utils.mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_popen:
                    stdout = open('tests/samples/output/svn').read()
                    stderr = ''
                    mock_popen.return_value = utils.DynamicIterable((stdout, stderr), raise_on_calls=[OSError('')])

                    execute(args)

            self.assertNotIn('project', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0])

    def test_svn_on_mac_with_xcode_tools_installed(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with utils.mock.patch('wakatime.projects.subversion.platform.system') as mock_system:
                mock_system.return_value = 'Darwin'

                with utils.mock.patch('wakatime.projects.subversion.Popen') as mock_popen:
                    stdout = open('tests/samples/output/svn').read()
                    stderr = ''
                    class Dynamic(object):
                        def __init__(self):
                            self.called = 0
                        def communicate(self):
                            self.called += 1
                            if self.called == 2:
                                return (stdout, stderr)
                        def wait(self):
                            if self.called == 1:
                                return 0
                    mock_popen.return_value = Dynamic()

                    execute(args)

        self.assertEquals('svn', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_mercurial_project_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            now = u(int(time.time()))
            entity = 'tests/samples/projects/hg/emptyfile.txt'
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            execute(args)

            self.assertEquals('hg', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
            self.assertEquals('test-hg-branch', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['branch'])

    def test_ioerror_when_reading_mercurial_branch(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            now = u(int(time.time()))
            entity = 'tests/samples/projects/hg/emptyfile.txt'
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            with utils.mock.patch('wakatime.projects.mercurial.open') as mock_open:
                mock_open.side_effect = IOError('')
                execute(args)

            self.assertEquals('hg', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
            self.assertEquals('default', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['branch'])

    @log_capture()
    def test_project_map(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map/emptyfile.txt'
        config = 'tests/samples/configs/project_map.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = "\n".join([u(' ').join(x) for x in logs.actual()])
        expected = u('')
        self.assertEquals(log_output, expected)

    @log_capture()
    def test_project_map_group_usage(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map42/emptyfile.txt'
        config = 'tests/samples/configs/project_map.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map42', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = "\n".join([u(' ').join(x) for x in logs.actual()])
        expected = u('')
        self.assertEquals(log_output, expected)

    @log_capture()
    def test_project_map_with_invalid_regex(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map42/emptyfile.txt'
        config = 'tests/samples/configs/project_map_invalid.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        output = [u(' ').join(x) for x in logs.actual()]
        expected = u('WakaTime WARNING Regex error (unexpected end of regular expression) for projectmap pattern: invalid[({regex')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unterminated character set at position 7) for projectmap pattern: invalid[({regex')
        self.assertEquals(output[0], expected)

    @log_capture()
    def test_project_map_with_replacement_group_index_error(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map42/emptyfile.txt'
        config = 'tests/samples/configs/project_map_malformed.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)

        self.assertEquals(retval, API_ERROR)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = "\n".join([u(' ').join(x) for x in logs.actual()])
        expected = u('WakaTime WARNING Regex error (tuple index out of range) for projectmap pattern: proj-map{3}')
        self.assertEquals(log_output, expected)

    @log_capture()
    def test_project_map_allows_duplicate_keys(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map/emptyfile.txt'
        config = 'tests/samples/configs/project_map_with_duplicate_keys.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map-duplicate-5', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = "\n".join([u(' ').join(x) for x in logs.actual()])
        expected = u('')
        self.assertEquals(log_output, expected)

    @log_capture()
    def test_project_map_allows_colon_in_key(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map/emptyfile.txt'
        config = 'tests/samples/configs/project_map_with_colon_in_key.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map-match', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        log_output = "\n".join([u(' ').join(x) for x in logs.actual()])
        expected = u('')
        self.assertEquals(log_output, expected)
