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


from functools import wraps

# def sshtunnelconfig(fn):
#     @wraps(fn)
#     def wrapper(
#         *args,

#         # SSH Tunnel Configurations
#         ssh_host=None,
#         ssh_port=None,
#         ssh_username=None,
#         ssh_password=None,
#         ssh_private_key=None,
#         ssh_private_key_password=None,

#         **kwargs
#     ):
#         ssh_conf = dict(
#             ssh_host=ssh_host,
#             ssh_port=ssh_port,
#             ssh_username=ssh_username,
#             ssh_password=ssh_password,
#             ssh_private_key=ssh_private_key,
#             ssh_private_key_password=ssh_private_key_password
#         )
#         return fn(*args, sshtunnelconf=ssh_conf, **kwargs)
#     return wrapper


# @sshtunnelconfig
def get(url, params=None, sshtunnelconf: T.Optional[ssh.Config] = None, **kwargs):
    return request('get', url, sshtunnelconf=sshtunnelconf,
                   params=params, **kwargs)


def options(url, **kwargs):
    return request('options', url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault('allow_redirects', False)
    return request('head', url, **kwargs)


# @sshtunnelconfig
# def post(url, data=None, json=None,
#         ssh_conf: T.Optional[T.Dict[str, T.Any]] = None,
#         **kwargs):
def post(url, data=None, json=None, sshtunnelconf: T.Optional[ssh.Config] = None, **kwargs):
    return request('post', url, sshtunnelconf=sshtunnelconf,
                   data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request('put', url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    return request('delete', url, **kwargs)
