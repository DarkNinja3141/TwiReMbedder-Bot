__all__ = ["Ignore", "EmbedLimit"]

from dataclasses import dataclass


class _Ignore:
    """Use as a context manager to ignore exceptions"""
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True


Ignore = _Ignore()


@dataclass
class EmbedLimit:
    title: int = 256
    description: int = 2048
    fields: int = 25
    field_name: int = 256
    field_value: int = 1024
    footer_text: int = 2048
    author_name: int = 256
