__all__ = ["Ignore"]


class _Ignore:
    """Use as a context manager to ignore exceptions"""
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True


Ignore = _Ignore()
