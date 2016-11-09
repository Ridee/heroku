# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest
from mock import Mock, call

from heroku import HTTPStatusException, HerokuAPIClient, HerokuResponseMixin, make_request


@pytest.fixture
def http_connection(mocker):
    connection_mock = mocker.patch('heroku.HTTPConnection')
    return connection_mock


@pytest.fixture
def https_connection(mocker):
    connection_mock = mocker.patch('heroku.HTTPSConnection')
    return connection_mock


@pytest.mark.parametrize('uri,calls', [
    ('http://google.com/', (call(host='google.com'), None)),
    ('https://google.com/', (None, call(host='google.com'))),
])
def test_make_request_scheme(uri, calls, http_connection, https_connection):
    http_call, https_call = calls
    make_request('GET', uri)
    if http_call:
        assert http_call in http_connection.mock_calls
    if https_call:
        assert https_call in https_connection.mock_calls


@pytest.mark.parametrize('uri', [
    'ftp://google.com/',
    'ftps://google.com/',
    'ssh://google.com/',
])
def test_make_request_scheme_fails(uri):
    with pytest.raises(ValueError):
        make_request(method='GET', uri=uri)


@pytest.mark.parametrize('parameters,http_calls', [
    (
            dict(method='GET', uri='http://google.com/'),
            [
                call(host='google.com'),
                call().request(method='GET', url='/', body=None, headers={}),
                call().getresponse(),
                call().getresponse().read(),
            ]
    ),
    (
            dict(method='POST', uri='http://google.com/api', body='asdf'),
            [
                call(host='google.com'),
                call().request(method='POST', url='/api', body='asdf', headers={}),
                call().getresponse(),
                call().getresponse().read(),
            ]
    ),
    (
            dict(method='POST', uri='http://google.com/app', body='asdf', headers={'a': 'b'}),
            [
                call(host='google.com'),
                call().request(method='POST', url='/app', body='asdf', headers={'a': 'b'}),
                call().getresponse(),
                call().getresponse().read(),
            ]
    ),
])
def test_make_request_calls(parameters, http_calls, http_connection, https_connection):
    make_request(**parameters)
    assert http_calls == http_connection.mock_calls


def test_make_request_return_value(http_connection, https_connection):
    response = make_request(method='PST', uri='http://goo/', body='dat body', headers={'asd': 'aan'})
    code, headers, body = response
    assert code == http_connection.return_value.getresponse.return_value.status
    assert headers == http_connection.return_value.getresponse.return_value.headers
    assert body == http_connection.return_value.getresponse.return_value.read.return_value


@pytest.mark.parametrize('parameters,result', [
    ((100, {'a': 'b'}, '{}'), (100, {'a': 'b'}, {}))
])
def test_heroku_response_mixin(parameters, result):
    response = HerokuResponseMixin.treat_response(*parameters)
    assert result == response


try:
    from json import JSONDecodeError
except:
    JSONDecodeError = ValueError


@pytest.mark.parametrize('response,exception', [
    (
            (422, {'a': 'b'}, b'This is an error'),
            dict(expected_exception=HTTPStatusException, message='422 This is an error')
    ),
    (
            (429, {'a': 'b'}, b'This is an error'),
            dict(expected_exception=HTTPStatusException, message='429 This is an error')
    ),
    (
            (200, {'a': 'b'}, b'{"a"}'),
            dict(expected_exception=JSONDecodeError, message='Expecting : delimiter: line 1 column 5 (char 4)')
    ),
])
def test_heroku_response_mixin(response, exception):
    with pytest.raises(**exception):
        HerokuResponseMixin.treat_response(response=response)


@pytest.mark.parametrize('args,call', [
    (
            dict(method='GET', path='/sap'),
            call(
                method='GET',
                uri='http://goo/sap',
                headers={
                    'Accept': 'application/vnd.heroku+json; version=3',
                    'Content-Type': 'application/json',
                    'Authorization': 'OmFzZGY=',
                },
                body=None
            )
    ),
        (
        dict(method='GET', path='/sap', headers={'asdf': 'abc'}),
        call(
            method='GET',
            uri='http://goo/sap',
            headers={
                'asdf': 'abc',
                'Accept': 'application/vnd.heroku+json; version=3',
                'Content-Type': 'application/json',
                'Authorization': 'OmFzZGY=',
            },
            body=None
        )
    )
])
def test_heroku_api_client_request(args, call):
    request_mock = Mock(return_value=(Mock(), Mock(), b'{"a": "c"}'))
    client = HerokuAPIClient(base_uri='http://goo', api_key='asdf', request=request_mock)
    code, headers, body = client.request(**args)
    assert code == request_mock.return_value[0]
    assert headers == request_mock.return_value[1]
    assert body == {'a': 'c'}
    request_mock.mock_calls = [call]
