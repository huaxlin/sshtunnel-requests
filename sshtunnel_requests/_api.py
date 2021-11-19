import typing as T
from . import sessions
from . import ssh


def request(
    method,
    url,
    *,
    sshtunnelconf: ssh.Config,
    **kwargs
):
    ssh_conf = {'ssh_' + k: v for k, v in sshtunnelconf.as_dict().items()}
    with sessions.Session(**ssh_conf) as session:
        return session.request(method=method, url=url, **kwargs)


SSH_CONF: ssh.Config = None


def get(url, params=None, **kwargs):
    return request('get', url, sshtunnelconf=SSH_CONF, params=params, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request('post', url, sshtunnelconf=SSH_CONF,
                   data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    return request('delete', url, **kwargs)
