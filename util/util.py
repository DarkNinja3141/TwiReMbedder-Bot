__all__ = ["debug_guilds", "Ignore", "DiscordLimit", "EmbedLimit", "find", "remove_file"]

import errno
import os
import typing
from dataclasses import dataclass

from config import config


def debug_guilds() -> typing.Optional[typing.List[int]]:
    return config.debug.guild_ids if config.debug else None


class _Ignore:
    """Use as a context manager to ignore exceptions"""
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True


Ignore = _Ignore()


@dataclass
class DiscordLimit:
    file_limit: int = 8000000


@dataclass
class EmbedLimit:
    title: int = 256
    description: int = 2048
    fields: int = 25
    field_name: int = 256
    field_value: int = 1024
    footer_text: int = 2048
    author_name: int = 256


_T = typing.TypeVar('_T')
_VT = typing.TypeVar('_VT')


def find(items: typing.Iterable[_T], predicate: typing.Callable[[_T], bool], default: _VT = None):
    return next((x for x in items if predicate(x)), default)


def remove_file(filename):
    """
    https://stackoverflow.com/a/10840586
    """
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred
