from logging import getLogger
from requests.sessions import Session as _Session
from furl import furl

from . import ssh

logger = getLogger(__name__)


class SessionRedirectMixin:
    def get_redirect_target(self, resp):
        """通过隧道访问的HTTP请求被重定向，可能会有BUG，将重定向行为INFO，便于判断"""
        if resp.is_redirect:
            logger.info('[%d] redirect location: %s' % (resp.status_code, resp.headers['location']))
        return super().get_redirect_target(resp)


class _SSHTunnelSession(SessionRedirectMixin, _Session):
    pass


class Session(_SSHTunnelSession):
    def __init__(
        self,
        ssh_host,
        ssh_port,
        ssh_username=None,
        ssh_password=None,
        ssh_private_key=None,
        ssh_private_key_password=None
    ):
        self.ssh_conf = ssh.Config(**{
            'host': ssh_host,
            'port': ssh_port,
            'username': ssh_username,
            'password': ssh_password,
            'private_key': ssh_private_key,
            'private_key_password': ssh_private_key_password,
        })
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        # tunnel_url = ssh.get_tunnel_url_with_create(url, self.ssh_conf)
        conn = ssh.create_connection(url, self.ssh_conf)

        _furl = furl(url)
        _furl.host = conn.tunnel.local_bind_host
        _furl.port = conn.tunnel.local_bind_port
        tunnel_local_bind_url = _furl.url

        return super().request(method, tunnel_local_bind_url, *args, **kwargs)


def session(
    ssh_host,
    ssh_port,
    ssh_username=None,
    ssh_password=None,
    ssh_private_key=None,
    ssh_private_key_password=None
):
    return Session(
        ssh_host,
        ssh_port,
        ssh_username,
        ssh_password,
        ssh_private_key,
        ssh_private_key_password
    )
