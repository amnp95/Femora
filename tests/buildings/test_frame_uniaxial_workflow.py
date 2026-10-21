"""Material + G + density must not need a continuum material or tangent lookup."""
import os

import numpy as np
import pytest

from femora import Model
from femora.tools.buildings import SteelConcentricallyBracedFrame3D
from femora.tools.sections import aisc


def make_frame(nonlinear=False, **options):
    model = Model()
    material = (model.material.uniaxial.steel01(Fy=150000, E0=200e6, b=.01)
                if nonlinear else model.material.uniaxial.elastic(E=200e6))
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=2, x_bays=[6], y_bays=[8], floor_masses=[100, 80], **options)
    frame.build(model, material=material, G=76.923e6, material_density=7.85)
    return model, frame


@pytest.mark.parametrize("option", ["section_model", "steel_material", "brace_model", "brace_material", "brace_area", "brace_E"])
def test_removed_constructor_options_are_rejected(option):
    with pytest.raises(TypeError, match="unexpected keyword"):
        SteelConcentricallyBracedFrame3D(**{option: None})


@pytest.mark.parametrize("option", ["section_model", "steel_material"])
def test_removed_category_options_are_rejected(option):
    with pytest.raises(ValueError, match="supported modeling options"):
        SteelConcentricallyBracedFrame3D(member_options={"Beam_X": {option: None}})


def test_continuum_material_is_rejected():
    model = Model()
    material = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
    with pytest.raises(ValueError, match="uniaxial material"):
        SteelConcentricallyBracedFrame3D().build(model, material, G=76.923e6)


def test_custom_braces_use_same_geometry_for_stiffness_and_mass():
    properties = dict(A=.01, Iy=2e-5, Iz=3e-5)
    model, frame = make_frame(brace_properties=properties, brace_area_scale=1.5)
    properties["A"] = 100
    for member in frame._member_definitions:
        if member["kind"] != "brace":
            continue
        tag = member["definition"]
        geometry = frame._mass_geometry[tag]
        assert geometry == pytest.approx(dict(A=.015, Iy=3e-5, Iz=4.5e-5))
        assert model.element.get(tag).get_section().get_area() == pytest.approx(.015)
        assert member["material_density"] == 7.85
    assert frame.summarize_archetype()["brace_properties"]["A"] == .01


@pytest.mark.parametrize("properties", [
    {}, dict(A=.01), dict(A=0, Iy=0, Iz=0),
    dict(A=.01, Iy=-1, Iz=0), dict(A=float("nan"), Iy=0, Iz=0),
    dict(A=.01, Iy=0, Iz=float("inf")), dict(A=.01, Iy=0, Iz=0, J=1),
])
def test_invalid_custom_brace_geometry(properties):
    with pytest.raises(ValueError, match="brace_properties"):
        SteelConcentricallyBracedFrame3D(brace_properties=properties)


def test_custom_braces_cannot_also_select_aisc_sections():
    with pytest.raises(ValueError, match="not both"):
        SteelConcentricallyBracedFrame3D(
            brace_properties=dict(A=.01, Iy=0, Iz=0), brace_sections="HSS8X8X3/8")


@pytest.mark.parametrize("nonlinear", [False, True])
def test_only_uniaxial_materials_and_fiber_sections(nonlinear):
    model, frame = make_frame(nonlinear)
    assert all(mat.material_type == "uniaxialMaterial" for mat in model.material.get_all().values())
    assert all("section Fiber" in section.to_tcl() for section in model.section.get_all().values())
    for member in frame._member_definitions:
        element = model.element.get(member["definition"])
        assert member["material_density"] == 7.85
        if member["kind"] != "brace":
            assert element.get_section().GJ == pytest.approx(
                76.923e6 * frame._mass_geometry[element.tag]["J"])


def test_assigned_sections_and_category_material_density_overrides():
    model = Model()
    material = model.material.uniaxial.elastic(user_name="default", E=200e6)
    softer = model.material.uniaxial.elastic(user_name="beam", E=100e6)
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=2, x_bays=[6], y_bays=[8], floor_masses=[0, 0],
        beam_sections={(1, "X", 0, 0): "W14X90", (1, "Y", 0, 0): "W18X35"},
        brace_sections=["HSS8X8X3/8", "HSS6X6X3/8"],
        member_options={"Beam_X": {"material": softer, "G": 50e6, "material_density": 4.0},
                        "Brace": {"material_density": 3.0}})
    part = frame.build(model, material, G=76.923e6, material_density=7.85)
    expected_mass = 0
    for member in frame._member_definitions:
        tag = member["definition"]
        geometry = frame._mass_geometry[tag]
        density = frame._member_densities[tag]
        expected_mass += density * geometry["A"] * sum(np.linalg.norm(q-p) for p, q in member["segments"])
        if member["category"] == "Beam_X":
            assert density == 4.0
            assert model.element.get(tag).get_section().GJ == pytest.approx(50e6 * geometry["J"])
            assert all(patch.material is softer for patch in model.element.get(tag).get_section().patches)
        if member["kind"] == "brace":
            name = "HSS8X8X3/8" if member["story"] == 1 else "HSS6X6X3/8"
            assert geometry["A"] == pytest.approx(aisc.get_section_properties(name, "m")["A"])
    mesh = part.get_mesh() if hasattr(part, "get_mesh") else part.mesh
    assert mesh.point_data["Mass"][:, 0].sum() == pytest.approx(expected_mass, rel=1e-6)
    physical = mesh.point_data["ndf"] < 1000
    assert np.all(mesh.point_data["Mass"][physical, :6] > 0)


def test_density_override_is_used_even_when_default_density_is_zero():
    model = Model()
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[6], y_bays=[6], floor_masses=[0],
        member_options={"Beam_X": {"material_density": 7.85}})
    part = frame.build(model, model.material.uniaxial.elastic(E=200e6), G=76e6)
    assert part.mesh.point_data["Mass"][:, :6].sum() > 0


def test_floor_rotational_inertias_are_preserved():
    model = Model()
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[6], y_bays=[8], floor_masses=[100])
    part = frame.build(model, model.material.uniaxial.elastic(E=200e6), G=76e6)
    mass = part.mesh.point_data["Mass"][part.mesh.point_data["ndf"] >= 1000, :6]
    np.testing.assert_allclose(mass, [[100, 100, 100, 100*8**2/12,
                                     100*6**2/12, 100*(6**2+8**2)/12]], rtol=1e-6)


@pytest.mark.parametrize("G", [None, 0, -1, float("nan")])
def test_uniaxial_requires_positive_G(G):
    model = Model()
    frame = SteelConcentricallyBracedFrame3D(num_stories=1, x_bays=[6], y_bays=[6])
    with pytest.raises(ValueError, match="G"):
        frame.build(model, model.material.uniaxial.elastic(E=200e6), G=G)


@pytest.mark.parametrize("density", [-1, float("nan"), float("inf")])
def test_invalid_density_rejected(density):
    model = Model()
    with pytest.raises(ValueError, match="density"):
        SteelConcentricallyBracedFrame3D().build(
            model, model.material.uniaxial.elastic(E=200e6), G=76e6, material_density=density)


@pytest.mark.skipif(not os.environ.get("FEMORA_OPENSEES"), reason="Native OpenSees not configured")
@pytest.mark.parametrize("law", ["Elastic", "Steel01"])
def test_native_modes_with_uniaxial_material(law):
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[6], y_bays=[6], floor_masses=[100])
    definition = dict(type="Elastic", E=200e6) if law == "Elastic" else dict(type="Steel01", E0=200e6, Fy=345000, b=.01)
    modes = frame.get_modes(3, material=definition, G=76.923e6, material_density=7.85,
                            opensees_exe=os.environ["FEMORA_OPENSEES"])
    assert np.all(np.isfinite(modes["frequencies"]))
    assert np.all(modes["frequencies"] > 0)
