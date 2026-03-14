from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pyvista as pv


class PartitionerError(RuntimeError):
    """Raised when a partitioning method fails or returns invalid output."""


PartitionerFunc = Callable[[pv.UnstructuredGrid, int], np.ndarray]


@dataclass(frozen=True)
class _RegisteredPartitioner:
    func: Callable[..., np.ndarray]
    is_available: Callable[[], bool]


class PartitionerRegistry:
    """Registry for Femora mesh partitioners.

    A partitioner maps a mesh's cells to integer partition ids in
    ``[0, num_partitions-1]``.
    """

    _partitioners: Dict[str, _RegisteredPartitioner] = {}

    @staticmethod
    def register(
        name: str,
        func: Callable[..., np.ndarray],
        *,
        is_available: Optional[Callable[[], bool]] = None,
    ) -> None:
        key = name.strip().lower()
        if not key:
            raise ValueError("Partitioner name cannot be empty")
        PartitionerRegistry._partitioners[key] = _RegisteredPartitioner(
            func=func,
            is_available=is_available or (lambda: True),
        )

    @staticmethod
    def get_available_types(*, include_unavailable: bool = False) -> List[str]:
        if include_unavailable:
            return sorted(PartitionerRegistry._partitioners.keys())
        return sorted(
            name
            for name, reg in PartitionerRegistry._partitioners.items()
            if reg.is_available()
        )

    @staticmethod
    def validate(name: str) -> None:
        key = name.strip().lower()
        if key not in PartitionerRegistry._partitioners:
            raise ValueError(
                f"Invalid partitioner: {name}. Available: {PartitionerRegistry.get_available_types(include_unavailable=True)}"
            )

        if not PartitionerRegistry._partitioners[key].is_available():
            raise ImportError(
                f"Partitioner '{name}' is registered but not available in this environment. "
                "Install the required optional dependency for this partitioner."
            )

    @staticmethod
    def partition(
        mesh: pv.UnstructuredGrid,
        num_partitions: int,
        *,
        partitioner: str = "kd-tree",
        **kwargs: Any,
    ) -> np.ndarray:
        if num_partitions < 1:
            raise ValueError(f"num_partitions must be >= 1. Got {num_partitions}.")

        key = partitioner.strip().lower()
        PartitionerRegistry.validate(key)

        labels = PartitionerRegistry._partitioners[key].func(mesh, num_partitions, **kwargs)
        labels = np.asarray(labels, dtype=int)

        if labels.shape != (mesh.n_cells,):
            raise PartitionerError(
                f"Partitioner '{partitioner}' returned shape {labels.shape}, expected ({mesh.n_cells},)."
            )

        if labels.size:
            if labels.min() < 0:
                raise PartitionerError(f"Partitioner '{partitioner}' produced negative ids")
            if labels.max() >= num_partitions:
                raise PartitionerError(
                    f"Partitioner '{partitioner}' produced ids up to {labels.max()}, but num_partitions={num_partitions}."
                )

        return labels


def _cell_centers(mesh: pv.UnstructuredGrid) -> np.ndarray:
    centers = mesh.cell_centers()
    return np.asarray(centers.points, dtype=float)


def _balanced_labels_from_sorted_order(sorted_cell_ids: np.ndarray, num_partitions: int) -> np.ndarray:
    n = int(sorted_cell_ids.size)
    labels = np.empty(n, dtype=int)
    # Partition indices into nearly-equal chunks.
    cuts = np.linspace(0, n, num_partitions + 1, dtype=int)
    for part_id in range(num_partitions):
        start = int(cuts[part_id])
        end = int(cuts[part_id + 1])
        labels[start:end] = part_id
    out = np.empty(n, dtype=int)
    out[sorted_cell_ids] = labels
    return out


def _partition_kd_tree(mesh: pv.UnstructuredGrid, num_partitions: int) -> np.ndarray:
    """Simple KD-tree partitioning using recursive bisection of cell centers."""
    pts = _cell_centers(mesh)
    n_cells = pts.shape[0]
    if n_cells == 0:
        return np.zeros((0,), dtype=int)
    if num_partitions == 1:
        return np.zeros((n_cells,), dtype=int)

    labels = np.full(n_cells, -1, dtype=int)
    next_label = 0

    def split(indices: np.ndarray, parts: int) -> None:
        nonlocal next_label
        if parts <= 1 or indices.size == 0:
            labels[indices] = next_label
            next_label += 1
            return

        # Split along axis with largest spread.
        subset = pts[indices]
        mins = subset.min(axis=0)
        maxs = subset.max(axis=0)
        axis = int(np.argmax(maxs - mins))

        order = np.argsort(subset[:, axis], kind="mergesort")
        mid = int(order.size // 2)
        left = indices[order[:mid]]
        right = indices[order[mid:]]

        left_parts = parts // 2
        right_parts = parts - left_parts
        split(left, left_parts)
        split(right, right_parts)

    split(np.arange(n_cells, dtype=int), num_partitions)
    if (labels < 0).any():
        raise PartitionerError("kd-tree partitioner failed to assign all cells")
    # Re-label to ensure ids are contiguous [0..k-1]
    unique = np.unique(labels)
    remap = {old: new for new, old in enumerate(unique.tolist())}
    return np.vectorize(remap.get, otypes=[int])(labels).astype(int)


def _partition_geometric(mesh: pv.UnstructuredGrid, num_partitions: int) -> np.ndarray:
    """Geometric recursive coordinate bisection (RCB) of cell centers."""
    pts = _cell_centers(mesh)
    n_cells = pts.shape[0]
    if n_cells == 0:
        return np.zeros((0,), dtype=int)
    if num_partitions == 1:
        return np.zeros((n_cells,), dtype=int)

    labels = np.full(n_cells, -1, dtype=int)
    next_label = 0

    def split(indices: np.ndarray, parts: int) -> None:
        nonlocal next_label
        if parts <= 1 or indices.size == 0:
            labels[indices] = next_label
            next_label += 1
            return

        subset = pts[indices]
        axis = int(np.argmax(np.var(subset, axis=0)))
        order = np.argsort(subset[:, axis], kind="mergesort")
        mid = int(order.size // 2)
        left = indices[order[:mid]]
        right = indices[order[mid:]]

        left_parts = parts // 2
        right_parts = parts - left_parts
        split(left, left_parts)
        split(right, right_parts)

    split(np.arange(n_cells, dtype=int), num_partitions)
    if (labels < 0).any():
        raise PartitionerError("geometric partitioner failed to assign all cells")
    unique = np.unique(labels)
    remap = {old: new for new, old in enumerate(unique.tolist())}
    return np.vectorize(remap.get, otypes=[int])(labels).astype(int)


def _morton_key_ints(coords: np.ndarray) -> np.ndarray:
    """Compute 64-bit Morton (Z-order) keys for 3D integer coordinates.

    Notes:
        This is a 21-bit-per-axis Morton code (63 bits total) packed into
        ``uint64``. Inputs are expected to be in ``[0, 2**21-1]``; the partitioner
        quantizes coordinates accordingly.
    """
    coords = coords.astype(np.uint64, copy=False)
    x = coords[:, 0]
    y = coords[:, 1]
    z = coords[:, 2]

    def part1by2(v: np.ndarray) -> np.ndarray:
        # Spread 21 bits so there are 2 zeros between each bit.
        v = v & 0x1FFFFF
        v = (v | (v << 32)) & 0x1F00000000FFFF
        v = (v | (v << 16)) & 0x1F0000FF0000FF
        v = (v | (v << 8)) & 0x100F00F00F00F00F
        v = (v | (v << 4)) & 0x10C30C30C30C30C3
        v = (v | (v << 2)) & 0x1249249249249249
        return v

    # Maintain the same x/y/z bit ordering as the previous implementation.
    return (part1by2(x) << 2) | (part1by2(y) << 1) | part1by2(z)


def _partition_morton(mesh: pv.UnstructuredGrid, num_partitions: int) -> np.ndarray:
    pts = _cell_centers(mesh)
    n_cells = pts.shape[0]
    if n_cells == 0:
        return np.zeros((0,), dtype=int)
    if num_partitions == 1:
        return np.zeros((n_cells,), dtype=int)

    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    span = np.where(maxs > mins, maxs - mins, 1.0)
    norm = (pts - mins) / span

    # Use 21-bit quantization to match the 64-bit Morton implementation.
    bits = 21
    scale = (1 << bits) - 1
    q = np.clip((norm * scale).round(), 0, scale).astype(np.uint64)
    keys = _morton_key_ints(q)
    order = np.argsort(keys, kind="mergesort")
    return _balanced_labels_from_sorted_order(order, num_partitions)


def _hilbert_c2i(p: int, x: List[int]) -> int:
    """Convert n-D coordinates to a 1D Hilbert index.

    This uses a direct implementation of the well-known Skilling algorithm.
    Here we only use n=3.
    """

    n = len(x)
    x = x[:]  # local copy
    M = 1 << (p - 1)

    # Inverse undo excess work
    Q = M
    while Q > 1:
        P = Q - 1
        for i in range(n - 1, -1, -1):
            if x[i] & Q:
                x[0] ^= P
            else:
                t = (x[0] ^ x[i]) & P
                x[0] ^= t
                x[i] ^= t
        Q >>= 1

    # Gray encode
    for i in range(1, n):
        x[i] ^= x[i - 1]
    t = 0
    Q = M
    while Q > 1:
        if x[n - 1] & Q:
            t ^= Q - 1
        Q >>= 1
    for i in range(n):
        x[i] ^= t

    # Transpose to index
    index = 0
    for i in range(p - 1, -1, -1):
        for j in range(n):
            index = (index << 1) | ((x[j] >> i) & 1)
    return int(index)


def _hilbert_keys_3d(q: np.ndarray, p: int) -> np.ndarray:
    """Vectorized 3D Hilbert index for integer coordinates.

    Args:
        q: Array of shape (N, 3) with integer coordinates in ``[0, 2**p - 1]``.
        p: Number of bits per axis.

    Returns:
        Array of shape (N,) with ``uint64`` Hilbert indices.

    Notes:
        This is a vectorized form of the Skilling coordinate-to-index algorithm
        used in `_hilbert_c2i`, avoiding per-point Python loops.
    """
    q = np.asarray(q)
    if q.ndim != 2 or q.shape[1] != 3:
        raise ValueError(f"Expected q shape (N,3), got {q.shape}")

    x0 = q[:, 0].astype(np.uint64, copy=True)
    x1 = q[:, 1].astype(np.uint64, copy=True)
    x2 = q[:, 2].astype(np.uint64, copy=True)

    M = np.uint64(1) << np.uint64(p - 1)

    # Inverse undo excess work (Skilling)
    Q = M
    while Q > 1:
        P = Q - 1

        # i = 2
        mask = (x2 & Q) != 0
        np.bitwise_xor(x0, P, out=x0, where=mask)
        t = np.bitwise_and(np.bitwise_xor(x0, x2), P)
        inv = ~mask
        np.bitwise_xor(x0, t, out=x0, where=inv)
        np.bitwise_xor(x2, t, out=x2, where=inv)

        # i = 1
        mask = (x1 & Q) != 0
        np.bitwise_xor(x0, P, out=x0, where=mask)
        t = np.bitwise_and(np.bitwise_xor(x0, x1), P)
        inv = ~mask
        np.bitwise_xor(x0, t, out=x0, where=inv)
        np.bitwise_xor(x1, t, out=x1, where=inv)

        # i = 0 (only affects x0)
        mask = (x0 & Q) != 0
        np.bitwise_xor(x0, P, out=x0, where=mask)

        Q >>= 1

    # Gray encode
    x1 ^= x0
    x2 ^= x1

    t = np.zeros_like(x0)
    Q = M
    while Q > 1:
        P = Q - 1
        mask = (x2 & Q) != 0
        np.bitwise_xor(t, P, out=t, where=mask)
        Q >>= 1

    x0 ^= t
    x1 ^= t
    x2 ^= t

    # Transpose to index
    index = np.zeros(x0.shape[0], dtype=np.uint64)
    for i in range(p - 1, -1, -1):
        index <<= 3
        index |= ((x0 >> i) & 1) << 2
        index |= ((x1 >> i) & 1) << 1
        index |= ((x2 >> i) & 1)

    return index


def _partition_hilbert(mesh: pv.UnstructuredGrid, num_partitions: int) -> np.ndarray:
    pts = _cell_centers(mesh)
    n_cells = pts.shape[0]
    if n_cells == 0:
        return np.zeros((0,), dtype=int)
    if num_partitions == 1:
        return np.zeros((n_cells,), dtype=int)

    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    span = np.where(maxs > mins, maxs - mins, 1.0)
    norm = (pts - mins) / span

    p = 21
    scale = (1 << p) - 1
    q = np.clip((norm * scale).round(), 0, scale).astype(np.uint64)

    keys = _hilbert_keys_3d(q, p)

    order = np.argsort(keys, kind="mergesort")
    return _balanced_labels_from_sorted_order(order, num_partitions)


def _is_pymetis_available() -> bool:
    return importlib.util.find_spec("pymetis") is not None


def _build_cell_adjacency(mesh: pv.UnstructuredGrid) -> List[List[int]]:
    n = int(mesh.n_cells)
    adjacency: List[List[int]] = [[] for _ in range(n)]
    for cell_id in range(n):
        neigh = mesh.cell_neighbors(cell_id, connections="faces")
        adjacency[cell_id] = [int(i) for i in neigh]
    return adjacency


def _partition_metis(mesh: pv.UnstructuredGrid, num_partitions: int) -> np.ndarray:
    if not _is_pymetis_available():
        raise ImportError("pymetis is required for the 'metis' partitioner")

    import pymetis  # type: ignore

    n_cells = int(mesh.n_cells)
    if n_cells == 0:
        return np.zeros((0,), dtype=int)
    if num_partitions == 1:
        return np.zeros((n_cells,), dtype=int)

    # Prefer METIS' mesh partitioning interface (lets METIS build the graph in C).
    # This avoids the expensive Python/VTK neighbor queries needed to construct
    # an element adjacency list.
    n_parts = int(min(num_partitions, n_cells))
    if n_parts <= 1:
        return np.zeros((n_cells,), dtype=int)

    if hasattr(pymetis, "part_mesh"):
        offsets = np.asarray(mesh.offset)
        conn = np.asarray(mesh.cell_connectivity)
        connectivity = [
            conn[int(offsets[i]) : int(offsets[i + 1])].tolist() for i in range(n_cells)
        ]

        mesh_partition = pymetis.part_mesh(
            n_parts,
            connectivity=connectivity,
            gtype=getattr(pymetis, "GType", None).NODAL if hasattr(pymetis, "GType") else None,
        )

        parts = getattr(mesh_partition, "element_part", None)
        if parts is None:
            # Fallback to tuple-style return: (edge_cuts, element_part, vertex_part)
            parts = mesh_partition[1]
    else:
        # Backward fallback for very old pymetis builds.
        adjacency = _build_cell_adjacency(mesh)
        _, parts = pymetis.part_graph(n_parts, adjacency=adjacency)

    labels = np.asarray(parts, dtype=int)
    if labels.shape != (n_cells,):
        raise PartitionerError(
            f"METIS returned shape {labels.shape}, expected ({n_cells},)."
        )
    return labels


# Register built-ins
PartitionerRegistry.register("kd-tree", _partition_kd_tree)
PartitionerRegistry.register("geometric", _partition_geometric)
PartitionerRegistry.register("morton", _partition_morton)
PartitionerRegistry.register("hilbert", _partition_hilbert)
PartitionerRegistry.register("metis", _partition_metis, is_available=_is_pymetis_available)


__all__ = [
    "PartitionerError",
    "PartitionerRegistry",
]
