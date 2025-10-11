from __future__ import annotations

from typing import Dict, List, Union, Any, Optional

from .load_base import Load, LoadRegistry


class SpLoad(Load):
    """
    Single-point constraint wrapper for the OpenSees ``sp`` command.

    TCL form::

        sp <nodeTag> <dof> <value>

    Supports a single ``node_tag`` or a :class:`NodeMask` to expand across
    multiple nodes. When a mask is used, tags are obtained via
    ``NodeMask.to_tags()`` and pids are derived per node from the mesh.

    Attributes:
        node_tag (Optional[int]): Target node tag for a single node.
        dof (int): 1-based DOF index.
        value (float): Prescribed value.
        pids (List[int]): Optional cores; defaults to ``[0]`` and is overridden
            per node when a mask is provided.
        node_mask: Optional :class:`NodeMask` to target multiple nodes.
    """

    def __init__(self, **kwargs):
        super().__init__("SpLoad")
        v = self.validate(**kwargs)
        self.node_tag: Optional[int] = v.get("node_tag")
        self.dof: int = v["dof"]
        self.value: float = v["value"]
        # Optional list of pids (cores) where this sp applies
        self.pids: List[int] = v.get("pids", [])
        # Optional NodeMask
        self.node_mask = v.get("node_mask")

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Parameters metadata for UI/inspection.

        Returns:
            List[tuple]: Tuples of (name, description).
        """
        return [
            ("node_tag", "Tag of the node (optional if node_mask provided)"),
            ("dof", "Degree of freedom index (1-based)"),
            ("value", "Prescribed value"),
            ("pids", "Optional list of core ids (ints) where to emit this sp"),
            ("node_mask", "Optional NodeMask to expand into multiple nodes"),
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, bool, list, tuple]]:
        """
        Return a serializable dictionary of the current load state.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple]]
        """
        return {
            "node_tag": self.node_tag,
            "dof": self.dof,
            "value": self.value,
            "pids": list(self.pids),
            "node_mask": self.node_mask,
            "pattern_tag": self.pattern_tag,
        }

    @staticmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """
        Validate constructor/update parameters for SpLoad.

        Args:
            **kwargs: Supported keys: ``node_tag`` (int), ``node_mask`` (NodeMask),
                ``dof`` (int 1-based), ``value`` (float), ``pids`` (list[int]).

        Returns:
            Dict[str, Any]: Normalized values.

        Raises:
            ValueError: On missing or invalid parameters.
        """
        node_tag = None
        node_mask = None
        if "node_mask" in kwargs and kwargs["node_mask"] is not None:
            node_mask = kwargs["node_mask"]
            try:
                from femora.components.mask.mask_base import NodeMask as _NodeMask
            except Exception:
                _NodeMask = None  # type: ignore
            if _NodeMask is not None and not isinstance(node_mask, _NodeMask):
                raise ValueError("node_mask must be a NodeMask")
        if "node_tag" in kwargs and kwargs["node_tag"] is not None:
            try:
                node_tag = int(kwargs["node_tag"])
                if node_tag < 1:
                    raise ValueError
            except Exception:
                raise ValueError("node_tag must be a positive integer")
        if node_mask is None and node_tag is None:
            raise ValueError("Either node_tag or node_mask must be specified")

        if "dof" not in kwargs:
            raise ValueError("dof must be specified")
        try:
            dof = int(kwargs["dof"])
            if dof < 1:
                raise ValueError
        except Exception:
            raise ValueError("dof must be a positive integer (1-based)")

        if "value" not in kwargs:
            raise ValueError("value must be specified")
        try:
            value = float(kwargs["value"])
        except Exception:
            raise ValueError("value must be numeric")

        out: Dict[str, Any] = {"dof": dof, "value": value}
        if node_tag is not None:
            out["node_tag"] = node_tag
        if node_mask is not None:
            out["node_mask"] = node_mask
        if "pids" in kwargs and kwargs["pids"] is not None:
            p = kwargs["pids"]
            if not isinstance(p, (list, tuple)):
                raise ValueError("pids must be a list/tuple of integers")
            try:
                pids = sorted({int(x) for x in p})
            except Exception:
                raise ValueError("pids must be integers")
            out["pids"] = pids
        else:
            out["pids"] = [0]

        return out

    def update_values(self, **kwargs) -> None:
        """
        Update the load's values after validation.

        Args:
            **kwargs: Same keys as :meth:`validate`.
        """
        v = self.validate(
            node_tag=kwargs.get("node_tag", self.node_tag),
            dof=kwargs.get("dof", self.dof),
            value=kwargs.get("value", self.value),
            pids=kwargs.get("pids", self.pids),
            node_mask=kwargs.get("node_mask", self.node_mask),
        )
        self.node_tag = v.get("node_tag")
        self.dof = v["dof"]
        self.value = v["value"]
        self.pids = v.get("pids", [])
        self.node_mask = v.get("node_mask")

    def to_tcl(self) -> str:
        """
        Convert the sp load to its TCL command(s).

        When ``node_mask`` is provided, emits one ``sp`` line per node tag.
        pids are derived per node from the mesh when available; otherwise uses
        stored ``pids``.

        Returns:
            str: TCL command string (single or multi-line).
        """
        def wrap_with_pid_for_node(nid: int, s: str) -> str:
            pids = self.pids
            if self.node_mask is not None and hasattr(self.node_mask._mesh, 'node_core_map'):
                pids = self.node_mask._mesh.node_core_map[nid] or [0]
            if pids:
                cond = " || ".join(f"($pid == {pid})" for pid in pids)
                return f"if {{{cond}}} {{ {s} }}"
            return s

        if self.node_mask is not None:
            id_list = self.node_mask.to_list()
            tag_list = self.node_mask.to_tags()
            lines: List[str] = []
            for nid, node_tag in zip(id_list, tag_list):
                lines.append(wrap_with_pid_for_node(int(nid), f"sp {int(node_tag)} {self.dof} {self.value}"))
            return "\n".join(lines)
        else:
            cmd = f"sp {self.node_tag} {self.dof} {self.value}"
            return wrap_with_pid_for_node(int(self.node_tag) if self.node_tag is not None else 0, cmd)


# Register type
LoadRegistry.register_load_type("sp", SpLoad)
LoadRegistry.register_load_type("spload", SpLoad)


