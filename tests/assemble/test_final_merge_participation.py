import pytest

from femora.components.Assemble.Assembler import Assembler
from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element
from femora.components.event.event_bus import EventBus

from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
from femora.components.element.std_brick import stdBrickElement
from femora.components.Mesh.meshPartInstance import StructuredRectangular3D


@pytest.fixture()
def femora_clean_state():
    """Reset global Femora registries that impact assembly.

    Femora keeps several global registries (MeshParts, Materials, Elements,
    Assembler singleton sections, EventBus subscribers). This fixture clears
    them so tests stay deterministic and order-independent.
    """
    old_subscribers = EventBus._subscribers.copy()
    EventBus._subscribers.clear()

    # Clear model registries
    MeshPart.clear_all_mesh_parts()
    Material.clear_all_materials()
    Element.clear_all_elements()

    assembler = Assembler.get_instance()
    assembler.clear_assembly_sections()
    assembler.delete_assembled_mesh()

    try:
        yield assembler
    finally:
        assembler.clear_assembly_sections()
        assembler.delete_assembled_mesh()
        MeshPart.clear_all_mesh_parts()
        Material.clear_all_materials()
        Element.clear_all_elements()
        EventBus._subscribers = old_subscribers


def _make_two_adjacent_brick_meshparts():
    mat = ElasticIsotropicMaterial(user_name="mat", E=200e3, nu=0.3, rho=0.0)
    ele = stdBrickElement(ndof=3, material=mat)

    # Two cubes that share the x=1 face (4 coincident points)
    StructuredRectangular3D(
        user_name="part_a",
        element=ele,
        **{
            "X Min": 0.0,
            "X Max": 1.0,
            "Y Min": 0.0,
            "Y Max": 1.0,
            "Z Min": 0.0,
            "Z Max": 1.0,
            "Nx Cells": 1,
            "Ny Cells": 1,
            "Nz Cells": 1,
        },
    )

    StructuredRectangular3D(
        user_name="part_b",
        element=ele,
        **{
            "X Min": 1.0,
            "X Max": 2.0,
            "Y Min": 0.0,
            "Y Max": 1.0,
            "Z Min": 0.0,
            "Z Max": 1.0,
            "Nx Cells": 1,
            "Ny Cells": 1,
            "Nz Cells": 1,
        },
    )

    return "part_a", "part_b"


@pytest.mark.parametrize(
    "participate_b, expected_points",
    [
        (True, 12),   # interface points merged (16 -> 12)
        (False, 16),  # part_b excluded from final merge, no interface merging
    ],
)
def test_final_merge_participation_controls_cross_section_merging(
    femora_clean_state: Assembler,
    participate_b: bool,
    expected_points: int,
):
    assembler = femora_clean_state
    part_a, part_b = _make_two_adjacent_brick_meshparts()

    assembler.create_section(
        meshparts=[part_a],
        num_partitions=1,
        merge_points=False,
        merge_in_final=True,
    )
    assembler.create_section(
        meshparts=[part_b],
        num_partitions=1,
        merge_points=False,
        merge_in_final=participate_b,
    )

    assembler.Assemble(merge_points=True)

    assert assembler.AssembeledMesh is not None
    assert int(assembler.AssembeledMesh.n_points) == int(expected_points)
