from __future__ import annotations

from typing import List

from femora.components.load.load_base import Load, LoadManager
from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class PlainPattern(Pattern):
    """OpenSees ``Plain`` load pattern with attached loads.

    A plain pattern references one managed ``TimeSeries`` and owns a collection
    of loads that render inside the pattern block.

    Tcl form:
        ``pattern Plain <patternTag> <timeSeriesTag> [-fact factor] { ... }``
    """

    def __init__(self, time_series: TimeSeries, factor: float = 1.0):
        """Create a plain load pattern.

        Args:
            time_series: Managed ``TimeSeries`` referenced by this pattern.
            factor: Optional scale factor applied to contained loads.

        Raises:
            ValueError: If ``time_series`` is invalid or unmanaged.
        """
        super().__init__("Plain")
        if not isinstance(time_series, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        if time_series.tag is None:
            raise ValueError("time_series must be managed before it is used by a pattern")
        self.time_series = time_series
        self.factor = float(factor)
        self._loads: List[Load] = []

    def add_load_instance(self, load: Load) -> None:
        """Attach an existing load to this pattern.

        Args:
            load: Load instance to emit inside the pattern block.

        Raises:
            ValueError: If ``load`` is not a ``Load`` instance.
        """
        if not isinstance(load, Load):
            raise ValueError("load must be an instance of Load")
        if load in self._loads:
            return
        load.pattern_tag = self.tag
        self._loads.append(load)

    def remove_load(self, load: Load) -> None:
        """Detach a load from this pattern if it is currently attached.

        Args:
            load: Load instance to remove.
        """
        if load in self._loads:
            self._loads.remove(load)
            load.pattern_tag = None

    def clear_loads(self) -> None:
        """Detach all loads from this pattern."""
        for load in self._loads:
            load.pattern_tag = None
        self._loads.clear()

    def get_loads(self) -> List[Load]:
        """Return a copy of the loads attached to this pattern."""
        return list(self._loads)

    def to_tcl(self) -> str:
        """Render this pattern and its attached loads as an OpenSees TCL block."""
        fact = f" -fact {self.factor}" if self.factor != 1.0 else ""
        lines = [f"pattern Plain {self._require_tag()} {self.time_series.tag}{fact} {{"]
        for load in self._loads:
            lines.append(f"\t{load.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    class _AddLoadProxy:
        """Factory proxy that creates loads and attaches them to this pattern."""

        def __init__(self, pattern: "PlainPattern"):
            """Create a proxy for ``pattern``."""
            self._pattern = pattern
            self._manager = LoadManager()

        def node(self, **kwargs) -> Load:
            """Create a nodal load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.node``.

            Returns:
                Created and attached load instance.
            """
            load = self._manager.node(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def element(self, **kwargs) -> Load:
            """Create an element load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.element``.

            Returns:
                Created and attached load instance.
            """
            load = self._manager.element(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def ele(self, **kwargs) -> Load:
            """Alias for :meth:`element`."""
            return self.element(**kwargs)

        def sp(self, **kwargs) -> Load:
            """Create a single-point load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.sp``.

            Returns:
                Created and attached load instance.
            """
            load = self._manager.sp(**kwargs)
            self._pattern.add_load_instance(load)
            return load

    @property
    def add_load(self) -> "PlainPattern._AddLoadProxy":
        """Return a proxy for creating loads directly on this pattern."""
        return PlainPattern._AddLoadProxy(self)
