# -*- coding: utf-8 -*-


import tempfile
from wakatime.session_cache import SessionCache
from . import utils


class SessionCacheTestCase(utils.TestCase):

    def test_can_connect(self):

        db_file = None
        with tempfile.NamedTemporaryFile() as fh:
            db_file = fh.name

        cache = SessionCache()
        cache.DB_FILE = db_file
        session = cache.get()
        session.headers.update({'x-test': 'abc'})
        cache.save(session)
        cached_session = cache.get()
        self.assertEquals(cached_session.headers.get('x-test'), 'abc')
