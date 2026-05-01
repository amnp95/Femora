from __future__ import annotations

from typing import List

from femora.core.ground_motion_base import GroundMotion


class InterpolatedGroundMotion(GroundMotion):
    """OpenSees Interpolated ground motion."""

    def __init__(
        self,
        ground_motions: List[GroundMotion],
        factors: List[float],
    ):
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
        gm_tags = []
        for gm in self.ground_motions:
            if gm.tag is None:
                raise ValueError("Interpolated ground motions must be managed before rendering TCL")
            gm_tags.append(str(gm.tag))
        factors = " ".join(map(str, self.factors))
        return f"groundMotion {self._require_tag()} Interpolated {' '.join(gm_tags)} -fact {factors}"
