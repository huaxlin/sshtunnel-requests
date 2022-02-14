from dataclasses import dataclass
from typing import Optional
from os import PathLike


@dataclass(unsafe_hash=True)
class Configuration:
    host: str
    username: str
    password: Optional[str] = None
    port: int = 22
    private_key: Optional[PathLike] = None
    private_key_password: Optional[str] = None
