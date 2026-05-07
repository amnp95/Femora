from __future__ import annotations

from typing import Optional, Sequence, Union

from femora.components.time_series._helpers import as_bool, as_float, parse_float_list
from femora.core.time_series_base import TimeSeries


class PathTimeSeries(TimeSeries):
    """OpenSees ``Path`` time series.

    A path series can read values from a file or from inline values. Time can be
    defined by a constant ``dt``, inline time values, or a time file.

    Tcl form:
        ``timeSeries Path <tag> <-dt dt | -time {...} | -fileTime file>
        <-values {...} | -filePath file> [options...]``
    """

    def __init__(
        self,
        dt: Optional[float] = None,
        values: Optional[Union[str, Sequence[float]]] = None,
        filePath: Optional[str] = None,
        factor: float = 1.0,
        useLast: bool = False,
        prependZero: bool = False,
        startTime: float = 0.0,
        time: Optional[Union[str, Sequence[float]]] = None,
        fileTime: Optional[str] = None,
    ):
        """Create a path time series.

        Args:
            dt: Constant time step. Mutually exclusive with ``time`` and
                ``fileTime``.
            values: Inline force/acceleration values as a sequence or
                comma-separated string. Mutually exclusive with ``filePath``.
            filePath: File containing path values. Mutually exclusive with
                ``values``.
            factor: Scale factor applied to values.
            useLast: Whether OpenSees should hold the final value after the
                path ends.
            prependZero: Whether OpenSees should prepend a zero value.
            startTime: Start time offset.
            time: Inline time values. Mutually exclusive with ``dt`` and
                ``fileTime``.
            fileTime: File containing time values. Mutually exclusive with
                ``dt`` and ``time``.

        Raises:
            ValueError: If exactly one value source and exactly one time source
                are not provided, or if supplied values are invalid.
        """
        super().__init__("Path")

        sources = sum(item is not None for item in (values, filePath))
        if sources != 1:
            raise ValueError("Exactly one of values or filePath must be provided")

        time_sources = sum(item is not None for item in (dt, time, fileTime))
        if time_sources != 1:
            raise ValueError("Exactly one of dt, time or fileTime must be provided")

        self.dt = None if dt is None else as_float(dt, "dt")
        if self.dt is not None and self.dt <= 0:
            raise ValueError("dt must be greater than 0")

        self.values = parse_float_list(values, "values")
        self.filePath = None if filePath is None else str(filePath)
        self.factor = as_float(factor, "factor")
        self.useLast = as_bool(useLast, "useLast")
        self.prependZero = as_bool(prependZero, "prependZero")
        self.startTime = as_float(startTime, "startTime")
        self.time = parse_float_list(time, "time")
        self.fileTime = None if fileTime is None else str(fileTime)

    def to_tcl(self) -> str:
        """Render this time series as an OpenSees TCL command."""
        cmd = f"timeSeries Path {self._require_tag()}"
        if self.dt is not None:
            cmd += f" -dt {self.dt}"
        if self.filePath is not None:
            cmd += f" -filePath {self.filePath}"
        elif self.values is not None:
            cmd += f" -values {{{' '.join(map(str, self.values))}}}"
        if self.time is not None:
            cmd += f" -time {{{' '.join(map(str, self.time))}}}"
        if self.fileTime is not None:
            cmd += f" -fileTime {self.fileTime}"
        if self.factor != 1.0:
            cmd += f" -factor {self.factor}"
        if self.useLast:
            cmd += " -useLast"
        if self.prependZero:
            cmd += " -prependZero"
        if self.startTime != 0.0:
            cmd += f" -startTime {self.startTime}"
        return cmd
