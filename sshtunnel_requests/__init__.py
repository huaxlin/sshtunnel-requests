__version__ = '0.0.2'

from .sessions import session, Session  # noqa


def SSHTunnelRequests(**kwargs):
    from . import _api
    from .ssh import Config

    _api.SSH_CONF = Config(**kwargs)

    return _api


def from_url(url, private_key=None, private_key_password=None):
    """
    For example::

        ssh://[[username]:[password]]@localhost:22
    """
    from urllib.parse import ParseResult, urlparse
    from . import _api
    from .ssh import Config

    parsed: ParseResult = urlparse(url)
    if parsed.scheme != 'ssh':
        raise ValueError('only support "ssh" scheme, '
                         f'but got {parsed.scheme}')

    _api.SSH_CONF = Config(
        host=parsed.hostname,
        username=parsed.username,
        port=parsed.port,
        password=parsed.password,
        private_key=private_key,
        private_key_password=private_key_password        
    )

    return _api
