from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union, Any

from .load_base import Load, LoadRegistry


class ElementLoad(Load):
    """Represents an elemental load for OpenSees' `eleLoad` command.

    This class provides a wrapper for defining and managing elemental loads
    on beam elements, supporting uniform and point load distributions
    in 2D or 3D. It allows targeting elements via explicit tags, ranges,
    or an `ElementMask`.

    Supported forms:
        - 2D uniform: `-type -beamUniform Wy [Wx]`
        - 3D uniform: `-type -beamUniform Wy Wz [Wx]`
        - 2D point:   `-type -beamPoint   Py xL [Px]`
        - 3D point:   `-type -beamPoint   Py Pz xL [Px]`

    Selection:
        Provide either `ele_tags` (explicit tag list), `ele_range` (start,end),
        or an :class:`ElementMask` (preferred). With a mask, TCL is emitted on
        tag level via `ElementMask.to_tags()`, while `pid` is inferred from the
        first element's core unless explicitly set.

    Attributes:
        kind (str): The type of load, either `'beamUniform'` or `'beamPoint'`.
        ele_tags (Optional[List[int]]): Explicit list of element tags to apply
            the load to. Mutually exclusive with `ele_range` and `element_mask`.
        ele_range (Optional[Tuple[int, int]]): A tuple `(start, end)` defining
            a range of element tags to apply the load to. Mutually exclusive
            with `ele_tags` and `element_mask`.
        params (Dict[str, float]): Numeric parameters for the load, varying
            by `kind` and dimension (e.g., `{'Wy': 10.0, 'Wx': 5.0}`).
        pid (Optional[int]): The core ID to emit the load for. Defaults to 0
            if not explicitly set and `element_mask` is not used.
        element_mask: Optional `ElementMask` object to dynamically select
            multiple elements. Mutually exclusive with `ele_tags` and
            `ele_range`.

    Example:
        >>> import femora as fm
        >>> from femora.components.load.element_load import ElementLoad
        >>> # Create a uniform beam load
        >>> uniform_load = ElementLoad(
        ...     kind="beamUniform",
        ...     ele_tags=[1, 2, 3],
        ...     params={"Wy": -10.0}
        ... )
        >>> print(uniform_load.to_tcl())
        eleLoad -ele 1 2 3 -type -beamUniform -10.0
        >>> # Create a point load on a range of elements
        >>> point_load = ElementLoad(
        ...     kind="beamPoint",
        ...     ele_range=(10, 12),
        ...     params={"Py": -50.0, "xL": 0.5}
        ... )
        >>> print(point_load.to_tcl())
        eleLoad -range 10 12 -type -beamPoint -50.0 0.5
    """

    def __init__(self, **kwargs):
        """Initializes an ElementLoad instance.

        The elemental load can be a uniform or point load, defined for specific
        elements or a range, and with particular parameters.

        Args:
            **kwargs: Keyword arguments for defining the load.
                Refer to :meth:`validate` for supported arguments and their types.
                Common arguments include:
                - `kind` (str): `'beamUniform'` or `'beamPoint'`.
                - `ele_tags` (list[int]): List of element tags.
                - `ele_range` (tuple[int, int]): Start and end element tags.
                - `element_mask` (`ElementMask`): Object to dynamically select elements.
                - `params` (dict[str, float]): Numeric parameters for the load.
                - `pid` (int): Processor ID.

        Raises:
            ValueError: If any provided arguments are missing or invalid
                during validation.
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
        """Returns metadata about the parameters for ElementLoad.

        This method provides a list of tuples, where each tuple contains
        a parameter name and its description. This is typically used for
        UI generation or inspection.

        Returns:
            List[tuple]: A list of `(name, description)` tuples for
                each parameter.

        Example:
            >>> from femora.components.load.element_load import ElementLoad
            >>> params_meta = ElementLoad.get_parameters()
            >>> print(params_meta[0])
            ('kind', "Load kind: 'beamUniform' or 'beamPoint'")
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
        """Returns a serializable dictionary of the current load's state.

        This dictionary contains all the relevant properties of the load,
        suitable for serialization or inspection.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple, dict]]:
                A dictionary representing the current state of the load.

        Example:
            >>> from femora.components.load.element_load import ElementLoad
            >>> load = ElementLoad(kind="beamUniform", ele_tags=[1], params={"Wy": -10.0})
            >>> values = load.get_values()
            >>> print(values["kind"])
            beamUniform
            >>> print(values["params"]["Wy"])
            -10.0
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
        """Ensures a value is numeric and converts it to a float.

        Args:
            name: The name of the parameter being checked, used in error messages.
            value: The value to be converted to a float.

        Returns:
            float: The numeric representation of the value.

        Raises:
            ValueError: If the value cannot be converted to a float.
        """
        try:
            return float(value)
        except Exception:
            raise ValueError(f"{name} must be numeric")

    @staticmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """Validates and normalizes constructor/update parameters for ElementLoad.

        This method processes the input keyword arguments, performs type
        and value checks, and returns a dictionary of normalized values.
        It ensures that mutual exclusivity rules for element selection
        (`ele_tags`, `ele_range`, `element_mask`) are respected and that
        all required numeric parameters for the specified `kind` are present.

        Args:
            **kwargs: Supported keys:
                - `kind` (str): Must be `'beamUniform'` or `'beamPoint'`.
                - `ele_tags` (list[int]): A non-empty list of positive integers.
                - `ele_range` (Tuple[int, int]): A tuple `(start, end)` of positive
                  integers where `end >= start`.
                - `element_mask` (`ElementMask`): An instance of `ElementMask`.
                - `params` (Dict[str, float]): A dictionary of numeric values.
                  Required keys vary by `kind` (e.g., `Wy` for uniform, `Py` and `xL`
                  for point loads).
                - `pid` (int): An optional integer core ID.

        Returns:
            Dict[str, Any]: A dictionary containing the validated and
                normalized parameters.

        Raises:
            ValueError: If any parameter is missing, has an invalid type,
                or violates a rule (e.g., mutual exclusivity or value range).

        Example:
            >>> from femora.components.load.element_load import ElementLoad
            >>> # Valid uniform load
            >>> valid_uniform_params = ElementLoad.validate(
            ...     kind="beamUniform", ele_tags=[1, 2], params={"Wy": -5.0}
            ... )
            >>> print(valid_uniform_params["kind"])
            beamUniform
            >>> # Invalid load due to missing parameter
            >>> try:
            ...     ElementLoad.validate(kind="beamPoint", ele_range=(1,1), params={"Py": -10.0})
            ... except ValueError as e:
            ...     print(e)
            params.Py and params.xL are required for beamPoint
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
        """Updates the elemental load's parameters after validation.

        This method allows modifying the load's properties. All provided
        keyword arguments are validated using :meth:`validate` before
        applying the changes.

        Args:
            **kwargs: Same keys and validation rules as for the
                :meth:`validate` method.

        Example:
            >>> from femora.components.load.element_load import ElementLoad
            >>> load = ElementLoad(kind="beamUniform", ele_tags=[1], params={"Wy": -10.0})
            >>> print(load.to_tcl())
            eleLoad -ele 1 -type -beamUniform -10.0
            >>> load.update_values(params={"Wy": -20.0, "Wz": -5.0})
            >>> print(load.to_tcl())
            eleLoad -ele 1 -type -beamUniform -20.0 -5.0
            >>> load.update_values(ele_range=(10, 15), kind="beamPoint", params={"Py": -30.0, "xL": 0.25})
            >>> print(load.to_tcl())
            eleLoad -range 10 15 -type -beamPoint -30.0 0.25
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
        """Generates the TCL element selector string.

        This helper method creates either an `-ele` or `-range` selector
        based on the `ele_tags` or `ele_range` attributes.

        Returns:
            str: The TCL string representing the element selection.
        """
        if self.ele_tags is not None:
            tags_str = " ".join(str(e) for e in self.ele_tags)
            return f"-ele {tags_str}"
        assert self.ele_range is not None
        i, j = self.ele_range
        return f"-range {i} {j}"

    def to_tcl(self) -> str:
        """Converts the element load definition to its OpenSees TCL command(s).

        This method constructs the `eleLoad` command string based on the
        configured load `kind`, selection method (`ele_tags`, `ele_range`,
        or `element_mask`), and numeric parameters.
        If an `element_mask` is provided, it builds an `-ele` selector
        using element tags derived from the mask.
        The `pid` (core ID) is inferred from the first element's core
        if `element_mask` is used and `pid` is not explicitly set.

        Returns:
            str: The TCL command string for the element load. If `pid` is set
                or inferred, the command will be wrapped in an `if {$pid == X}`
                block.

        Example:
            >>> from femora.components.load.element_load import ElementLoad
            >>> # Uniform load on specific elements
            >>> uniform_load = ElementLoad(
            ...     kind="beamUniform",
            ...     ele_tags=[1, 2],
            ...     params={"Wy": -10.0, "Wx": 5.0}
            ... )
            >>> print(uniform_load.to_tcl())
            eleLoad -ele 1 2 -type -beamUniform -10.0 5.0
            >>> # Point load on a range with processor ID
            >>> point_load = ElementLoad(
            ...     kind="beamPoint",
            ...     ele_range=(5, 7),
            ...     params={"Py": -100.0, "xL": 0.75, "Pz": -20.0},
            ...     pid=1
            ... )
            >>> print(point_load.to_tcl())
            if {$pid == 1} { eleLoad -range 5 7 -type -beamPoint -100.0 -20.0 0.75 }
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