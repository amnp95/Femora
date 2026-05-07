from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class ConstantTimeSeries(TimeSeries):
    """OpenSees ``Constant`` time series.

    Tcl form:
        ``timeSeries Constant <tag> -factor <factor>``
    """

    def __init__(self, factor: float = 1.0):
        """Create a constant time series.

        Args:
            factor: Constant scale factor applied for the whole analysis.

        Raises:
            ValueError: If ``factor`` cannot be converted to ``float``.
        """
        super().__init__("Constant")
        self.factor = as_float(factor, "factor")

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        return f"timeSeries Constant {self._require_tag()} -factor {self.factor}"
