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
from functools import partial

from ..packages import simplejson as json

from .base import BaseProject


log = logging.getLogger(__name__)


class ProjectMap(BaseProject):
    def process(self):
        if not self.settings:
            return False

        self.project = self._find_project()
        return self.project != None

    def _find_project(self):
        has_option = partial(self.settings.has_option, 'projectmap')
        get_option = partial(self.settings.get, 'projectmap')
        paths = self._path_generator()

        projects = map(get_option, filter(has_option, paths))
        return projects[0] if projects else None

    def branch(self):
        return None

    def name(self):
        return self.project

    def _path_generator(self):
        """
        Generates paths from the current directory up to the user's home folder
        stripping anything in the path before the home path
        """

        path = self.path.replace(os.environ['HOME'], '')
        while path != os.path.dirname(path):
            yield path
            path = os.path.dirname(path)
