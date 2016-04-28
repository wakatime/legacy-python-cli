# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests
from wakatime.packages.requests.models import Response

import os
import shutil
import tempfile
import time
from wakatime.compat import u
from wakatime.exceptions import NotYetImplemented
from wakatime.projects.base import BaseProject
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

    def test_svn_project_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with utils.mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_popen:
                stdout = open('tests/samples/output/svn').read()
                stderr = ''
                mock_popen.return_value = (stdout, stderr)

                now = u(int(time.time()))
                entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]

                execute(args)

                self.assertEquals('svn', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_svn_exception_handled(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with utils.mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with utils.mock.patch('wakatime.projects.subversion.Popen') as mock_popen:
                mock_popen.side_effect = OSError('')

                with utils.mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_communicate:
                    mock_communicate.side_effect = OSError('')

                    now = u(int(time.time()))
                    entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
                    config = 'tests/samples/configs/good_config.cfg'

                    args = ['--file', entity, '--config', config, '--time', now]

                    execute(args)

                    self.assertNotIn('project', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0])

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

    def test_project_map(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map/emptyfile.txt'
        config = 'tests/samples/configs/project_map.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])

    def test_project_map_group_usage(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map42/emptyfile.txt'
        config = 'tests/samples/configs/project_map.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        execute(args)

        self.assertEquals('proj-map42', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
