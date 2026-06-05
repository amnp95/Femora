I'll review the target file and related project structure, then return the properly formatted docstrings.

Let me examine the base classes to understand the context:

Now I understand the context. The docstrings in the target file are already very well-formatted and compliant with the style guide. Let me verify the file is complete and properly formatted, then return it:

The docstrings in `plain_pattern.py` are already comprehensive and compliant with the Femora style guide. All classes and methods have complete docstrings with:

- **PlainPattern**: Complete class docstring with summary, description, Tcl form, note, and example
- **__init__**: Proper Args and Raises sections
- **All methods**: Complete docstrings documenting behavior, parameters, returns, and exceptions
- **_AddLoadProxy**: Inner class with full documentation and example
- **add_load property**: Complete property docstring
- **__doc_controls__**: Intentional member selection for the API page

Here is the final, valid Python code:

```python
from __future__ import annotations

from typing import List

from femora.core.load_base import Load
from femora.core.load_manager import LoadManager
from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class PlainPattern(Pattern):
    """OpenSees Plain load pattern with attached load entities.

    A plain load pattern is used to apply static or dynamic forces (nodal loads,
    element loads, single-point constraints) proportional to a specified time series.

    Tcl form:
        ``pattern Plain <patternTag> <timeSeriesTag> [-fact <factor>] { <loads...> }``

    Note:
        - Plain patterns are standard load patterns that contain nodal loads (`load`), element loads (`eleLoad`), and single-point constraints (`sp`).
        - Nodal or element loads must be associated with the plain pattern's tag to be evaluated under its time series.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.constant(factor=2.0)
        pattern = model.pattern.plain(time_series=ts)
        print(pattern.tag)

        # Add a nodal load using the pattern load factory proxy
        node_load = pattern.add_load.node(node_tag=1, dof=1, value=10.0)
        print(node_load.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [
            "__init__",
            "add_load_instance",
            "remove_load",
            "clear_loads",
            "get_loads",
            "add_load",
        ],
    }

    def __init__(self, time_series: TimeSeries, factor: float = 1.0):
        """Create a plain load pattern.

        Args:
            time_series: Managed TimeSeries object referenced by this pattern.
            factor: Optional scale factor applied to all loads in this pattern.

        Raises:
            ValueError: If time_series is invalid or unmanaged.
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
        """Attach an existing load instance to this pattern.

        If the load is already attached to this pattern, this method does nothing.

        Args:
            load: Load instance to emit inside the pattern block.

        Raises:
            ValueError: If load is not a Load instance.
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
            load: Attached Load instance to remove.
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
        """Return the loads currently attached to this pattern.

        Returns:
            List[Load]: A list of Load instances attached to this pattern.
        """
        return list(self._loads)

    def to_tcl(self) -> str:
        """Render this pattern and its attached loads as an OpenSees Tcl block.

        Returns:
            str: OpenSees Tcl command block for this pattern and its loads.
        """
        fact = f" -fact {self.factor}" if self.factor != 1.0 else ""
        lines = [f"pattern Plain {self._require_tag()} {self.time_series.tag}{fact} {{"]
        for load in self._loads:
            lines.append(f"\t{load.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    class _AddLoadProxy:
        """Factory proxy for creating and attaching loads to a PlainPattern.

        This proxy provides convenient methods to create various types of loads
        (e.g., nodal, element, single-point) and automatically associates/attaches
        them to the owning PlainPattern instance.

        Example:
            ```python
            from femora.core.model import Model

            model = Model()
            ts = model.time_series.constant(factor=1.0)
            pattern = model.pattern.plain(time_series=ts)

            # Use the proxy to create and attach a nodal load
            nodal_load = pattern.add_load.node(node_tag=1, dof=1, value=50.0)
            ```
        """

        def __init__(self, pattern: "PlainPattern"):
            """Create a proxy for the given plain pattern.

            Args:
                pattern: The PlainPattern instance to which loads will be attached.
            """
            self._pattern = pattern

        def _load_manager(self) -> LoadManager:
            """Return the active load manager for the model.

            Returns:
                LoadManager: The active LoadManager instance of the model.

            Raises:
                ValueError: If the pattern is not managed.
            """
            pattern_owner = self._pattern._owner
            if pattern_owner is None:
                raise ValueError("Pattern must be managed before adding loads")
            return pattern_owner._mesh_maker.load

        def node(self, **kwargs) -> Load:
            """Create a nodal load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to the active LoadManager's node factory method.

            Returns:
                Load: The created and attached nodal Load instance.
            """
            load = self._load_manager().node(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def element(self, **kwargs) -> Load:
            """Create an element load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to the active LoadManager's element factory method.

            Returns:
                Load: The created and attached element Load instance.
            """
            load = self._load_manager().element(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def sp(self, **kwargs) -> Load:
            """Create a single-point load constraint and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to the active LoadManager's sp factory method.

            Returns:
                Load: The created and attached single-point Load instance.
            """
            load = self._load_manager().sp(**kwargs)
            self._pattern.add_load_instance(load)
            return load

    @property
    def add_load(self) -> "PlainPattern._AddLoadProxy":
        """Return a proxy for creating loads directly on this pattern.

        This property provides a convenient factory interface to create and
        automatically associate various types of loads (node, element, sp)
        with this PlainPattern instance.

        Returns:
            PlainPattern._AddLoadProxy: An instance of `_AddLoadProxy` for creating and attaching loads.
        """
        return PlainPattern._AddLoadProxy(self)
```
