from dataclasses import asdict, dataclass
from logging import getLogger
from urllib.parse import ParseResult, urlparse

from sshtunnel_requests.sessions import Session
from sshtunnel_requests.ssh import Configuration

logger = getLogger(__name__)


@dataclass
class Requests(Configuration):

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
        with Session(**asdict(self)) as session:
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
