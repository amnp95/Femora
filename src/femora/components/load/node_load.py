from __future__ import annotations

from typing import Dict, List, Union, Any, Optional

from .load_base import Load, LoadRegistry


class NodeLoad(Load):
    """Nodal load wrapper for the OpenSees ``load`` command.

    This class supports either a single ``node_tag`` or a :class:`NodeMask`
    to expand to multiple nodes. When a mask is provided, TCL is emitted
    on tag level via ``NodeMask.to_tags()``, while DOF padding/truncation
    and pid derivation use mask IDs and mesh metadata.

    The TCL form is::

        load <nodeTag> <values...>

    Attributes:
        node_tag (Optional[int]): Target node tag when applying to a single node.
        values (List[float]): Reference load vector; padded/truncated to each
            node's DOF when using masks.
        pids (List[int]): Optional list of core IDs. Defaults to ``[0]`` when
            not set; overridden by mask-derived pids if a mask is supplied.
        node_mask: Optional :class:`NodeMask` to target multiple nodes.

    Example:
        >>> import femora as fm
        >>> load = fm.NodeLoad(node_tag=10, values=[1.0, -2.0, 0.0])
        >>> print(load.node_tag)
        10
        >>> print(load.values)
        [1.0, -2.0, 0.0]
    """

    def __init__(self, **kwargs):
        """Initializes a NodeLoad.

        Args:
            node_tag: Optional integer tag of the target node. Either `node_tag`
                or `node_mask` must be provided.
            values: A list of float values for each degree of freedom. This
                list will be padded or truncated based on the node's DOF
                when using a mask.
            pids: Optional list of core IDs (integers) where this load
                participates. Defaults to `[0]` if not specified.
            node_mask: Optional :class:`NodeMask` instance to apply the load
                to multiple nodes. Either `node_tag` or `node_mask` must be
                provided.

        Raises:
            ValueError: If required parameters are missing or invalid, as
                determined by :meth:`validate`.
        """
        super().__init__("NodeLoad")
        validated = self.validate(**kwargs)
        self.node_tag: Optional[int] = validated.get("node_tag")
        self.values: List[float] = validated["values"]
        # Optional list of pids (cores) where this node participates
        self.pids: List[int] = validated.get("pids", [])
        # Optional mask of nodes
        self.node_mask = validated.get("node_mask")

    @staticmethod
    def get_parameters() -> List[tuple]:
        """Return parameters metadata for UI/inspection.

        Returns:
            list[tuple]: Tuples of (name, description).
        """
        return [
            ("node_tag", "Tag of node on which the loads act (optional if node_mask provided)"),
            ("values", "List of load values for each DOF"),
            ("pids", "Optional list of core ids (ints) where to emit this load"),
            ("node_mask", "Optional NodeMask to expand into multiple nodes"),
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, bool, list, tuple]]:
        """Return a serializable dictionary of the current load state.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple]]: A dictionary
                representing the current state of the load, including its node
                tag, values, PIDs, node mask, and pattern tag.
        """
        return {
            "node_tag": self.node_tag,
            "values": list(self.values),
            "pids": list(self.pids),
            "node_mask": self.node_mask,
            "pattern_tag": self.pattern_tag,
        }

    @staticmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """Validate constructor/update parameters for NodeLoad.

        Args:
            node_tag: The integer tag of the target node.
            node_mask: A :class:`NodeMask` instance to apply the load to
                multiple nodes.
            values: A list of float values for each degree of freedom.
            pids: A list of integers representing the core IDs where this
                load participates.

        Returns:
            Dict[str, Any]: A dictionary containing the normalized and
                validated parameters.

        Raises:
            ValueError: If any required parameters are missing or if any
                parameters have invalid types or values.
        """
        node_tag = None
        node_mask = None
        if "node_mask" in kwargs and kwargs["node_mask"] is not None:
            node_mask = kwargs["node_mask"]
            # Lazy import to avoid cycles
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

        if "values" not in kwargs:
            raise ValueError("values must be specified as a list of floats")
        values_in = kwargs["values"]
        if not isinstance(values_in, (list, tuple)) or len(values_in) == 0:
            raise ValueError("values must be a non-empty list/tuple of floats")
        try:
            values = [float(v) for v in values_in]
        except Exception:
            raise ValueError("values must be numeric")

        out: Dict[str, Any] = {"values": values}
        if node_tag is not None:
            out["node_tag"] = node_tag
        if node_mask is not None:
            out["node_mask"] = node_mask

        # Optional pids (default [0] if not provided)
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
        """Update the load's values after validation.

        Args:
            **kwargs: Parameters to update. Supported keys are the same
                as those accepted by the :meth:`NodeLoad.validate` method.
        """
        validated = self.validate(
            node_tag=kwargs.get("node_tag", self.node_tag),
            values=kwargs.get("values", self.values),
            pids=kwargs.get("pids", self.pids),
            node_mask=kwargs.get("node_mask", self.node_mask),
        )
        self.node_tag = validated.get("node_tag")
        self.values = validated["values"]
        self.pids = validated.get("pids", [])
        self.node_mask = validated.get("node_mask")

    def to_tcl(self) -> str:
        """Convert the nodal load to its TCL command string.

        When `node_mask` is provided, this method emits one `load` command
        line per node tag. Load vectors are padded or truncated based on
        each node's degrees of freedom. PIDs (core IDs) are derived per node
        from the mesh (if available in the `node_mask`), otherwise the
        instance's stored `pids` are used.

        Returns:
            str: A TCL command string, which can be single or multi-line
                depending on whether a `node_mask` is used.

        Example:
            >>> import femora as fm
            >>> # Single node load
            >>> load1 = fm.NodeLoad(node_tag=10, values=[1.0, -2.0, 0.0])
            >>> print(load1.to_tcl())
            if ($pid == 0) { load 10 1.0 -2.0 0.0 }
            >>>
            >>> # Load with PIDs
            >>> load2 = fm.NodeLoad(node_tag=20, values=[5.0, 0.0], pids=[0, 1])
            >>> print(load2.to_tcl())
            if (($pid == 0) || ($pid == 1)) { load 20 5.0 0.0 }
            >>>
            >>> # Example with NodeMask requires a Mesh for context
            >>> from femora.components.mask import NodeMask
            >>> from femora.core import Mesh
            >>> mesh = Mesh()
            >>> mesh.add_node(1, [0,0,0], ndf=3)
            >>> mesh.add_node(2, [1,0,0], ndf=6)
            >>> mesh.add_node(3, [2,0,0], ndf=3)
            >>> node_mask = NodeMask(nodes=[1, 2, 3], mesh=mesh)
            >>> load3 = fm.NodeLoad(node_mask=node_mask, values=[5.0, 0.0, -10.0, 0.0, 0.0, 0.0])
            >>> print(load3.to_tcl())
            if ($pid == 0) { load 1 5.0 0.0 -10.0 }
            if ($pid == 0) { load 2 5.0 0.0 -10.0 0.0 0.0 0.0 }
            if ($pid == 0) { load 3 5.0 0.0 -10.0 }
        """
        def wrap_with_pid_for_node(nid: int, s: str) -> str:
            # Prefer pids from the mask's mesh index if available, else self.pids
            pids = self.pids
            if self.node_mask is not None and hasattr(self.node_mask._mesh, 'node_core_map'):
                pids = self.node_mask._mesh.node_core_map[nid] or [0]
            if pids:
                cond = " || ".join(f"($pid == {pid})" for pid in pids)
                return f"if {{{cond}}} {{ {s} }}"
            return s

        if self.node_mask is not None:
            # Expand to multiple nodes, truncating/padding values by node ndf
            mesh = self.node_mask._mesh  # type: ignore[attr-defined]
            id_list = self.node_mask.to_list()
            tag_list = self.node_mask.to_tags()
            lines: List[str] = []
            for nid, node_tag in zip(id_list, tag_list):
                ndf = int(mesh.node_ndf[nid]) if hasattr(mesh, 'node_ndf') else len(self.values)
                vals = list(self.values)[:ndf]
                if len(vals) < ndf:
                    vals = vals + [0.0] * (ndf - len(vals))
                values_str = " ".join(str(v) for v in vals)
                lines.append(wrap_with_pid_for_node(int(nid), f"load {int(node_tag)} {values_str}"))
            return "\n\t".join(lines)
        else:
            values_str = " ".join(str(v) for v in self.values)
            cmd = f"load {self.node_tag} {values_str}"
            return wrap_with_pid_for_node(int(self.node_tag) if self.node_tag is not None else 0, cmd)


# Register type
LoadRegistry.register_load_type("node", NodeLoad)
LoadRegistry.register_load_type("nodeload", NodeLoad)