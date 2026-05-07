from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union

from femora.components.time_series import (
    ConstantTimeSeries,
    LinearTimeSeries,
    PathTimeSeries,
    PulseTimeSeries,
    RampTimeSeries,
    RectangularTimeSeries,
    TriangularTimeSeries,
    TrigTimeSeries,
)
from femora.core.time_series_base import TimeSeries


class TimeSeriesManager:
    """Local manager for ``TimeSeries`` lifecycle and tag assignment.

    The manager is intentionally not a singleton. Each instance owns an
    independent tag space so future model or ``MeshMaker`` instances can keep
    their own time-series collections.
    """

    def __init__(self):
        """Create an empty manager with tags starting at ``1``."""
        self._time_series: Dict[int, TimeSeries] = {}
        self._start_tag = 1

    def add(self, time_series: TimeSeries) -> TimeSeries:
        """Add an existing time series and assign a tag if needed.

        Args:
            time_series: Unmanaged or already-managed ``TimeSeries`` instance.

        Returns:
            The same ``time_series`` instance after it is stored by this manager.

        Raises:
            TypeError: If ``time_series`` is not a ``TimeSeries`` instance.
            ValueError: If its preassigned tag conflicts with a different
                object already managed here.
        """
        if not isinstance(time_series, TimeSeries):
            raise TypeError("time_series must be a TimeSeries instance")
        if time_series.tag is None:
            time_series.tag = self._next_available_tag()
        elif time_series.tag in self._time_series and self._time_series[time_series.tag] is not time_series:
            raise ValueError(f"TimeSeries tag {time_series.tag} already exists")
        self._time_series[time_series.tag] = time_series
        return time_series

    def get(self, tag: int) -> Optional[TimeSeries]:
        """Return the time series with ``tag`` if it exists.

        Args:
            tag: Time-series tag to look up.

        Returns:
            The matching ``TimeSeries`` instance, or ``None``.
        """
        return self._time_series.get(tag)

    __len__ = lambda self: len(self._time_series)

    __iter__ = lambda self: iter(self._time_series.values())


    def get_all(self) -> Dict[int, TimeSeries]:
        """Return a shallow copy of all managed time series keyed by tag."""
        return dict(self._time_series)

    def remove(self, tag: int) -> None:
        """Remove a managed time series and compact the remaining tags.

        Args:
            tag: Tag of the time series to remove. Missing tags are ignored.
        """
        time_series = self._time_series.pop(tag, None)
        if time_series is not None:
            time_series.tag = None
            self._reassign_tags()

    def clear(self) -> None:
        """Remove all time series and clear their assigned tags."""
        for time_series in self._time_series.values():
            time_series.tag = None
        self._time_series.clear()

    def set_tag_start(self, start_tag: int) -> None:
        """Set the first tag used by this manager and retag existing objects.

        Args:
            start_tag: Positive integer for the first assigned tag.

        Raises:
            ValueError: If ``start_tag`` is less than ``1``.
        """
        start_tag = int(start_tag)
        if start_tag < 1:
            raise ValueError("start_tag must be a positive integer")
        self._start_tag = start_tag
        self._reassign_tags()

    def constant(self, factor: float = 1.0) -> ConstantTimeSeries:
        """Create and manage a ``ConstantTimeSeries``.

        Args:
            factor: Constant scale factor.

        Returns:
            Managed ``ConstantTimeSeries`` instance.
        """
        return self.add(ConstantTimeSeries(factor=factor))  # type: ignore[return-value]

    def linear(self, factor: float = 1.0) -> LinearTimeSeries:
        """Create and manage a ``LinearTimeSeries``.

        Args:
            factor: Linear scale factor.

        Returns:
            Managed ``LinearTimeSeries`` instance.
        """
        return self.add(LinearTimeSeries(factor=factor))  # type: ignore[return-value]

    def trig(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ) -> TrigTimeSeries:
        """Create and manage a ``TrigTimeSeries``.

        Args:
            tStart: Start time of the trigonometric series.
            tEnd: End time of the trigonometric series.
            period: Period of the sinusoidal cycle.
            factor: Load factor amplitude.
            shift: Phase shift.

        Returns:
            Managed ``TrigTimeSeries`` instance.
        """
        return self.add(TrigTimeSeries(tStart, tEnd, period, factor, shift))  # type: ignore[return-value]

    def ramp(
        self,
        tStart: float = 0.0,
        tRamp: float = 1.0,
        smoothness: float = 0.0,
        offset: float = 0.0,
        cFactor: float = 1.0,
    ) -> RampTimeSeries:
        """Create and manage a ``RampTimeSeries``.

        Args:
            tStart: Start time of the ramp.
            tRamp: Duration of the ramp.
            smoothness: Smoothness value between ``0`` and ``1``.
            offset: Vertical offset.
            cFactor: Load factor scale.

        Returns:
            Managed ``RampTimeSeries`` instance.
        """
        return self.add(RampTimeSeries(tStart, tRamp, smoothness, offset, cFactor))  # type: ignore[return-value]

    def triangular(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ) -> TriangularTimeSeries:
        """Create and manage a ``TriangularTimeSeries``.

        Args:
            tStart: Start time of the triangular wave.
            tEnd: End time of the triangular wave.
            period: Wave period.
            factor: Load factor amplitude.
            shift: Phase shift.

        Returns:
            Managed ``TriangularTimeSeries`` instance.
        """
        return self.add(TriangularTimeSeries(tStart, tEnd, period, factor, shift))  # type: ignore[return-value]

    def rectangular(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        factor: float = 1.0,
        shift: float = 0.0,
    ) -> RectangularTimeSeries:
        """Create and manage a ``RectangularTimeSeries``.

        Args:
            tStart: Start time of the rectangular wave.
            tEnd: End time of the rectangular wave.
            period: Wave period.
            factor: Load factor amplitude.
            shift: Phase shift.

        Returns:
            Managed ``RectangularTimeSeries`` instance.
        """
        return self.add(RectangularTimeSeries(tStart, tEnd, period, factor, shift))  # type: ignore[return-value]

    def pulse(
        self,
        tStart: float = 0.0,
        tEnd: float = 1.0,
        period: float = 1.0,
        width: float = 0.5,
        factor: float = 1.0,
        shift: float = 0.0,
    ) -> PulseTimeSeries:
        """Create and manage a ``PulseTimeSeries``.

        Args:
            tStart: Start time of the pulse series.
            tEnd: End time of the pulse series.
            period: Pulse period.
            width: Pulse width as a fraction of the period.
            factor: Load factor amplitude.
            shift: Phase shift.

        Returns:
            Managed ``PulseTimeSeries`` instance.
        """
        return self.add(PulseTimeSeries(tStart, tEnd, period, width, factor, shift))  # type: ignore[return-value]

    def path(
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
    ) -> PathTimeSeries:
        """Create and manage a ``PathTimeSeries``.

        Args:
            dt: Constant time step. Mutually exclusive with ``time`` and
                ``fileTime``.
            values: Inline path values as a sequence or comma-separated string.
                Mutually exclusive with ``filePath``.
            filePath: File containing path values. Mutually exclusive with
                ``values``.
            factor: Scale factor applied to the path values.
            useLast: Whether OpenSees should hold the last value after the path
                ends.
            prependZero: Whether OpenSees should prepend a zero value.
            startTime: Time offset for the path.
            time: Inline time values. Mutually exclusive with ``dt`` and
                ``fileTime``.
            fileTime: File containing time values. Mutually exclusive with
                ``dt`` and ``time``.

        Returns:
            Managed ``PathTimeSeries`` instance.
        """
        return self.add(
            PathTimeSeries(
                dt=dt,
                values=values,
                filePath=filePath,
                factor=factor,
                useLast=useLast,
                prependZero=prependZero,
                startTime=startTime,
                time=time,
                fileTime=fileTime,
            )
        )  # type: ignore[return-value]

    def create_time_series(self, series_type: str, **kwargs) -> TimeSeries:
        """Create and manage a time series by type name.

        This compatibility factory delegates to the explicit factory methods
        such as :meth:`constant`, :meth:`linear`, and :meth:`path`.

        Args:
            series_type: Case-insensitive time-series type name.
            **kwargs: Constructor arguments for the selected concrete class.

        Returns:
            Managed ``TimeSeries`` instance.

        Raises:
            KeyError: If ``series_type`` is not registered.
        """
        factories = {
            "constant": self.constant,
            "linear": self.linear,
            "trig": self.trig,
            "ramp": self.ramp,
            "triangular": self.triangular,
            "rectangular": self.rectangular,
            "pulse": self.pulse,
            "path": self.path,
        }
        key = series_type.lower()
        if key not in factories:
            raise KeyError(f"TimeSeries type {series_type} not registered")
        return factories[key](**kwargs)

    get_time_series = get
    remove_time_series = remove
    get_all_time_series = get_all

    def _next_available_tag(self) -> int:
        """Return the next unused tag in this manager's local tag space."""
        tag = self._start_tag
        while tag in self._time_series:
            tag += 1
        return tag

    def _reassign_tags(self) -> None:
        """Retag all managed time series from ``_start_tag`` in tag order."""
        items: List[TimeSeries] = sorted(
            self._time_series.values(),
            key=lambda item: item.tag if item.tag is not None else 0,
        )
        self._time_series.clear()
        for offset, time_series in enumerate(items):
            time_series.tag = self._start_tag + offset
            self._time_series[time_series.tag] = time_series
