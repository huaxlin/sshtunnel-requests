from logging import getLogger

from furl import furl
from requests.sessions import Session as _Session

from . import ssh

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

    def __init__(self,
                 host,
                 port,
                 username=None,
                 password=None,
                 private_key=None,
                 private_key_password=None):
        self.ssh_conf = ssh.Config(
            **{
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'private_key': private_key,
                'private_key_password': private_key_password,
            })
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        # 在这里持有 connection 引用；保证调用下面 .request() 时，conn._tunnel 不会因为弱引用而被销毁；
        # 当下面的 .request() return 后，即拿到了 response，则 tunnel 链接被销毁；
        # 多线程情况下，tunnel 理论上能够被重复使用，但是单线程使用for循环的情况下，理论上无法重复利用，这里需要优化。
        conn = ssh.create_connection(url, self.ssh_conf)

        _furl = furl(url)
        _furl.host = conn.tunnel.local_bind_host
        _furl.port = conn.tunnel.local_bind_port
        tunnel_local_bind_url = _furl.url

        return super().request(method, tunnel_local_bind_url, *args, **kwargs)

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


def session(host,
            port,
            username=None,
            password=None,
            private_key=None,
            private_key_password=None):
    return Session(host, port, username, password, private_key,
                   private_key_password)
