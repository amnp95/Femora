from typing import Dict, List, Union
from femora.core.element_base import Element, ElementRegistry


class GhostNodeElement(Element):
    """A virtual element that owns nodes without generating an OpenSees element.

    GhostNodeElement is used when you need nodes to exist in the Femora model
    without them belonging to a physical structural element.  Common use-cases:

    - **Center-of-mass nodes** for buildings (mass-only, no structural element).
    - **Control/reference nodes** used by constraints or recorders.
    - **Mass application points** that don't participate in the element stiffness.

    The element uses PyVista ``CellType.VERTEX`` cells (one node per cell) so
    that the nodes stay in the mesh pipeline, survive the cleaning/merge step,
    and are written during TCL export.  The ``to_tcl`` method returns a TCL
    comment so no real ``element`` command is emitted.

    Merge Protection:
        Every GhostNodeElement instance is assigned a **unique sentinel ndf**
        value (≥ 1000).  Because the assembler's ``mesh.clean()`` uses
        ``merging_array_name="ndf"``, points are only merged when their ndf
        values match.  Unique sentinels ensure that:

        * Ghost nodes are *never* merged with co-located structural nodes.
        * Ghost nodes are *never* merged with other ghost nodes.

        At TCL export the sentinel is transparently mapped back to the real
        DOF count (3 or 6) via :meth:`resolve_ndf`.

    Example:
        ```python
        from femora.components.element.ghost_node import GhostNodeElement

        # Create two ghost-node elements at the same position — they will
        # NOT be merged because each gets a unique sentinel ndf.
        ghost_a = GhostNodeElement(ndof=6)
        ghost_b = GhostNodeElement(ndof=6)
        ```
    """

    # ---- class-level sentinel bookkeeping ----
    _SENTINEL_START = 1000          # first sentinel value
    _sentinel_counter = _SENTINEL_START  # bumped per instance
    _ndf_map: Dict[int, int] = {}   # sentinel → real DOF count

    def __init__(self, ndof: int = 3, **kwargs):
        """Initialize a GhostNodeElement.

        Args:
            ndof: Number of degrees of freedom per node.  Must be 3 or 6.
                Defaults to 3.
            **kwargs: Additional keyword arguments forwarded to the base
                ``Element`` constructor.

        Raises:
            ValueError: If *ndof* is not 3 or 6.
        """
        if ndof not in (3, 6):
            raise ValueError(
                f"GhostNodeElement requires 3 or 6 DOFs, but got {ndof}"
            )

        # Store the real DOF count for reference
        self._real_ndof = ndof

        # Reserve a unique sentinel ndf — prevents merging with anything
        sentinel_ndof = GhostNodeElement._next_sentinel(ndof)

        # No material, section, or transformation required
        super().__init__("GhostNode", sentinel_ndof, **kwargs)

    # ------------------------------------------------------------------
    # Sentinel helpers
    # ------------------------------------------------------------------
    @classmethod
    def _next_sentinel(cls, real_ndof: int) -> int:
        """Reserve and return the next unique sentinel ndf value.

        Args:
            real_ndof: The real DOF count (3 or 6) to map back to at export.

        Returns:
            A unique sentinel ndf integer (≥ 1000).
        """
        sentinel = cls._sentinel_counter
        cls._sentinel_counter += 1
        cls._ndf_map[sentinel] = real_ndof
        return sentinel

    @classmethod
    def resolve_ndf(cls, ndf_value: int) -> int:
        """Map a (possibly sentinel) ndf value to the real DOF count.

        If *ndf_value* is a ghost sentinel it is resolved via the internal
        map.  Otherwise it is returned unchanged.  This is the single
        function that ``MeshMaker.export_to_tcl`` should call.

        Args:
            ndf_value: Raw ndf value from the mesh ``point_data["ndf"]``.

        Returns:
            The real DOF count to write into the TCL ``node`` command.
        """
        return cls._ndf_map.get(int(ndf_value), int(ndf_value))

    @classmethod
    def is_ghost_ndf(cls, ndf_value: int) -> bool:
        """Check whether an ndf value is a ghost-node sentinel.

        Args:
            ndf_value: The ndf value to check.

        Returns:
            True if the value is a ghost-node sentinel.
        """
        return int(ndf_value) >= cls._SENTINEL_START

    @property
    def real_ndof(self) -> int:
        """The actual DOF count written to the TCL ``node`` command."""
        return self._real_ndof

    # ------------------------------------------------------------------
    # to_tcl  –  returns a TCL comment (no structural element)
    # ------------------------------------------------------------------
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Return a TCL comment — no OpenSees element command is emitted.

        The owning node(s) are still written by the export loop; only the
        ``element …`` line is replaced with a comment.

        Args:
            tag: Element tag (unused).
            nodes: Node tags (unused).

        Returns:
            A TCL comment string.
        """
        return "# GhostNode (no element command)"

    # ------------------------------------------------------------------
    # Abstract-method implementations
    # ------------------------------------------------------------------
    @classmethod
    def get_parameters(cls) -> List[str]:
        """GhostNodeElement has no configurable parameters.

        Returns:
            An empty list.
        """
        return []

    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Allowed DOF counts per node.

        Returns:
            ``['3', '6']``.
        """
        return ["3", "6"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions (none for this element).

        Returns:
            An empty list.
        """
        return []

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """No parameters to validate — returns *kwargs* unchanged.

        Args:
            **kwargs: (ignored).

        Returns:
            The unchanged *kwargs* dictionary.
        """
        return kwargs

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for the given parameter keys.

        Since GhostNodeElement has no parameters, all values are ``None``.

        Args:
            keys: Parameter names to look up.

        Returns:
            Dictionary mapping each key to ``None``.
        """
        return {k: None for k in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update parameters (no-op for GhostNodeElement).

        Args:
            values: Parameter mapping (ignored).
        """
        pass


# Register so it can be created through ElementRegistry.create_element()
ElementRegistry.register_element_type("GhostNode", GhostNodeElement)
