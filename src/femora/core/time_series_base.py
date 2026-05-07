from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TimeSeries(ABC):
    """Abstract base class for OpenSees time series.

    Time series instances do not self-register. A TimeSeriesManager owns tags,
    lookup, removal, and retagging for a local model context.

    Args:
        series_type: OpenSees time series type name, such as ``Constant`` or
            ``Path``.

    Attributes:
        tag: Manager-assigned OpenSees tag. It remains ``None`` until the
            instance is added to a :class:`TimeSeriesManager`.
        series_type: OpenSees time series type name used by concrete classes.
    """

    def __init__(self, series_type: str):
        self.tag: Optional[int] = None
        self.series_type = series_type

    def _require_tag(self) -> int:
        """Return the assigned tag or fail if the instance is unmanaged.

        Concrete ``to_tcl`` implementations call this so an unmanaged object
        fails early instead of rendering an invalid OpenSees command.

        Returns:
            The manager-assigned integer tag.

        Raises:
            ValueError: If this time series has not been added to a manager.
        """
        if self.tag is None:
            raise ValueError("TimeSeries must be managed before rendering TCL")
        return self.tag

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees ``timeSeries`` command.

        Returns:
            TCL command string for this time series.
        """
        raise NotImplementedError
