import math
import re

import numpy as np
import pytest

from femora import Model
from femora.tools.buildings import Building, SteelConcentricallyBracedFrame3D


@pytest.fixture
def frame():
    model = Model()
    model.clear_model()
    building = SteelConcentricallyBracedFrame3D(
        num_stories=2, x_bays=[4., 5.], y_bays=[6.],
        story_heights=[4., 3.], floor_masses=[100., 200.], origin=(10., -20., 7.),
    )
    steel = model.material.uniaxial.elastic(E=200e6)
    building.build(model, steel, G=76.923e6, material_density=7.85)
    model.assembler.create_section([building.name_prefix], num_partitions=1, partition_algorithm="kd-tree")
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
    building.create_rigid_diaphragms(model, verbose=False)
    yield model, building
    model.clear_model()


def pattern_for(frame, **kwargs):
    model, building = frame
    return building.create_pushover_pattern(
        model, time_series=model.time_series.linear(), base_shear=900., **kwargs,
    )


@pytest.mark.parametrize("distribution, expected", [
    ("mass", [300., 600.]), ("uniform", [300., 600.]),
    ("mass_height", [200., 700.]), ("triangular", [200., 700.]),
    ([3., 1.], [675., 225.]),
])
def test_floor_distribution_and_tcl(frame, distribution, expected):
    model, building = frame
    pattern = pattern_for(frame, distribution=distribution)
    loads = pattern.get_loads()
    np.testing.assert_allclose([load.values[0] for load in loads], expected)
    assert [load.node_mask.to_tags()[0] for load in loads] == building._com_node_tags
    assert all(load.values[1:] == [0.] * 5 for load in loads)
    # COM metadata uses unique sentinels, but OpenSees loads must have six values.
    commands = re.findall(r"\bload\s+(\d+)\s+([^}]+)", pattern.to_tcl())
    assert len(commands) == 2
    assert all(len(values.split()) == 6 for _, values in commands)


@pytest.mark.parametrize("direction, unit", [("y", [0., 1.]), (180., [-1., 0.]), (45., [2**-.5, 2**-.5])])
def test_direction_and_eccentricity(frame, direction, unit):
    pattern = pattern_for(frame, direction=direction, distribution="mass", eccentricity=(2., -3.))
    values = np.array([load.values for load in pattern.get_loads()])
    np.testing.assert_allclose(values[:, :2].sum(axis=0), np.array(unit) * 900., atol=1e-10)
    np.testing.assert_allclose(values[:, 5], 2 * values[:, 1] + 3 * values[:, 0])


@pytest.mark.parametrize("shape, expected", [([-1., -2.], [180., 720.]), ([-1., 1.], [-900., 1800.])])
def test_modal_profile(frame, shape, expected):
    pattern = pattern_for(frame, distribution="modal", mode_shape=shape)
    np.testing.assert_allclose([load.values[0] for load in pattern.get_loads()], expected)


@pytest.mark.parametrize("options", [
    {"base_shear": 0.}, {"base_shear": -1.}, {"base_shear": math.nan},
    {"direction": "z"}, {"direction": math.inf}, {"eccentricity": [1.]},
    {"distribution": [0., 0.]}, {"distribution": [-1., 2.]},
    {"distribution": [1.]}, {"distribution": [1., math.nan]},
    {"distribution": "unknown"}, {"distribution": "modal"},
    {"distribution": "modal", "mode_shape": [2., -1.]},
    {"distribution": "mass", "mode_shape": [1., 2.]},
])
def test_invalid_inputs_do_not_register_pattern(frame, options):
    model, building = frame
    series = model.time_series.linear()
    before = dict(model.pattern.get_all())
    arguments = dict(time_series=series, base_shear=900.)
    arguments.update(options)
    with pytest.raises(ValueError):
        building.create_pushover_pattern(model, **arguments)
    assert model.pattern.get_all() == before


def test_explicit_series_and_diaphragms_required(frame):
    model, building = frame
    with pytest.raises(TypeError):
        building.create_pushover_pattern(model, base_shear=900.)
    with pytest.raises(ValueError, match="time_series"):
        building.create_pushover_pattern(model, time_series=None, base_shear=900.)
    series = model.time_series.constant()
    building._com_node_tags = []
    with pytest.raises(ValueError, match="rigid_diaphragms"):
        building.create_pushover_pattern(model, time_series=series, base_shear=900.)


def test_base_interface_is_explicit():
    with pytest.raises(NotImplementedError):
        Building().create_pushover_pattern(None, time_series=None, base_shear=1.)
