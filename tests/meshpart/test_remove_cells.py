import numpy as np
import pytest

from femora import Model


def make_part():
    model = Model()
    model.clear_model()
    material = model.material.nd.elastic_isotropic(E=1000, nu=.3, rho=2)
    element = model.element.brick.std(ndof=3, material=material)
    part = model.meshpart.volume.geometric_rectangular_grid(
        user_name="soil", element=element,
        x_min=0, x_max=2, y_min=0, y_max=1, z_min=0, z_max=1,
        nx=2, ny=1, nz=1,
    )
    return model, part


@pytest.mark.parametrize("selection", [[True, False], [0]])
def test_remove_cells_preserves_data_and_discards_unused_points(selection):
    model, part = make_part()
    part.mesh.cell_data["test_id"] = [10, 20]
    part.mesh.point_data["test_value"] = part.mesh.points[:, 0]
    part.remove_cells(selection)
    assert part.mesh.n_cells == 1
    assert part.mesh.n_points == 8
    np.testing.assert_array_equal(part.mesh.cell_data["test_id"], [20])
    np.testing.assert_array_equal(part.mesh.point_data["test_value"], part.mesh.points[:, 0])


@pytest.mark.parametrize("selection", [[True], [-1], [2], [0.5], [[0]]])
def test_invalid_selection(selection):
    model, part = make_part()
    with pytest.raises(ValueError):
        part.remove_cells(selection)
    assert part.mesh.n_cells == 2


def test_empty_and_complete_removal():
    model, part = make_part()
    part.remove_cells([])
    assert part.mesh.n_cells == 2
    part.remove_cells([0, 1])
    assert part.mesh.n_cells == 0
    assert part.mesh.n_points == 0


def test_section_snapshot_cannot_be_silently_invalidated():
    model, part = make_part()
    model.assembler.create_section(meshparts=["soil"], num_partitions=0)
    with pytest.raises(ValueError, match="assembly sections"):
        part.remove_cells([0])
