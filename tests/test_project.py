# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests
from wakatime.packages.requests.models import Response

import logging
import os
import platform
import shutil
import tempfile
import time
from testfixtures import log_capture
from wakatime.compat import u, open
from wakatime.constants import API_ERROR, SUCCESS
from wakatime.exceptions import NotYetImplemented
from wakatime.projects.base import BaseProject
from wakatime.projects.git import Git
from .utils import ANY, DynamicIterable, TestCase, TemporaryDirectory, CustomResponse, mock, json


class ProjectTestCase(TestCase):
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

    def shared(self, expected_project='', expected_branch=ANY, entity='', config='good_config.cfg', extra_args=[]):
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        config = os.path.join('tests/samples/configs', config)
        if not os.path.exists(entity):
            entity = os.path.realpath(os.path.join('tests/samples', entity))

        now = u(int(time.time()))
        args = ['--file', entity, '--config', config, '--time', now] + extra_args

        retval = execute(args)
        self.assertEquals(retval, SUCCESS)
        self.assertNothingPrinted()

        heartbeat = {
            'language': ANY,
            'lines': ANY,
            'entity': os.path.realpath(entity),
            'project': expected_project,
            'branch': expected_branch,
            'dependencies': ANY,
            'time': float(now),
            'type': 'file',
            'is_write': False,
            'user_agent': ANY,
        }
        self.assertHeartbeatSent(heartbeat)

        self.assertHeartbeatNotSavedOffline()
        self.assertOfflineHeartbeatsSynced()
        self.assertSessionCacheSaved()

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

        calls = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args_list

        body = calls[0][0][0].body
        data = json.loads(body)[0]
        self.assertEquals(None, data.get('project'))

        body = calls[1][0][0].body
        data = json.loads(body)[0]
        self.assertEquals('alt-project', data['project'])

    def test_wakatime_project_file(self):
        self.shared(
            expected_project='waka-project-file',
            entity='projects/wakatime_project_file/emptyfile.txt',
        )

    def test_git_project_detected(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        self.shared(
            expected_project='git',
            expected_branch='master',
            entity=os.path.join(tempdir, 'git', 'emptyfile.txt'),
        )

    @log_capture()
    def test_ioerror_when_reading_git_branch(self, logs):
        logging.disable(logging.NOTSET)

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        entity = os.path.join(tempdir, 'git', 'emptyfile.txt')

        with mock.patch('wakatime.projects.git.open') as mock_open:
            mock_open.side_effect = IOError('')

            self.shared(
                expected_project='git',
                expected_branch='master',
                entity=entity,
            )

        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        expected = 'OSError' if self.isPy33OrNewer else 'IOError'
        self.assertIn(expected, actual)

    def test_git_detached_head_not_used_as_branch(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-detached-head', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        entity = os.path.join(tempdir, 'git', 'emptyfile.txt')

        self.shared(
            expected_project='git',
            expected_branch=None,
            entity=entity,
        )

    def test_svn_project_detected(self):
        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with mock.patch('wakatime.projects.subversion.Subversion._has_xcode_tools') as mock_has_xcode:
                mock_has_xcode.return_value = True

                with mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_popen:
                    stdout = open('tests/samples/output/svn').read()
                    stderr = ''
                    mock_popen.return_value = DynamicIterable((stdout, stderr), max_calls=1)

                    expected = None if platform.system() == 'Windows' else 'svn'
                    self.shared(
                        expected_project=expected,
                        entity='projects/svn/afolder/emptyfile.txt',
                    )

    @log_capture()
    def test_svn_exception_handled(self, logs):
        logging.disable(logging.NOTSET)

        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with mock.patch('wakatime.projects.subversion.Subversion._has_xcode_tools') as mock_has_xcode:
                mock_has_xcode.return_value = True

                with mock.patch('wakatime.projects.subversion.Popen') as mock_popen:
                    mock_popen.side_effect = OSError('')

                    with mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_communicate:
                        mock_communicate.side_effect = OSError('')

                        self.shared(
                            expected_project=None,
                            entity='projects/svn/afolder/emptyfile.txt',
                        )

                        self.assertNothingPrinted()
                        self.assertNothingLogged(logs)

    def test_svn_on_mac_without_xcode_tools_installed(self):
        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with mock.patch('wakatime.projects.subversion.platform.system') as mock_system:
                mock_system.return_value = 'Darwin'

                with mock.patch('wakatime.projects.subversion.Popen.communicate') as mock_popen:
                    stdout = open('tests/samples/output/svn').read()
                    stderr = ''
                    mock_popen.return_value = DynamicIterable((stdout, stderr), raise_on_calls=[OSError('')])

                    self.shared(
                        expected_project=None,
                        entity='projects/svn/afolder/emptyfile.txt',
                    )

    def test_svn_on_mac_with_xcode_tools_installed(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/projects/svn/afolder/emptyfile.txt'
        config = 'tests/samples/configs/good_config.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            with mock.patch('wakatime.projects.subversion.platform.system') as mock_system:
                mock_system.return_value = 'Darwin'

                with mock.patch('wakatime.projects.subversion.Popen') as mock_popen:
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

        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            now = u(int(time.time()))
            entity = 'tests/samples/projects/hg/emptyfile.txt'
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            execute(args)

            self.assertEquals('hg', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
            self.assertEquals('test-hg-branch', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['branch'])

    @log_capture()
    def test_ioerror_when_reading_mercurial_branch(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with mock.patch('wakatime.projects.git.Git.process') as mock_git:
            mock_git.return_value = False

            now = u(int(time.time()))
            entity = 'tests/samples/projects/hg/emptyfile.txt'
            config = 'tests/samples/configs/good_config.cfg'

            args = ['--file', entity, '--config', config, '--time', now]

            with mock.patch('wakatime.projects.mercurial.open') as mock_open:
                mock_open.side_effect = IOError('')
                execute(args)

            self.assertEquals('hg', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
            self.assertEquals('default', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['branch'])

            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'OSError' if self.isPy33OrNewer else 'IOError'
            self.assertIn(expected, actual)

    def test_git_submodule_detected(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='asubmodule',
            expected_branch='asubbranch',
            entity=entity,
        )

    def test_git_submodule_detected_and_enabled_globally(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='asubmodule',
            expected_branch='asubbranch',
            entity=entity,
            config='git-submodules-enabled.cfg',
        )

    def test_git_submodule_detected_but_disabled_globally(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='git',
            expected_branch='master',
            entity=entity,
            config='git-submodules-disabled.cfg',
        )

    def test_git_submodule_detected_and_disabled_using_regex(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='git',
            expected_branch='master',
            entity=entity,
            config='git-submodules-disabled-using-regex.cfg',
        )

    def test_git_submodule_detected_and_enabled_using_regex(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='asubmodule',
            expected_branch='asubbranch',
            entity=entity,
            config='git-submodules-enabled-using-regex.cfg',
        )

    @log_capture()
    def test_git_submodule_detected_with_invalid_regex(self, logs):
        logging.disable(logging.NOTSET)

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        entity = os.path.join(tempdir, 'git', 'asubmodule', 'emptyfile.txt')

        self.shared(
            expected_project='git',
            expected_branch='master',
            entity=entity,
            config='git-submodules-invalid-regex.cfg',
        )

        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        expected = u('WakaTime WARNING Regex error (unbalanced parenthesis) for disable git submodules pattern: \\(invalid regex)')
        if self.isPy35OrNewer:
            expected = 'WakaTime WARNING Regex error (unbalanced parenthesis at position 15) for disable git submodules pattern: \\(invalid regex)'
        self.assertEquals(expected, actual)

    def test_git_worktree_detected(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-worktree', os.path.join(tempdir, 'git-wt'))
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git-wt', 'dot_git'), os.path.join(tempdir, 'git-wt', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        entity = os.path.join(tempdir, 'git-wt', 'emptyfile.txt')

        self.shared(
            expected_project='git',
            expected_branch='worktree-detection-branch',
            entity=entity,
        )

    def test_git_worktree_not_detected_when_commondir_missing(self):
        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-worktree', os.path.join(tempdir, 'git-wt'))
        shutil.copytree('tests/samples/projects/git', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git-wt', 'dot_git'), os.path.join(tempdir, 'git-wt', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))

        os.remove(os.path.join(tempdir, 'git', '.git', 'worktrees', 'git-worktree', 'commondir'))

        entity = os.path.join(tempdir, 'git-wt', 'emptyfile.txt')

        self.shared(
            expected_project=None,
            expected_branch='worktree-detection-branch',
            entity=entity,
        )

    @log_capture()
    def test_git_path_from_gitdir_link_file(self, logs):
        logging.disable(logging.NOTSET)

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        path = os.path.join(tempdir, 'git', 'asubmodule')

        git = Git(None)
        result = git._path_from_gitdir_link_file(path)

        expected = os.path.realpath(os.path.join(tempdir, 'git', '.git', 'modules', 'asubmodule'))
        self.assertEquals(expected, result)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_git_path_from_gitdir_link_file_handles_exceptions(self, logs):
        logging.disable(logging.NOTSET)

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'dot_git'), os.path.join(tempdir, 'git', '.git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        self.orig_open = open
        self.count = 0

        with mock.patch('wakatime.projects.git.open') as mock_open:

            def side_effect_function(*args, **kwargs):
                self.count += 1
                if self.count <= 1:
                    raise IOError('')
                return self.orig_open(*args, **kwargs)

            mock_open.side_effect = side_effect_function

            git = Git(None)
            path = os.path.join(tempdir, 'git', 'asubmodule')
            result = git._path_from_gitdir_link_file(path)

            expected = os.path.realpath(os.path.join(tempdir, 'git', '.git', 'modules', 'asubmodule'))
            self.assertEquals(expected, result)
            self.assertNothingPrinted()
            self.assertNothingLogged(logs)

        with mock.patch('wakatime.projects.git.open') as mock_open:
            mock_open.side_effect = UnicodeDecodeError('utf8', ''.encode('utf8'), 0, 0, '')

            git = Git(None)
            path = os.path.join(tempdir, 'git', 'asubmodule')
            result = git._path_from_gitdir_link_file(path)

            self.assertIsNone(result)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'UnicodeDecodeError'
            self.assertIn(expected, actual)

        with mock.patch('wakatime.projects.git.open') as mock_open:
            mock_open.side_effect = IOError('')

            git = Git(None)
            path = os.path.join(tempdir, 'git', 'asubmodule')
            result = git._path_from_gitdir_link_file(path)

            self.assertIsNone(result)
            self.assertNothingPrinted()
            actual = self.getLogOutput(logs)
            expected = 'OSError' if self.isPy33OrNewer else 'IOError'
            self.assertIn(expected, actual)

    @log_capture()
    def test_git_path_from_gitdir_link_file_handles_invalid_link(self, logs):
        logging.disable(logging.NOTSET)

        tempdir = tempfile.mkdtemp()
        shutil.copytree('tests/samples/projects/git-with-submodule', os.path.join(tempdir, 'git'))
        shutil.move(os.path.join(tempdir, 'git', 'asubmodule', 'dot_git'), os.path.join(tempdir, 'git', 'asubmodule', '.git'))

        path = os.path.join(tempdir, 'git', 'asubmodule')

        git = Git(None)
        result = git._path_from_gitdir_link_file(path)

        expected = None
        self.assertEquals(expected, result)
        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

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

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

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

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_project_map_with_invalid_regex(self, logs):
        logging.disable(logging.NOTSET)
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = CustomResponse()

        now = u(int(time.time()))
        entity = 'tests/samples/projects/project_map42/emptyfile.txt'
        config = 'tests/samples/configs/project_map_invalid.cfg'

        args = ['--file', entity, '--config', config, '--time', now]
        retval = execute(args)
        self.assertEquals(retval, SUCCESS)

        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        expected = u('WakaTime WARNING Regex error (unexpected end of regular expression) for projectmap pattern: invalid[({regex')
        if self.isPy35OrNewer:
            expected = u('WakaTime WARNING Regex error (unterminated character set at position 7) for projectmap pattern: invalid[({regex')
        self.assertEquals(expected, actual)

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
        self.assertNothingPrinted()
        actual = self.getLogOutput(logs)
        expected = u('WakaTime WARNING Regex error (tuple index out of range) for projectmap pattern: proj-map{3}')
        self.assertEquals(expected, actual)

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

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

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

        self.assertNothingPrinted()
        self.assertNothingLogged(logs)

    @log_capture()
    def test_exclude_unknown_project_when_project_detected(self, logs):
        logging.disable(logging.NOTSET)

        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with TemporaryDirectory() as tempdir:
            entity = 'tests/samples/codefiles/emptyfile.txt'
            shutil.copy(entity, os.path.join(tempdir, 'emptyfile.txt'))
            entity = os.path.realpath(os.path.join(tempdir, 'emptyfile.txt'))
            config = 'tests/samples/configs/exclude_unknown_project.cfg'

            args = ['--file', entity, '--project', 'proj-arg', '--config', config, '--log-file', '~/.wakatime.log']
            execute(args)

            self.assertNothingPrinted()
            self.assertNothingLogged(logs)
            self.assertEquals('proj-arg', self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['project'])
