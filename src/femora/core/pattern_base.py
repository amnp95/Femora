from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Pattern(ABC):
    """Abstract base class for OpenSees load/excitation patterns.

    Pattern instances do not self-register. A :class:`PatternManager` owns tag
    assignment and lifecycle operations for a local model context.

    Args:
        pattern_type: OpenSees pattern type name, such as ``Plain``,
            ``UniformExcitation``, or ``MultipleSupport``.

    Attributes:
        tag: Manager-assigned OpenSees load-pattern tag. It remains ``None``
            until the instance is added to a manager.
        pattern_type: OpenSees pattern type name used by concrete classes.
    """

    def __init__(self, pattern_type: str):
        self.tag: Optional[int] = None
        self.pattern_type = pattern_type

    def _require_tag(self) -> int:
        """Return the assigned tag or fail if the instance is unmanaged.

        Returns:
            The manager-assigned integer tag.

        Raises:
            ValueError: If this pattern has not been added to a manager.
        """
        if self.tag is None:
            raise ValueError("Pattern must be managed before rendering TCL")
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees ``pattern`` command.

        Returns:
            TCL command string or TCL block for this pattern.
        """
        raise NotImplementedError
