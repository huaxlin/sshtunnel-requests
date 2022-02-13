from dataclasses import asdict, dataclass
from logging import getLogger
from os import PathLike
from typing import Optional
from urllib.parse import ParseResult, urlparse

from sshtunnel_requests.sessions import Session

logger = getLogger(__name__)


@dataclass
class Requests:
    host: str
    username: str
    password: Optional[str] = None
    port: int = 22
    private_key: Optional[PathLike] = None
    private_key_password: Optional[str] = None

    def __post_init__(self):
        from functools import partial

        from sshtunnel import SSHTunnelForwarder

        self.tunnel_partial = partial(
            SSHTunnelForwarder,
            ssh_address_or_host=(self.host, self.port),
            ssh_username=self.username,
            ssh_password=self.password,
            ssh_pkey=self.private_key,
            ssh_private_key_password=self.private_key_password)
        from .cache import TunnelCache
        self.cacher = TunnelCache(self.tunnel_partial)

    @classmethod
    def from_url(cls,
                 url,
                 private_key=None,
                 private_key_password=None) -> "Requests":
        """
        For example::

            ssh://[[username]:[password]]@localhost:22
        """
        parsed: ParseResult = urlparse(url)
        if parsed.scheme != 'ssh':
            raise ValueError('only support "ssh" scheme, '
                             f'but got {parsed.scheme}')

        obj = cls(host=parsed.hostname,
                  username=parsed.username,
                  password=parsed.password,
                  port=parsed.port,
                  private_key=private_key,
                  private_key_password=private_key_password)
        return obj

    def request(self, method: str, url: str, **kwargs):
        with Session(**asdict(self), cacher=self.cacher) as session:
            return session.request(method, url, **kwargs)

    # api --------------------------------------------------------------------

    def get(self, url, params=None, **kwargs):
        return self.request('get', url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request('put', url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request('patch', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('delete', url, **kwargs)
