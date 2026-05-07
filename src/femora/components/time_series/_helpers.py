from __future__ import annotations

from typing import Iterable, List, Optional, Union


def as_float(value, name: str) -> float:
    """Convert a constructor argument to ``float`` with a field-specific error.

    Args:
        value: Input value to convert.
        name: Parameter name used in the validation error.

    Returns:
        The converted floating-point value.

    Raises:
        ValueError: If ``value`` cannot be converted to ``float``.
    """
    try:
        return float(value)
    except Exception:
        raise ValueError(f"{name} must be a number")


def as_bool(value, name: str) -> bool:
    """Validate that a constructor argument is a boolean.

    Args:
        value: Input value to validate.
        name: Parameter name used in the validation error.

    Returns:
        The original boolean value.

    Raises:
        ValueError: If ``value`` is not a ``bool``.
    """
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def parse_float_list(value, name: str) -> Optional[List[float]]:
    """Parse a float sequence accepted by ``PathTimeSeries``.

    Args:
        value: ``None``, a comma-separated string, or an iterable of numeric
            values.
        name: Parameter name used in the validation error.

    Returns:
        ``None`` when ``value`` is ``None``; otherwise a list of floats.

    Raises:
        ValueError: If ``value`` is not a string or iterable of numeric values.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return [float(item) for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable):
        return [float(item) for item in value]
    raise ValueError(f"{name} must be a list/tuple or comma-separated string")


Number = Union[int, float]
