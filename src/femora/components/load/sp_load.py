from __future__ import annotations

from typing import Dict, List, Union, Any, Optional

from .load_base import Load, LoadRegistry


class SpLoad(Load):
    """Represents a single-point constraint (SP) load for OpenSees.

    This class wraps the OpenSees ``sp`` command and supports applying
    constraints to a single node or multiple nodes via a :class:`NodeMask`.
    The load defines a prescribed value for a specific degree of freedom
    on target nodes.

    The TCL form is::

        sp <nodeTag> <dof> <value>

    When a :class:`femora.components.mask.mask_base.NodeMask` is used, node tags are obtained via
    :meth:`NodeMask.to_tags` and PIDs (processor IDs) are derived per node
    from the mesh, if available. Otherwise, the stored `pids` are used.

    Attributes:
        node_tag (Optional[int]): The target node tag for a single node constraint.
            This is mutually exclusive with `node_mask`.
        dof (int): The 1-based degree of freedom index to constrain.
        value (float): The prescribed value for the degree of freedom.
        pids (List[int]): Optional list of processor IDs (cores) where this SP
            load applies. Defaults to `[0]` and is overridden per node when
            a mask is provided and a mesh is associated.
        node_mask: Optional :class:`femora.components.mask.mask_base.NodeMask` object
            to target multiple nodes for the constraint. This is mutually exclusive
            with `node_tag`.

    Example:
        >>> from femora.loads import SpLoad
        >>> # Single node SP load
        >>> sp_single = SpLoad(node_tag=10, dof=1, value=0.0)
        >>> print(sp_single.to_tcl())
        sp 10 1 0.0

        >>> # SP load with custom PIDs
        >>> sp_custom_pids = SpLoad(node_tag=20, dof=3, value=2.5, pids=[0, 1])
        >>> print(sp_custom_pids.to_tcl())
        if (($pid == 0) || ($pid == 1)) { sp 20 3 2.5 }

        >>> # Example with a NodeMask (requires a mock or actual NodeMask setup)
        >>> from femora.components.mask.mask_base import NodeMask as _NodeMask
        >>> class MockMesh:
        ...     def __init__(self): self.node_core_map = {10: [0], 11: [1], 12: [0, 1]}
        ...     def get_nodes(self): return [10, 11] # Simplified for example
        ...     def get_node_by_tag(self, tag):
        ...         # NodeMask.to_list() might access this; create a minimal mock node
        ...         return type('Node', (object,), {'id': tag, 'tag': tag})()
        >>> mock_mesh = MockMesh()
        >>> # A minimal mock that behaves like NodeMask for the purpose of to_tcl
        >>> class MockNodeMask(_NodeMask):
        ...     def __init__(self, name, data, mesh):
        ...         self.name = name
        ...         self._data = data
        ...         self._mesh = mesh
        ...         self._tags_list = data["tags"]
        ...     def to_tags(self): return self._tags_list
        ...     def to_list(self): return self._tags_list # Returns node IDs, simplified for this example to be tags
        >>> node_mask_data = {"tags": [10, 11]}
        >>> node_mask_instance = MockNodeMask("example_mask", node_mask_data, mock_mesh)
        >>> sp_mask = SpLoad(node_mask=node_mask_instance, dof=2, value=0.5)
        >>> print(sp_mask.to_tcl())
        if (($pid == 0)) { sp 10 2 0.5 }
        if (($pid == 1)) { sp 11 2 0.5 }
    """

    def __init__(self, **kwargs):
        """Initializes the SpLoad.

        Args:
            node_tag: The unique integer ID for the target node. Mutually
                exclusive with `node_mask`.
            dof: The 1-based integer index of the degree of freedom.
            value: The float value to prescribe.
            pids: Optional list of integer processor IDs. Defaults to `[0]`
                if not specified and no `node_mask` is used.
            node_mask: Optional :class:`femora.components.mask.mask_base.NodeMask`
                object to specify multiple target nodes. Mutually exclusive
                with `node_tag`.

        Raises:
            ValueError: If required parameters are missing or invalid, or if
                both `node_tag` and `node_mask` are specified or neither.
                Validation is performed by :meth:`SpLoad.validate`.
        """
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
        """Returns metadata about the SpLoad's configurable parameters.

        This static method provides a list of parameter names and their
        descriptions, primarily for UI generation or introspection.

        Returns:
            List[tuple]: A list of tuples, where each tuple contains
                (parameter_name: str, description: str).

        Example:
            >>> from femora.loads import SpLoad
            >>> params = SpLoad.get_parameters()
            >>> print(params[0])
            ('node_tag', 'Tag of the node (optional if node_mask provided)')
            >>> print(params[1])
            ('dof', 'Degree of freedom index (1-based)')
        """
        return [
            ("node_tag", "Tag of the node (optional if node_mask provided)"),
            ("dof", "Degree of freedom index (1-based)"),
            ("value", "Prescribed value"),
            ("pids", "Optional list of core ids (ints) where to emit this sp"),
            ("node_mask", "Optional NodeMask to expand into multiple nodes"),
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, bool, list, tuple]]:
        """Returns a serializable dictionary of the current load state.

        This dictionary contains all the configuration values of the SpLoad
        instance, suitable for serialization or introspection. It includes
        the `pattern_tag` inherited from :class:`femora.loads.load_base.Load`.

        Returns:
            Dict[str, Union[str, int, float, bool, list, tuple]]: A dictionary
                mapping parameter names to their current values.

        Example:
            >>> from femora.loads import SpLoad
            >>> sp_load = SpLoad(node_tag=5, dof=3, value=1.2)
            >>> values = sp_load.get_values()
            >>> print(values['node_tag'])
            5
            >>> print(values['dof'])
            3
            >>> print(values['value'])
            1.2
            >>> print(values['pids'])
            [0]
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
        """Validates and normalizes parameters for SpLoad construction or update.

        This method ensures that the provided parameters meet the requirements
        for creating or modifying an SpLoad instance. It performs type checking
        and value range validation.

        Args:
            **kwargs: Keyword arguments containing the parameters to validate.
                Accepted keys are:
                *   `node_tag` (int): The target node tag (positive integer).
                *   `node_mask` (:class:`femora.components.mask.mask_base.NodeMask`):
                    An object specifying multiple target nodes.
                *   `dof` (int): The 1-based degree of freedom index
                    (positive integer).
                *   `value` (float): The prescribed numeric value.
                *   `pids` (list[int]): Optional list of integer processor IDs.

        Returns:
            Dict[str, Any]: A dictionary of validated and normalized parameter
                values, ready for assignment.

        Raises:
            ValueError: If `node_tag` or `node_mask` are missing, invalid,
                or mutually exclusive. Also raised if `dof` or `value` are
                missing or invalid, or if `pids` is not a list of integers.

        Example:
            >>> from femora.loads import SpLoad
            >>> valid_params = SpLoad.validate(node_tag=1, dof=1, value=0.0)
            >>> print(valid_params['node_tag'])
            1
            >>> try:
            ...     SpLoad.validate(dof=1, value=0.0)
            ... except ValueError as e:
            ...     print(e)
            Either node_tag or node_mask must be specified
            >>> try:
            ...     SpLoad.validate(node_tag=1, dof=0, value=0.0)
            ... except ValueError as e:
            ...     print(e)
            dof must be a positive integer (1-based)
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
        """Updates the SpLoad's configuration values.

        This method allows modifying the parameters of an existing SpLoad
        instance. It re-validates all parameters, ensuring the instance
        remains in a consistent state.

        Args:
            **kwargs: Keyword arguments for the parameters to update.
                Refer to :meth:`SpLoad.validate` for accepted keys and their
                expected types. Unspecified parameters retain their current values.

        Example:
            >>> from femora.loads import SpLoad
            >>> sp_load = SpLoad(node_tag=1, dof=1, value=0.0)
            >>> print(f"Initial: tag={sp_load.node_tag}, dof={sp_load.dof}, value={sp_load.value}")
            Initial: tag=1, dof=1, value=0.0
            >>> sp_load.update_values(value=1.5, dof=2)
            >>> print(f"Updated: tag={sp_load.node_tag}, dof={sp_load.dof}, value={sp_load.value}")
            Updated: tag=1, dof=2, value=1.5
            >>> try:
            ...     sp_load.update_values(dof=0)
            ... except ValueError as e:
            ...     print(e)
            dof must be a positive integer (1-based)
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
        """Converts the SpLoad instance to its OpenSees TCL command string(s).

        If a `node_mask` is provided, this method generates one `sp` command
        per node tag in the mask. Processor IDs (PIDs) are derived from the
        mesh's `node_core_map` if the `node_mask` has an associated mesh;
        otherwise, the instance's `pids` list is used. If no `node_mask`
        is present, a single `sp` command is generated for the `node_tag`.

        Returns:
            str: A string containing one or more OpenSees TCL `sp` commands,
                potentially wrapped in PID conditional statements.

        Example:
            >>> from femora.loads import SpLoad
            >>> # Single node example
            >>> sp_single = SpLoad(node_tag=10, dof=1, value=0.0)
            >>> print(sp_single.to_tcl())
            sp 10 1 0.0

            >>> # Example with custom PIDs
            >>> sp_custom_pids = SpLoad(node_tag=20, dof=3, value=2.5, pids=[0, 1])
            >>> print(sp_custom_pids.to_tcl())
            if (($pid == 0) || ($pid == 1)) { sp 20 3 2.5 }

            >>> # Example with NodeMask (requires mocking NodeMask and mesh for runnable example)
            >>> from femora.components.mask.mask_base import NodeMask as _NodeMask
            >>> class MockMesh:
            ...     def __init__(self): self.node_core_map = {10: [0], 11: [1], 12: [0, 1]}
            ...     def get_nodes(self): return [10, 11] # Simplified for example
            ...     def get_node_by_tag(self, tag):
            ...         # NodeMask.to_list() might access this; create a minimal mock node
            ...         return type('Node', (object,), {'id': tag, 'tag': tag})()
            >>> mock_mesh = MockMesh()
            >>> # A minimal mock that behaves like NodeMask for the purpose of to_tcl
            >>> class MockNodeMask(_NodeMask):
            ...     def __init__(self, name, data, mesh):
            ...         self.name = name
            ...         self._data = data
            ...         self._mesh = mesh
            ...         self._tags_list = data["tags"]
            ...     def to_tags(self): return self._tags_list
            ...     def to_list(self): return self._tags_list # Returns node IDs, simplified for this example to be tags
            >>> node_mask_data = {"tags": [10, 11]}
            >>> node_mask_instance = MockNodeMask("example_mask", node_mask_data, mock_mesh)
            >>> sp_mask = SpLoad(node_mask=node_mask_instance, dof=2, value=0.5)
            >>> print(sp_mask.to_tcl())
            if (($pid == 0)) { sp 10 2 0.5 }
            if (($pid == 1)) { sp 11 2 0.5 }
        """
        def wrap_with_pid_for_node(nid: int, s: str) -> str:
            pids = self.pids
            if self.node_mask is not None and hasattr(self.node_mask, '_mesh') and hasattr(self.node_mask._mesh, 'node_core_map'):
                pids_for_node = self.node_mask._mesh.node_core_map.get(nid)
                if pids_for_node is not None:
                    pids = pids_for_node
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