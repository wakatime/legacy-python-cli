# -*- coding: utf-8 -*-


import tempfile
from wakatime.session_cache import SessionCache
from . import utils


class SessionCacheTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
    ]

    def test_can_crud_session(self):
        with tempfile.NamedTemporaryFile() as fh:
            cache = SessionCache()
            cache.DB_FILE = fh.name

            session = cache.get()
            session.headers.update({'x-test': 'abc'})
            cache.save(session)
            session = cache.get()
            self.assertEquals(session.headers.get('x-test'), 'abc')
            cache.delete()
            session = cache.get()
            self.assertEquals(session.headers.get('x-test'), None)

    def test_handles_connection_exception(self):
        with tempfile.NamedTemporaryFile() as fh:
            cache = SessionCache()
            cache.DB_FILE = fh.name

            with utils.mock.patch('wakatime.session_cache.SessionCache.connect') as mock_connect:
                mock_connect.side_effect = OSError('')

                session = cache.get()
                session.headers.update({'x-test': 'abc'})
                cache.save(session)
                session = cache.get()
                self.assertEquals(session.headers.get('x-test'), None)
                cache.delete()
                session = cache.get()
                self.assertEquals(session.headers.get('x-test'), None)
