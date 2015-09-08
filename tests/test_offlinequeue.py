# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.offlinequeue import Queue
from wakatime.packages import requests

import os
import tempfile
import time
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils


class OfflineQueueTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_heartbeat_saved_from_error_response(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--config', config, '--time', now]
        execute(args)

        queue = Queue()
        saved_heartbeat = queue.pop()
        self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])

    def test_heartbeat_discarded_from_400_response(self):
        response = Response()
        response.status_code = 400
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--config', config, '--time', now]
        execute(args)

        queue = Queue()
        saved_heartbeat = queue.pop()
        self.assertEquals(None, saved_heartbeat)

    def test_offline_heartbeat_sent_after_success_response(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/twolinefile.txt'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--config', config, '--time', now]
        execute(args)

        response.status_code = 201
        execute(args)

        queue = Queue()
        saved_heartbeat = queue.pop()
        self.assertEquals(None, saved_heartbeat)

    def test_empty_project_can_be_saved(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        with tempfile.NamedTemporaryFile() as fh:

            now = u(int(time.time()))
            entity = fh.name
            config = 'tests/samples/sample.cfg'

            args = ['--file', entity, '--config', config, '--time', now]
            execute(args)

            queue = Queue()
            saved_heartbeat = queue.pop()
            self.assertEquals(os.path.realpath(entity), saved_heartbeat['entity'])
