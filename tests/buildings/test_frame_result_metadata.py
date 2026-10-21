import numpy as np
import pytest

from femora import Model
from femora.tools.buildings import SteelConcentricallyBracedFrame3D
from femora.results.building import read_building_metadata


def test_constructed_roles_and_subdivisions_are_preserved(tmp_path):
    model = Model()
    model.clear_model()
    material = model.material.uniaxial.elastic(E=200e6)
    frame = SteelConcentricallyBracedFrame3D(num_stories=1, x_bays=[8], y_bays=[8], n_ele_col=2)
    frame.build(model, material, G=76.923e6)
    model.assembler.create_section(meshparts=[frame.name_prefix], num_partitions=1, partition_algorithm="kd-tree")
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
    frame.get_recorders(model, acceleration_basis="relative")
    metadata = frame._results_metadata(model)
    columns = [member for member in metadata["members"] if member["kind"] == "column"]
    braces = [member for member in metadata["members"] if member["kind"] == "brace"]
    assert len(columns) == 4
    assert all(len(member["elements"]) == 2 for member in columns)
    assert len(braces) == 8
    assert len(set(tag for member in metadata["members"] for tag in member["elements"])) == len(metadata["element_tags"])
    assert not list(tmp_path.iterdir())
    model.export_to_tcl(str(tmp_path / "model.tcl"), progress_callback=lambda *_: None)
    assert not list(tmp_path.glob("*.h5"))
    path = tmp_path / "structure.h5"
    frame.export_metadata(model, path, units={"force": "kN", "moment": "kN*m"})
    restored = read_building_metadata(path)
    assert restored["members"] == metadata["members"]
    assert restored["units"]["force"] == "kN"
    assert restored["acceleration_basis"] == "relative"
    np.testing.assert_array_equal(restored["element_tags"], metadata["element_tags"])


def test_metadata_requires_assembly():
    model = Model()
    model.clear_model()
    frame = SteelConcentricallyBracedFrame3D()
    with pytest.raises(ValueError, match="Assemble"):
        frame._results_metadata(model)
