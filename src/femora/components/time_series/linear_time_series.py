from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class LinearTimeSeries(TimeSeries):
    """OpenSees ``Linear`` time series.

    Tcl form:
        ``timeSeries Linear <tag> -factor <factor>``
    """

    def __init__(self, factor: float = 1.0):
        """Create a linearly varying time series.

        Args:
            factor: Scale factor applied to pseudo-time.

        Raises:
            ValueError: If ``factor`` cannot be converted to ``float``.
        """
        super().__init__("Linear")
        self.factor = as_float(factor, "factor")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        return f"timeSeries Linear {self._require_tag()} -factor {self.factor}"
