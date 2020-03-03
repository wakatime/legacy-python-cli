# -*- coding: utf-8 -*-
"""
    wakatime.wakatime-cli
    ~~~~~~~~~~~~~~~~~~~~~

    Command-line entry point.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import sys
from wakatime import execute


if __name__ == "__main__":
    sys.exit(execute(sys.argv[1:]))
