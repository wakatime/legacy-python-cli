# -*- coding: utf-8 -*-
"""
    wakatime.main
    ~~~~~~~~~~~~~

    wakatime module entry point.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function

import base64
import logging
import os
import platform
import re
import sys
import time
import traceback
import socket
try:
    import ConfigParser as configparser
except ImportError:  # pragma: nocover
    import configparser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packages'))

from .__about__ import __version__
from .compat import u, open, is_py3
from .constants import SUCCESS, API_ERROR, CONFIG_FILE_PARSE_ERROR
from .logger import setup_logging
from .offlinequeue import Queue
from .packages import argparse
from .packages import requests
from .packages.requests.exceptions import RequestException
from .project import get_project_info
from .session_cache import SessionCache
from .stats import get_file_stats
try:
    from .packages import simplejson as json  # pragma: nocover
except (ImportError, SyntaxError):  # pragma: nocover
    import json
try:
    from .packages import tzlocal
except:  # pragma: nocover
    from .packages import tzlocal3 as tzlocal


log = logging.getLogger('WakaTime')


class FileAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            if os.path.isfile(values):
                values = os.path.realpath(values)
        except:  # pragma: nocover
            pass
        setattr(namespace, self.dest, values)


def parseConfigFile(configFile=None):
    """Returns a configparser.SafeConfigParser instance with configs
    read from the config file. Default location of the config file is
    at ~/.wakatime.cfg.
    """

    if not configFile:
        configFile = os.path.join(os.path.expanduser('~'), '.wakatime.cfg')

    configs = configparser.SafeConfigParser()
    try:
        with open(configFile, 'r', encoding='utf-8') as fh:
            try:
                configs.readfp(fh)
            except configparser.Error:
                print(traceback.format_exc())
                return None
    except IOError:
        print(u('Error: Could not read from config file {0}').format(u(configFile)))
    return configs


def parseArguments():
    """Parse command line arguments and configs from ~/.wakatime.cfg.
    Command line arguments take precedence over config file settings.
    Returns instances of ArgumentParser and SafeConfigParser.
    """

    # define supported command line arguments
    parser = argparse.ArgumentParser(
            description='Common interface for the WakaTime api.')
    parser.add_argument('--entity', dest='entity', metavar='FILE',
            action=FileAction,
            help='absolute path to file for the heartbeat; can also be a '+
                 'url, domain, or app when --entitytype is not file')
    parser.add_argument('--file', dest='file', action=FileAction,
            help=argparse.SUPPRESS)
    parser.add_argument('--key', dest='key',
            help='your wakatime api key; uses api_key from '+
                '~/.wakatime.conf by default')
    parser.add_argument('--write', dest='isWrite',
            action='store_true',
            help='when set, tells api this heartbeat was triggered from '+
                 'writing to a file')
    parser.add_argument('--plugin', dest='plugin',
            help='optional text editor plugin name and version '+
                 'for User-Agent header')
    parser.add_argument('--time', dest='timestamp', metavar='time',
            type=float,
            help='optional floating-point unix epoch timestamp; '+
                 'uses current time by default')
    parser.add_argument('--lineno', dest='lineno',
            help='optional line number; current line being edited')
    parser.add_argument('--cursorpos', dest='cursorpos',
            help='optional cursor position in the current file')
    parser.add_argument('--entitytype', dest='entity_type',
            help='entity type for this heartbeat. can be one of "file", '+
                 '"url", "domain", or "app"; defaults to file.')
    parser.add_argument('--proxy', dest='proxy',
                        help='optional https proxy url; for example: '+
                        'https://user:pass@localhost:8080')
    parser.add_argument('--project', dest='project',
            help='optional project name')
    parser.add_argument('--alternate-project', dest='alternate_project',
            help='optional alternate project name; auto-discovered project takes priority')
    parser.add_argument('--hostname', dest='hostname', help='hostname of current machine.')
    parser.add_argument('--disableoffline', dest='offline',
            action='store_false',
            help='disables offline time logging instead of queuing logged time')
    parser.add_argument('--hidefilenames', dest='hidefilenames',
            action='store_true',
            help='obfuscate file names; will not send file names to api')
    parser.add_argument('--exclude', dest='exclude', action='append',
            help='filename patterns to exclude from logging; POSIX regex '+
                 'syntax; can be used more than once')
    parser.add_argument('--include', dest='include', action='append',
            help='filename patterns to log; when used in combination with '+
                 '--exclude, files matching include will still be logged; '+
                 'POSIX regex syntax; can be used more than once')
    parser.add_argument('--ignore', dest='ignore', action='append',
            help=argparse.SUPPRESS)
    parser.add_argument('--logfile', dest='logfile',
            help='defaults to ~/.wakatime.log')
    parser.add_argument('--apiurl', dest='api_url',
            help='heartbeats api url; for debugging with a local server')
    parser.add_argument('--timeout', dest='timeout', type=int,
            help='number of seconds to wait when sending heartbeats to api')
    parser.add_argument('--config', dest='config',
            help='defaults to ~/.wakatime.conf')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
            help='turns on debug messages in log file')
    parser.add_argument('--version', action='version', version=__version__)

    # parse command line arguments
    args = parser.parse_args()

    # use current unix epoch timestamp by default
    if not args.timestamp:
        args.timestamp = time.time()

    # parse ~/.wakatime.cfg file
    configs = parseConfigFile(args.config)
    if configs is None:
        return args, configs

    # update args from configs
    if not args.key:
        default_key = None
        if configs.has_option('settings', 'api_key'):
            default_key = configs.get('settings', 'api_key')
        elif configs.has_option('settings', 'apikey'):
            default_key = configs.get('settings', 'apikey')
        if default_key:
            args.key = default_key
        else:
            parser.error('Missing api key')
    if not args.entity_type:
        args.entity_type = 'file'
    if not args.entity:
        if args.file:
            args.entity = args.file
        else:
            parser.error('argument --entity is required')
    if not args.exclude:
        args.exclude = []
    if configs.has_option('settings', 'ignore'):
        try:
            for pattern in configs.get('settings', 'ignore').split("\n"):
                if pattern.strip() != '':
                    args.exclude.append(pattern)
        except TypeError:  # pragma: nocover
            pass
    if configs.has_option('settings', 'exclude'):
        try:
            for pattern in configs.get('settings', 'exclude').split("\n"):
                if pattern.strip() != '':
                    args.exclude.append(pattern)
        except TypeError:  # pragma: nocover
            pass
    if not args.include:
        args.include = []
    if configs.has_option('settings', 'include'):
        try:
            for pattern in configs.get('settings', 'include').split("\n"):
                if pattern.strip() != '':
                    args.include.append(pattern)
        except TypeError:  # pragma: nocover
            pass
    if args.offline and configs.has_option('settings', 'offline'):
        args.offline = configs.getboolean('settings', 'offline')
    if not args.hidefilenames and configs.has_option('settings', 'hidefilenames'):
        args.hidefilenames = configs.getboolean('settings', 'hidefilenames')
    if not args.proxy and configs.has_option('settings', 'proxy'):
        args.proxy = configs.get('settings', 'proxy')
    if not args.verbose and configs.has_option('settings', 'verbose'):
        args.verbose = configs.getboolean('settings', 'verbose')
    if not args.verbose and configs.has_option('settings', 'debug'):
        args.verbose = configs.getboolean('settings', 'debug')
    if not args.logfile and configs.has_option('settings', 'logfile'):
        args.logfile = configs.get('settings', 'logfile')
    if not args.api_url and configs.has_option('settings', 'api_url'):
        args.api_url = configs.get('settings', 'api_url')
    if not args.timeout and configs.has_option('settings', 'timeout'):
        try:
            args.timeout = int(configs.get('settings', 'timeout'))
        except ValueError:
            print(traceback.format_exc())

    return args, configs


def should_exclude(entity, include, exclude):
    if entity is not None and entity.strip() != '':
        try:
            for pattern in include:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    if compiled.search(entity):
                        return False
                except re.error as ex:
                    log.warning(u('Regex error ({msg}) for include pattern: {pattern}').format(
                        msg=u(ex),
                        pattern=u(pattern),
                    ))
        except TypeError:  # pragma: nocover
            pass
        try:
            for pattern in exclude:
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    if compiled.search(entity):
                        return pattern
                except re.error as ex:
                    log.warning(u('Regex error ({msg}) for exclude pattern: {pattern}').format(
                        msg=u(ex),
                        pattern=u(pattern),
                    ))
        except TypeError:  # pragma: nocover
            pass
    return False


def get_user_agent(plugin):
    ver = sys.version_info
    python_version = '%d.%d.%d.%s.%d' % (ver[0], ver[1], ver[2], ver[3], ver[4])
    user_agent = u('wakatime/{ver} ({platform}) Python{py_ver}').format(
        ver=u(__version__),
        platform=u(platform.platform()),
        py_ver=python_version,
    )
    if plugin:
        user_agent = u('{user_agent} {plugin}').format(
            user_agent=user_agent,
            plugin=u(plugin),
        )
    else:
        user_agent = u('{user_agent} Unknown/0').format(
            user_agent=user_agent,
        )
    return user_agent


def send_heartbeat(project=None, branch=None, hostname=None, stats={}, key=None, entity=None,
        timestamp=None, isWrite=None, plugin=None, offline=None, entity_type='file',
        hidefilenames=None, proxy=None, api_url=None, timeout=None, **kwargs):
    """Sends heartbeat as POST request to WakaTime api server.
    """

    if not api_url:
        api_url = 'https://api.wakatime.com/api/v1/heartbeats'
    if not timeout:
        timeout = 30
    log.debug('Sending heartbeat to api at %s' % api_url)
    data = {
        'time': timestamp,
        'entity': entity,
        'type': entity_type,
    }
    if hidefilenames and entity is not None and entity_type == 'file':
        extension = u(os.path.splitext(data['entity'])[1])
        data['entity'] = u('HIDDEN{0}').format(extension)
    if stats.get('lines'):
        data['lines'] = stats['lines']
    if stats.get('language'):
        data['language'] = stats['language']
    if stats.get('dependencies'):
        data['dependencies'] = stats['dependencies']
    if stats.get('lineno'):
        data['lineno'] = stats['lineno']
    if stats.get('cursorpos'):
        data['cursorpos'] = stats['cursorpos']
    if isWrite:
        data['is_write'] = isWrite
    if project:
        data['project'] = project
    if branch:
        data['branch'] = branch
    log.debug(data)

    # setup api request
    request_body = json.dumps(data)
    api_key = u(base64.b64encode(str.encode(key) if is_py3 else key))
    auth = u('Basic {api_key}').format(api_key=api_key)
    headers = {
        'User-Agent': get_user_agent(plugin),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': auth,
    }
    if hostname:
        headers['X-Machine-Name'] = hostname
    proxies = {}
    if proxy:
        proxies['https'] = proxy

    # add Olson timezone to request
    try:
        tz = tzlocal.get_localzone()
    except:
        tz = None
    if tz:
        headers['TimeZone'] = u(tz.zone)

    session_cache = SessionCache()
    session = session_cache.get()

    # log time to api
    response = None
    try:
        response = session.post(api_url, data=request_body, headers=headers,
                                 proxies=proxies, timeout=timeout)
    except RequestException:
        exception_data = {
            sys.exc_info()[0].__name__: u(sys.exc_info()[1]),
        }
        if log.isEnabledFor(logging.DEBUG):
            exception_data['traceback'] = traceback.format_exc()
        if offline:
            queue = Queue()
            queue.push(data, json.dumps(stats), plugin)
            if log.isEnabledFor(logging.DEBUG):
                log.warn(exception_data)
        else:
            log.error(exception_data)
    else:
        response_code = response.status_code if response is not None else None
        response_content = response.text if response is not None else None
        if response_code == requests.codes.created or response_code == requests.codes.accepted:
            log.debug({
                'response_code': response_code,
            })
            session_cache.save(session)
            return True
        if offline:
            if response_code != 400:
                queue = Queue()
                queue.push(data, json.dumps(stats), plugin)
                if response_code == 401:
                    log.error({
                        'response_code': response_code,
                        'response_content': response_content,
                    })
                elif log.isEnabledFor(logging.DEBUG):
                    log.warn({
                        'response_code': response_code,
                        'response_content': response_content,
                    })
            else:
                log.error({
                    'response_code': response_code,
                    'response_content': response_content,
                })
        else:
            log.error({
                'response_code': response_code,
                'response_content': response_content,
            })
    session_cache.delete()
    return False


def execute(argv=None):
    if argv:
        sys.argv = ['wakatime'] + argv

    args, configs = parseArguments()
    if configs is None:
        return CONFIG_FILE_PARSE_ERROR

    setup_logging(args, __version__)

    try:
        exclude = should_exclude(args.entity, args.include, args.exclude)
        if exclude is not False:
            log.debug(u('Skipping because matches exclude pattern: {pattern}').format(
                pattern=u(exclude),
            ))
            return SUCCESS

        if args.entity_type != 'file' or os.path.isfile(args.entity):

            stats = get_file_stats(args.entity,
                                   entity_type=args.entity_type,
                                   lineno=args.lineno,
                                   cursorpos=args.cursorpos)

            project = args.project or args.alternate_project
            branch = None
            if args.entity_type == 'file':
                project, branch = get_project_info(configs, args)

            kwargs = vars(args)
            kwargs['project'] = project
            kwargs['branch'] = branch
            kwargs['stats'] = stats
            kwargs['hostname'] = args.hostname or socket.gethostname()
            kwargs['timeout'] = args.timeout

            if send_heartbeat(**kwargs):
                queue = Queue()
                while True:
                    heartbeat = queue.pop()
                    if heartbeat is None:
                        break
                    sent = send_heartbeat(
                        project=heartbeat['project'],
                        entity=heartbeat['entity'],
                        timestamp=heartbeat['time'],
                        branch=heartbeat['branch'],
                        hostname=kwargs['hostname'],
                        stats=json.loads(heartbeat['stats']),
                        key=args.key,
                        isWrite=heartbeat['is_write'],
                        plugin=heartbeat['plugin'],
                        offline=args.offline,
                        hidefilenames=args.hidefilenames,
                        entity_type=heartbeat['type'],
                        proxy=args.proxy,
                        api_url=args.api_url,
                        timeout=args.timeout,
                    )
                    if not sent:
                        break
                return SUCCESS

            return API_ERROR

        else:
            log.debug('File does not exist; ignoring this heartbeat.')
            return SUCCESS
    except:
        log.traceback()
