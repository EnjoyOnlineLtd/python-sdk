# -*- coding: utf-8 -*-
import platform

import requests
from requests.auth import AuthBase

from qiniu import config
from .auth import RequestsAuth
from . import __version__

from tornado.concurrent import TracebackFuture
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest
from tornado import gen
from tornado import stack_context
import urllib
import sys
import json


_sys_info = '{0}; {1}'.format(platform.system(), platform.machine())
_python_ver = platform.python_version()

USER_AGENT = 'QiniuPython/{0} ({1}; ) Python/{2}'.format(__version__, _sys_info, _python_ver)

_session = None
_headers = {'User-Agent': USER_AGENT}


def __return_wrapper(resp):
    if resp.status_code != 200 or resp.headers.get('X-Reqid') is None:
        return None, ResponseInfo(resp)
    ret = resp.json() if resp.text != '' else {}
    return ret, ResponseInfo(resp)


def _init():
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=config.get_default('connection_pool'), pool_maxsize=config.get_default('connection_pool'),
        max_retries=config.get_default('connection_retries'))
    session.mount('http://', adapter)
    global _session
    _session = session


def build_authorization(auth, url, body):
    token = ""
    if body:
        token = auth.token_of_request(url, body, 'application/x-www-form-urlencoded')
    else:
        token = auth.token_of_request(url)
    return 'QBox {0}'.format(token)



@gen.coroutine
def _post(url, data, files, request_auth):
    if files:
        raise NotImplementedError("does not support files upload")
    body = ""
    if data:
        body = urllib.urlencode(data)
    headers = {
        'Authorization': build_authorization(request_auth.auth, url, data),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    request = HTTPRequest(url, body=body, method="POST", headers=headers)
    client = AsyncHTTPClient()
    response = yield client.fetch(request)
    response_text = response.body
    retval = {}
    if response_text:
        retval = json.loads(response_text)
    raise gen.Return(retval)


@gen.coroutine
def _get(url, params, auth):
    full_url = '%s?%s' % (url, urllib.urlencode(params))
    headers = {
        'Authorization': build_authorization(auth, full_url, None)
    }
    request = HTTPRequest(full_url, headers=headers)
    client = AsyncHTTPClient()
    response = yield client.fetch(request)
    response_text = response.body
    retval = {}
    if response_text:
        retval = json.loads(response_text)
    raise gen.Return(retval)


class _TokenAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'UpToken {0}'.format(self.token)
        return r


def _post_with_token(url, data, token):
    return _post(url, data, None, _TokenAuth(token))


def _post_file(url, data, files):
    return _post(url, data, files, None)


def _post_with_auth(url, data, auth):
    return _post(url, data, None, RequestsAuth(auth))


class ResponseInfo(object):
    """七牛HTTP请求返回信息类

    该类主要是用于获取和解析对七牛发起各种请求后的响应包的header和body。

    Attributes:
        status_code: 整数变量，响应状态码
        text_body:   字符串变量，响应的body
        req_id:      字符串变量，七牛HTTP扩展字段，参考 http://developer.qiniu.com/docs/v6/api/reference/extended-headers.html
        x_log:       字符串变量，七牛HTTP扩展字段，参考 http://developer.qiniu.com/docs/v6/api/reference/extended-headers.html
        error:       字符串变量，响应的错误内容
    """

    def __init__(self, response, exception=None):
        """用响应包和异常信息初始化ResponseInfo类"""
        self.__response = response
        self.exception = exception
        if response is None:
            self.status_code = -1
            self.text_body = None
            self.req_id = None
            self.x_log = None
            self.error = str(exception)
        else:
            self.status_code = response.status_code
            self.text_body = response.text
            self.req_id = response.headers.get('X-Reqid')
            self.x_log = response.headers.get('X-Log')
            if self.status_code >= 400:
                ret = response.json() if response.text != '' else None
                if ret is None or ret['error'] is None:
                    self.error = 'unknown'
                else:
                    self.error = ret['error']
            if self.req_id is None and self.status_code == 200:
                self.error = 'server is not qiniu'

    def ok(self):
        return self.status_code == 200 and self.req_id is not None

    def need_retry(self):
        if self.__response is None or self.req_id is None:
            return True
        code = self.status_code
        if (code // 100 == 5 and code != 579) or code == 996:
            return True
        return False

    def connect_failed(self):
        return self.__response is None or self.req_id is None

    def __str__(self):
        return ', '.join(['%s:%s' % item for item in self.__dict__.items()])

    def __repr__(self):
        return self.__str__()
