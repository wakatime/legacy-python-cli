# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.offlinequeue import Queue
from wakatime.packages import requests

import logging
import os
import sqlite3
import sys
import time
from testfixtures import log_capture
from wakatime.compat import u
from wakatime.constants import (
    AUTH_ERROR,
    SUCCESS,
)
from wakatime.packages.requests.models import Response
from . import utils
try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json


class OfflineQueueTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
        ['wakatime.session_cache.SessionCache.connect', None],
    ]

    def test_heartbeat_saved_from_error_response(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])

    def test_heartbeat_discarded_from_400_response(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 400
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(None, saved_heartbeat)

    def test_offline_heartbeat_sent_after_success_response(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                response.status_code = 201
                execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(None, saved_heartbeat)

    def test_all_offline_heartbeats_sent_after_success_response(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                config = 'tests/samples/configs/good_config.cfg'

                now1 = u(int(time.time()))
                entity1 = 'tests/samples/codefiles/emptyfile.txt'
                project1 = 'proj1'

                args = ['--file', entity1, '--config', config, '--time', now1, '--project', project1]
                execute(args)

                now2 = u(int(time.time()))
                entity2 = 'tests/samples/codefiles/twolinefile.txt'
                project2 = 'proj2'

                args = ['--file', entity2, '--config', config, '--time', now2, '--project', project2]
                execute(args)

                # send heartbeats from offline queue after 201 response
                now3 = u(int(time.time()))
                entity3 = 'tests/samples/codefiles/python.py'
                project3 = 'proj3'
                args = ['--file', entity3, '--config', config, '--time', now3, '--project', project3]
                response.status_code = 201
                execute(args)

                # offline queue should be empty
                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(None, saved_heartbeat)

                calls = self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].call_args_list

                body = calls[0][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), os.path.abspath(entity1))
                self.assertEquals(data.get('project'), project1)
                self.assertEquals(u(int(data.get('time'))), now1)

                body = calls[1][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), os.path.abspath(entity2))
                self.assertEquals(data.get('project'), project2)
                self.assertEquals(u(int(data.get('time'))), now2)

                body = calls[2][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), os.path.abspath(entity3))
                self.assertEquals(data.get('project'), project3)
                self.assertEquals(u(int(data.get('time'))), now3)

                body = calls[3][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), os.path.abspath(entity1))
                self.assertEquals(data.get('project'), project1)
                self.assertEquals(u(int(data.get('time'))), now1)

                body = calls[4][0][0].body
                data = json.loads(body)
                self.assertEquals(data.get('entity'), os.path.abspath(entity2))
                self.assertEquals(data.get('project'), project2)
                self.assertEquals(u(int(data.get('time'))), now2)

    def test_auth_error_when_sending_offline_heartbeats(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                config = 'tests/samples/configs/good_config.cfg'

                now1 = u(int(time.time()))
                entity1 = 'tests/samples/codefiles/emptyfile.txt'
                project1 = 'proj1'

                args = ['--file', entity1, '--config', config, '--time', now1, '--project', project1]
                execute(args)

                now2 = u(int(time.time()))
                entity2 = 'tests/samples/codefiles/twolinefile.txt'
                project2 = 'proj2'

                args = ['--file', entity2, '--config', config, '--time', now2, '--project', project2]
                execute(args)

                # send heartbeats from offline queue after 201 response
                now3 = u(int(time.time()))
                entity3 = 'tests/samples/codefiles/python.py'
                project3 = 'proj3'
                args = ['--file', entity3, '--config', config, '--time', now3, '--project', project3]

                class CustomResponse(Response):
                    count = 0
                    @property
                    def status_code(self):
                        if self.count > 2:
                            return 401
                        self.count += 1
                        return 201
                    @status_code.setter
                    def status_code(self, value):
                        pass
                response = CustomResponse()
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                retval = execute(args)
                self.assertEquals(retval, AUTH_ERROR)

                # offline queue should be empty
                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')
                self.assertEquals(os.path.realpath(entity2), saved_heartbeat['entity'])

    def test_500_error_when_sending_offline_heartbeats(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                config = 'tests/samples/configs/good_config.cfg'

                now1 = u(int(time.time()))
                entity1 = 'tests/samples/codefiles/emptyfile.txt'
                project1 = 'proj1'

                args = ['--file', entity1, '--config', config, '--time', now1, '--project', project1]
                execute(args)

                now2 = u(int(time.time()))
                entity2 = 'tests/samples/codefiles/twolinefile.txt'
                project2 = 'proj2'

                args = ['--file', entity2, '--config', config, '--time', now2, '--project', project2]
                execute(args)

                # send heartbeats from offline queue after 201 response
                now3 = u(int(time.time()))
                entity3 = 'tests/samples/codefiles/python.py'
                project3 = 'proj3'
                args = ['--file', entity3, '--config', config, '--time', now3, '--project', project3]

                class CustomResponse(Response):
                    count = 0
                    @property
                    def status_code(self):
                        if self.count > 2:
                            return 500
                        self.count += 1
                        return 201
                    @status_code.setter
                    def status_code(self, value):
                        pass
                response = CustomResponse()
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                retval = execute(args)
                self.assertEquals(retval, SUCCESS)

                # offline queue should be empty
                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')
                self.assertEquals(os.path.realpath(entity2), saved_heartbeat['entity'])

    def test_empty_project_can_be_saved(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/emptyfile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')
                self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])

    def test_get_handles_connection_exception(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                with utils.mock.patch('wakatime.offlinequeue.Queue.connect') as mock_connect:
                    mock_connect.side_effect = sqlite3.Error('')

                    response.status_code = 201
                    execute(args)

                    queue = Queue()
                    saved_heartbeat = queue.pop()
                    self.assertEquals(None, saved_heartbeat)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])

    def test_push_handles_connection_exception(self):
        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                response = Response()
                response.status_code = 500
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                with utils.mock.patch('wakatime.offlinequeue.Queue.connect') as mock_connect:
                    mock_connect.side_effect = sqlite3.Error('')

                    args = ['--file', entity, '--config', config, '--time', now]
                    execute(args)

                    response.status_code = 201
                    execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(None, saved_heartbeat)

    def test_get_db_file(self):
        queue = Queue()
        db_file = queue.get_db_file()
        expected = os.path.join(os.path.expanduser('~'), '.wakatime.db')
        self.assertEquals(db_file, expected)

    @log_capture()
    def test_heartbeat_saved_when_requests_raises_exception(self, logs):
        logging.disable(logging.NOTSET)

        with utils.NamedTemporaryFile() as fh:
            with utils.mock.patch('wakatime.offlinequeue.Queue.get_db_file') as mock_db_file:
                mock_db_file.return_value = fh.name

                exception_msg = u("Oops, requests raised an exception. This is a test.")
                self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].side_effect = AttributeError(exception_msg)

                now = u(int(time.time()))
                entity = 'tests/samples/codefiles/twolinefile.txt'
                config = 'tests/samples/configs/good_config.cfg'

                args = ['--file', entity, '--config', config, '--time', now]
                execute(args)

                queue = Queue()
                saved_heartbeat = queue.pop()
                self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])

                self.assertEquals(sys.stdout.getvalue(), '')
                self.assertEquals(sys.stderr.getvalue(), '')

                output = [u(' ').join(x) for x in logs.actual()]
                self.assertIn(exception_msg, output[0])

                self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
                self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()
