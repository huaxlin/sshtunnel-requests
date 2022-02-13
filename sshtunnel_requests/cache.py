import threading
from functools import namedtuple, partial
from logging import getLogger
from typing import Dict, Optional
from weakref import ReferenceType, WeakValueDictionary

from sshtunnel import SSHTunnelForwarder

logger = getLogger(__name__)


class RemoteBindAddress(namedtuple('RemoteBindAddress', ('host', 'port'))):

    def __str__(self):
        return f'{self.host}:{self.port}'


class Connection:

    def __init__(self, tunnel_partial, remote_bind_address) -> None:
        self.remote_bind_address = remote_bind_address
        self.tunnel_partial = tunnel_partial
        self._tunnel = None
        self.create_tunnel_connection_lock = threading.Lock()

    def __del__(self):
        if self._tunnel is not None:
            self._tunnel.close()

    @property
    def tunnel(self) -> SSHTunnelForwarder:
        with self.create_tunnel_connection_lock:
            if self._tunnel is None:
                self._tunnel = self.tunnel_partial(
                    remote_bind_address=self.remote_bind_address)
                self._tunnel.start()
        return self._tunnel


class TunnelCache:

    def __init__(self, tunnel_partial) -> None:
        self.tunnel_partial = tunnel_partial
        self.lock = threading.Lock()
        self.pool: Dict[RemoteBindAddress,
                        ReferenceType[Connection]] = WeakValueDictionary()

    def get(self, remote_address: RemoteBindAddress):
        with self.lock:
            if conn := self.pool.get(remote_address):
                return conn
            self.pool[remote_address] = conn = Connection(
                self.tunnel_partial, remote_address)
            return conn


class ConnectionManager:
    """
    Usage:
        >>> manager = ConnectionManager()
        >>> for url in fetch_urls:
        >>>     conn = Connection(...)  # cacher.get(remote_address)
        >>>     # requests.get(url) through connection
        >>>     manager.called(remote_address, conn)
    """

    def __init__(self) -> None:
        self.connections_holder: Dict[RemoteBindAddress, threading.Event] = {}

    def called(self, remote_bind_address: RemoteBindAddress,
               connection: Connection) -> None:
        if remote_bind_address not in self.connections_holder:
            self.connections_holder[
                remote_bind_address] = self.thread_temporary_hold(
                    connection, remote_bind_address)
            return

        # heartbeat to thread-hold
        self.connections_holder[remote_bind_address].set()

    def thread_temporary_hold(self, connection: Connection,
                              remote_bind_address):
        if remote_bind_address in self.connections_holder:
            raise Exception(
                f"Programming Error: connection of {remote_bind_address!r} has bean hold"
            )

        def fn(holder: dict,
               remote_bind_address: RemoteBindAddress,
               connection: Connection,
               heartbeat: threading.Event,
               countdown: int = 5):
            from time import ctime
            conn = connection
            cnt = countdown

            while cnt > 0:
                logger.info(
                    f'holding {remote_bind_address} -- {type(conn)}@{hex(id(conn))} '
                    f'{countdown - cnt} seconds...')
                if not heartbeat.wait(1):
                    cnt -= 1
                else:
                    heartbeat.clear()
                    cnt = countdown
            # connection hold timeout
            del holder[remote_bind_address]

        heartbeat = threading.Event()
        countdown = 5
        thread = threading.Thread(
            target=fn,
            name=f'{remote_bind_address} connection ref holder',
            args=(self.connections_holder, remote_bind_address, connection,
                  heartbeat, countdown),
            daemon=True)
        thread.start()
        return heartbeat


manager = ConnectionManager()
