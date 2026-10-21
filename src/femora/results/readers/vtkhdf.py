# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Lazy access to transient OpenSees VTKHDF recorder output."""

from __future__ import annotations

from pathlib import Path
from typing import FrozenSet, Optional, Union

import h5py
import numpy as np
import pyvista as pv

from ..base import (
    CELL_FRAME,
    CELL_HISTORY,
    MESH,
    POINT_FRAME,
    POINT_HISTORY,
    Component,
    ResultReader,
)
from ..exceptions import ResultFormatError


_COMPONENTS = {"x": 0, "y": 1, "z": 2}


class VTKHDFResultReader(ResultReader):
    """Read one VTKHDF result file without eagerly loading transient fields."""

    def __init__(self, path: Union[str, Path]) -> None:
        super().__init__(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"VTKHDF result file not found: {self.path}")
        self._file: Optional[h5py.File] = None
        self._mesh: Optional[pv.UnstructuredGrid] = None
        self._validate_layout()

    @property
    def capabilities(self) -> FrozenSet[str]:
        capabilities = {MESH}
        if self.available_point_responses:
            capabilities.update({POINT_HISTORY, POINT_FRAME})
        if self.available_cell_responses:
            capabilities.update({CELL_HISTORY, CELL_FRAME})
        return frozenset(capabilities)

    @property
    def _vtkhdf(self) -> h5py.Group:
        if self._file is None:
            self._file = h5py.File(self.path, "r")
        try:
            return self._file["VTKHDF"]
        except KeyError as exc:
            raise ResultFormatError(f"{self.path} does not contain /VTKHDF") from exc

    def _validate_layout(self) -> None:
        required = ("Points", "Steps")
        with h5py.File(self.path, "r") as result:
            if "VTKHDF" not in result:
                raise ResultFormatError(f"{self.path} does not contain /VTKHDF")
            vtkhdf = result["VTKHDF"]
            missing = [name for name in required if name not in vtkhdf]
            if missing:
                raise ResultFormatError(
                    f"{self.path} is missing VTKHDF entries: {', '.join(missing)}"
                )
            if "Values" not in vtkhdf["Steps"]:
                raise ResultFormatError(f"{self.path} is missing VTKHDF step values")

    @property
    def times(self) -> np.ndarray:
        return self._vtkhdf["Steps"]["Values"][()]

    @property
    def number_of_steps(self) -> int:
        return int(self._vtkhdf["Steps"]["Values"].shape[0])

    @property
    def available_point_responses(self) -> tuple[str, ...]:
        return self._available_responses("PointData")

    @property
    def available_cell_responses(self) -> tuple[str, ...]:
        return self._available_responses("CellData")

    def _available_responses(self, location: str) -> tuple[str, ...]:
        offsets_name = f"{location}Offsets"
        steps = self._vtkhdf["Steps"]
        if offsets_name not in steps or location not in self._vtkhdf:
            return ()
        offsets = steps[offsets_name]
        fields = self._vtkhdf[location]
        return tuple(sorted(name for name in fields if name in offsets))

    @property
    def mesh(self) -> pv.UnstructuredGrid:
        if self._mesh is None:
            self._mesh = pv.UnstructuredGrid(pv.read(self.path))
        return self._mesh

    @property
    def number_of_points(self) -> int:
        if "NumberOfPoints" in self._vtkhdf:
            return self._first_mesh_count("NumberOfPoints")
        return int(self._vtkhdf["Points"].shape[0])

    @property
    def number_of_cells(self) -> int:
        if "NumberOfCells" in self._vtkhdf:
            return self._first_mesh_count("NumberOfCells")
        return int(self.mesh.n_cells)

    def _first_mesh_count(self, name):
        counts = np.asarray(self._vtkhdf[name][()]).reshape(-1)
        steps = self._vtkhdf["Steps"]
        if "PartOffsets" in steps and "NumberOfParts" in steps:
            start = int(steps["PartOffsets"][0])
            parts = int(steps["NumberOfParts"][0])
            return int(counts[start:start+parts].sum())
        # OpenSees appends a count for every transient step, not extra cells.
        return int(counts[0]) if self.number_of_steps > 1 else int(counts.sum())

    def point_history(
        self,
        response: str,
        point_index: int,
        component: Component = None,
    ) -> np.ndarray:
        return self._history("PointData", response, point_index, component)

    def cell_history(
        self,
        response: str,
        cell_index: int,
        component: Component = None,
    ) -> np.ndarray:
        return self._history("CellData", response, cell_index, component)

    def point_frame(
        self,
        response: str,
        step: int,
        component: Component = None,
    ) -> np.ndarray:
        return self._frame("PointData", response, step, component)

    def cell_frame(
        self,
        response: str,
        step: int,
        component: Component = None,
    ) -> np.ndarray:
        return self._frame("CellData", response, step, component)

    def _history(
        self,
        location: str,
        response: str,
        entity_index: int,
        component: Component,
    ) -> np.ndarray:
        entity_count = self._entity_count(location)
        if entity_index < 0 or entity_index >= entity_count:
            raise IndexError(
                f"{location} index {entity_index} is outside [0, {entity_count})"
            )
        values, offsets = self._response_data(location, response)
        indices = offsets[()] + entity_index
        # Regular transient meshes permit a strided read instead of expensive
        # HDF5 fancy indexing over thousands of individual samples.
        stride = int(indices[1] - indices[0]) if len(indices) > 1 else 0
        if stride > 0 and np.all(np.diff(indices) == stride):
            history = values[int(indices[0]):int(indices[-1]) + 1:stride]
        else:
            history = values[indices]
        return self._select_component(history, component)

    def _frame(
        self,
        location: str,
        response: str,
        step: int,
        component: Component,
    ) -> np.ndarray:
        values, offsets = self._response_data(location, response)
        number_of_steps = offsets.shape[0]
        normalized_step = step if step >= 0 else number_of_steps + step
        if normalized_step < 0 or normalized_step >= number_of_steps:
            raise IndexError(f"Step {step} is outside [0, {number_of_steps})")
        start = int(offsets[normalized_step])
        stop = start + self._entity_count(location)
        frame = values[start:stop]
        return self._select_component(frame, component)

    def _response_data(
        self,
        location: str,
        response: str,
    ) -> tuple[h5py.Dataset, h5py.Dataset]:
        offsets_name = f"{location}Offsets"
        try:
            values = self._vtkhdf[location][response]
            offsets = self._vtkhdf["Steps"][offsets_name][response]
        except KeyError as exc:
            available = (
                self.available_point_responses
                if location == "PointData"
                else self.available_cell_responses
            )
            raise KeyError(
                f"Transient {location} response '{response}' is unavailable; "
                f"available responses: {', '.join(available) or 'none'}"
            ) from exc
        return values, offsets

    def _entity_count(self, location: str) -> int:
        return self.number_of_points if location == "PointData" else self.number_of_cells

    @staticmethod
    def _select_component(values: np.ndarray, component: Component) -> np.ndarray:
        if component is None:
            return values
        if values.ndim < 2:
            raise ValueError("A component cannot be selected from a scalar response")
        index = (
            _COMPONENTS.get(component.lower(), None)
            if isinstance(component, str)
            else component
        )
        if index is None or not isinstance(index, int):
            raise ValueError("component must be an integer or one of 'x', 'y', or 'z'")
        if index < 0 or index >= values.shape[1]:
            raise IndexError(
                f"Component {component!r} is unavailable for shape {values.shape}"
            )
        return values[:, index]

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
