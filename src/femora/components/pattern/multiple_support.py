from __future__ import annotations

from typing import List

from femora.core.ground_motion_base import GroundMotion
from femora.core.pattern_base import Pattern


class ImposedMotion:
    """OpenSees ``imposedMotion`` entry for a ``MultipleSupport`` pattern.

    Tcl form:
        ``imposedMotion <nodeTag> <dof> <groundMotionTag>``
    """

    def __init__(self, node_tag: int, dof: int, ground_motion: GroundMotion):
        """Create an imposed support motion constraint.

        Args:
            node_tag: Node tag where the motion is imposed.
            dof: 1-based DOF direction.
            ground_motion: Managed ground motion used as the prescribed motion.

        Raises:
            ValueError: If ``node_tag`` or ``dof`` is invalid, or if
                ``ground_motion`` is not managed.
        """
        try:
            self.node_tag = int(node_tag)
            self.dof = int(dof)
        except Exception:
            raise ValueError("node_tag and dof must be integers")
        if self.node_tag < 1:
            raise ValueError("node_tag must be a positive integer")
        if self.dof < 1:
            raise ValueError("dof must be a positive integer")
        if not isinstance(ground_motion, GroundMotion):
            raise ValueError("ground_motion must be a GroundMotion object")
        if ground_motion.tag is None:
            raise ValueError("ground_motion must be managed before it is used by imposedMotion")
        self.ground_motion = ground_motion

    def to_tcl(self) -> str:
        """Render this imposed motion as an OpenSees TCL command."""
        if self.ground_motion.tag is None:
            raise ValueError("ground_motion must have a tag before rendering imposedMotion")
        return f"imposedMotion {self.node_tag} {self.dof} {self.ground_motion.tag}"


class MultipleSupportPattern(Pattern):
    """OpenSees ``MultipleSupport`` excitation pattern.

    The pattern emits referenced ground-motion definitions followed by the
    imposed-motion constraints that use them. Referenced ground motions are
    deduplicated by tag and dependencies of interpolated ground motions are
    emitted before the interpolated motion itself.

    Tcl form:
        ``pattern MultipleSupport <patternTag> { groundMotion... imposedMotion... }``
    """

    def __init__(self):
        """Create an empty multiple-support excitation pattern."""
        super().__init__("MultipleSupport")
        self._imposed_motions: List[ImposedMotion] = []

    def add_imposed_motion(
        self,
        node_tag: int,
        dof: int,
        ground_motion: GroundMotion,
    ) -> ImposedMotion:
        """Create and attach an imposed motion to this pattern.

        Args:
            node_tag: Node tag where the motion is imposed.
            dof: 1-based DOF direction.
            ground_motion: Managed ground motion used as the prescribed motion.

        Returns:
            Created ``ImposedMotion`` instance.
        """
        imposed_motion = ImposedMotion(node_tag, dof, ground_motion)
        self._imposed_motions.append(imposed_motion)
        return imposed_motion

    def get_imposed_motions(self) -> List[ImposedMotion]:
        """Return a copy of imposed motions attached to this pattern."""
        return list(self._imposed_motions)

    def clear_imposed_motions(self) -> None:
        """Remove all imposed motions from this pattern."""
        self._imposed_motions.clear()

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees TCL block."""
        lines = [f"pattern MultipleSupport {self._require_tag()} {{"]
        for ground_motion in self._referenced_ground_motions():
            lines.append(f"\t{ground_motion.to_tcl()}")
        for imposed_motion in self._imposed_motions:
            lines.append(f"\t{imposed_motion.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    def _referenced_ground_motions(self) -> List[GroundMotion]:
        """Return referenced ground motions in dependency-safe render order."""
        ordered: List[GroundMotion] = []
        seen: set[int] = set()

        def visit(ground_motion: GroundMotion) -> None:
            if ground_motion.tag is None:
                raise ValueError("Referenced ground motions must be managed before rendering TCL")
            for dependency in getattr(ground_motion, "ground_motions", []):
                visit(dependency)
            if ground_motion.tag not in seen:
                seen.add(ground_motion.tag)
                ordered.append(ground_motion)

        for imposed_motion in self._imposed_motions:
            visit(imposed_motion.ground_motion)
        return ordered
