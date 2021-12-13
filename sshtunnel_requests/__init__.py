__version__ = '0.0.3'

from ._requests import Requests  # noqa
from .sessions import Session, session  # noqa


def from_url(url, private_key=None, private_key_password=None):
    """
    For example::

        ssh://[[username]:[password]]@localhost:22
    """

    return Requests.from_url(url,
                             private_key=private_key,
                             private_key_password=private_key_password)
