from __future__ import annotations

from typing import List

from femora.core.ground_motion_base import GroundMotion


class InterpolatedGroundMotion(GroundMotion):
    """OpenSees ``Interpolated`` ground motion.

    An interpolated ground motion combines previously managed ground motions
    using a list of interpolation factors. The referenced ground motions must
    already have manager-assigned tags before this object can render Tcl,
    because OpenSees references them by tag inside the interpolation command.

    Tags are not assigned by this class; create instances through
    ``GroundMotionManager.interpolated(...)`` or add them to a manager before
    calling ``to_tcl()``.

    Tcl form:
        ``groundMotion <tag> Interpolated <gmTag1> <gmTag2> ... -fact
        <factor1> <factor2> ...``
    """

    def __init__(
        self,
        ground_motions: List[GroundMotion],
        factors: List[float],
    ):
        """Create an interpolated ground motion.

        Args:
            ground_motions: Ground motions to combine. Each item must be a
                ``GroundMotion`` instance.
            factors: Interpolation factors. Must have the same length as
                ``ground_motions``.

        Raises:
            ValueError: If the ground-motion list is empty, contains invalid
                objects, the factors list is empty, lengths differ, or factors
                are not numeric.
        """
        super().__init__("Interpolated")

        if not isinstance(ground_motions, (list, tuple)) or not ground_motions:
            raise ValueError("ground_motions must be a non-empty list or tuple")
        if not all(isinstance(gm, GroundMotion) for gm in ground_motions):
            raise ValueError("ground_motions must contain GroundMotion objects")
        if not isinstance(factors, (list, tuple)) or not factors:
            raise ValueError("factors must be a non-empty list or tuple")
        if len(factors) != len(ground_motions):
            raise ValueError("factors must have the same length as ground_motions")

        try:
            factor_values = [float(value) for value in factors]
        except Exception:
            raise ValueError("factors must be numeric")

        self.ground_motions = list(ground_motions)
        self.factors = factor_values

    def to_tcl(self) -> str:
        """Render the OpenSees ``groundMotion`` Tcl command.

        Returns:
            A Tcl command for this interpolated ground motion.

        Raises:
            ValueError: If this ground motion or any referenced ground motion
                has not been added to a manager and therefore has no tag.
        """
        gm_tags = []
        for gm in self.ground_motions:
            if gm.tag is None:
                raise ValueError("Interpolated ground motions must be managed before rendering TCL")
            gm_tags.append(str(gm.tag))
        factors = " ".join(map(str, self.factors))
        return f"groundMotion {self._require_tag()} Interpolated {' '.join(gm_tags)} -fact {factors}"
