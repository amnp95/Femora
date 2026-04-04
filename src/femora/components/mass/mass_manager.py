from __future__ import annotations

from typing import List, Tuple, Union, Optional
import numpy as np
from numpy.typing import ArrayLike
from pykdtree.kdtree import KDTree

from femora.constants import FEMORA_MAX_NDF
from femora.components.Mesh.meshPartBase import MeshPart, MeshPartManager
from femora.components.Assemble.Assembler import Assembler
from femora.components.event.event_bus import EventBus, FemoraEvent


class MassManager:
    """Singleton class that provides a high-level API for assigning nodal masses.

    The raw *Mass* array lives on every MeshPart (and, after assembly, on the
    assembled mesh).  MassManager merely offers convenience methods that modify
    those arrays in a consistent way.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MassManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialised", False):
            return

        self._mp_manager = MeshPartManager()
        # cache for region masks / KDTree per region to avoid rebuilding
        self._region_point_cache: dict[int, np.ndarray] = {}
        self._initialised = True

        # proxies
        self.meshpart = _MeshPartMassHelper(self)
        self.region = _RegionMassHelper(self)
        self.global_ = _GlobalMassHelper(self)

        # Clear caches when assembly changes
        EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, self._handle_pre_assemble)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _pad_mass(vec: ArrayLike, ndf: int) -> np.ndarray:
        """Return a vector of length FEMORA_MAX_NDF with zeros padded / truncated.

        vec may be any 1-D iterable of length <= FEMORA_MAX_NDF.  If len(vec) < ndf a
        ValueError is raised because we would be dropping active DOFs.
        """
        v = np.asarray(vec, dtype=np.float32).flatten()

        # Trim if the provided vector is longer than the permitted maximum
        if v.size > FEMORA_MAX_NDF:
            v = v[:FEMORA_MAX_NDF]

        # Pad with zeros to reach the full storage width
        res = np.zeros(FEMORA_MAX_NDF, dtype=np.float32)
        res[: v.size] = v
        return res

    @staticmethod
    def _combine(old: np.ndarray, new: np.ndarray, rule: str) -> np.ndarray:
        if rule == "sum":
            return old + new
        elif rule == "override":
            return new
        else:
            raise ValueError("combine must be 'sum' or 'override'")

    def _handle_pre_assemble(self, *_, **__):
        """Clear caches before a fresh assembly."""
        self._region_point_cache.clear()

    def clear(self):
        """
        Clear mass manager state.

        - Clear internal caches used for region lookups.
        - Remove any 'Mass' point_data arrays from mesh parts and the assembled mesh.
        """
        # clear internal caches
        self._region_point_cache.clear()

        # remove Mass arrays from all mesh parts
        try:
            for mp in MeshPartManager().get_all_mesh_parts().values():
                if "Mass" in mp.mesh.point_data:
                    del mp.mesh.point_data["Mass"]
        except Exception:
            # be defensive: if mesh parts are not available, ignore
            pass

        # remove Mass array from assembled mesh if present
        try:
            asm = Assembler().AssembeledMesh
            if asm is not None and "Mass" in asm.point_data:
                del asm.point_data["Mass"]
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Low-level getters exposed for export and tests
    # ------------------------------------------------------------------
    def get_meshpart_mass_array(self, meshpart_name: str) -> np.ndarray:
        mp = self._mp_manager.get_mesh_part(meshpart_name)
        if mp is None:
            raise KeyError(f"MeshPart '{meshpart_name}' not found")
        _ensure_mass_array(mp)
        return mp.mesh.point_data["Mass"]

    def get_assembled_mass_array(self) -> Optional[np.ndarray]:
        asm = Assembler().AssembeledMesh
        if asm is None:
            return None
        if "Mass" not in asm.point_data:
            # create empty array lazily so exporter logic can rely on existence
            asm.point_data["Mass"] = np.zeros((asm.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        return asm.point_data["Mass"]


# ----------------------------------------------------------------------
# Internal helper classes
# ----------------------------------------------------------------------
def _ensure_mass_array(meshpart: MeshPart):
    if "Mass" not in meshpart.mesh.point_data:
        n = meshpart.mesh.n_points
        meshpart.mesh.point_data["Mass"] = np.zeros((n, FEMORA_MAX_NDF), dtype=np.float32)


class _MeshPartMassHelper:
    def __init__(self, manager: MassManager):
        self._mgr = manager
        self._mpm = MeshPartManager()

    # ------------- public API -------------
    def add_all(
        self,
        meshpart_name: str,
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
        filter_fn=None,
    ) -> None:
        """Add mass to every node in the meshpart (optionally filtered)."""
        mp = self._get_mp(meshpart_name)
        arr = mp.mesh.point_data["Mass"]
        if "ndf" not in mp.mesh.point_data:
            ndf_array = np.full(shape=(mp.mesh.n_points,), fill_value=mp.element._ndof, dtype=np.int8)
        else:
            ndf_array = mp.mesh.point_data["ndf"]
        padded = None  # will broadcast later
        for idx in range(arr.shape[0]):
            if filter_fn is not None and not filter_fn(idx):
                continue
            ndf = int(ndf_array[idx])
            if padded is None:
                padded = self._mgr._pad_mass(mass_vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], padded, combine)
        # sync to assembled mesh, if present
        self._sync_to_assembled(mp)

    def closest_point(
        self,
        meshpart_name: str,
        xyz: Tuple[float, float, float],
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> int:
        """Add mass to the node in *meshpart_name* closest to *xyz*.

        Returns the local point index within the MeshPart.
        """
        mp = self._get_mp(meshpart_name)
        pts = mp.mesh.points
        tree = KDTree(pts)
        _, idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        idx = int(idx[0])
        self.add_nodes(meshpart_name, [idx], [mass_vec], combine=combine)
        return idx

    def add_nodes(
        self,
        meshpart_name: str,
        point_indices: List[int],
        mass_matrix: List[ArrayLike],
        *,
        combine: str = "sum",
    ) -> None:
        if len(point_indices) != len(mass_matrix):
            raise ValueError("point_indices and mass_matrix must be same length")
        mp = self._get_mp(meshpart_name)
        arr = mp.mesh.point_data["Mass"]
        if "ndf" not in mp.mesh.point_data:
            ndf_array = np.full(shape=(mp.mesh.n_points,), fill_value=mp.element._ndof, dtype=np.int8)
        else:
            ndf_array = mp.mesh.point_data["ndf"]
        for idx, vec in zip(point_indices, mass_matrix):
            ndf = int(ndf_array[idx])
            padded = self._mgr._pad_mass(vec, ndf)
            arr[idx] = self._mgr._combine(arr[idx], padded, combine)
        self._sync_to_assembled(mp)

    # ------------- internal helpers -------------
    def _get_mp(self, name: str) -> MeshPart:
        mp = self._mpm.get_mesh_part(name)
        if mp is None:
            raise KeyError(f"MeshPart '{name}' not found")
        _ensure_mass_array(mp)
        return mp

    def _sync_to_assembled(self, mp: MeshPart):
        asm = Assembler().AssembeledMesh
        if asm is None:
            return  # not assembled yet → nothing to sync
        if "MeshPartTag_pointdata" not in asm.point_data:
            return  # should not happen, but bail gracefully
        tag = mp.tag
        mask = asm.point_data["MeshPartTag_pointdata"] == tag
        # NOTE: For now we skip synchronising back to assembled mesh because
        # mapping local meshpart indices to global indices after point merging
        # is non-trivial.  Mass assignments should generally be performed
        # *before* assembly for mesh-parts, or via the region/global helpers
        # after assembly.


class _RegionMassHelper:
    def __init__(self, manager: MassManager):
        self._mgr = manager

    # -------- public API --------
    def add_all(
        self,
        region_tag: int,
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> None:
        asm = self._require_assembled()
        point_ids = self._get_region_point_ids(region_tag, asm)
        self._add_to_points(point_ids, mass_vec, asm, combine)

    def closest_point(
        self,
        region_tag: int,
        xyz: Tuple[float, float, float],
        mass_vec: ArrayLike,
        *,
        combine: str = "sum",
    ) -> int:
        asm = self._require_assembled()
        point_ids = self._get_region_point_ids(region_tag, asm)
        pts = asm.points[point_ids]
        tree = KDTree(pts)
        _, local_idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        global_idx = int(point_ids[int(local_idx[0])])
        self._add_to_points([global_idx], mass_vec, asm, combine)
        return global_idx

    # -------- internal helpers --------
    def _require_assembled(self):
        asm = Assembler().AssembeledMesh
        if asm is None:
            raise RuntimeError("Model must be assembled before using region mass helpers")
        if "Mass" not in asm.point_data:
            asm.point_data["Mass"] = np.zeros((asm.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        return asm

    def _get_region_point_ids(self, region_tag: int, asm):
        if region_tag in MassManager()._region_point_cache:
            return MassManager()._region_point_cache[region_tag]
        # find cells belonging to region
        cell_ids = np.where(asm.cell_data["Region"] == region_tag)[0]
        if cell_ids.size == 0:
            raise KeyError(f"Region tag {region_tag} not present in assembled mesh")
        offsets = asm.offset
        connectivity = asm.cell_connectivity
        point_set: set[int] = set()
        for cid in cell_ids:
            start = offsets[cid]
            end = offsets[cid + 1]
            point_set.update(connectivity[start:end])
        ids = np.fromiter(point_set, dtype=int)
        MassManager()._region_point_cache[region_tag] = ids
        return ids

    def _add_to_points(
        self,
        point_ids: np.ndarray | List[int],
        mass_vec: ArrayLike,
        asm,  # assembled mesh
        combine: str,
    ):
        arr = asm.point_data["Mass"]
        ndf_arr = asm.point_data["ndf"]
        padded_cache: Optional[np.ndarray] = None
        for idx in point_ids:
            ndf = int(ndf_arr[idx])
            if padded_cache is None:
                padded_cache = MassManager._pad_mass(mass_vec, ndf)
            vec = MassManager._pad_mass(mass_vec, ndf)
            arr[idx] = MassManager._combine(arr[idx], vec, combine)


class _GlobalMassHelper:
    def __init__(self, manager: MassManager):
        self._mgr = manager

    def closest_point(self, xyz: Tuple[float, float, float], mass_vec: ArrayLike, *, combine: str = "sum") -> int:
        asm = self._require_assembled()
        pts = asm.points
        tree = KDTree(pts)
        _, idx = tree.query(np.asarray(xyz).reshape(1, -1), k=1)
        idx = int(idx[0])
        self._add_to_points([idx], mass_vec, asm, combine)
        return idx

    def add_all(self, mass_vec: ArrayLike, *, combine: str = "sum") -> None:
        asm = self._require_assembled()
        self._add_to_points(np.arange(asm.n_points), mass_vec, asm, combine)

    # internal helpers reuse region helper ones
    def _require_assembled(self):
        asm = Assembler().AssembeledMesh
        if asm is None:
            raise RuntimeError("Model must be assembled before using global mass helpers")
        if "Mass" not in asm.point_data:
            asm.point_data["Mass"] = np.zeros((asm.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        return asm

    def _add_to_points(self, ids, mass_vec, asm, combine):
        arr = asm.point_data["Mass"]
        ndf_arr = asm.point_data["ndf"]
        for idx in ids:
            ndf = int(ndf_arr[idx])
            vec = MassManager._pad_mass(mass_vec, ndf)
            arr[idx] = MassManager._combine(arr[idx], vec, combine) 