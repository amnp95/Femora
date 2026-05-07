from __future__ import annotations

from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class UniformExcitation(Pattern):
    """OpenSees ``UniformExcitation`` pattern.

    Uniform excitation applies one managed acceleration time series to the
    selected global DOF direction. OpenSees reports nodal responses relative to
    this support motion for this pattern type.

    Tcl form:
        ``pattern UniformExcitation <tag> <dof> -accel <tsTag>
        [-vel0 vel0] [-fact factor]``
    """

    def __init__(
        self,
        dof: int,
        time_series: TimeSeries,
        vel0: float = 0.0,
        factor: float = 1.0,
    ):
        """Create a uniform excitation pattern.

        Args:
            dof: 1-based excitation direction.
            time_series: Managed acceleration ``TimeSeries``.
            vel0: Initial velocity.
            factor: Scale factor applied to the acceleration series.

        Raises:
            ValueError: If ``dof`` is invalid, ``time_series`` is not a
                ``TimeSeries``, or ``time_series`` has not been managed.
        """
        super().__init__("UniformExcitation")
        try:
            self.dof = int(dof)
        except Exception:
            raise ValueError("dof must be an integer")
        if self.dof < 1:
            raise ValueError("dof must be a positive integer")
        if not isinstance(time_series, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        if time_series.tag is None:
            raise ValueError("time_series must be managed before it is used by a pattern")
        self.time_series = time_series
        self.vel0 = float(vel0)
        self.factor = float(factor)

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees TCL command."""
        cmd = f"pattern UniformExcitation {self._require_tag()} {self.dof} -accel {self.time_series.tag}"
        if self.vel0 != 0.0:
            cmd += f" -vel0 {self.vel0}"
        if self.factor != 1.0:
            cmd += f" -fact {self.factor}"
        return cmd
