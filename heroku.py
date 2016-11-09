# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging
from base64 import b64encode

import six
from six.moves.http_client import HTTPConnection, HTTPException, HTTPSConnection
from six.moves.urllib_parse import urlparse

logger = logging.getLogger(__name__)


class HTTPStatusException(HTTPException):
    def __init__(self, status, msg, *args, **kwargs):
        error_string = '{} {}'.format(status, msg)
        super(HTTPStatusException, self).__init__(error_string, *args, **kwargs)
        self.status = status
        self.message = msg


def make_request(method, uri, headers=None, body=None):
    """
    This function should make a request, connection reuse, etc. is left to the implementation

    :param str|unicode method: HTTP Verb
    :param str|unicode uri: Server/path to make the request to
    :param dict headers: Headers to send
    :param str|unicode body: Body to send
    :return: Request result
    :rtype: Tuple of return_code (int), headers (dict), body (str|bytes)
    """
    parsed_url = urlparse(uri)
    if parsed_url.scheme == 'https':
        connector = HTTPSConnection(host=parsed_url.netloc)
    elif parsed_url.scheme == 'http':
        connector = HTTPConnection(host=parsed_url.netloc)
    else:
        raise ValueError('Schema is not HTTP nor HTTPS')
    _, full_path = uri.split(parsed_url.netloc, 1)
    connector.request(method=method, url=full_path, body=body, headers=headers or {})
    response = connector.getresponse()
    status_code = response.status
    body = response.read()
    headers = response.headers
    return status_code, headers, body


class BaseClient(object):
    def __init__(self, request=None):
        self.make_request = request or make_request


class HerokuHeaderMixin(object):
    @staticmethod
    def heroku_headers():
        return {
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json',
        }


class HerokuAuthenticationMixin(object):
    api_key = ''

    def authenticate(self):
        auth_string = ':{}'.format(self.api_key)
        auth_64 = b64encode(auth_string.encode())
        return {'Authorization': auth_64.decode()}


class HerokuResponseMixin(object):
    @staticmethod
    def treat_response(response):
        code, headers, body = response
        decoded_body = body.decode('utf-8')
        if code == 422:
            error_string = 'Client Error: {}'.format(decoded_body)
            logger.error(error_string)
            raise HTTPStatusException(code, error_string)
        if code == 429:
            error_string = 'Rate limit exceeded: {}'.format(decoded_body)
            logger.info(error_string)
            raise HTTPStatusException(code, error_string)
        return code, headers, json.loads(decoded_body)


class HerokuAPIClient(BaseClient, HerokuHeaderMixin, HerokuAuthenticationMixin, HerokuResponseMixin):
    def __init__(self, base_uri, api_key, request=None):
        super(HerokuAPIClient, self).__init__(request=request)
        self.base_uri = base_uri
        self.api_key = api_key

    def request(self, method, path, headers=None, body=None):
        if not headers:
            headers = {}
        headers.update(self.heroku_headers())
        headers.update(self.authenticate())
        response = self.make_request(method=method, uri=self.base_uri + path, headers=headers, body=body)
        return self.treat_response(response=response)


class HerokuClient(object):
    def __init__(self, api_key, request=None):
        self.api = HerokuAPIClient('https://api.heroku.com', api_key=api_key, request=request)
        self.postgres_api = HerokuAPIClient('https://postgres-api.heroku.com', api_key=api_key, request=request)
