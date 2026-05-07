"""Compatibility imports for the old TimeSeries module path."""

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
from femora.core.time_series_manager import TimeSeriesManager

__all__ = [
    "TimeSeries",
    "TimeSeriesManager",
    "ConstantTimeSeries",
    "LinearTimeSeries",
    "TrigTimeSeries",
    "RampTimeSeries",
    "TriangularTimeSeries",
    "RectangularTimeSeries",
    "PulseTimeSeries",
    "PathTimeSeries",
]
