from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class GroundMotion(ABC):
    """Abstract base class for OpenSees ground motions.

    A ground motion defines the displacement, velocity, and/or acceleration
    history used by OpenSees imposed-motion constraints. Concrete subclasses
    are responsible for validating their own physical parameters and rendering
    the corresponding ``groundMotion`` Tcl command.

    Ground motions intentionally do not self-register and do not assign their
    own tags. A :class:`femora.core.ground_motion_manager.GroundMotionManager`
    owns instance storage, tag assignment, retagging, and deletion. This keeps
    the base class independent from any particular model and allows separate
    managers, such as future separate ``MeshMaker`` instances, to maintain
    independent ground-motion collections.

    Attributes:
        tag: OpenSees ground-motion tag assigned by a ``GroundMotionManager``.
            It is ``None`` until the instance is added to a manager.
        motion_type: OpenSees ground-motion type name, such as ``"Plain"`` or
            ``"Interpolated"``.
    """

    def __init__(self, motion_type: str):
        """Initialize common ground-motion state.

        Args:
            motion_type: OpenSees ground-motion type name used by subclasses.
        """
        self.tag: Optional[int] = None
        self.motion_type = motion_type

    def _require_tag(self) -> int:
        """Return this ground motion's tag or fail if unmanaged.

        Returns:
            The integer tag assigned by a ``GroundMotionManager``.

        Raises:
            ValueError: If the ground motion has not been added to a manager.
        """
        if self.tag is None:
            raise ValueError(
                "GroundMotion has no tag. Create it through GroundMotionManager "
                "or add it to the manager before rendering TCL."
            )
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees ``groundMotion`` command.

        Subclasses should call ``_require_tag()`` before rendering so unmanaged
        ground motions fail clearly instead of emitting invalid Tcl.
        """
        raise NotImplementedError
