# -*- coding: utf-8 -*-


import os
from wakatime.session_cache import SessionCache
from wakatime.logger import setup_logging
from . import utils


class SessionCacheTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        ['wakatime.offlinequeue.Queue.connect', None],
    ]

    def setUp(self):
        super(SessionCacheTestCase, self).setUp()

        class MockArgs(object):
            timestamp = 0
            is_write = False
            entity = ''
            version = ''
            plugin = ''
            verbose = False
            log_file = ''
        self.args = MockArgs()
        setup_logging(self.args, self.args.version)

    def test_can_crud_session(self):
        with utils.NamedTemporaryFile() as fh:
            cache = SessionCache()

            with utils.mock.patch('wakatime.session_cache.SessionCache._get_db_file') as mock_dbfile:
                mock_dbfile.return_value = fh.name

                session = cache.get()
                session.headers.update({'x-test': 'abc'})
                cache.save(session)
                session = cache.get()
                self.assertEquals(session.headers.get('x-test'), 'abc')
                cache.delete()
                session = cache.get()
                self.assertEquals(session.headers.get('x-test'), None)

    def test_handles_connection_exception(self):
        with utils.NamedTemporaryFile() as fh:
            cache = SessionCache()

            with utils.mock.patch('wakatime.session_cache.SessionCache._get_db_file') as mock_dbfile:
                mock_dbfile.return_value = fh.name

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

    def test_uses_wakatime_home_env_variable(self):
        with utils.TemporaryDirectory() as tempdir:
            expected = os.path.realpath(os.path.join(os.path.expanduser('~'), '.wakatime.db'))

            cache = SessionCache()
            actual = cache._get_db_file()
            self.assertEquals(actual, expected)

            with utils.mock.patch('os.environ.get') as mock_env:
                mock_env.return_value = os.path.realpath(tempdir)

                expected = os.path.realpath(os.path.join(tempdir, '.wakatime.db'))
                actual = cache._get_db_file()
                self.assertEquals(actual, expected)
