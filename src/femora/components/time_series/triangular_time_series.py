I’ll align the docstrings to the Femora style and quickly verify the real manager usage path for triangular time series examples before editing.

I found the manager entry point and will read that section to make the class example accurate.

I’ve updated the docstrings and now I’m running the project tests to ensure everything remains clean.

from __future__ import annotations

from femora.components.time_series._helpers import as_float
from femora.core.time_series_base import TimeSeries


class TriangularTimeSeries(TimeSeries):
    """Represent a triangular-wave OpenSees time series.

    This time series generates a periodic triangular signal between ``tStart``
    and ``tEnd`` with optional amplitude scaling and phase shifting.

    Tcl form:
        ``timeSeries Triangular <tag> <tStart> <tEnd> <period>
        -factor <factor> -shift <shift>``

    Attributes:
        tag: Manager-assigned identifier after this instance is added to
            ``model.timeSeries``.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        ts = model.timeSeries.triangular(
            tStart=0.0,
            tEnd=10.0,
            period=1.0,
            factor=2.0,
            shift=0.25,
        )
        print(ts.tag)
        ```
    """

    def __init__(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ):
        """Create a triangular-wave time series with validated inputs.

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
        """Render this time series as an OpenSees Tcl command.

        Returns:
            Tcl command string for the ``Triangular`` time series.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        return (
            f"timeSeries Triangular {self._require_tag()} "
            f"{self.tStart} {self.tEnd} {self.period} "
            f"-factor {self.factor} -shift {self.shift}"
        )
