from __future__ import annotations

from typing import Optional, Tuple, List, Dict

import numpy as np

try:
    import pyvista as pv  # type: ignore
except Exception:  # pragma: no cover
    pv = None  # type: ignore

from femora.components.Assemble.Assembler import Assembler
from femora.components.event.event_bus import EventBus, FemoraEvent
from .mask_base import MeshIndex, NodeMask, ElementMask


class MaskManager:
    """
    Entrypoint for creating node/element masks after assembly.

    This class builds a :class:`MeshIndex` snapshot from the current assembled
    mesh and exposes typed views via ``nodes`` and ``elements`` properties.

    Usage::

        mm = MaskManager.from_assembled()
        top_nodes = mm.nodes.by_bbox(0, 10, -1e9, 1e9, -1e9, 1e9)
        elems = top_nodes.touching_elements().by_material(3)

    Guard:
        Raises ``RuntimeError`` if called before assembly is completed.
    """

    _cached_index: MeshIndex | None = None

    def __init__(self, mesh_index: MeshIndex):
        self._mesh = mesh_index

    @classmethod
    def from_assembled(cls) -> 'MaskManager':
        assembler = Assembler.get_instance()
        grid = assembler.get_mesh()
        if grid is None:
            raise RuntimeError("MaskManager requires an assembled mesh; call Assembler.Assemble() first")
        if cls._cached_index is None:
            cls._cached_index = cls._build_index_from_grid(grid)
        return cls(cls._cached_index)

    @classmethod
    def _build_index_from_grid(cls, grid) -> MeshIndex:
        # Node arrays
        node_coords = np.asarray(grid.points)
        node_ids = np.arange(node_coords.shape[0], dtype=int)
        node_ndf = np.asarray(grid.point_data.get("ndf", np.zeros((node_coords.shape[0],), dtype=int)))

        # Element arrays
        ncells = int(grid.n_cells)
        elem_tags = grid.cell_data.get("ElementTag")
        element_ids = np.asarray(elem_tags, dtype=int) if elem_tags is not None else np.arange(ncells, dtype=int)

        # Connectivity from offset and cell_connectivity
        offsets = np.asarray(grid.offset)
        connectivity = np.asarray(grid.cell_connectivity)
        conn_list: List[np.ndarray] = []
        for i, start in enumerate(offsets):
            end = int(offsets[i + 1]) if i + 1 < len(offsets) else int(connectivity.size)
            conn_list.append(connectivity[start:end].astype(int, copy=False))

        # Centroids and attributes
        element_centroids = np.asarray(grid.cell_centers().points)
        element_types = np.asarray(getattr(grid, "celltypes", np.zeros((ncells,), dtype=int)))
        material_tags = np.asarray(grid.cell_data.get("MaterialTag", np.zeros(ncells, dtype=int)))
        section_tags = np.asarray(grid.cell_data.get("SectionTag", np.zeros(ncells, dtype=int)))
        region_tags = np.asarray(grid.cell_data.get("Region", np.zeros(ncells, dtype=int)))
        core_ids = np.asarray(grid.cell_data.get("Core", np.zeros(ncells, dtype=int)))

        # Node -> pids map: collect core ids per element and propagate to incident nodes
        node_core_map: List[List[int]] = [list() for _ in range(node_ids.size)]
        elem_id_to_index: Dict[int, int] = {}
        for idx, eid in enumerate(element_ids.tolist()):
            elem_id_to_index[int(eid)] = idx
            pid = int(core_ids[idx])
            for nidx in conn_list[idx].tolist():
                if pid not in node_core_map[int(nidx)]:
                    node_core_map[int(nidx)].append(pid)

        return MeshIndex(
            node_ids=node_ids,
            node_coords=node_coords,
            element_ids=element_ids,
            element_connectivity=conn_list,
            element_centroids=element_centroids,
            element_types=element_types,
            material_tags=material_tags,
            section_tags=section_tags,
            region_tags=region_tags,
            core_ids=core_ids,
            node_ndf=node_ndf,
            node_core_map=node_core_map,
            element_id_to_index=elem_id_to_index,
        )
        
    @property
    def nodes(self) -> NodeMask:
        """Return a ``NodeMask`` initialized with all nodes."""
        return NodeMask(self._mesh, self._mesh.node_ids)

    @property
    def elements(self) -> ElementMask:
        """Return an ``ElementMask`` initialized with all elements."""
        return ElementMask(self._mesh, self._mesh.element_ids)


def _mask_on_post_assemble(**kwargs):
    assembler = Assembler.get_instance()
    grid = kwargs.get('assembled_mesh', assembler.get_mesh())
    if grid is not None:
        MaskManager._cached_index = MaskManager._build_index_from_grid(grid)


EventBus.subscribe(FemoraEvent.POST_ASSEMBLE, _mask_on_post_assemble)


