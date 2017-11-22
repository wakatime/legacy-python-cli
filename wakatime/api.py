# -*- coding: utf-8 -*-
"""
    wakatime.api
    ~~~~~~~~~~~~

    :copyright: (c) 2017 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""


from __future__ import print_function

import base64
import logging
import sys
import traceback

from .compat import u, is_py3, json
from .constants import API_ERROR, AUTH_ERROR, SUCCESS, UNKNOWN_ERROR

from .offlinequeue import Queue
from .packages.requests.exceptions import RequestException
from .session_cache import SessionCache
from .utils import get_hostname, get_user_agent
from .packages import tzlocal


log = logging.getLogger('WakaTime')


try:
    from .packages import requests
except ImportError:
    log.traceback(logging.ERROR)
    print(traceback.format_exc())
    log.error('Please upgrade Python to the latest version.')
    print('Please upgrade Python to the latest version.')
    sys.exit(UNKNOWN_ERROR)


def send_heartbeats(heartbeats, args, configs, use_ntlm_proxy=False):
    """Send heartbeats to WakaTime API.

    Returns `SUCCESS` when heartbeat was sent, otherwise returns an error code.
    """

    if len(heartbeats) == 0:
        return SUCCESS

    api_url = args.api_url
    if not api_url:
        api_url = 'https://api.wakatime.com/api/v1/users/current/heartbeats.bulk'
    log.debug('Sending heartbeats to api at %s' % api_url)
    timeout = args.timeout
    if not timeout:
        timeout = 60

    data = [h.sanitize().dict() for h in heartbeats]
    log.debug(data)

    # setup api request
    request_body = json.dumps(data)
    api_key = u(base64.b64encode(str.encode(args.key) if is_py3 else args.key))
    auth = u('Basic {api_key}').format(api_key=api_key)
    headers = {
        'User-Agent': get_user_agent(args.plugin),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': auth,
    }

    hostname = get_hostname(args)
    if hostname:
        headers['X-Machine-Name'] = u(hostname).encode('utf-8')

    # add Olson timezone to request
    try:
        tz = tzlocal.get_localzone()
    except:
        tz = None
    if tz:
        headers['TimeZone'] = u(tz.zone).encode('utf-8')

    session_cache = SessionCache()
    session = session_cache.get()

    should_try_ntlm = False
    proxies = {}
    if args.proxy:
        if use_ntlm_proxy:
            from .packages.requests_ntlm import HttpNtlmAuth
            username = args.proxy.rsplit(':', 1)
            password = ''
            if len(username) == 2:
                password = username[1]
            username = username[0]
            session.auth = HttpNtlmAuth(username, password, session)
        else:
            should_try_ntlm = '\\' in args.proxy
            proxies['https'] = args.proxy

    # send request to api
    response, code = None, None
    try:
        response = session.post(api_url, data=request_body, headers=headers,
                                proxies=proxies, timeout=timeout,
                                verify=not args.nosslverify)
    except RequestException:
        if should_try_ntlm:
            return send_heartbeats(heartbeats, args, configs, use_ntlm_proxy=True)
        else:
            exception_data = {
                sys.exc_info()[0].__name__: u(sys.exc_info()[1]),
            }
            if log.isEnabledFor(logging.DEBUG):
                exception_data['traceback'] = traceback.format_exc()
            if args.offline:
                queue = Queue(args, configs)
                queue.push_many(heartbeats)
                if log.isEnabledFor(logging.DEBUG):
                    log.warn(exception_data)
            else:
                log.error(exception_data)

    except:  # delete cached session when requests raises unknown exception
        if should_try_ntlm:
            return send_heartbeats(heartbeats, args, configs, use_ntlm_proxy=True)
        else:
            exception_data = {
                sys.exc_info()[0].__name__: u(sys.exc_info()[1]),
                'traceback': traceback.format_exc(),
            }
            if args.offline:
                queue = Queue(args, configs)
                queue.push_many(heartbeats)
                log.warn(exception_data)

    else:
        code = response.status_code if response is not None else None
        content = response.text if response is not None else None
        try:
            results = response.json() if response is not None else []
        except:
            if log.isEnabledFor(logging.DEBUG):
                log.traceback(logging.WARNING)
            results = []
        if code == requests.codes.created or code == requests.codes.accepted:
            log.debug({
                'response_code': code,
            })

            for i in range(len(results)):
                if len(heartbeats) <= i:
                    log.debug('Results from server do not match heartbeats sent.')
                    break

                try:
                    c = results[i][1]
                except:
                    c = 0
                try:
                    text = json.dumps(results[i][0])
                except:
                    if log.isEnabledFor(logging.DEBUG):
                        log.traceback(logging.WARNING)
                    text = ''
                handle_result([heartbeats[i]], c, text, args, configs)

            session_cache.save(session)
            return SUCCESS

        if should_try_ntlm:
            return send_heartbeats(heartbeats, args, configs, use_ntlm_proxy=True)
        else:
            handle_result(heartbeats, code, content, args, configs)

    session_cache.delete()
    return AUTH_ERROR if code == 401 else API_ERROR


def handle_result(h, code, content, args, configs):
    if code != requests.codes.created and code != requests.codes.accepted:
        if args.offline:
            if code == 400:
                log.error({
                    'response_code': code,
                    'response_content': content,
                })
            else:
                if log.isEnabledFor(logging.DEBUG):
                    log.warn({
                        'response_code': code,
                        'response_content': content,
                    })
                queue = Queue(args, configs)
                queue.push_many(h)
        else:
            log.error({
                'response_code': code,
                'response_content': content,
            })
