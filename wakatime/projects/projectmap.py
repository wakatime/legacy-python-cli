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
        self.config = self._load_config()
        if self.config:
            log.debug(self.config)
            return True

        return False

    def branch(self):
        return None

    def name(self):
        for path in self._path_generator():
            if path in self.config:
                return self.config[path]

        return None

    def _load_config(self):
        map_path = "%s/.waka-projectmap" % os.environ['HOME']
        if os.path.isfile(map_path):
            with open(map_path) as map_file:
                try:
                    return json.load(map_file)
                except (IOError, json.JSONDecodeError) as e:
                    log.exception("ProjectMap Exception: ")

        return False

    def _path_generator(self):
        path = self.path.replace(os.environ['HOME'], '')
        while path != os.path.dirname(path):
            yield path
            path = os.path.dirname(path)
