from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class PulseTimeSeries(TimeSeries):
    """OpenSees ``Pulse`` time series.

    Tcl form:
        ``timeSeries Pulse <tag> <tStart> <tEnd> <period> -width <width>
        -factor <factor> -shift <shift>``
    """

    def __init__(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        width: float = 0.5,
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a periodic pulse time series.

        Args:
            tStart: Start time of the pulse series.
            tEnd: End time of the pulse series.
            period: Pulse period.
            width: Pulse width as a fraction of the period.
            factor: Load factor amplitude.
            shift: Phase shift.

        Raises:
            ValueError: If numeric arguments are invalid, ``tStart >= tEnd``,
                ``period <= 0``, or ``width`` is not between ``0`` and ``1``.
        """
        super().__init__("Pulse")
        self.tStart = as_float(tStart, "tStart")
        self.tEnd = as_float(tEnd, "tEnd")
        self.period = as_float(period, "period")
        self.width = as_float(width, "width")
        self.factor = as_float(factor, "factor")
        self.shift = as_float(shift, "shift")
        if self.tStart >= self.tEnd:
            raise ValueError("tStart must be less than tEnd")
        if self.period <= 0:
            raise ValueError("period must be greater than 0")
        if not 0 < self.width < 1:
            raise ValueError("width must be between 0 and 1")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        return (
            f"timeSeries Pulse {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} -width {self.width} "
            f"-factor {self.factor} -shift {self.shift}"
        )
