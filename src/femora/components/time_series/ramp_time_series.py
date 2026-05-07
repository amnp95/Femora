from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class RampTimeSeries(TimeSeries):
    """OpenSees ``Ramp`` time series.

    Tcl form:
        ``timeSeries Ramp <tag> <tStart> <tRamp> -smooth <smoothness>
        -offset <offset> -factor <cFactor>``
    """

    def __init__(
        self,
        tStart: float = 0.0,
        tRamp: float = 1.0,
        smoothness: float = 0.0,
        offset: float = 0.0,
        cFactor: float = 1.0,
    ):
        """Create a ramp time series.

        Args:
            tStart: Start time of the ramp.
            tRamp: Duration of the ramp.
            smoothness: Smoothness parameter in the inclusive range ``[0, 1]``.
            offset: Vertical offset.
            cFactor: Scale factor.

        Raises:
            ValueError: If numeric arguments are invalid or ``smoothness`` is
                outside ``[0, 1]``.
        """
        super().__init__("Ramp")
        self.tStart = as_float(tStart, "tStart")
        self.tRamp = as_float(tRamp, "tRamp")
        self.smoothness = as_float(smoothness, "smoothness")
        self.offset = as_float(offset, "offset")
        self.cFactor = as_float(cFactor, "cFactor")
        if not 0 <= self.smoothness <= 1:
            raise ValueError("smoothness must be between 0 and 1")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        return (
            f"timeSeries Ramp {self._require_tag()} {self.tStart} {self.tRamp}"
            f" -smooth {self.smoothness} -offset {self.offset} -factor {self.cFactor}"
        )
