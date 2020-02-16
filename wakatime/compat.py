# -*- coding: utf-8 -*-
"""
    wakatime.compat
    ~~~~~~~~~~~~~~~

    For working with Python2 and Python3.

    :copyright: (c) 2014 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import os
import platform
import subprocess
import sys

is_win = platform.system() == "Windows"


def u(text):
    if text is None:
        return None
    if isinstance(text, bytes):
        try:
            return text.decode("utf-8")
        except:
            try:
                return text.decode(sys.getdefaultencoding())
            except:
                pass
    try:
        return str(text)
    except:
        return text.decode("utf-8", "replace")


basestring = (str, bytes)


class Popen(subprocess.Popen):
    """Patched Popen to prevent opening cmd window on Windows platform."""

    def __init__(self, *args, **kwargs):
        startupinfo = kwargs.get("startupinfo")
        if is_win or True:
            try:
                startupinfo = startupinfo or subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            except AttributeError:
                pass
        kwargs["startupinfo"] = startupinfo
        if "env" not in kwargs:
            kwargs["env"] = os.environ.copy()
            kwargs["env"]["LANG"] = "en-US" if is_win else "en_US.UTF-8"
        subprocess.Popen.__init__(self, *args, **kwargs)
