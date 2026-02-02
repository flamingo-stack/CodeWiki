"""
Helper utilities for data processing.

This module is in a separate dependency package that should be analyzed
alongside the main codebase.
"""

from typing import Any, Dict


def validate_input(data: Dict[str, Any]) -> bool:
    """Validate input data structure.

    Args:
        data: Input data to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False

    required_keys = ["type", "value"]
    return all(key in data for key in required_keys)


def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process input data and return transformed result.

    Args:
        data: Input data to process

    Returns:
        Processed data
    """
    if not validate_input(data):
        raise ValueError("Invalid input data")

    # Transform data
    result = {
        "original": data,
        "processed_type": data["type"].upper(),
        "processed_value": str(data["value"]).strip(),
        "timestamp": "2024-01-01T00:00:00Z"
    }

    return result


def format_output(data: Dict[str, Any]) -> str:
    """Format processed data for output.

    Args:
        data: Data to format

    Returns:
        Formatted string representation
    """
    return f"[{data.get('processed_type', 'UNKNOWN')}] {data.get('processed_value', '')}"
