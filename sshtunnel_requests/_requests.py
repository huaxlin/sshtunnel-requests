import threading
from functools import namedtuple, partial
from logging import getLogger
from os import PathLike
from typing import Dict, Optional
from urllib.parse import ParseResult, urlparse
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


class Requests:

    def __init__(self,
                 host: str,
                 username: str,
                 password: Optional[str] = None,
                 port: int = 22,
                 private_key: Optional[PathLike] = None,
                 private_key_password: Optional[str] = None) -> None:

        self.tunnel_partial = partial(
            SSHTunnelForwarder,
            ssh_address_or_host=(host, port),
            ssh_username=username,
            ssh_password=password,
            ssh_pkey=private_key,
            ssh_private_key_password=private_key_password)
        self.cacher = TunnelCache(self.tunnel_partial)
        self.manager = ConnectionManager()

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
        import requests
        from furl import furl

        _furl = furl(url)
        remote_address = RemoteBindAddress(host=_furl.host, port=_furl.port)
        conn = self.cacher.get(remote_address)

        # replace the actual request url to local bind url
        _furl.host = conn.tunnel.local_bind_host
        _furl.port = conn.tunnel.local_bind_port
        tunnel_local_bind_url = _furl.url

        response = requests.request(method, tunnel_local_bind_url, **kwargs)

        self.manager.called(remote_address, conn)
        return response

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
