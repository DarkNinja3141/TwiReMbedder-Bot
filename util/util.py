__all__ = ["debug_guilds", "Ignore", "DiscordLimit", "EmbedLimit", "find", "remove_file", "supplier", "interval"]

import errno
import operator
import os
import typing
from dataclasses import dataclass

from config import config


def debug_guilds() -> typing.Optional[typing.List[int]]:
    return config.debug.guild_ids if config.debug else None


class _Ignore:
    """ Use as a context manager to ignore exceptions

    Usage:

    .. code-block:: python
        with Ignore:
            pass

    Call with exception types to filter specifically
    ex: Ignore(Exception1, Exception2)
    """
    def __init__(self, *exceptions):
        self.exceptions = set(exceptions)

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return len(self.exceptions) == 0 or exc_type in self.exceptions

    def __call__(self, *args, **kwargs):
        return _Ignore(*args)


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


def supplier(value: _T) -> typing.Callable[[], _T]:
    """Returns a function that returns a constant value"""
    return lambda *_, **__: value


# noinspection PyPep8Naming
class interval:
    """Usage: x in interval(start, end)"""
    def __init__(self, start=None, end=None, incl_start=True, incl_end=True):
        self.start = start
        self.end = end
        self.start_comparator = (operator.le if incl_start else operator.lt) if start is not None else supplier(True)
        self.end_comparator = (operator.le if incl_end else operator.lt) if end is not None else supplier(True)

    def __contains__(self, item):
        return self.start_comparator(self.start, item) and self.end_comparator(item, self.end)
