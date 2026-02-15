from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union, Any

from .load_base import Load, LoadRegistry


class ElementLoad(Load):
    """Represents an elemental load for OpenSees' `eleLoad` command.

    This class provides a flexible interface to define uniform or point loads
    applied to beam elements, supporting both 2D and 3D forms. It allows
    selection of target elements via explicit tags, a range of tags, or
    an :class:`ElementMask` for more complex selections.

    Attributes:
        kind (str): The type of load, either `'beamUniform'` or `'beamPoint'`.
        ele_tags (Optional[List[int]]): Explicit list of element tags to apply
            the load to. Mutually exclusive with `ele_range` and `element_mask`.
        ele_range (Optional[Tuple[int, int]]): A tuple `(start, end)`
            representing a range of element tags to apply the load to. Mutually
            exclusive with `ele_tags` and `element_mask`.
        params (Dict[str, float]): A dictionary holding the numeric parameters
            of the load, which vary based on `kind` and dimension (e.g., 'Wy',
            'Wz', 'Wx' for uniform loads; 'Py', 'Pz', 'Px', 'xL' for point loads).
        pid (Optional[int]): The ID of the core (process) to which this load
            should be emitted. Defaults to 0 if not explicitly set and
            `element_mask` is not used. If `element_mask` is used, the pid is
            inferred from the first element's core unless overridden.
        element_mask: Optional :class:`ElementMask` object to dynamically select
            multiple elements. This is the preferred method for complex selections.

    Example:
        >>> from femora.loads.element_load import ElementLoad
        >>> # Define a uniform beam load in 2D
        >>> uniform_load = ElementLoad(
        ...     kind="beamUniform",
        ...     ele_range=(1, 5),
        ...     params={"Wy": -10.0}
        ... )
        >>> print(uniform_load.to_tcl())
        eleLoad -range 1 5 -type -beamUniform -10.0
        >>> # Define a point load on a single element
        >>> point_load = ElementLoad(
        ...     kind="beamPoint",
        ...     ele_tags=[10],
        ...     params={"Py": -5.0, "xL": 0.5}
        ... )
        >>> print(point_load.to_tcl())
        eleLoad -ele 10 -type -beamPoint -5.0 0.5
    """

    def __init__(self, **kwargs):
        """Initializes an ElementLoad object.

        Args:
            kind: The type of load, either `'beamUniform'` or `'beamPoint'`.
            ele_tags: Optional. A list of element tags for the load. Mutually
                exclusive with `ele_range` and `element_mask`.
            ele_range: Optional. A tuple `(start, end)` defining a range of
                element tags. Mutually exclusive with `ele_tags` and `element_mask`.
            params: A dictionary of numeric parameters specific to the load `kind`.
                For `beamUniform`, keys can be `Wy`, `Wz`, `Wx`. For `beamPoint`,
                keys can be `Py`, `Pz`, `Px`, `xL`.
            pid: Optional. The core ID (process) to emit this load for. If not
                provided, defaults to 0.
            element_mask: Optional. An :class:`ElementMask` instance to select
                target elements dynamically. Mutually exclusive with `ele_tags`
                and `ele_range`.

        Raises:
            ValueError: If validation of input parameters fails.
        """
        super().__init__("ElementLoad")
        v = self.validate(**kwargs)
        self.kind: str = v["kind"]
        self.ele_tags: Optional[List[int]] = v.get("ele_tags")
        self.ele_range: Optional[Tuple[int, int]] = v.get("ele_range")
        # numeric args, vary by kind/dimension; store generically
        self.params: Dict[str, float] = v["params"]
        # Single pid (core) for elements
        self.pid: Optional[int] = v.get("pid")
        # Optional ElementMask
        self.element_mask = v.get("element_mask")

    @staticmethod
    def get_parameters() -> List[tuple]:
        """Returns metadata about the load's parameters for UI or inspection.

        This method provides a list of tuples, where each tuple contains the
        parameter's name and a short description.

        Returns:
            List[tuple]: A list of `(name, description)` tuples for each
                configurable parameter of the load.

        Example:
            >>> from femora.loads.element_load import ElementLoad
            >>> params_info = ElementLoad.get_parameters()
            >>> for name, desc in params_info:
            ...     print(f"- {name}: {desc}")
            - kind: Load kind: 'beamUniform' or 'beamPoint'
            - ele_tags: Explicit element tags list (mutually exclusive with ele_range)
            - ele_range: Tuple (start, end) element tag range (mutually exclusive with ele_tags)
            - params: Dictionary of numeric parameters per kind/dimension
            - pid: Optional core id (int) for which to emit this load
            - element_mask: Optional ElementMask to expand into multiple elements
        """
        return [
            ("kind", "Load kind: 'beamUniform' or 'beamPoint'"),
            ("ele_tags", "Explicit element tags list (mutually exclusive with ele_range)"),
            ("ele_range", "Tuple (start, end) element tag range (mutually exclusive with ele_tags)"),
            ("params", "Dictionary of numeric parameters per kind/dimension"),
            ("pid", "Optional core id (int) for which to emit this load"),
            ("element_mask", "Optional ElementMask to expand into multiple elements"),
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, bool, list, tuple, dict]]:
        """Returns a serializable dictionary of the current load state.

        This method is useful for persisting the load definition or for
        debugging. The output dictionary contains all essential properties
        of the element load.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple, dict]]: A
                dictionary representing the current state of the load.

        Example:
            >>> from femora.loads.element_load import ElementLoad
            >>> load = ElementLoad(
            ...     kind="beamUniform",
            ...     ele_tags=[1, 2, 3],
            ...     params={"Wy": -5.0}
            ... )
            >>> values = load.get_values()
            >>> print(values["kind"])
            beamUniform
            >>> print(values["ele_tags"])
            [1, 2, 3]
            >>> print(values["params"]["Wy"])
            -5.0
        """
        return {
            "kind": self.kind,
            "ele_tags": list(self.ele_tags) if self.ele_tags is not None else None,
            "ele_range": tuple(self.ele_range) if self.ele_range is not None else None,
            "params": dict(self.params),
            "pid": self.pid,
            "element_mask": self.element_mask,
            "pattern_tag": self.pattern_tag,
        }

    @staticmethod
    def _require_numeric(name: str, value: Any) -> float:
        """Converts a value to a float or raises a ValueError.

        Args:
            name: The name of the parameter being converted, used in error messages.
            value: The value to attempt conversion for.

        Returns:
            float: The numeric representation of the input value.

        Raises:
            ValueError: If the `value` cannot be converted to a float.
        """
        try:
            return float(value)
        except Exception:
            raise ValueError(f"{name} must be numeric")

    @staticmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """Validates and normalizes constructor/update parameters for ElementLoad.

        This static method ensures that all input parameters are correctly
        formatted and logically consistent before being assigned to an
        `ElementLoad` instance. It handles type conversion and mutual
        exclusivity checks.

        Args:
            **kwargs: Keyword arguments containing the load parameters.
                Supported keys include: `kind`, `ele_tags`,
                `ele_range`, `element_mask`, `params`, `pid`.

        Returns:
            Dict[str, Any]: A dictionary of normalized and validated parameter
                values, ready for object instantiation or update.

        Raises:
            ValueError: On missing, invalid, or mutually exclusive parameters.

        Example:
            >>> from femora.loads.element_load import ElementLoad
            >>> valid_params = ElementLoad.validate(
            ...     kind="beamUniform",
            ...     ele_range=(1, 10),
            ...     params={"Wy": -2.5, "Wx": 0.5},
            ...     pid=1
            ... )
            >>> print(valid_params["kind"])
            beamUniform
            >>> print(valid_params["ele_range"])
            (1, 10)
            >>> print(valid_params["params"]["Wy"])
            -2.5
            >>> # Example of invalid input
            >>> try:
            ...     ElementLoad.validate(kind="invalid_kind")
            ... except ValueError as e:
            ...     print(e)
            kind must be 'beamUniform' or 'beamPoint'
        """
        if "kind" not in kwargs:
            raise ValueError("kind must be provided: 'beamUniform' or 'beamPoint'")
        kind = str(kwargs["kind"]).strip()
        if kind not in ("beamUniform", "beamPoint"):
            raise ValueError("kind must be 'beamUniform' or 'beamPoint'")

        ele_tags = kwargs.get("ele_tags")
        ele_range = kwargs.get("ele_range")
        element_mask = kwargs.get("element_mask")
        if element_mask is not None:
            try:
                from femora.components.mask.mask_base import ElementMask as _ElementMask
            except Exception:
                _ElementMask = None  # type: ignore
            if _ElementMask is not None and not isinstance(element_mask, _ElementMask):
                raise ValueError("element_mask must be an ElementMask")

        if element_mask is None:
            if (ele_tags is None and ele_range is None) or (ele_tags is not None and ele_range is not None):
                raise ValueError("Provide either ele_tags or ele_range or element_mask")
        if ele_tags is not None:
            if not isinstance(ele_tags, (list, tuple)) or len(ele_tags) == 0:
                raise ValueError("ele_tags must be a non-empty list/tuple of ints")
            try:
                ele_tags = [int(e) for e in ele_tags]
            except Exception:
                raise ValueError("ele_tags must be integers")
            if any(e < 1 for e in ele_tags):
                raise ValueError("ele_tags must be positive integers")
        if ele_range is not None:
            if not (isinstance(ele_range, (list, tuple)) and len(ele_range) == 2):
                raise ValueError("ele_range must be a tuple/list of (start, end)")
            try:
                i, j = int(ele_range[0]), int(ele_range[1])
            except Exception:
                raise ValueError("ele_range bounds must be integers")
            if i < 1 or j < 1 or j < i:
                raise ValueError("ele_range must be positive and end >= start")
            ele_range = (i, j)

        params_in = kwargs.get("params", {})
        if not isinstance(params_in, dict):
            raise ValueError("params must be a dictionary of numeric values")

        params: Dict[str, float] = {}
        if kind == "beamUniform":
            # 2D: Wy[, Wx]; 3D: Wy, Wz[, Wx]
            if "Wy" not in params_in:
                raise ValueError("params.Wy is required for beamUniform")
            params["Wy"] = ElementLoad._require_numeric("Wy", params_in["Wy"])
            if "Wz" in params_in:
                params["Wz"] = ElementLoad._require_numeric("Wz", params_in["Wz"])
            if "Wx" in params_in:
                params["Wx"] = ElementLoad._require_numeric("Wx", params_in["Wx"])
        else:  # beamPoint
            # 2D: Py, xL[, Px]; 3D: Py, Pz, xL[, Px]
            if "Py" not in params_in or "xL" not in params_in:
                raise ValueError("params.Py and params.xL are required for beamPoint")
            params["Py"] = ElementLoad._require_numeric("Py", params_in["Py"])
            params["xL"] = ElementLoad._require_numeric("xL", params_in["xL"])
            if "Pz" in params_in:
                params["Pz"] = ElementLoad._require_numeric("Pz", params_in["Pz"])
            if "Px" in params_in:
                params["Px"] = ElementLoad._require_numeric("Px", params_in["Px"])

        out: Dict[str, Any] = {"kind": kind, "params": params}
        if ele_tags is not None:
            out["ele_tags"] = ele_tags
        if ele_range is not None:
            out["ele_range"] = ele_range
        if element_mask is not None:
            out["element_mask"] = element_mask
        if "pid" in kwargs and kwargs["pid"] is not None:
            try:
                out["pid"] = int(kwargs["pid"])
            except Exception:
                raise ValueError("pid must be an integer")
        else:
            out["pid"] = 0
        return out

    def update_values(self, **kwargs) -> None:
        """Updates the current load's properties after validation.

        This method allows modifying the existing `ElementLoad` instance with
        new parameters. The input `kwargs` are validated using
        :meth:`ElementLoad.validate` to ensure data integrity.

        Args:
            **kwargs: The parameters to update. Accepts the same keys as
                :meth:`ElementLoad.validate`, such as `kind`, `ele_tags`,
                `ele_range`, `params`, `pid`, and `element_mask`.

        Example:
            >>> from femora.loads.element_load import ElementLoad
            >>> load = ElementLoad(
            ...     kind="beamUniform",
            ...     ele_tags=[1, 2],
            ...     params={"Wy": -10.0}
            ... )
            >>> print(load.to_tcl())
            eleLoad -ele 1 2 -type -beamUniform -10.0
            >>> load.update_values(
            ...     ele_range=(3, 5),
            ...     params={"Wy": -15.0, "Wz": -5.0}
            ... )
            >>> print(load.to_tcl())
            eleLoad -range 3 5 -type -beamUniform -15.0 -5.0
        """
        v = self.validate(
            kind=kwargs.get("kind", self.kind),
            ele_tags=kwargs.get("ele_tags", self.ele_tags),
            ele_range=kwargs.get("ele_range", self.ele_range),
            params=kwargs.get("params", self.params),
            pid=kwargs.get("pid", self.pid),
            element_mask=kwargs.get("element_mask", self.element_mask),
        )
        self.kind = v["kind"]
        self.ele_tags = v.get("ele_tags")
        self.ele_range = v.get("ele_range")
        self.params = v["params"]
        self.pid = v.get("pid")
        self.element_mask = v.get("element_mask")

    def _selector_tcl(self) -> str:
        """Generates the TCL element selector string for `ele_tags` or `ele_range`.

        This is an internal helper method used by `to_tcl` to construct the
        appropriate `-ele` or `-range` argument for the OpenSees command.

        Returns:
            str: The TCL string representing the element selection (e.g., `-ele 1 2 3` or `-range 1 5`).
        """
        if self.ele_tags is not None:
            tags_str = " ".join(str(e) for e in self.ele_tags)
            return f"-ele {tags_str}"
        assert self.ele_range is not None
        i, j = self.ele_range
        return f"-range {i} {j}"

    def to_tcl(self) -> str:
        """Converts the element load definition into its equivalent TCL command(s).

        This method constructs the OpenSees `eleLoad` command string based on
        the current properties of the `ElementLoad` instance. If an
        `element_mask` is provided, it generates an `-ele` selector from the
        mask's tags. The process ID (pid) is automatically inferred from the
        first element's core if `element_mask` is used and `pid` is not
        explicitly set, otherwise it defaults to 0.

        Returns:
            str: The full TCL command string(s) for the `eleLoad` command.
                If `pid` is set or inferred, the command is wrapped in an
                `if {$pid == X}` block.

        Example:
            >>> from femora.loads.element_load import ElementLoad
            >>> # Uniform load on a range of elements
            >>> load_uniform = ElementLoad(
            ...     kind="beamUniform",
            ...     ele_range=(1, 5),
            ...     params={"Wy": -10.0}
            ... )
            >>> print(load_uniform.to_tcl())
            eleLoad -range 1 5 -type -beamUniform -10.0
            >>> # Point load on specific elements with 3D parameters
            >>> load_point = ElementLoad(
            ...     kind="beamPoint",
            ...     ele_tags=[10, 11],
            ...     params={"Py": -5.0, "Pz": -2.0, "xL": 0.75}
            ... )
            >>> print(load_point.to_tcl())
            eleLoad -ele 10 11 -type -beamPoint -5.0 -2.0 0.75
            >>> # Load with a specific PID (core)
            >>> load_pid = ElementLoad(
            ...     kind="beamUniform",
            ...     ele_tags=[20],
            ...     params={"Wy": -20.0},
            ...     pid=1
            ... )
            >>> print(load_pid.to_tcl())
            if {$pid == 1} { eleLoad -ele 20 -type -beamUniform -20.0 }
        """
        if self.element_mask is not None:
            ids = self.element_mask.to_list()
            tags = self.element_mask.to_tags()
            # Build -ele selector for these tags
            sel = "-ele " + " ".join(str(t) for t in tags)
        else:
            sel = self._selector_tcl()
        if self.kind == "beamUniform":
            parts: List[str] = ["eleLoad", sel, "-type", "-beamUniform"]
            # Order: Wy [Wz] [Wx] with optional presence
            if "Wy" in self.params:
                parts.append(str(self.params["Wy"]))
            if "Wz" in self.params:
                parts.append(str(self.params["Wz"]))
            if "Wx" in self.params:
                parts.append(str(self.params["Wx"]))
            cmd = " ".join(parts)
        else:
            parts = ["eleLoad", sel, "-type", "-beamPoint"]
            # Order: Py [Pz] xL [Px]
            parts.append(str(self.params["Py"]))
            if "Pz" in self.params:
                parts.append(str(self.params["Pz"]))
            parts.append(str(self.params["xL"]))
            if "Px" in self.params:
                parts.append(str(self.params["Px"]))
            cmd = " ".join(parts)

        # If mask provided, try to derive pid from first element's core
        pid = self.pid
        if self.element_mask is not None and hasattr(self.element_mask._mesh, 'element_id_to_index'):
            mesh = self.element_mask._mesh  # type: ignore[attr-defined]
            if ids:
                first = int(ids[0])
                if first in mesh.element_id_to_index:
                    pid = int(mesh.core_ids[mesh.element_id_to_index[first]])

        if pid is not None:
            return f"if {{$pid == {pid}}} {{ {cmd} }}"
        return cmd


# Register type
LoadRegistry.register_load_type("element", ElementLoad)
LoadRegistry.register_load_type("eleload", ElementLoad)