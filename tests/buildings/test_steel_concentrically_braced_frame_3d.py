from types import SimpleNamespace

import numpy as np
import pytest

from femora.tools.buildings import (
    Building,
    ConventionalSteelBracedFrame,
    SteelConcentricallyBracedFrame3D,
)


def test_public_class_is_independent():
    assert issubclass(SteelConcentricallyBracedFrame3D, Building)
    assert not issubclass(SteelConcentricallyBracedFrame3D, ConventionalSteelBracedFrame)


def test_same_geometry_and_parameters():
    options = dict(num_stories=5, floor_masses=[250.0] * 5, brace_pattern="x")
    old = ConventionalSteelBracedFrame(**options)
    new = SteelConcentricallyBracedFrame3D(**options)
    for old_axis, new_axis in zip(old.get_coordinates(), new.get_coordinates()):
        np.testing.assert_array_equal(old_axis, new_axis)
    assert old.floor_masses == new.floor_masses
    assert old.brace_bays_x == new.brace_bays_x
    assert old.brace_bays_y == new.brace_bays_y
    assert new.summarize_archetype()["archetype_name"] == "SteelConcentricallyBracedFrame3D"


@pytest.mark.parametrize("g", [-9.81, -1.0, np.nan, np.inf, -np.inf])
def test_invalid_gravity_fails_before_model_access(g):
    building = SteelConcentricallyBracedFrame3D()
    with pytest.raises(ValueError, match="nonnegative gravity magnitude"):
        building.create_gravity_pattern(None, g=g)


def test_positive_gravity_creates_downward_floor_loads():
    building = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[8.0], y_bays=[8.0], floor_masses=[250.0],
    )
    loads = []
    pattern = SimpleNamespace(add_load=SimpleNamespace(node=lambda **kwargs: loads.append(kwargs)))
    mesh = SimpleNamespace(
        points=np.array([[0., 0., 4.], [8., 0., 4.], [0., 8., 4.], [8., 8., 4.]]),
        point_data={"ndf": np.full(4, 6)},
    )
    model = SimpleNamespace(
        assembled_mesh=mesh,
        time_series=SimpleNamespace(constant=lambda **kwargs: object()),
        pattern=SimpleNamespace(plain=lambda **kwargs: pattern),
        mask=SimpleNamespace(nodes=SimpleNamespace(by_ids=lambda ids:
            SimpleNamespace(is_empty=lambda: False, ids=ids))),
    )
    assert building.create_gravity_pattern(model, g=9.81) is pattern
    assert len(loads) == 1
    assert len(loads[0]["node_mask"].ids) == 4
    assert loads[0]["values"] == [0., 0., -613.125, 0., 0., 0.]
