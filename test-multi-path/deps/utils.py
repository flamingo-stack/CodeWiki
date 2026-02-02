"""
Additional utility functions.
"""


def sanitize_string(text: str) -> str:
    """Remove special characters from string.

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    return "".join(c for c in text if c.isalnum() or c.isspace())


def calculate_hash(data: str) -> int:
    """Calculate simple hash of string data.

    Args:
        data: Input data

    Returns:
        Hash value
    """
    return hash(data) % (10 ** 8)
