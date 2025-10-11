from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union, Any

from .load_base import Load, LoadRegistry


class ElementLoad(Load):
    """
    Elemental load wrapper for the OpenSees ``eleLoad`` command.

    Supported forms:
        - 2D uniform: ``-type -beamUniform Wy [Wx]``
        - 3D uniform: ``-type -beamUniform Wy Wz [Wx]``
        - 2D point:   ``-type -beamPoint   Py xL [Px]``
        - 3D point:   ``-type -beamPoint   Py Pz xL [Px]``

    Selection:
        Provide either ``ele_tags`` (explicit tag list), ``ele_range`` (start,end),
        or an :class:`ElementMask` (preferred). With a mask, TCL is emitted on
        tag level via ``ElementMask.to_tags()``, while pid is inferred from the
        first element's core unless explicitly set.

    Attributes:
        kind (str): Either ``'beamUniform'`` or ``'beamPoint'``.
        ele_tags (Optional[List[int]]): Explicit element tags.
        ele_range (Optional[Tuple[int,int]]): Range of element tags.
        params (Dict[str,float]): Numeric parameters per form/dimension.
        pid (Optional[int]): Core to emit for; defaults to 0 if not set.
        element_mask: Optional :class:`ElementMask` to target multiple elements.
    """

    def __init__(self, **kwargs):
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
        """
        Parameters metadata for UI/inspection.

        Returns:
            List[tuple]: Tuples of (name, description).
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
        """
        Return a serializable dictionary of the current load state.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple, dict]]
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
        try:
            return float(value)
        except Exception:
            raise ValueError(f"{name} must be numeric")

    @staticmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """
        Validate constructor/update parameters for ElementLoad.

        Args:
            **kwargs: Supported keys: ``kind`` (str), ``ele_tags`` (list[int]),
                ``ele_range`` (Tuple[int,int]), ``element_mask`` (ElementMask),
                ``params`` (Dict[str,float]), ``pid`` (int).

        Returns:
            Dict[str, Any]: Normalized values.

        Raises:
            ValueError: On missing or invalid parameters.
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
        """
        Update the load's values after validation.

        Args:
            **kwargs: Same keys as :meth:`validate`.
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
        if self.ele_tags is not None:
            tags_str = " ".join(str(e) for e in self.ele_tags)
            return f"-ele {tags_str}"
        assert self.ele_range is not None
        i, j = self.ele_range
        return f"-range {i} {j}"

    def to_tcl(self) -> str:
        """
        Convert the element load to its TCL command(s).

        With ``element_mask``, builds an ``-ele`` selector using element tags.
        pid is inferred from the first element's core unless explicitly set.

        Returns:
            str: TCL command string.
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


