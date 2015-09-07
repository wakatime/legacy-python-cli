# -*- coding: utf-8 -*-


import os
import django
import simplejson as json
from wakatime import utils
from mypackage.mymodule import myfunction
from . import privatemodule

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
