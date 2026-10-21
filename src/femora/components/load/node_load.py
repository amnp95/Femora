# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Any, List, Optional

from femora.core.load_base import Load


def _coerce_positive_int(value: Any, field: str) -> int:
    """Coerce a value to a positive integer.

    Args:
        value: The value to be converted.
        field: The name of the field being validated (for error messages).

    Returns:
        The validated positive integer.

    Raises:
        ValueError: If the value cannot be converted to a positive integer or
            is less than 1.
    """
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if number < 1:
        raise ValueError(f"{field} must be a positive integer")
    return number


def _coerce_load_values(values: Any) -> List[float]:
    """Coerce input load values to a list of floats.

    Args:
        values: The load values (list or tuple) to be validated.

    Returns:
        A list of validated float values.

    Raises:
        ValueError: If the input is not a non-empty list or tuple of numeric
            values.
    """
    if not isinstance(values, (list, tuple)) or len(values) == 0:
        raise ValueError("values must be a non-empty list/tuple of floats")
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError) as exc:
        raise ValueError("values must be numeric") from exc


def _coerce_pids(pids: Any) -> List[int]:
    """Coerce partition IDs to a sorted list of unique integers.

    Args:
        pids: The partition IDs (list or tuple) to be validated.

    Returns:
        A sorted list of unique validated integers.

    Raises:
        ValueError: If the input is not a list or tuple of integer values.
    """
    if not isinstance(pids, (list, tuple)):
        raise ValueError("pids must be a list/tuple of integers")
    try:
        return sorted({int(x) for x in pids})
    except (TypeError, ValueError) as exc:
        raise ValueError("pids must be integers") from exc


class NodeLoad(Load):
    """Nodal load component for applying forces or moments to nodes.

    NodeLoad represents a node-based load applied directly to a node's degrees
    of freedom. It is typically registered under a Plain pattern to represent
    external static or dynamic excitations.

    Tcl form:
        ``load <nodeTag> <value1> <value2> ...``

    Note:
        - The number of specified load values should match the number of degrees
          of freedom (NDF) at the target node.
        - If a `node_mask` is provided, the load will be automatically expanded
          and applied to all selected nodes.
        - In parallel computing contexts, partition IDs (`pids`) specify which
          processor core(s) should execute the command.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ts = model.time_series.constant(factor=1.0)
        pattern = model.pattern.plain(time_series=ts)

        # Apply a force of 5.0 in X and -10.0 in Y to node 1
        load = pattern.add_load.node(
            node_tag=1,
            values=[5.0, -10.0],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        *,
        values: List[float],
        node_tag: Optional[int] = None,
        node_mask: Optional[object] = None,
        pids: Optional[List[int]] = None,
    ) -> None:
        """Create a nodal load component.

        Args:
            values: Nodal force or moment values corresponding to the active
                degrees of freedom (DOFs) at the node.
            node_tag: Optional explicit tag of the target node.
            node_mask: Optional NodeMask object to apply the load to multiple
                nodes.
            pids: Optional processor partition IDs for parallel executions.

        Raises:
            ValueError: If neither `node_tag` nor `node_mask` is specified,
                if `node_mask` is not a NodeMask instance, or if any input
                parameter fails validation.
        """
        super().__init__()

        if node_mask is not None:
            from femora.components.mask.mask_base import NodeMask

            if not isinstance(node_mask, NodeMask):
                raise ValueError("node_mask must be a NodeMask")

        if node_tag is not None:
            node_tag = _coerce_positive_int(node_tag, "node_tag")

        if node_mask is None and node_tag is None:
            raise ValueError("Either node_tag or node_mask must be specified")

        self.node_tag = node_tag
        self.values = _coerce_load_values(values)
        self.pids = _coerce_pids(pids) if pids is not None else [0]
        self.node_mask = node_mask

    def to_tcl(self) -> str:
        """Render this load component as OpenSees Tcl commands.

        Returns:
            The OpenSees load command string(s) for the node(s).
        """
        from femora.components.element.ghost_node import GhostNodeElement

        def wrap_with_pid_for_node(nid: int, s: str) -> str:
            pids = self.pids
            if self.node_mask is not None and hasattr(self.node_mask._mesh, "node_core_map"):
                pids = self.node_mask._mesh.node_core_map[nid] or [0]
            if pids:
                cond = " || ".join(f"($pid == {pid})" for pid in pids)
                return f"if {{{cond}}} {{ {s} }}"
            return s

        if self.node_mask is not None:
            mesh = self.node_mask._mesh
            id_list = self.node_mask.to_list()
            tag_list = self.node_mask.to_tags()
            lines: List[str] = []
            for nid, node_tag in zip(id_list, tag_list):
                ndf = GhostNodeElement.resolve_ndf(
                    int(mesh.node_ndf[nid]) if hasattr(mesh, "node_ndf") else len(self.values)
                )
                vals = list(self.values)[:ndf]
                if len(vals) < ndf:
                    vals = vals + [0.0] * (ndf - len(vals))
                values_str = " ".join(str(v) for v in vals)
                lines.append(wrap_with_pid_for_node(int(nid), f"load {int(node_tag)} {values_str}"))
            return "\n\t".join(lines)

        values_str = " ".join(str(v) for v in self.values)
        cmd = f"load {self.node_tag} {values_str}"
        return wrap_with_pid_for_node(int(self.node_tag) if self.node_tag is not None else 0, cmd)


__all__ = ["NodeLoad"]
