from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class GroundMotion(ABC):
    """Base class for OpenSees ground motions.

    Ground motions do not self-register. A ``GroundMotionManager`` owns tags and
    lifecycle so base classes stay focused on behavior.
    """

    def __init__(self, motion_type: str):
        self.tag: Optional[int] = None
        self.motion_type = motion_type

    def _require_tag(self) -> int:
        if self.tag is None:
            raise ValueError(
                "GroundMotion has no tag. Create it through GroundMotionManager "
                "or add it to the manager before rendering TCL."
            )
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees groundMotion command."""
        raise NotImplementedError
