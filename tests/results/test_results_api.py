# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from pathlib import Path

import h5py
import numpy as np
import pytest

import femora as fm
from femora.results import ResultFormatError, VTKHDFResultReader
from femora.results.registry import ResultReaderRegistry
from femora.results.result_set import open_results


def _write_response_file(
    path: Path,
    *,
    times: np.ndarray,
    point_count: int = 3,
    value_offset: float = 0.0,
) -> Path:
    points = np.column_stack(
        (
            np.arange(point_count, dtype=float),
            np.zeros(point_count),
            np.zeros(point_count),
        )
    )
    offsets = np.arange(times.size, dtype=np.int64) * point_count
    displacement = np.empty((times.size * point_count, 3), dtype=float)
    acceleration = np.empty_like(displacement)
    for step, time in enumerate(times):
        start = step * point_count
        stop = start + point_count
        displacement[start:stop] = value_offset + time + points
        acceleration[start:stop] = value_offset + 10.0 * time + points

    with h5py.File(path, "w") as result:
        vtkhdf = result.create_group("VTKHDF")
        vtkhdf.create_dataset("Points", data=points)
        vtkhdf.create_group("CellData")
        point_data = vtkhdf.create_group("PointData")
        point_data.create_dataset("acceleration", data=acceleration)
        point_data.create_dataset("displacement", data=displacement)
        steps = vtkhdf.create_group("Steps")
        steps.create_dataset("Values", data=times)
        steps.create_group("CellDataOffsets")
        point_offsets = steps.create_group("PointDataOffsets")
        point_offsets.create_dataset("acceleration", data=offsets)
        point_offsets.create_dataset("displacement", data=offsets)
    return path


def test_vtkhdf_reader_extracts_histories_and_frames_lazily(tmp_path):
    path = _write_response_file(
        tmp_path / "result0.vtkhdf",
        times=np.array([0.0, 0.1, 0.2]),
    )

    with VTKHDFResultReader(path) as result:
        assert result.available_point_responses == (
            "acceleration",
            "displacement",
        )
        np.testing.assert_allclose(
            result.point_history("acceleration", 1, component="x"),
            [1.0, 2.0, 3.0],
        )
        np.testing.assert_allclose(
            result.point_frame("displacement", 1),
            [[0.1, 0.1, 0.1], [1.1, 0.1, 0.1], [2.1, 0.1, 0.1]],
        )


def test_transient_counts_are_not_summed_over_time(tmp_path):
    path = _write_response_file(tmp_path / "counts.vtkhdf", times=np.array([0., .1, .2]))
    with h5py.File(path, "a") as target:
        root = target["VTKHDF"]
        root.create_dataset("NumberOfCells", data=[2, 2, 2])
        root.create_dataset("NumberOfPoints", data=[3, 3, 3])
        root["CellData"].create_dataset("force3D", data=np.arange(72).reshape(6, 12))
        root["Steps/CellDataOffsets"].create_dataset("force3D", data=[0, 2, 4])
    with VTKHDFResultReader(path) as result:
        assert result.number_of_cells == 2
        assert result.number_of_points == 3
        assert result.cell_frame("force3D", 0).shape == (2, 12)
        assert result.cell_history("force3D", 1).shape == (3, 12)


def test_open_discovers_partition_files_and_validates_times(tmp_path):
    times = np.array([0.0, 0.1, 0.2])
    _write_response_file(tmp_path / "result0.vtkhdf", times=times)
    _write_response_file(
        tmp_path / "result1.vtkhdf",
        times=times,
        value_offset=100.0,
    )

    with fm.results.open(str(tmp_path / "result*.vtkhdf")) as results:
        assert results.number_of_partitions == 2
        np.testing.assert_allclose(results.times, times)
        assert results.available_point_responses == (
            "acceleration",
            "displacement",
        )


def test_partition_time_mismatch_is_reported(tmp_path):
    _write_response_file(
        tmp_path / "result0.vtkhdf",
        times=np.array([0.0, 0.1]),
    )
    _write_response_file(
        tmp_path / "result1.vtkhdf",
        times=np.array([0.0, 0.2]),
    )

    with fm.results.open(str(tmp_path / "result*.vtkhdf")) as results:
        with pytest.raises(ResultFormatError, match="same recorded times"):
            _ = results.times


def test_unknown_result_suffix_has_clear_error(tmp_path):
    path = tmp_path / "response.unknown"
    path.write_text("result")

    with pytest.raises(ResultFormatError, match="No result reader"):
        fm.results.open(path)


def test_named_reader_supports_ambiguous_file_suffixes(tmp_path):
    path = _write_response_file(
        tmp_path / "response.out",
        times=np.array([0.0, 0.1]),
    )
    registry = ResultReaderRegistry()
    registry.register("custom-vtkhdf", VTKHDFResultReader)

    with open_results(
        path,
        format="custom-vtkhdf",
        registry=registry,
    ) as results:
        assert results.number_of_steps == 2
