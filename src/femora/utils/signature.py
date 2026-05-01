from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, Optional, TypeVar


F = TypeVar("F", bound=Callable[..., Any])


def forward_signature(
    source: Callable[..., Any] | type,
    *,
    drop_first: bool = True,
    doc: Optional[str] = None,
) -> Callable[[F], F]:
    """Forward a callable/class constructor signature to another callable.

    This is useful for manager/factory methods whose implementation accepts
    ``**kwargs`` but should expose the signature of the object they construct.

    Args:
        source: Callable to copy the signature from. If a class is provided,
            its ``__init__`` signature is used.
        drop_first: Drop the first source parameter. Defaults to ``True`` for
            forwarding class ``__init__(self, ...)`` signatures.
        doc: Optional docstring override. If omitted, the source docstring is
            used when available.
    """

    source_callable = source.__init__ if isinstance(source, type) else source
    signature = inspect.signature(source_callable)
    parameters = list(signature.parameters.values())
    if drop_first and parameters:
        parameters = parameters[1:]
    forwarded_signature = signature.replace(parameters=parameters)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper.__signature__ = forwarded_signature  # type: ignore[attr-defined]
        wrapper.__doc__ = doc if doc is not None else getattr(source, "__doc__", None)
        return wrapper  # type: ignore[return-value]

    return decorator
