"""Compatibility imports for the old Pattern module path.

New code should import base/manager classes from ``femora.core`` and concrete
pattern classes from ``femora.components.pattern``.
"""

from femora.components.pattern.h5drm_pattern import H5DRMPattern
from femora.components.pattern.multiple_support import ImposedMotion, MultipleSupportPattern
from femora.components.pattern.plain_pattern import PlainPattern
from femora.components.pattern.uniform_excitation import UniformExcitation
from femora.core.pattern_base import Pattern
from femora.core.pattern_manager import PatternManager


class PatternRegistry:
    """Compatibility registry facade backed by concrete pattern classes.

    New code should prefer :class:`femora.core.pattern_manager.PatternManager`.
    This class remains so older code that dynamically creates patterns by name
    can continue to run.
    """

    _pattern_types = {
        "uniformexcitation": UniformExcitation,
        "uniform_excitation": UniformExcitation,
        "h5drm": H5DRMPattern,
        "plain": PlainPattern,
        "multiplesupport": MultipleSupportPattern,
        "multiple_support": MultipleSupportPattern,
    }

    @classmethod
    def register_pattern_type(cls, name: str, pattern_class):
        """Register a concrete pattern class by name.

        Args:
            name: Case-insensitive pattern type key.
            pattern_class: Class used by :meth:`create_pattern`.
        """
        cls._pattern_types[name.lower()] = pattern_class

    @classmethod
    def get_pattern_types(cls):
        """Return the registered pattern type names."""
        return list(cls._pattern_types.keys())

    @classmethod
    def create_pattern(cls, pattern_type: str, **kwargs):
        """Create an unmanaged pattern by registered type name.

        Args:
            pattern_type: Case-insensitive pattern type key.
            **kwargs: Constructor arguments for the selected pattern class.

        Returns:
            Unmanaged pattern instance.

        Raises:
            KeyError: If ``pattern_type`` is not registered.
        """
        key = pattern_type.lower()
        if key not in cls._pattern_types:
            raise KeyError(f"Pattern type {pattern_type} not registered")
        return cls._pattern_types[key](**kwargs)


__all__ = [
    "Pattern",
    "PatternManager",
    "PatternRegistry",
    "UniformExcitation",
    "H5DRMPattern",
    "PlainPattern",
    "ImposedMotion",
    "MultipleSupportPattern",
]
