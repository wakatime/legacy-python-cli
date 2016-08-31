# -*- coding: utf-8 -*-
# vim: set filetype=python

from __future__ import print_statement

import os, sys
import django.forms.monstertruck
from app import *
from flask import session
import simplejson as json
from . import privatemodule
from jinja import tags
from pygments.lexers import BaseLexer
from . import LocalClass
from . import MyClass as MyParser
from ..compat import u
from sqlalchemy import (
    functions as sqlfunctions,
    orm as sqlorm,
)

try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY


class MyClass(object):
    """this class
    """

    def method1(self):
        a = 1 + 2
        b = 'hello world!'
        for x in y:
            print(x)
        raise Exception()
