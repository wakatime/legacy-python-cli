# -*- coding: utf-8 -*-
"""
    wakatime
    ~~~~~~~~

    Action event appender for Wakati.Me, auto time tracking for text editors.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function

__title__ = 'wakatime'
__version__ = '0.4.8'
__author__ = 'Alan Hamlett'
__license__ = 'BSD'
__copyright__ = 'Copyright 2013 Alan Hamlett'


import base64
import logging
import os
import platform
import re
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packages'))
from .log import setup_logging
from .project import find_project
from .stats import get_file_stats
from .packages import argparse
from .packages import simplejson as json
from .packages import tzlocal
try:
    from urllib2 import HTTPError, Request, urlopen
except ImportError:
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen


log = logging.getLogger(__name__)


class FileAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        values = os.path.realpath(values)
        setattr(namespace, self.dest, values)


def parseArguments(argv):
    try:
        sys.argv
    except AttributeError:
        sys.argv = argv
    parser = argparse.ArgumentParser(
            description='Wakati.Me event api appender')
    parser.add_argument('--file', dest='targetFile', metavar='file',
            action=FileAction, required=True,
            help='absolute path to file for current action')
    parser.add_argument('--time', dest='timestamp', metavar='time',
            type=float,
            help='optional floating-point unix epoch timestamp; '+
                'uses current time by default')
    parser.add_argument('--write', dest='isWrite',
            action='store_true',
            help='note action was triggered from writing to a file')
    parser.add_argument('--plugin', dest='plugin',
            help='optional text editor plugin name and version '+
                'for User-Agent header')
    parser.add_argument('--key', dest='key',
            help='your wakati.me api key; uses api_key from '+
                '~/.wakatime.conf by default')
    parser.add_argument('--ignore', dest='ignore', action='append',
            help='filename patterns to ignore for reporting')
    parser.add_argument('--logfile', dest='logfile',
            help='defaults to ~/.wakatime.log')
    parser.add_argument('--config', dest='config',
            help='defaults to ~/.wakatime.conf')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
            help='turns on debug messages in log file')
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args(args=argv[1:])
    parse_config(args)
    if not args.timestamp:
        args.timestamp = time.time()
    return args


def parse_config(args):
    if not args.config:
        args.config = os.path.join(os.path.expanduser('~'), '.wakatime.conf')
    try:
        cf = open(args.config)
        for line in cf:
            line = line.split('=', 1)
            line[0] = line[0].strip()
            if line[0] == 'api_key':
                if args.key is None:
                    args.key = line[1].strip()
            elif line[0] == 'logfile':
                if args.logfile is None:
                    args.logfile = line[1].strip()
            elif line[0] == 'verbose':
                args.verbose = True
            elif line[0] == 'ignore':
                if args.ignore is None:
                    args.ignore = []
                args.ignore.append(line[1].strip())
        cf.close()
    except IOError:
        print('Error: Could not read from config file.')


def get_user_agent(plugin):
    ver = sys.version_info
    python_version = '%d.%d.%d.%s.%d' % (ver[0], ver[1], ver[2], ver[3], ver[4])
    user_agent = 'wakatime/%s (%s) Python%s' % (__version__,
        platform.platform(), python_version)
    if plugin:
        user_agent = user_agent+' '+plugin
    return user_agent


def send_action(project=None, branch=None, stats={}, key=None, targetFile=None,
        timestamp=None, isWrite=None, plugin=None, **kwargs):
    url = 'https://www.wakati.me/api/v1/actions'
    log.debug('Sending action to api at %s' % url)
    data = {
        'time': timestamp,
        'file': targetFile,
    }
    if stats.get('lines'):
        data['lines'] = stats['lines']
    if stats.get('language'):
        data['language'] = stats['language']
    if isWrite:
        data['is_write'] = isWrite
    if project:
        data['project'] = project
    if branch:
        data['branch'] = branch
    log.debug(data)

    # setup api request
    request = Request(url=url, data=str.encode(json.dumps(data)))
    request.add_header('User-Agent', get_user_agent(plugin))
    request.add_header('Content-Type', 'application/json')
    auth = 'Basic %s' % bytes.decode(base64.b64encode(str.encode(key)))
    request.add_header('Authorization', auth)

    # add Olson timezone to request
    tz = tzlocal.get_localzone()
    if tz:
        request.add_header('TimeZone', str(tz.zone))

    # log time to api
    response = None
    try:
        response = urlopen(request)
    except HTTPError as exc:
        exception_data = {
            'response_code': exc.getcode(),
            sys.exc_info()[0].__name__: str(sys.exc_info()[1]),
        }
        if log.isEnabledFor(logging.DEBUG):
            exception_data['traceback'] = traceback.format_exc()
        log.error(exception_data)
    except:
        exception_data = {
            sys.exc_info()[0].__name__: str(sys.exc_info()[1]),
        }
        if log.isEnabledFor(logging.DEBUG):
            exception_data['traceback'] = traceback.format_exc()
        log.error(exception_data)
    else:
        if response.getcode() == 201:
            log.debug({
                'response_code': response.getcode(),
            })
            return True
        log.error({
            'response_code': response.getcode(),
            'response_content': response.read(),
        })
    return False


def main(argv=None):
    if not argv:
        argv = sys.argv
    args = parseArguments(argv)
    setup_logging(args, __version__)
    if os.path.isfile(args.targetFile):
        log.debug('Checking file %s against ignores' % args.targetFile)
        for item in args.ignore:
            if re.search(item, args.targetFile):
                log.debug('File matches %s, not reporting' % item)
                return 103

        branch = None
        name = None
        stats = get_file_stats(args.targetFile)
        project = find_project(args.targetFile)
        if project:
            branch = project.branch()
            name = project.name()
        if send_action(
                project=name,
                branch=branch,
                stats=stats,
                **vars(args)
            ):
            return 0
        return 102
    else:
        log.debug('File does not exist; ignoring this action.')
    return 101

