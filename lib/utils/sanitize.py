"""
Utilities for sanitizing sensitive data.
"""

from typing import Any


def sanitize_log_data(data: Any) -> Any:
    """
    Sanitizes data for logging, removing sensitive information.

    Args:
        data: Data to be sanitized.

    Returns:
        Sanitized data.
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key.lower() in ["password", "secret", "token", "key", "credential"]:
                sanitized[key] = "******"
            else:
                sanitized[key] = sanitize_log_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data
