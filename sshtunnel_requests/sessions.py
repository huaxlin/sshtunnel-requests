from logging import getLogger
from os import PathLike
from typing import Optional

from furl import furl
from requests.sessions import Session as _Session

from sshtunnel_requests.cache import CacheDescriptor
from sshtunnel_requests.cache import RemoteBindAddress
from sshtunnel_requests.ssh import Configuration

logger = getLogger(__name__)


class SessionRedirectMixin:

    def get_redirect_target(self, resp):
        """通过隧道访问的HTTP请求被重定向，可能会有BUG，将重定向行为INFO，便于判断"""
        if resp.is_redirect:
            logger.info('[%d] redirect location: %s' %
                        (resp.status_code, resp.headers['location']))
        return super().get_redirect_target(resp)


class _SSHTunnelSession(SessionRedirectMixin, _Session):
    pass


class Session(_SSHTunnelSession):
    caches = CacheDescriptor()

    def __init__(self,
                 host: str,
                 username: str,
                 password: Optional[str] = None,
                 port: int = 22,
                 private_key: Optional[PathLike] = None,
                 private_key_password: Optional[str] = None) -> None:
        self.ssh_config = Configuration(
            host=host, username=username, password=password, port=port,
            private_key=private_key,
            private_key_password=private_key_password)

        super().__init__()

    @classmethod
    def from_url(cls, url, private_key=None, private_key_password=None):
        """
        For example::

            ssh://[[username]:[password]]@localhost:22
        """
        from urllib.parse import ParseResult, urlparse

        parsed: ParseResult = urlparse(url)
        if parsed.scheme != 'ssh':
            raise ValueError('only support "ssh" scheme, '
                             f'but got {parsed.scheme}')

        session = cls(host=parsed.hostname,
                      username=parsed.username,
                      port=parsed.port,
                      password=parsed.password,
                      private_key=private_key,
                      private_key_password=private_key_password)
        return session

    def request(self, method, url, *args, **kwargs):
        f = furl(url)

        remote_address = RemoteBindAddress(host=f.host, port=f.port)

        with self.caches.get(remote_address) as conn:
            # replace the actual request url to local bind url
            f.host, f.port = conn.tunnel.local_bind_host, conn.tunnel.local_bind_port
            tunnel_local_bind_url = f.url

            return super().request(method, tunnel_local_bind_url, *args, **kwargs)


def session(host,
            port,
            username=None,
            password=None,
            private_key=None,
            private_key_password=None):
    return Session(host=host,
                   port=port,
                   username=username,
                   password=password,
                   private_key=private_key,
                   private_key_password=private_key_password)
