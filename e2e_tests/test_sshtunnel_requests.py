import logging
import os

import pytest
import sshtunnel
import sshtunnel_requests

sshtunnel.DEFAULT_LOGLEVEL = 1
logging.basicConfig(
    format=
    '%(asctime)s| %(levelname)-4.3s|%(threadName)10.9s/%(lineno)04d@%(module)-10.9s| %(message)s',
    level=1)

SSH_SERVER_HOST = '127.0.0.1'
SSH_SERVER_PORT = 2223
SSH_SERVER_USERNAME = 'linuxserver'
SSH_PKEY = os.path.join(os.path.dirname(__file__), 'ssh-server-config',
                        'ssh_host_rsa_key')
SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN = '10.5.0.5'


class TestSSHTunnelRequests():

    def test_one_request(self):
        stlrequests = sshtunnel_requests.SSHTunnelRequests(
            host=SSH_SERVER_HOST,
            username=SSH_SERVER_USERNAME,
            port=SSH_SERVER_PORT,
            private_key=SSH_PKEY)
        resp = stlrequests.get(
            f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/ip')
        assert resp.json() == {'origin': '10.5.0.2'}


class TestFromURL():

    def test_one_requests(self):
        stlrequests = sshtunnel_requests.from_url(
            f'ssh://{SSH_SERVER_USERNAME}@{SSH_SERVER_HOST}:{SSH_SERVER_PORT}',
            SSH_PKEY)
        resp = stlrequests.get(
            f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/ip')
        assert resp.json() == {'origin': '10.5.0.2'}


@pytest.fixture
def session_from_url():
    session = sshtunnel_requests.Session.from_url(
        f'ssh://{SSH_SERVER_USERNAME}@{SSH_SERVER_HOST}:{SSH_SERVER_PORT}',
        SSH_PKEY)
    return session


@pytest.fixture
def session_from_class():
    session = sshtunnel_requests.Session(host=SSH_SERVER_HOST,
                                         username=SSH_SERVER_USERNAME,
                                         port=SSH_SERVER_PORT,
                                         private_key=SSH_PKEY)
    return session


@pytest.fixture
def session_from_function():
    session = sshtunnel_requests.session(host=SSH_SERVER_HOST,
                                         username=SSH_SERVER_USERNAME,
                                         port=SSH_SERVER_PORT,
                                         private_key=SSH_PKEY)
    return session


@pytest.fixture(params=['from_url', 'from_class', 'from_function'])
def session(request):
    return request.getfixturevalue('session_' + request.param)


def test_session(session):

    assert session.cookies.values() == list()
    resp = session.get(
        f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/cookies/set/sessioncookie/123456789'
    )
    assert resp.json() == {'cookies': {'sessioncookie': '123456789'}}
    assert session.cookies.values() == ['123456789']
    resp = session.get(f'http://{SSH_SERVER_REMOTE_SIDE_HOST_HTTPBIN}/ip')
    assert 'Cookie' in resp.request.headers
    assert resp.request.headers['Cookie'] == 'sessioncookie=123456789'
    assert resp.json() == {'origin': '10.5.0.2'}
