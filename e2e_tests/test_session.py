import pytest
import sshtunnel_requests

from const import *


@pytest.fixture
def session_from_url():
    return sshtunnel_requests.Session.from_url(SSH_URL, SSH_PKEY)


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
