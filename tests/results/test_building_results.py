"""Verify structural interpretation independently of the OpenSees executable."""
import copy

import numpy as np
import pyvista as pv
import pytest

from femora.results import BuildingResults, ResultSet, ResultFormatError, UnsupportedResultOperation
from femora.results.base import ResultReader
from femora.results.building import read_building_metadata, write_building_metadata


class Reader(ResultReader):
    def __init__(self):
        super().__init__("test.vtkhdf")
        self._mesh = pv.UnstructuredGrid(np.array([2, 0, 1, 2, 2, 0, 2, 1, 2]),
            np.array([3, 3, 3]), np.array([[0., 0., 0.], [0., 0., 4.], [4., 0., 4.]]))
        self.points = dict(nodeTags=np.tile([10, 11, 12], (3, 1))[:, :, None],
                           displacement=np.zeros((3, 3, 3)), acceleration=np.zeros((3, 3, 3)))
        self.points["displacement"][1, :, 0] = [0, .02, .04]
        self.points["acceleration"][1, :, 0] = [0, 2, 4]
        self.cells = dict(eleTags=np.tile([100, 101, 102], (3, 1))[:, :, None], force3D=np.zeros((3, 3, 12)))
        self.cells["force3D"][1, 0, :6] = [-10, 0, -30, 0, -2, 0]
        self.cells["force3D"][1, 1, 6:] = [-5, 0, -15, 0, 0, 0]
        self.cells["force3D"][1, 2, :] = 999  # Horizontal beam must not enter the base cut.
        self.closed = False

    capabilities = property(lambda self: frozenset({"mesh", "point_history", "cell_history"}))
    times = property(lambda self: np.array([0., .1, .2]))
    number_of_steps = property(lambda self: 3)
    available_point_responses = property(lambda self: tuple(self.points))
    available_cell_responses = property(lambda self: tuple(self.cells))
    mesh = property(lambda self: self._mesh)

    def point_history(self, response, index, component=None):
        values = self.points[response][:, index]
        return values if component is None else values[:, component]

    def cell_history(self, response, index, component=None):
        values = self.cells[response][:, index]
        return values if component is None else values[:, component]

    def point_frame(self, response, step, component=None):
        return self.points[response][step]

    def cell_frame(self, response, step, component=None):
        return self.cells[response][step]

    def close(self):
        self.closed = True


@pytest.fixture
def metadata():
    return dict(node_tags=np.array([10, 11, 12]), coordinates=np.array([[0., 0., 0.], [0., 0., 4.], [4., 0., 4.]]),
                element_tags=np.array([100, 101, 102]), connectivity=np.array([[10, 11], [12, 10], [11, 12]]),
                members=[dict(member=1, kind="column", story=1, elements=[100]),
                         dict(member=2, kind="brace", story=1, elements=[101]),
                         dict(member=3, kind="beam", story=1, elements=[102])],
                floor_nodes=[[10], [11, 12]], floor_elevations=[0., 4.], moment_reference=[2., 0., 0.],
                units=dict(length="m", force="kN", moment="kN*m", acceleration="m/s^2"),
                acceleration_basis="relative", abscissa="time_s")


def test_floor_responses_and_explicit_acceleration_conversion(metadata):
    with BuildingResults(ResultSet([Reader()]), metadata) as results:
        assert results.floor_displacement().iloc[1, 0] == pytest.approx(.03)
        assert results.interstory_drift().iloc[1, 0] == pytest.approx(.0075)
        assert results.floor_acceleration().iloc[1, 0] == 3
        absolute = results.floor_acceleration(basis="absolute", ground_motion=([0, .1, .2], [0, 2, 0]))
        assert absolute.iloc[1, 0] == 5
        assert absolute.attrs["basis"] == "absolute"
        with pytest.raises(UnsupportedResultOperation, match="explicit ground_motion"):
            results.floor_acceleration(basis="absolute")
        with pytest.raises(ValueError, match="cover"):
            results.floor_acceleration(basis="absolute", ground_motion=([0, .1], [0, 2]))


def test_forces_include_braces_use_correct_end_and_moment_arm(metadata):
    results = BuildingResults(ResultSet([Reader()]), metadata)
    assert results.base_shear().iloc[1, 0] == 15
    assert results.story_shear().iloc[1, 0] == 15
    assert results.overturning_moment().iloc[1, 0] == 92
    assert results.overturning_moment(reference=[0, 0, 0]).iloc[1, 0] == 2
    forces = results.member_forces(kind="brace", end="j")
    assert forces.iloc[1, 0] == -5
    assert forces.columns.names == ["member", "element", "end", "component"]
    assert results.members().loc[2, "kind"] == "brace"


def test_missing_force_fields_raise_instead_of_zero(metadata):
    reader = Reader()
    del reader.cells["force3D"]
    results = BuildingResults(ResultSet([reader]), metadata)
    with pytest.raises(UnsupportedResultOperation, match="force3D"):
        results.base_shear()
    with pytest.raises(UnsupportedResultOperation, match="localForce3D"):
        results.member_forces(coordinate_system="local")
    assert len(results.summary()) > 0


def test_partition_duplicates_are_not_double_counted(metadata):
    reader = Reader()
    duplicate = Reader()
    results = BuildingResults(ResultSet([reader, duplicate]), metadata)
    assert results.base_shear().iloc[1, 0] == 15
    duplicate.cells["force3D"][1, 0, 0] += 1
    with pytest.raises(ResultFormatError, match="Conflicting partition"):
        results.base_shear()


def test_metadata_roundtrip_and_explicit_exports(tmp_path, metadata, monkeypatch):
    metadata_path = tmp_path / "structure.h5"
    write_building_metadata(metadata_path, metadata)
    restored = read_building_metadata(metadata_path)
    np.testing.assert_array_equal(restored["connectivity"], metadata["connectivity"])
    reader = Reader()
    monkeypatch.setattr("femora.results.building.open_results", lambda source: ResultSet([reader]))
    with BuildingResults.open("ignored", metadata=metadata_path) as results:
        assert len(list(tmp_path.iterdir())) == 1
        paths = results.export_csv(tmp_path / "csv", responses=["interstory_drift", "base_shear"])
        assert all(path.exists() for path in paths)
        summary = results.summary(responses=["base_shear"])
        assert summary.iloc[0]["peak_abs"] == 15
    assert reader.closed


def test_mismatched_metadata_is_rejected(metadata):
    changed = copy.deepcopy(metadata)
    changed["coordinates"][1, 0] += .5
    with pytest.raises(ResultFormatError, match="coordinates disagree"):
        BuildingResults(ResultSet([Reader()]), changed)


def test_mismatched_partition_times_are_rejected(metadata):
    class ShiftedReader(Reader):
        times = property(lambda self: np.array([0., .11, .2]))
    with pytest.raises(ResultFormatError, match="same recorded times"):
        BuildingResults(ResultSet([Reader(), ShiftedReader()]), metadata)
