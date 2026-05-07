"""Concrete OpenSees time-series implementations.

Base classes and managers live in :mod:`femora.core`; this package contains
only concrete ``TimeSeries`` subclasses.
"""

from .constant_time_series import ConstantTimeSeries
from .linear_time_series import LinearTimeSeries
from .trig_time_series import TrigTimeSeries
from .ramp_time_series import RampTimeSeries
from .triangular_time_series import TriangularTimeSeries
from .rectangular_time_series import RectangularTimeSeries
from .pulse_time_series import PulseTimeSeries
from .path_time_series import PathTimeSeries

__all__ = [
    "ConstantTimeSeries",
    "LinearTimeSeries",
    "TrigTimeSeries",
    "RampTimeSeries",
    "TriangularTimeSeries",
    "RectangularTimeSeries",
    "PulseTimeSeries",
    "PathTimeSeries",
]
