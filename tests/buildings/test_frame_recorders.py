import pytest

from femora import Model
from femora.tools.buildings import SteelConcentricallyBracedFrame3D


@pytest.fixture
def assembled():
    model = Model()
    model.clear_model()
    material = model.material.uniaxial.elastic(E=200e6)
    frame = SteelConcentricallyBracedFrame3D(num_stories=1, x_bays=[8], y_bays=[8])
    frame.build(model, material, G=76.923e6)
    model.assembler.create_section(meshparts=[frame.name_prefix], num_partitions=1, partition_algorithm="kd-tree")
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
    return model, frame


def test_vtkhdf_default_and_scope(assembled):
    model, frame = assembled
    recorder = frame.get_recorders(model)
    assert recorder.resp_types == ["disp", "vel", "accel", "force3D", "localForce3D"]
    assert recorder.region is frame.building_region
    recorder = frame.get_recorders(model, whole_model=True)
    assert recorder.region is None


def test_vtkhdf_aliases_return_one_recorder(assembled):
    model, frame = assembled
    recorder = frame.get_recorders(model, node_responses=["displacement", "acceleration"],
                                   element_responses=["force", "localForce"])
    assert recorder.resp_types == ["disp", "accel", "force3D", "localForce3D"]


def test_alternate_formats_and_fallbacks_are_not_accepted(assembled):
    model, frame = assembled
    with pytest.raises(TypeError):
        frame.get_recorders(model, recorder_format="mpco")
    with pytest.raises(TypeError):
        frame.get_recorders(model, force_fallback=True)
