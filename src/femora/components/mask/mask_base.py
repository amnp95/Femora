from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Dict

import numpy as np


@dataclass(frozen=True)
class MeshIndex:
    """
    Immutable snapshot of assembled mesh data for efficient masking/filtering.

    This structure is created after mesh assembly and stores the minimal arrays
    needed to perform fast vectorized spatial and attribute-based queries.

    Notes:
        - Node IDs and element IDs are zero-based indices derived from the
          assembled grid ordering.
        - ``element_connectivity`` stores node indices per element, referencing
          the global ``node_ids`` array.
        - ``element_centroids`` are precomputed for convenience and performance
          in spatial queries.
        - Attribute arrays (``material_tags``, ``section_tags``, ``region_tags``,
          ``core_ids``) mirror the assembled grid cell_data fields, and
          ``node_ndf`` mirrors point_data["ndf"].
    """

    # Nodes
    node_ids: np.ndarray              # (N,) ints
    node_coords: np.ndarray           # (N, 3) floats
    node_ndf: np.ndarray              # (N,) ints, DOFs per node
    node_core_map: List[List[int]]    # (N,) list of core ids per node (can be multiple)

    # Elements
    element_ids: np.ndarray           # (M,) ints (cell indices or explicit ids)
    element_connectivity: List[np.ndarray]  # per element list of node indices
    element_centroids: np.ndarray     # (M, 3) floats
    element_types: np.ndarray         # (M,) dtype=str or object
    material_tags: np.ndarray         # (M,) ints
    section_tags: np.ndarray          # (M,) ints
    region_tags: np.ndarray           # (M,) ints
    core_ids: np.ndarray              # (M,) ints partition ids
    element_id_to_index: Dict[int, int]  # map element id -> row index


class _BaseMask:
    """
    Base class for typed masks over nodes or elements.

    The mask holds a reference to the ``MeshIndex`` and a 1D array of selected
    entity IDs (node IDs for ``NodeMask``, element IDs for ``ElementMask``).
    """
    def __init__(self, mesh: MeshIndex, ids: np.ndarray):
        """
        Initialize a mask.

        Args:
            mesh (MeshIndex): Immutable snapshot of the assembled mesh to query.
            ids (np.ndarray): 1D array of selected entity IDs (node or element
                IDs depending on the concrete mask). The array will be
                normalized to sorted unique integers.
        """
        self._mesh = mesh
        # store as sorted unique int array for stable ops
        ids = np.asarray(ids, dtype=int)
        if ids.ndim != 1:
            ids = ids.reshape(-1)
        self._ids = np.unique(ids)

    def to_list(self) -> List[int]:
        """
        Return the selection as a Python list of IDs.

        Returns:
            List[int]: List of selected IDs in ascending order.
        """
        return [int(i) for i in self._ids.tolist()]

    def to_set(self) -> set:
        """
        Return the selection as a Python set of IDs.

        Returns:
            set: Set of selected IDs.
        """
        return set(self.to_list())

    def __len__(self) -> int:
        """
        Return the number of selected entities.

        Returns:
            int: Count of IDs in this mask.
        """
        return int(self._ids.size)

    def is_empty(self) -> bool:
        """
        Check if the selection is empty.

        Returns:
            bool: True when no IDs are selected, False otherwise.
        """
        return self._ids.size == 0


class NodeMask(_BaseMask):
    """
    A mask of node IDs with chainable spatial and predicate-based filters.

    All methods return a new ``NodeMask`` instance (immutability at API level).
    """
    def by_ids(self, ids: Sequence[int]) -> 'NodeMask':
        """
        Intersect the current node mask with specific node IDs.

        Args:
            ids (Sequence[int]): Node IDs to retain.

        Returns:
            NodeMask: New mask containing the intersection.
        """
        ids_arr = np.intersect1d(self._mesh.node_ids, np.array(ids, dtype=int))
        return NodeMask(self._mesh, ids_arr)

    def by_bbox(self, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float) -> 'NodeMask':
        """
        Filter nodes inside an axis-aligned bounding box.

        Args:
            xmin (float): Minimum x.
            xmax (float): Maximum x.
            ymin (float): Minimum y.
            ymax (float): Maximum y.
            zmin (float): Minimum z.
            zmax (float): Maximum z.

        Returns:
            NodeMask: New mask with nodes in the box.
        """
        xyz = self._mesh.node_coords
        sel = (
            (xyz[:, 0] >= xmin) & (xyz[:, 0] <= xmax) &
            (xyz[:, 1] >= ymin) & (xyz[:, 1] <= ymax) &
            (xyz[:, 2] >= zmin) & (xyz[:, 2] <= zmax)
        )
        return NodeMask(self._mesh, self._mesh.node_ids[sel])

    def near_point(self, point: Tuple[float, float, float], radius: float) -> 'NodeMask':
        """
        Filter nodes within a distance from a point.

        Args:
            point (Tuple[float, float, float]): Reference point (x, y, z).
            radius (float): Radial distance threshold.

        Returns:
            NodeMask: New mask with nodes inside the sphere.
        """
        p = np.asarray(point, dtype=float).reshape(1, 3)
        d2 = np.sum((self._mesh.node_coords - p) ** 2, axis=1)
        sel = d2 <= float(radius) ** 2
        return NodeMask(self._mesh, self._mesh.node_ids[sel])
    
    def along_line(self, point1: Tuple[float, float, float], point2: Tuple[float, float, float], radius: float) -> 'NodeMask':
        """
        Filter nodes within a distance from a line segment defined by two points.

        Args:
            point1 (Tuple[float, float, float]): First endpoint of the line segment (x, y, z).
            point2 (Tuple[float, float, float]): Second endpoint of the line segment (x, y, z).
            radius (float): Radial distance threshold.
        Returns:
            NodeMask: New mask with nodes inside the cylindrical region around the line segment.
        """
        p1 = np.asarray(point1, dtype=float).reshape(1, 3)
        p2 = np.asarray(point2, dtype=float).reshape(1, 3)
        line_vec = p2 - p1
        line_len2 = np.dot(line_vec, line_vec.T)[0, 0]
        if line_len2 == 0:
            # point1 and point2 are the same point
            return self.near_point(point1, radius)
        node_vecs = self._mesh.node_coords - p1
        t = np.clip(np.dot(node_vecs, line_vec.T) / line_len2, 0, 1)
        proj_points = p1 + t * line_vec
        d2 = np.sum((self._mesh.node_coords - proj_points) ** 2, axis=1)
        sel = d2 <= float(radius) ** 2
        return NodeMask(self._mesh, self._mesh.node_ids[sel])
    
    
    def along_axis(self, axis: str, vmin: float, vmax: float) -> 'NodeMask':
        """
        Filter nodes whose coordinate along an axis lies within a range.

        Args:
            axis (str): Axis name ('x', 'y', or 'z').
            vmin (float): Minimum coordinate value (inclusive).
            vmax (float): Maximum coordinate value (inclusive).

        Returns:
            NodeMask: New mask with nodes within the range.
        """
        ax = {'x': 0, 'y': 1, 'z': 2}[axis.lower()]
        x = self._mesh.node_coords[:, ax]
        sel = (x >= vmin) & (x <= vmax)
        return NodeMask(self._mesh, self._mesh.node_ids[sel])

    def by_predicate(self, fn: Callable[[int, np.ndarray], bool]) -> 'NodeMask':
        """
        Filter nodes using a custom predicate.

        Args:
            fn (Callable[[int, np.ndarray], bool]): Function receiving
                ``(node_id, coord)`` and returning True to keep the node.

        Returns:
            NodeMask: New mask with nodes passing the predicate.
        """
        mask = [fn(int(nid), self._mesh.node_coords[i]) for i, nid in enumerate(self._mesh.node_ids)]
        sel_ids = self._mesh.node_ids[np.array(mask, dtype=bool)]
        return NodeMask(self._mesh, sel_ids)

    def touching_elements(self) -> 'ElementMask':
        """
        Convert to an element mask of all elements connected to selected nodes.

        Returns:
            ElementMask: Elements with connectivity touching any node in this mask.
        """
        # build reverse mapping node_id -> local index
        id_to_idx = {int(nid): idx for idx, nid in enumerate(self._mesh.node_ids.tolist())}
        node_idx_set = {id_to_idx[int(n)] for n in self._ids if int(n) in id_to_idx}
        hits = []
        for ei, conn in enumerate(self._mesh.element_connectivity):
            if any((int(ci) in node_idx_set) for ci in conn.tolist()):
                hits.append(self._mesh.element_ids[ei])
        return ElementMask(self._mesh, np.asarray(hits, dtype=int))

    def to_tags(self, start_tag: int | None = None) -> List[int]:
        """
        Convert selected node IDs to OpenSees node tags.

        Args:
            start_tag (int | None): Starting node tag. If None, attempts to
                read from MeshMaker's configured node tag start; otherwise 1.

        Returns:
            List[int]: Node tags.
        """
        ids = self.to_list()
        if start_tag is None:
            try:
                from femora.components.MeshMaker import MeshMaker
                start_tag = MeshMaker.get_instance()._start_nodetag  # type: ignore[attr-defined]
            except Exception:
                start_tag = 1
        return [int(start_tag) + int(i) for i in ids]


class ElementMask(_BaseMask):
    """
    A mask of element IDs with chainable attribute and spatial filters.

    All methods return a new ``ElementMask`` instance (immutability at API level).
    """
    def by_ids(self, ids: Sequence[int]) -> 'ElementMask':
        """
        Intersect the current element mask with specific element IDs.

        Args:
            ids (Sequence[int]): Element IDs to retain.

        Returns:
            ElementMask: New mask containing the intersection.
        """
        ids_arr = np.intersect1d(self._mesh.element_ids, np.array(ids, dtype=int))
        return ElementMask(self._mesh, ids_arr)

    def by_type(self, name: str) -> 'ElementMask':
        """
        Filter elements by type name (case-insensitive).

        Args:
            name (str): Element type name to match.

        Returns:
            ElementMask: New mask with matching elements.
        """
        sel = np.array([str(t).lower() == name.lower() for t in self._mesh.element_types], dtype=bool)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_material(self, tag: int) -> 'ElementMask':
        """
        Filter elements by material tag.

        Args:
            tag (int): Material tag value.

        Returns:
            ElementMask: New mask with elements having this material tag.
        """
        sel = self._mesh.material_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_section(self, tag: int) -> 'ElementMask':
        """
        Filter elements by section tag.

        Args:
            tag (int): Section tag value.

        Returns:
            ElementMask: New mask with elements having this section tag.
        """
        sel = self._mesh.section_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_region(self, tag: int) -> 'ElementMask':
        """
        Filter elements by region value.

        Args:
            tag (int): Region value.

        Returns:
            ElementMask: New mask with elements in this region.
        """
        sel = self._mesh.region_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_core(self, core: int) -> 'ElementMask':
        """
        Filter elements by partition/core id.

        Args:
            core (int): Core/partition identifier.

        Returns:
            ElementMask: New mask with elements in this core.
        """
        sel = self._mesh.core_ids == int(core)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_bbox(self, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float, *, use_centroid: bool = True) -> 'ElementMask':
        """
        Filter elements inside an axis-aligned bounding box.

        Args:
            xmin (float): Minimum x.
            xmax (float): Maximum x.
            ymin (float): Minimum y.
            ymax (float): Maximum y.
            zmin (float): Minimum z.
            zmax (float): Maximum z.
            use_centroid (bool, optional): If True (default), filter by element
                centroid; otherwise include an element if any of its nodes lies
                in the box.

        Returns:
            ElementMask: New mask with elements in the box.
        """
        if use_centroid:
            xyz = self._mesh.element_centroids
            sel = (
                (xyz[:, 0] >= xmin) & (xyz[:, 0] <= xmax) &
                (xyz[:, 1] >= ymin) & (xyz[:, 1] <= ymax) &
                (xyz[:, 2] >= zmin) & (xyz[:, 2] <= zmax)
            )
            return ElementMask(self._mesh, self._mesh.element_ids[sel])
        else:
            # any node in bbox
            node_xyz = self._mesh.node_coords
            in_box = (
                (node_xyz[:, 0] >= xmin) & (node_xyz[:, 0] <= xmax) &
                (node_xyz[:, 1] >= ymin) & (node_xyz[:, 1] <= ymax) &
                (node_xyz[:, 2] >= zmin) & (node_xyz[:, 2] <= zmax)
            )
            hit_nodes = set(np.where(in_box)[0].tolist())
            hits = []
            for ei, conn in enumerate(self._mesh.element_connectivity):
                if any((int(ci) in hit_nodes) for ci in conn.tolist()):
                    hits.append(self._mesh.element_ids[ei])
            return ElementMask(self._mesh, np.asarray(hits, dtype=int))

    def by_predicate(self, fn: Callable[[int, np.ndarray, str, int, int, int], bool]) -> 'ElementMask':
        """
        Filter elements using a custom predicate.

        Args:
            fn (Callable[[int, np.ndarray, str, int, int, int], bool]): Function
                receiving ``(elem_id, centroid, type_name, material_tag,
                section_tag, region_tag)`` and returning True to keep it.

        Returns:
            ElementMask: New mask with elements passing the predicate.
        """
        out = []
        for i, eid in enumerate(self._mesh.element_ids):
            if fn(int(eid), self._mesh.element_centroids[i], str(self._mesh.element_types[i]), int(self._mesh.material_tags[i]), int(self._mesh.section_tags[i]), int(self._mesh.region_tags[i])):
                out.append(eid)
        return ElementMask(self._mesh, np.asarray(out, dtype=int))

    def to_nodes(self) -> 'NodeMask':
        """
        Convert selected elements to the set of incident nodes.

        Returns:
            NodeMask: Nodes that belong to any selected element.
        """
        nidx = set()
        for conn in self._mesh.element_connectivity:
            nidx.update(int(i) for i in conn.tolist())
        node_ids = self._mesh.node_ids[list(nidx)]
        return NodeMask(self._mesh, node_ids)

    def to_tags(self, start_tag: int | None = None) -> List[int]:
        """
        Convert selected element IDs to OpenSees element tags.

        Args:
            start_tag (int | None): Starting element tag. If None, attempts to
                read from MeshMaker's configured element tag start; otherwise 1.

        Returns:
            List[int]: Element tags.
        """
        ids = self.to_list()
        if start_tag is None:
            try:
                from femora.components.MeshMaker import MeshMaker
                start_tag = MeshMaker.get_instance()._start_ele_tag  # type: ignore[attr-defined]
            except Exception:
                start_tag = 1
        return [int(start_tag) + int(i) for i in ids]


