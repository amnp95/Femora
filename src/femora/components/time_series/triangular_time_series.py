from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class TriangularTimeSeries(TimeSeries):
    """OpenSees ``Triangular`` time series.

    Tcl form:
        ``timeSeries Triangular <tag> <tStart> <tEnd> <period>
        -factor <factor> -shift <shift>``
    """

    def __init__(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a triangular wave time series.

        Args:
            tStart: Start time of the wave.
            tEnd: End time of the wave.
            period: Wave period.
            factor: Load factor amplitude.
            shift: Phase shift.

        Raises:
            ValueError: If numeric arguments are invalid, ``tStart >= tEnd``,
                or ``period <= 0``.
        """
        super().__init__("Triangular")
        self.tStart = as_float(tStart, "tStart")
        self.tEnd = as_float(tEnd, "tEnd")
        self.period = as_float(period, "period")
        self.factor = as_float(factor, "factor")
        self.shift = as_float(shift, "shift")
        if self.tStart >= self.tEnd:
            raise ValueError("tStart must be less than tEnd")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        return (
            f"timeSeries Triangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-factor {self.factor} -shift {self.shift}"
        )
