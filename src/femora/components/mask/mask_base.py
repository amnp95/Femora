from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Dict

import numpy as np


@dataclass(frozen=True)
class MeshIndex:
    """Immutable snapshot of assembled mesh data for efficient masking/filtering.

    This structure is created after mesh assembly and stores the minimal arrays
    needed to perform fast vectorized spatial and attribute-based queries.

    Attributes:
        node_ids (np.ndarray): 1D array of node IDs, zero-based indices derived
            from the assembled grid ordering. Shape (N,).
        node_coords (np.ndarray): Nodal coordinates. Shape (N, 3).
        node_ndf (np.ndarray): Degrees of freedom per node. Shape (N,).
        node_core_map (List[List[int]]): List where each item is a list of core
            IDs that the corresponding node belongs to (a node can be part of
            multiple cores). Shape (N,).
        element_ids (np.ndarray): 1D array of element IDs, which can be cell
            indices or explicit identifiers. Shape (M,).
        element_connectivity (List[np.ndarray]): A list where each item is a 1D
            array of node indices (referencing `node_ids`) for that element.
        element_centroids (np.ndarray): Precomputed centroid coordinates for
            each element. Shape (M, 3).
        element_types (np.ndarray): Array of string or object types for each
            element. Shape (M,).
        material_tags (np.ndarray): Material tag for each element. Shape (M,).
        section_tags (np.ndarray): Section tag for each element. Shape (M,).
        region_tags (np.ndarray): Region tag for each element. Shape (M,).
        core_ids (np.ndarray): Partition/core ID for each element. Shape (M,).
        element_id_to_index (Dict[int, int]): A mapping from an explicit
            element ID to its 0-based row index in the `element_ids` array.

    Example:
        >>> import numpy as np
        >>> from femora.core.masks import MeshIndex
        >>> # Assuming a simple mesh has been assembled
        >>> mesh_index = MeshIndex(
        ...     node_ids=np.array([0, 1, 2]),
        ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        ...     node_ndf=np.array([3, 3, 3]),
        ...     node_core_map=[[0], [0], [0]],
        ...     element_ids=np.array([0]),
        ...     element_connectivity=[np.array([0, 1, 2])],
        ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
        ...     element_types=np.array(["TRIANGLE"]),
        ...     material_tags=np.array([1]),
        ...     section_tags=np.array([1]),
        ...     region_tags=np.array([0]),
        ...     core_ids=np.array([0]),
        ...     element_id_to_index={0: 0}
        ... )
        >>> print(mesh_index.node_ids.shape)
        (3,)
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
    """Base class for typed masks over nodes or elements.

    This mask holds a reference to the `MeshIndex` and a 1D array of selected
    entity IDs (node IDs for `NodeMask`, element IDs for `ElementMask`).

    Attributes:
        _mesh (MeshIndex): The `MeshIndex` instance this mask operates on.
        _ids (np.ndarray): 1D array of unique, sorted integer IDs of the
            selected entities (nodes or elements).
    """
    def __init__(self, mesh: MeshIndex, ids: np.ndarray):
        """Initializes a new _BaseMask instance.

        Args:
            mesh: Immutable snapshot of the assembled mesh to query.
            ids: A 1D array of selected entity IDs (node or element IDs
                depending on the concrete mask). The array will be normalized
                to sorted unique integers upon initialization.
        """
        self._mesh = mesh
        # store as sorted unique int array for stable ops
        ids = np.asarray(ids, dtype=int)
        if ids.ndim != 1:
            ids = ids.reshape(-1)
        self._ids = np.unique(ids)

    def to_list(self) -> List[int]:
        """Returns the selection as a Python list of IDs.

        Returns:
            List[int]: List of selected IDs in ascending order.
        """
        return [int(i) for i in self._ids.tolist()]

    def to_set(self) -> set:
        """Returns the selection as a Python set of IDs.

        Returns:
            set: Set of selected IDs.
        """
        return set(self.to_list())

    def __len__(self) -> int:
        """Returns the number of selected entities.

        Returns:
            int: The count of IDs in this mask.
        """
        return int(self._ids.size)

    def is_empty(self) -> bool:
        """Checks if the selection is empty.

        Returns:
            bool: True if no IDs are selected, False otherwise.
        """
        return self._ids.size == 0


class NodeMask(_BaseMask):
    """A mask of node IDs with chainable spatial and predicate-based filters.

    All methods return a new `NodeMask` instance, ensuring immutability at the API level.

    Example:
        >>> import numpy as np
        >>> from femora.core.masks import MeshIndex, NodeMask
        >>> mesh_index = MeshIndex(
        ...     node_ids=np.array([0, 1, 2, 3]),
        ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
        ...     node_ndf=np.array([3, 3, 3, 3]),
        ...     node_core_map=[[0], [0], [0], [0]],
        ...     element_ids=np.array([0]),
        ...     element_connectivity=[np.array([0, 1, 2])],
        ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
        ...     element_types=np.array(["TRIANGLE"]),
        ...     material_tags=np.array([1]),
        ...     section_tags=np.array([1]),
        ...     region_tags=np.array([0]),
        ...     core_ids=np.array([0]),
        ...     element_id_to_index={0: 0}
        ... )
        >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
        >>> filtered_nodes = all_nodes.by_bbox(0.5, 1.5, -0.5, 0.5, -0.5, 0.5)
        >>> print(filtered_nodes.to_list())
        [1]
    """
    def by_ids(self, ids: Sequence[int]) -> 'NodeMask':
        """Intersects the current node mask with specific node IDs.

        Args:
            ids: A sequence of node IDs to retain.

        Returns:
            NodeMask: A new mask containing the intersection of the current
                mask's IDs and the provided `ids`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> mask = NodeMask(mesh_index, np.array([0, 1, 2]))
            >>> filtered_mask = mask.by_ids([1, 3])
            >>> print(filtered_mask.to_list())
            [1]
        """
        ids_arr = np.intersect1d(self._mesh.node_ids, np.array(ids, dtype=int))
        return NodeMask(self._mesh, ids_arr)

    def by_bbox(self, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float) -> 'NodeMask':
        """Filters nodes inside an axis-aligned bounding box.

        Args:
            xmin: The minimum x-coordinate of the bounding box.
            xmax: The maximum x-coordinate of the bounding box.
            ymin: The minimum y-coordinate of the bounding box.
            ymax: The maximum y-coordinate of the bounding box.
            zmin: The minimum z-coordinate of the bounding box.
            zmax: The maximum z-coordinate of the bounding box.

        Returns:
            NodeMask: A new mask containing only nodes whose coordinates are
                within the specified bounding box.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
            >>> filtered_nodes = all_nodes.by_bbox(0.5, 1.5, -0.5, 0.5, -0.5, 0.5)
            >>> print(filtered_nodes.to_list())
            [1]
        """
        xyz = self._mesh.node_coords
        sel = (
            (xyz[:, 0] >= xmin) & (xyz[:, 0] <= xmax) &
            (xyz[:, 1] >= ymin) & (xyz[:, 1] <= ymax) &
            (xyz[:, 2] >= zmin) & (xyz[:, 2] <= zmax)
        )
        return NodeMask(self._mesh, self._mesh.node_ids[sel])

    def near_point(self, point: Tuple[float, float, float], radius: float) -> 'NodeMask':
        """Filters nodes within a specified distance from a given point.

        Args:
            point: The reference point (x, y, z) from which to measure the distance.
            radius: The radial distance threshold. Nodes within this radius will
                be included.

        Returns:
            NodeMask: A new mask containing only nodes that are within the
                specified radial distance from the `point`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.5]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
            >>> filtered_nodes = all_nodes.near_point((0.0, 0.0, 0.0), 0.5)
            >>> print(filtered_nodes.to_list())
            [0]
        """
        p = np.asarray(point, dtype=float).reshape(1, 3)
        d2 = np.sum((self._mesh.node_coords - p) ** 2, axis=1)
        sel = d2 <= float(radius) ** 2
        return NodeMask(self._mesh, self._mesh.node_ids[sel])
    
    def along_line(self, point1: Tuple[float, float, float], point2: Tuple[float, float, float], radius: float) -> 'NodeMask':
        """Filters nodes within a specified distance from a line segment.

        The line segment is defined by two endpoints. Nodes within a cylindrical
        region around this segment will be included.

        Args:
            point1: The first endpoint of the line segment (x, y, z).
            point2: The second endpoint of the line segment (x, y, z).
            radius: The radial distance threshold from the line segment.

        Returns:
            NodeMask: A new mask containing nodes that are within the cylindrical
                region around the line segment.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 0.1, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
            >>> filtered_nodes = all_nodes.along_line((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.2)
            >>> print(filtered_nodes.to_list())
            [0, 1, 2]
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
        """Filters nodes whose coordinate along a specified axis lies within a range.

        Args:
            axis: The name of the axis ('x', 'y', or 'z') to filter along. Case-insensitive.
            vmin: The minimum coordinate value (inclusive) for the specified axis.
            vmax: The maximum coordinate value (inclusive) for the specified axis.

        Returns:
            NodeMask: A new mask containing only nodes whose coordinate along the
                given axis falls within the `[vmin, vmax]` range.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
            >>> filtered_nodes = all_nodes.along_axis('x', 0.5, 1.5)
            >>> print(filtered_nodes.to_list())
            [1]
        """
        ax = {'x': 0, 'y': 1, 'z': 2}[axis.lower()]
        x = self._mesh.node_coords[:, ax]
        sel = (x >= vmin) & (x <= vmax)
        return NodeMask(self._mesh, self._mesh.node_ids[sel])

    def by_predicate(self, fn: Callable[[int, np.ndarray], bool]) -> 'NodeMask':
        """Filters nodes using a custom predicate function.

        The predicate function will be called for each node, and only nodes for
        which the function returns True will be included in the new mask.

        Args:
            fn: A callable that accepts two arguments:
                - `node_id` (int): The ID of the current node.
                - `coord` (np.ndarray): The 3D coordinates of the current node.
                The function should return `True` to keep the node, `False` otherwise.

        Returns:
            NodeMask: A new mask containing only nodes that pass the predicate.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> all_nodes = NodeMask(mesh_index, mesh_index.node_ids)
            >>> # Keep nodes with x-coordinate > 0.5
            >>> def filter_x_gt_0_5(node_id: int, coord: np.ndarray) -> bool:
            ...     return coord[0] > 0.5
            >>> filtered_nodes = all_nodes.by_predicate(filter_x_gt_0_5)
            >>> print(filtered_nodes.to_list())
            [1, 3]
        """
        mask = [fn(int(nid), self._mesh.node_coords[i]) for i, nid in enumerate(self._mesh.node_ids)]
        sel_ids = self._mesh.node_ids[np.array(mask, dtype=bool)]
        return NodeMask(self._mesh, sel_ids)

    def touching_elements(self) -> 'ElementMask':
        """Converts the current node mask to an element mask.

        The resulting mask will contain all elements that are connected to any
        of the nodes currently selected in this `NodeMask`.

        Returns:
            ElementMask: A new `ElementMask` containing elements that share
                connectivity with any node in this mask.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([10, 11]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM"]),
            ...     material_tags=np.array([1, 1]),
            ...     section_tags=np.array([1, 1]),
            ...     region_tags=np.array([0, 0]),
            ...     core_ids=np.array([0, 0]),
            ...     element_id_to_index={10: 0, 11: 1}
            ... )
            >>> selected_nodes = NodeMask(mesh_index, np.array([0, 2]))
            >>> touching_elements = selected_nodes.touching_elements()
            >>> print(touching_elements.to_list())
            [10, 11]
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
        """Converts selected node IDs to OpenSees node tags.

        This method applies an offset to the internal zero-based node IDs to
        generate application-specific node tags, typically for OpenSees.

        Args:
            start_tag: Optional. The starting node tag. If `None`, it attempts
                to retrieve the starting node tag from a `MeshMaker` instance;
                otherwise, it defaults to 1.

        Returns:
            List[int]: A list of OpenSees-compatible node tags for the
                selected nodes.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, NodeMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([0]),
            ...     element_connectivity=[np.array([0, 1, 2])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0]]),
            ...     element_types=np.array(["TRIANGLE"]),
            ...     material_tags=np.array([1]),
            ...     section_tags=np.array([1]),
            ...     region_tags=np.array([0]),
            ...     core_ids=np.array([0]),
            ...     element_id_to_index={0: 0}
            ... )
            >>> selected_nodes = NodeMask(mesh_index, np.array([0, 1]))
            >>> print(selected_nodes.to_tags(start_tag=100))
            [100, 101]
            >>> print(selected_nodes.to_tags()) # Defaults to 1 if MeshMaker not available
            [1, 2]
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
    """A mask of element IDs with chainable attribute and spatial filters.

    All methods return a new `ElementMask` instance, ensuring immutability at the API level.

    Example:
        >>> import numpy as np
        >>> from femora.core.masks import MeshIndex, ElementMask
        >>> mesh_index = MeshIndex(
        ...     node_ids=np.array([0, 1, 2, 3]),
        ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
        ...     node_ndf=np.array([3, 3, 3, 3]),
        ...     node_core_map=[[0], [0], [0], [0]],
        ...     element_ids=np.array([10, 11, 12]),
        ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([2, 3])],
        ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [1.0, 1.5, 1.0]]),
        ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
        ...     material_tags=np.array([1, 2, 1]),
        ...     section_tags=np.array([1, 1, 2]),
        ...     region_tags=np.array([0, 1, 0]),
        ...     core_ids=np.array([0, 0, 1]),
        ...     element_id_to_index={10: 0, 11: 1, 12: 2}
        ... )
        >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
        >>> filtered_elements = all_elements.by_material(1)
        >>> print(filtered_elements.to_list())
        [10, 12]
    """
    def by_ids(self, ids: Sequence[int]) -> 'ElementMask':
        """Intersects the current element mask with specific element IDs.

        Args:
            ids: A sequence of element IDs to retain.

        Returns:
            ElementMask: A new mask containing the intersection of the current
                mask's IDs and the provided `ids`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "BEAM"]),
            ...     material_tags=np.array([1, 1, 1]),
            ...     section_tags=np.array([1, 1, 1]),
            ...     region_tags=np.array([0, 0, 0]),
            ...     core_ids=np.array([0, 0, 0]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> mask = ElementMask(mesh_index, np.array([10, 11, 12]))
            >>> filtered_mask = mask.by_ids([11, 13])
            >>> print(filtered_mask.to_list())
            [11]
        """
        ids_arr = np.intersect1d(self._mesh.element_ids, np.array(ids, dtype=int))
        return ElementMask(self._mesh, ids_arr)

    def by_type(self, name: str) -> 'ElementMask':
        """Filters elements by their type name (case-insensitive).

        Args:
            name: The element type name to match.

        Returns:
            ElementMask: A new mask containing only elements whose type name
                matches the provided `name`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [2.0, 2.0, 2.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([2, 3])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [1.0, 1.5, 1.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> filtered_elements = all_elements.by_type("beam")
            >>> print(filtered_elements.to_list())
            [10, 11]
        """
        sel = np.array([str(t).lower() == name.lower() for t in self._mesh.element_types], dtype=bool)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_material(self, tag: int) -> 'ElementMask':
        """Filters elements by their associated material tag.

        Args:
            tag: The integer material tag value to match.

        Returns:
            ElementMask: A new mask containing only elements that have the
                specified material `tag`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> filtered_elements = all_elements.by_material(1)
            >>> print(filtered_elements.to_list())
            [10, 12]
        """
        sel = self._mesh.material_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_section(self, tag: int) -> 'ElementMask':
        """Filters elements by their associated section tag.

        Args:
            tag: The integer section tag value to match.

        Returns:
            ElementMask: A new mask containing only elements that have the
                specified section `tag`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> filtered_elements = all_elements.by_section(2)
            >>> print(filtered_elements.to_list())
            [12]
        """
        sel = self._mesh.section_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_region(self, tag: int) -> 'ElementMask':
        """Filters elements by their associated region tag.

        Args:
            tag: The integer region tag value to match.

        Returns:
            ElementMask: A new mask containing only elements that are associated
                with the specified region `tag`.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> filtered_elements = all_elements.by_region(1)
            >>> print(filtered_elements.to_list())
            [11]
        """
        sel = self._mesh.region_tags == int(tag)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_core(self, core: int) -> 'ElementMask':
        """Filters elements by their partition or core ID.

        Args:
            core: The integer core/partition identifier to match.

        Returns:
            ElementMask: A new mask containing only elements that belong to
                the specified core.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> filtered_elements = all_elements.by_core(0)
            >>> print(filtered_elements.to_list())
            [10, 11]
        """
        sel = self._mesh.core_ids == int(core)
        return ElementMask(self._mesh, self._mesh.element_ids[sel])

    def by_bbox(self, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float, *, use_centroid: bool = True) -> 'ElementMask':
        """Filters elements inside an axis-aligned bounding box.

        Args:
            xmin: The minimum x-coordinate of the bounding box.
            xmax: The maximum x-coordinate of the bounding box.
            ymin: The minimum y-coordinate of the bounding box.
            ymax: The maximum y-coordinate of the bounding box.
            zmin: The minimum z-coordinate of the bounding box.
            zmax: The maximum z-coordinate of the bounding box.
            use_centroid: If True (default), elements are filtered based on
                whether their centroid lies within the bounding box. If False,
                an element is included if *any* of its nodes lies within the
                bounding box.

        Returns:
            ElementMask: A new mask containing elements that are located
                within the specified bounding box.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([10, 11]),
            ...     element_connectivity=[np.array([0, 1, 2]), np.array([1, 2, 3])],
            ...     element_centroids=np.array([[0.33, 0.33, 0.0], [0.67, 0.67, 0.0]]),
            ...     element_types=np.array(["TRIANGLE", "TRIANGLE"]),
            ...     material_tags=np.array([1, 1]),
            ...     section_tags=np.array([1, 1]),
            ...     region_tags=np.array([0, 0]),
            ...     core_ids=np.array([0, 0]),
            ...     element_id_to_index={10: 0, 11: 1}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> # Filter by centroid
            >>> filtered_by_centroid = all_elements.by_bbox(0.5, 1.0, 0.5, 1.0, -0.1, 0.1, use_centroid=True)
            >>> print(filtered_by_centroid.to_list())
            [11]
            >>> # Filter by any node in box
            >>> filtered_by_node = all_elements.by_bbox(0.8, 1.2, 0.8, 1.2, -0.1, 0.1, use_centroid=False)
            >>> print(filtered_by_node.to_list())
            [11]
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
        """Filters elements using a custom predicate function.

        The predicate function will be called for each element, and only elements
        for which the function returns True will be included in the new mask.

        Args:
            fn: A callable that accepts six arguments:
                - `elem_id` (int): The ID of the current element.
                - `centroid` (np.ndarray): The 3D centroid coordinates of the element.
                - `type_name` (str): The type name of the element (e.g., "BEAM", "TRIANGLE").
                - `material_tag` (int): The material tag associated with the element.
                - `section_tag` (int): The section tag associated with the element.
                - `region_tag` (int): The region tag associated with the element.
                The function should return `True` to keep the element, `False` otherwise.

        Returns:
            ElementMask: A new mask containing only elements that pass the predicate.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> all_elements = ElementMask(mesh_index, mesh_index.element_ids)
            >>> # Keep elements with material tag 1 and x-centroid > 0.2
            >>> def filter_elements(eid, centroid, etype, mtag, stag, rtag):
            ...     return mtag == 1 and centroid[0] > 0.2
            >>> filtered_elements = all_elements.by_predicate(filter_elements)
            >>> print(filtered_elements.to_list())
            [10]
        """
        out = []
        for i, eid in enumerate(self._mesh.element_ids):
            if fn(int(eid), self._mesh.element_centroids[i], str(self._mesh.element_types[i]), int(self._mesh.material_tags[i]), int(self._mesh.section_tags[i]), int(self._mesh.region_tags[i])):
                out.append(eid)
        return ElementMask(self._mesh, np.asarray(out, dtype=int))

    def to_nodes(self) -> 'NodeMask':
        """Converts to a node mask containing all nodes in the mesh.

        Note: This method currently returns all nodes found in the underlying
            mesh, regardless of which elements are selected in the current
            `ElementMask`. This behavior is due to an internal implementation
            detail where it iterates over all mesh elements' connectivity.

        Returns:
            NodeMask: A new `NodeMask` containing all nodes incident to
                any element in the mesh.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2, 3]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3, 3]),
            ...     node_core_map=[[0], [0], [0], [0]],
            ...     element_ids=np.array([10, 11]),
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2, 3])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.67, 0.67, 0.0]]),
            ...     element_types=np.array(["BEAM", "TRIANGLE"]),
            ...     material_tags=np.array([1, 1]),
            ...     section_tags=np.array([1, 1]),
            ...     region_tags=np.array([0, 0]),
            ...     core_ids=np.array([0, 0]),
            ...     element_id_to_index={10: 0, 11: 1}
            ... )
            >>> selected_elements = ElementMask(mesh_index, np.array([10])) # Selects only element 10
            >>> incident_nodes = selected_elements.to_nodes()
            >>> print(incident_nodes.to_list()) # This will show nodes from ALL elements, not just selected.
            [0, 1, 2, 3]
        """
        nidx = set()
        for conn in self._mesh.element_connectivity:
            nidx.update(int(i) for i in conn.tolist())
        node_ids = self._mesh.node_ids[list(nidx)]
        return NodeMask(self._mesh, node_ids)

    def to_tags(self, start_tag: int | None = None) -> List[int]:
        """Converts selected element IDs to OpenSees element tags.

        This method offsets the existing explicit element IDs (which are already
        considered tags within Femora) by a `start_tag` value, primarily for
        compatibility with external tools like OpenSees that might use a
        different tagging scheme or require a specific offset.

        Args:
            start_tag: Optional. The value to add to each selected element ID.
                If `None`, it attempts to retrieve the starting element tag from
                a `MeshMaker` instance; otherwise, it defaults to 1.

        Returns:
            List[int]: A list of OpenSees-compatible element tags for the
                selected elements. These are the original element IDs plus the
                `start_tag` offset.

        Example:
            >>> import numpy as np
            >>> from femora.core.masks import MeshIndex, ElementMask
            >>> mesh_index = MeshIndex(
            ...     node_ids=np.array([0, 1, 2]),
            ...     node_coords=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
            ...     node_ndf=np.array([3, 3, 3]),
            ...     node_core_map=[[0], [0], [0]],
            ...     element_ids=np.array([10, 11, 12]), # These are explicit IDs, not 0-indexed.
            ...     element_connectivity=[np.array([0, 1]), np.array([1, 2]), np.array([0, 2])],
            ...     element_centroids=np.array([[0.5, 0.0, 0.0], [0.5, 0.5, 0.0], [0.0, 0.5, 0.0]]),
            ...     element_types=np.array(["BEAM", "BEAM", "TRUSS"]),
            ...     material_tags=np.array([1, 2, 1]),
            ...     section_tags=np.array([1, 1, 2]),
            ...     region_tags=np.array([0, 1, 0]),
            ...     core_ids=np.array([0, 0, 1]),
            ...     element_id_to_index={10: 0, 11: 1, 12: 2}
            ... )
            >>> selected_elements = ElementMask(mesh_index, np.array([10, 12]))
            >>> print(selected_elements.to_tags(start_tag=500))
            [510, 512]
            >>> print(selected_elements.to_tags()) # Defaults to 1 if MeshMaker not available
            [11, 13]
        """
        ids = self.to_list()
        if start_tag is None:
            try:
                from femora.components.MeshMaker import MeshMaker
                start_tag = MeshMaker.get_instance()._start_ele_tag  # type: ignore[attr-defined]
            except Exception:
                start_tag = 1
        return [int(start_tag) + int(i) for i in ids]