# -*- coding: utf-8 -*-
"""
    wakatime.stats
    ~~~~~~~~~~~~~~

    Stats about files

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

import logging
import os
import sys

from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound


log = logging.getLogger(__name__)


def guess_language(file_name):
    lexer = None
    try:
        with open(file_name) as f:
            lexer = guess_lexer(f.read(512000))
    except (ClassNotFound, IOError):
        pass
    if lexer:
        return str(lexer.name)
    else:
        return None


def number_lines_in_file(file_name):
    lines = 0
    try:
        with open(file_name) as f:
            for line in f:
                lines += 1
    except IOError:
        return None
    return lines


def get_file_stats(file_name):
    stats = {
        'language': guess_language(file_name),
        'lines': number_lines_in_file(file_name),
    }
    return stats
