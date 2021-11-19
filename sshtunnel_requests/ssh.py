import typing as T
from dataclasses import dataclass
from dataclasses import field
from dataclasses import asdict
from logging import getLogger

logger = getLogger(__name__)


@dataclass(frozen=True)
class Config:
    host: str
    username: str
    port: int = field(default=22)
    password: T.Optional[str] = None
    private_key: T.Optional[str] = None
    # private_key_string: T.Optional[str] = None
    private_key_password: T.Optional[str] = None
    # set_keepalive: int = field(default=5)

    def as_dict(self) -> dict:
        return asdict(self)


from sshtunnel import SSHTunnelForwarder

from functools import namedtuple
class HostPort(namedtuple('HostPort', ('host', 'port'))):
    def __str__(self):
        return f'{self.host}:{self.port}'

    def __repr__(self):
        return f'{type(self).__name__} => {str(self)}'


class Connection:
    def __init__(
        self,
        remote_hp: HostPort,
        ssh_conf: T.Optional[Config] = None,
    ) -> None:
        self.remote_hp = remote_hp
        self.ssh_conf = ssh_conf
        self._tunnel: T.Optional[SSHTunnelForwarder] = None

    def __del__(self):
        if self._tunnel is not None:
            self._tunnel.close()

    @property
    def tunnel(self) -> SSHTunnelForwarder:
        if self._tunnel is None:
            self._tunnel = self.create_tunnel()
            self._tunnel.start()
            logger.info('Create SSH Tunnel: %s -> %s -> %s',
                        HostPort(self._tunnel.local_bind_host, self._tunnel.local_bind_port),
                        HostPort(self.ssh_conf.host, self.ssh_conf.port),
                        self.remote_hp)
        return self._tunnel

    def create_tunnel(self, ssh_conf=None):
        if ssh_conf is not None:
            self.ssh_conf = ssh_conf
        elif self.ssh_conf is None:
            raise ValueError()
        tunnel = SSHTunnelForwarder(
            (self.ssh_conf.host, self.ssh_conf.port),
            ssh_username=self.ssh_conf.username,
            ssh_password=self.ssh_conf.password,
            ssh_pkey=self.ssh_conf.private_key,
            ssh_private_key_password=self.ssh_conf.private_key_password,
            remote_bind_address=(self.remote_hp.host, self.remote_hp.port),
            set_keepalive=5
        )
        return tunnel


#
# weakref implement cacher
#
import threading
import weakref

class Cacher:
    def __init__(self, ssh_conf: Config) -> None:
        self.ssh_conf: Config = ssh_conf
        self.pool: T.Dict[HostPort, weakref.ReferenceType[Connection]] = weakref.WeakValueDictionary()
        self.lock = threading.Lock()

    def get(self, key: HostPort) -> Connection:
        with self.lock:
            conn = self.pool.get(key)
            if conn:
                return conn
            self.pool[key] = conn = Connection(key, self.ssh_conf)
            return conn


class Tunnels:
    """
        conn_1(remote-host/port) --+,
        conn_2(remote-host/port) --+--> cacher  ------------+
        conn_3(remote-host/port) --+'   (sshtunnel server)   \
                                                            `,-> cacher
        conn_a(remote-host/port) --+,                         /
        conn_b(rmeote-host/port) --+--> cacher  ------------+
                                        (sshtunnel server)
    """
    def __init__(self) -> None:
        self.pool: T.Dict[Config, Cacher] = {}
        self.lock = threading.Lock()

    def get(self, ssh_conf: Config) -> Cacher:
        with self.lock:
            cacher = self.pool.get(ssh_conf)
            if cacher:
                return cacher
            self.pool[ssh_conf] = cacher = Cacher(ssh_conf)
            return cacher


_tunnels = Tunnels()


def create_connection(url, ssh_conf):
    from furl import furl
    _furl = furl(url)

    cacher = _tunnels.get(ssh_conf)
    conn = cacher.get(HostPort(host=_furl.host, port=_furl.port))
    return conn
