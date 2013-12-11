# -*- coding: utf-8 -*-
"""
    wakatime.projects.projectmap
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Information from ~/.waka-projectmap mapping folders (relative to home folder)
    to project names

    :author: 3onyc
    :license: BSD, see LICENSE for more details.
"""

import logging
import os

from ..packages import simplejson as json

from .base import BaseProject


log = logging.getLogger(__name__)


class ProjectMap(BaseProject):
    def process(self):
        if self.settings:
            return True

        return False

    def branch(self):
        return None

    def name(self):
        for path in self._path_generator():
            if self.settings.has_option('projectmap', path):
                return self.settings.get('projectmap', path)

        return None

    def _path_generator(self):
        path = self.path.replace(os.environ['HOME'], '')
        while path != os.path.dirname(path):
            yield path
            path = os.path.dirname(path)
