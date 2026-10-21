import os
from pathlib import Path
import subprocess

import numpy as np
import pytest

from femora import Model
from femora.tools.sections import aisc
from femora.tools.buildings import SteelConcentricallyBracedFrame3D


def steel(model):
    return model.material.uniaxial.steel01(user_name="fiber_steel", Fy=345000., E0=200e6, b=0.01)


def test_w_fiber_geometry_and_tcl():
    model = Model()
    model.clear_model()
    mat = steel(model)
    section = aisc.create_section("W14X90", model, mat, type="Fiber", unit_system="m", GJ=1000)
    assert len(section.patches) == 3
    assert section.get_area() > 0
    assert section.get_Iy() > section.get_Iz() > 0
    assert section.to_tcl().count("patch rect") == 3
    assert "-GJ 1000" in section.to_tcl()
    # The rectangular approximation excludes rolled fillets and corner radii.
    elastic = aisc.create_section("W14X90", model,
        model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85), unit_system="m",
        user_name="elastic_reference")
    assert section.get_area() == pytest.approx(elastic.get_area(), rel=.06)
    assert section.get_Iy() == pytest.approx(elastic.get_Iy(), rel=.06)
    assert section.get_Iz() == pytest.approx(elastic.get_Iz(), rel=.06)


@pytest.mark.parametrize("kwargs", [{}, {"GJ": -1}, {"GJ": np.nan},
                                     {"GJ": 1, "web_fibers": (0, 2)}])
def test_invalid_fiber_parameters(kwargs):
    model = Model()
    model.clear_model()
    with pytest.raises(ValueError):
        aisc.create_section("W14X90", model, steel(model), type="Fiber", **kwargs)


def test_build_nonlinear_frame_with_member_mass():
    model = Model()
    model.clear_model()
    elastic = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[8], y_bays=[8], floor_masses=[100],
    )
    mesh = frame.build(model, steel(model), G=76.923e6, material_density=7.85)
    assert mesh is not None


@pytest.mark.skipif(not os.environ.get("FEMORA_OPENSEES"), reason="Native OpenSees not configured")
def test_native_fiber_cantilever_yields(tmp_path):
    model = Model()
    model.clear_model()
    mat = steel(model)
    section = aisc.create_section("W14X90", model, mat, type="Fiber", unit_system="m", GJ=1e5)
    # Bend about local y (strong axis); constrain unused tip DOFs.
    commands = [
        "wipe", "model BasicBuilder -ndm 3 -ndf 6",
        "node 1 0 0 0", "node 2 4 0 0",
        "fix 1 1 1 1 1 1 1", "fix 2 1 1 0 1 0 1",
        mat.to_tcl(), section.to_tcl(), "geomTransf Linear 1 0 0 1",
        f"element nonlinearBeamColumn 1 1 2 5 {section.tag} 1 -iter 30 1e-10",
        "timeSeries Linear 1", "pattern Plain 1 1 {load 2 0 0 1 0 0 0}",
        "constraints Plain", "numberer RCM", "system BandGeneral",
        "test NormDispIncr 1e-9 40", "algorithm Newton",
        "integrator DisplacementControl 2 3 0.001", "analysis Static",
        "set out [open response.txt w]",
        "for {set i 0} {$i < 100} {incr i} {",
        'if {[analyze 1] != 0} {error "cantilever failed"}',
        'puts $out "[nodeDisp 2 3] [getTime]"', "}", "close $out", "exit",
    ]
    tcl = tmp_path / "cantilever.tcl"
    tcl.write_text("\n".join(commands), encoding="ascii")
    run = subprocess.run([os.environ["FEMORA_OPENSEES"], str(tcl)], cwd=tmp_path,
                         capture_output=True, text=True, timeout=90)
    assert run.returncode == 0, run.stdout + run.stderr
    data = np.loadtxt(tmp_path / "response.txt")
    initial = data[0, 1] / data[0, 0]
    final = (data[-1, 1]-data[-2, 1]) / (data[-1, 0]-data[-2, 0])
    assert 0 < final < .5*initial


@pytest.mark.skipif(not os.environ.get("FEMORA_OPENSEES"), reason="Native OpenSees not configured")
@pytest.mark.parametrize("nonlinear_braces", [False, True])
def test_exported_fiber_building_runs(tmp_path, nonlinear_braces):
    model = Model(model_path=str(tmp_path))
    model.clear_model()
    elastic = model.material.nd.elastic_isotropic(user_name="elastic", E=200e6, nu=.3, rho=7.85)
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[8], y_bays=[8], floor_masses=[100],
        brace_bays_x={"front": [0], "back": [0]} if nonlinear_braces else {"front": [], "back": []},
        brace_bays_y={"left": [0], "right": [0]} if nonlinear_braces else {"left": [], "right": []},
    )
    frame.build(model, steel(model), G=76.923e6, material_density=7.85)
    model.assembler.create_section(meshparts=[frame.name_prefix], num_partitions=1,
                                   partition_algorithm="kd-tree")
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
    frame.apply_fixed_base(model)
    frame.create_rigid_diaphragms(model, verbose=False)
    model.process.add_step(frame.create_gravity_pattern(model, g=9.81))

    def analysis(name, integrator, steps):
        return model.analysis.static(name=name,
            constraint_handler=model.analysis.constraint.transformation(),
            numberer=model.analysis.numberer.rcm(), system=model.analysis.system.bandgeneral(),
            test=model.analysis.test.normdispincr(tol=1e-8, max_iter=50, print_flag=0),
            algorithm=model.analysis.algorithm.newton(), integrator=integrator,
            num_steps=steps, max_retries=0)

    model.process.add_step(analysis("gravity", model.analysis.integrator.loadcontrol(incr=0.), 1))
    model.process.add_step(model.actions.load_const())
    model.process.add_step(model.actions.set_time(0.))
    pattern = frame.create_pushover_pattern(model, time_series=model.time_series.linear(), base_shear=1000.)
    roof = pattern.get_loads()[-1].node_mask.to_tags()[0]
    model.process.add_step(pattern)
    model.process.add_step(model.recorder.node(file_name="{"+(tmp_path / "roof.txt").as_posix()+"}",
        nodes=[roof], dofs=[1], resp_type="disp", time=True, precision=15))
    model.process.add_step(analysis("push", model.analysis.integrator.displacementcontrol(
        node_tag=roof, dof=1, incr=.002), 100))
    model.process.add_step(model.actions.remove_recorders())
    tcl = tmp_path / "model.tcl"
    model.export_to_tcl(str(tcl), progress_callback=lambda *_: None)
    run = subprocess.run([os.environ["FEMORA_OPENSEES"], str(tcl)], cwd=tmp_path,
                         capture_output=True, text=True, timeout=90)
    assert run.returncode == 0, run.stdout + run.stderr
    response = np.loadtxt(tmp_path / "roof.txt")
    assert response.shape == (100, 2)
    assert response[-1, 1] == pytest.approx(.2)
    initial = response[0, 0] / response[0, 1]
    final = (response[-1, 0]-response[-2, 0]) / .002
    assert 0 < final < .5*initial


def test_hss_properties_and_fibers():
    model = Model()
    model.clear_model()
    elastic = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
    reference = aisc.create_section("HSS8X8X3/8", model, elastic)
    assert reference.get_area() == pytest.approx(10.4)
    assert reference.get_Iy() == pytest.approx(100.)
    assert reference.get_Iz() == pytest.approx(100.)
    assert reference.get_J() == pytest.approx(160.)
    fiber = aisc.create_section("HSS8X8X3/8", model, steel(model), type="Fiber",
                               GJ=1e5, user_name="hss_fiber")
    assert len(fiber.patches) == 4
    assert fiber.get_area() == pytest.approx(reference.get_area(), rel=.05)
    assert fiber.get_Iy() == pytest.approx(reference.get_Iy(), rel=.06)
    assert fiber.get_Iz() == pytest.approx(reference.get_Iz(), rel=.06)


def test_nonlinear_brace_preserves_mass():
    masses = []
    for nonlinear in (False, True):
        model = Model()
        model.clear_model()
        elastic = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
        frame = SteelConcentricallyBracedFrame3D(
            num_stories=1, x_bays=[8], y_bays=[8], floor_masses=[100],
)
        frame.build(model, steel(model) if nonlinear else model.material.uniaxial.elastic(user_name="axial_elastic", E=200e6), G=76.923e6, material_density=7.85)
        model.assembler.create_section(meshparts=[frame.name_prefix], num_partitions=1,
                                       partition_algorithm="kd-tree")
        model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
        masses.append(np.asarray(model.assembled_mesh.point_data["Mass"]).sum(axis=0))
        if nonlinear:
            section = frame._brace_elements[0].get_section()
            assert section.get_area() == pytest.approx(frame._mass_geometry[frame._brace_elements[0].tag]["A"])
            assert section.get_materials()[0].material_name == "Steel01"
    np.testing.assert_allclose(masses[0], masses[1])


def test_nonlinear_brace_requires_uniaxial_material():
    model = Model()
    model.clear_model()
    elastic = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
    frame = SteelConcentricallyBracedFrame3D(
        num_stories=1, x_bays=[8], y_bays=[8],
)
    with pytest.raises(ValueError, match="uniaxial material"):
        frame.build(model, elastic, G=76.923e6)


def test_hss_unit_conversion():
    model = Model()
    model.clear_model()
    material = model.material.nd.elastic_isotropic(E=200e6, nu=.3, rho=7.85)
    section = aisc.create_section("HSS8X6X3/8", model, material, unit_system="m")
    assert section.get_area() == pytest.approx(8.97 * .0254**2)
    assert section.get_Iy() == pytest.approx(79.1 * .0254**4)
    assert section.get_Iz() == pytest.approx(50.6 * .0254**4)
    assert section.get_J() == pytest.approx(100. * .0254**4)
