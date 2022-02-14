import threading
from collections import namedtuple
from logging import getLogger
from typing import Dict
from typing import Tuple
from weakref import WeakValueDictionary

from sshtunnel import SSHTunnelForwarder

from sshtunnel_requests.ssh import Configuration

logger = getLogger(__name__)

SSH_SERVERS_CACHE: Dict[Configuration, "TunnelCache"] = {}

HOLDERS: Dict[Tuple[Configuration, "RemoteBindAddress"], threading.Event] = {}
HOLD_TIMEOUT = 5


class RemoteBindAddress(namedtuple('RemoteBindAddress', ('host', 'port'))):

    def __str__(self):
        return f'{self.host}:{self.port}'


class Connection:

    def __init__(self, ssh_config: Configuration, remote_bind_address: RemoteBindAddress) -> None:
        self.ssh_config = ssh_config
        self.remote_bind_address = remote_bind_address
        self._tunnel = None
        self.create_tunnel_connection_lock = threading.Lock()

    def __del__(self):
        if self._tunnel is not None:
            self._tunnel.close()

    @property
    def tunnel(self) -> SSHTunnelForwarder:
        with self.create_tunnel_connection_lock:
            if self._tunnel is None:
                ssh_config = self.ssh_config
                self._tunnel = SSHTunnelForwarder(
                    ssh_address_or_host=(ssh_config.host, ssh_config.port),
                    ssh_username=ssh_config.username,
                    ssh_password=ssh_config.password,
                    ssh_pkey=ssh_config.private_key,
                    ssh_private_key_password=ssh_config.private_key_password,
                    remote_bind_address=self.remote_bind_address)
                self._tunnel.start()
        return self._tunnel

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        try:
            hold(self)
        except Exception as exc:
            if exc_type is not None:
                raise exc from exc_value
            raise exc

        if exc_type is not None:
            raise exc_value


class TunnelCache:

    def __init__(self, ssh_config: Configuration) -> None:
        self.ssh_config = ssh_config
        self.lock = threading.Lock()
        self.pool: WeakValueDictionary[RemoteBindAddress, Connection] = WeakValueDictionary()

    def get(self, remote_address: RemoteBindAddress):
        with self.lock:
            if conn := self.pool.get(remote_address):
                return conn
            self.pool[remote_address] = conn = Connection(self.ssh_config, remote_address)
            return conn


class CacheDescriptor:
    def __get__(self, instance, owner) -> TunnelCache:
        if cache := SSH_SERVERS_CACHE.get(instance.ssh_config):
            return cache
        SSH_SERVERS_CACHE[instance.ssh_config] = cache = TunnelCache(instance.ssh_config)
        return cache


class TemporaryHoldConnectionThread(threading.Thread):
    def __init__(self, connection: Connection, heartbeat: threading.Event, timeout: int):
        """
        Args:
            connection(Connection): the connection to hold
            timeout(int): hold connection timeout
        """
        super().__init__(daemon=True)
        self.connection = connection
        self.heartbeat = heartbeat
        self.timeout = timeout

    def run(self):
        countdown = self.timeout

        while countdown > 0:
            logger.info(
                f'holding {self.connection.remote_bind_address} '
                f'-- {type(self.connection)}@{hex(id(self.connection))} '
                f'{self.timeout - countdown} seconds...')
            if not self.heartbeat.wait(1):
                countdown -= 1
            else:
                # reset holder
                self.heartbeat.clear()
                countdown = self.timeout
        # connection hold timeout
        del HOLDERS[(self.connection.ssh_config, self.connection.remote_bind_address)]


def hold(connection: Connection, timeout: int = HOLD_TIMEOUT) -> None:
    key = (connection.ssh_config, connection.remote_bind_address)
    if key not in HOLDERS:
        heartbeat = threading.Event()
        t = TemporaryHoldConnectionThread(connection, heartbeat, timeout=timeout)
        t.start()
        HOLDERS[key] = heartbeat

    # heartbeat to thread-hold
    HOLDERS[key].set()
