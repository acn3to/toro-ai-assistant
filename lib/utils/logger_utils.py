"""
Utilities for logging and exception handling.
"""

import traceback


def get_traceback() -> str:
    """
    Captures the current exception's traceback.

    Returns:
        A string with the formatted traceback.
    """
    return traceback.format_exc()
