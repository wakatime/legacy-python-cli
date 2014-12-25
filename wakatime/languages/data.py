# -*- coding: utf-8 -*-
"""
    wakatime.languages.data
    ~~~~~~~~~~~~~~~~~~~~~~~

    Parse dependencies from data files.

    :copyright: (c) 2014 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

import os

from . import TokenParser


FILES = {
    'bower': {'exact': False, 'dependency': 'bower'},
}


class JsonParser(TokenParser):

    def parse(self, tokens=[]):
        self._process_file_name(os.path.basename(self.source_file))
        return self.dependencies

    def _process_file_name(self, file_name):
        for key, value in FILES.items():
            found = (key == file_name) if value.get('exact') else (key in file_name)
            if found:
                self.append(value['dependency'])
