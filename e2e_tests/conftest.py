import logging
from logging.config import dictConfig

import pytest

# sshtunnel.DEFAULT_LOGLEVEL = 1
dictconfig = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'requests': {
            'level': 'WARNING',
        },
        'urllib3': {
            'level': 'WARNING',
        },
        'transport': {
            'level': 'WARNING',
        },
    },
}

dictConfig(dictconfig)
logging.basicConfig(
    format=
    '%(asctime)s| %(levelname)-4.3s|%(threadName)10.9s/%(lineno)04d@%(module)-10.9s| %(message)s',
    # level=1)
    level=logging.DEBUG)


@pytest.fixture(scope='function', autouse=True)
def clean_ssh_servers_cache():
    from sshtunnel_requests.cache import SSH_SERVERS_CACHE
    SSH_SERVERS_CACHE.clear()

    from sshtunnel_requests.cache import HOLDERS
    HOLDERS.clear()
