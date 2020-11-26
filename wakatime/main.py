# -*- coding: utf-8 -*-
"""
    wakatime.main
    ~~~~~~~~~~~~~

    Module entry point.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


import logging
import sys
import time
import traceback

import simplejson

from .__about__ import __version__
from .api import get_time_today, send_heartbeats
from .arguments import parse_arguments
from .compat import u
from .constants import HEARTBEATS_PER_REQUEST, SUCCESS, UNKNOWN_ERROR
from .heartbeat import Heartbeat
from .logger import setup_logging
from .offlinequeue import Queue


try:
    from urllib3.contrib import pyopenssl

    def noop():
        pass

    pyopenssl.inject_into_urllib3 = noop
except ImportError:
    pass


log = logging.getLogger("WakaTime")


def execute(argv=None):
    if argv:
        sys.argv = ["wakatime"] + argv

    try:
        args, configs = parse_arguments()
    except SystemExit as ex:
        return ex.code

    setup_logging(args, __version__)

    if args.today or args.today_goal:
        text, retval = get_time_today(args)
        if text:
            print(text)
        return retval

    try:
        heartbeats = []

        hb = Heartbeat(vars(args), args, configs)
        if hb:
            heartbeats.append(hb)
        elif args.entity:
            log.debug(hb.skip)

        if args.extra_heartbeats:
            try:
                for extra_data in simplejson.loads(sys.stdin.readline()):
                    hb = Heartbeat(extra_data, args, configs)
                    if hb:
                        heartbeats.append(hb)
                    else:
                        log.debug(hb.skip)
            except simplejson.JSONDecodeError as ex:
                log.warning(
                    u("Malformed extra heartbeats json: {msg}").format(msg=u(ex),)
                )

        retval = SUCCESS
        while heartbeats:
            retval = send_heartbeats(heartbeats[:HEARTBEATS_PER_REQUEST], args, configs)
            heartbeats = heartbeats[HEARTBEATS_PER_REQUEST:]
            if retval != SUCCESS:
                break

        if heartbeats:
            Queue(args, configs).push_many(heartbeats)

        if retval == SUCCESS:
            queue = Queue(args, configs)
            for offline_heartbeats in queue.pop_many(args.sync_offline_activity):
                time.sleep(1)
                retval = send_heartbeats(offline_heartbeats, args, configs)
                if retval != SUCCESS:
                    break

        return retval

    except:
        log.traceback(logging.ERROR)
        print(traceback.format_exc())
        return UNKNOWN_ERROR
