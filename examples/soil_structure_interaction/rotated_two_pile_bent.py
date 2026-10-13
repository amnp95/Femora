# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

# femora-postprocess: examples/soil_structure_interaction/rotated_two_pile_bent_postprocess.py

# %% [markdown]
# # Rotated Two-Pile Bent under Uniform Excitation
#
# Two hollow fiber-section piles (x = +/-3.809 m) support a solid aluminum cap,
# embedded in a 30 m by 30 m nonlinear soil domain. The upper 1 m of each pile
# is intentionally uncoupled from the soil, matching the validation model.
# A staged base acceleration record excites the whole model uniformly in
# global x. The piles-plus-cap assembly is rotated about global z by
# 0, 30, 60, or 90 degrees; each angle is an independent remote case.

# %%
"""Rotated two-pile bent tutorial with a parallel remote Femora workflow.

Stages: build(angle_000/030/060/090) -> solve (4 x 33 ranks) -> postprocess/responses.
Task functions are context callbacks; importing this module runs no simulation.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import femora as fm
import numpy as np
from femora import Model
from femora.utils.paths import motions_dir


RANKS_PER_CASE = 33  # 1 structural + 32 soil partitions
MOTION_FILE = "CFG2_ax_base_02g_avg.acc"
POSTPROCESS = "rotated_two_pile_bent_postprocess.py"
EXPERIMENT_FILE = "selected_experiment_processed.h5"


def build_model(context, angle_degrees=0):
    """Build one rotated case in this task's folder and return its Tcl path."""
    if angle_degrees not in (0, 30, 60, 90):
        raise ValueError("angle_degrees must be 0, 30, 60, or 90")
    # The thesis input is in g; the model below uses m, N, kg, and s.
    gravity = 9.81
    motion_dt = 0.0127
    final_time = 50.0
    motion_path = (Path(context.workspace) / "motions" / MOTION_FILE).resolve()
    if not motion_path.is_file():
        raise FileNotFoundError(f"Missing staged base motion: {motion_path}")
    motion = np.loadtxt(motion_path)
    if motion.ndim != 1 or motion.size < 2 or not np.isfinite(motion).all():
        raise ValueError("Base motion must be a finite, one-column acceleration history")
    if (motion.size - 1) * motion_dt < final_time:
        raise ValueError("Base motion is shorter than the dynamic analysis")
    case_dir = Path(context.output_dir).resolve()
    results_dir = case_dir / "results"
    case_dir.mkdir(parents=True, exist_ok=True)
    model = Model(model_name="rotated_two_pile_bent", model_path=str(case_dir))
    model.clear_model()
    model.set_results_folder(results_dir.resolve().as_posix())

    #########################################################################
    # soil definition
    #########################################################################
    # --8<-- [start:soil]
    # All three mesh layers use the same nonlinear soil; the split at -1 m
    # controls interface coupling, not material assignment.
    soil_density = 1660.0  # 1.66 tonne/m3 in the source model
    nonlinear_material = model.material.nd.pressure_depend_multi_yield(
        user_name="nonlinear_soil",
        nd=3,
        rho=soil_density,
        refShearModul=1.0e8,
        refBulkModul=3.0e8,
        frictionAng=37.0,
        peakShearStra=0.1,
        refPress=80000.0,
        pressDependCoe=0.5,
        PTAng=20.0,
        contrac=0.05,
        dilat1=0.6,
        dilat2=3.0,
        liquefac1=5000.0,
        liquefac2=0.003,
        liquefac3=1.0,
        pa=101000.0,
        c=300.0,
    )
    soil_damping = model.damping.frequency_rayleigh(
        damping_factor=0.05, f1=0.2, f2=20.0,
    )
    soil_region = model.region.element(damping=soil_damping)
    soil_element = model.element.brick.std(
        ndof=3, material=nonlinear_material,
        b1=0.0, b2=0.0, b3=-soil_density * gravity,
        lumped=True,
    )
    # The top layer stays in the model but is excluded from pile coupling.
    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_grid_1", element=soil_element, region=soil_region,
        x_min=-15.0, x_max=15.0, y_min=-15.0, y_max=15.0,
        z_min=-28.0, z_max=-14.3, nx=30, ny=30, nz=7,
    )
    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_grid_2", element=soil_element, region=soil_region,
        x_min=-15.0, x_max=15.0, y_min=-15.0, y_max=15.0,
        z_min=-14.3, z_max=-1.0, nx=30, ny=30, nz=13,
    )
    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil_grid_3", element=soil_element, region=soil_region,
        x_min=-15.0, x_max=15.0, y_min=-15.0, y_max=15.0,
        z_min=-1.0, z_max=0.0, nx=30, ny=30, nz=1,
    )
    # --8<-- [end:soil]

    # ########################################################################
    # piles
    # ########################################################################
    # --8<-- [start:piles]
    aluminum_e = 6.89e10
    aluminum_nu = 0.33
    aluminum_density = 2700.0
    pile_inner_radius, pile_outer_radius = 0.449072, 0.4953
    cap_base_z = 3.9
    cap_top_z = 7.28
    model.material.uniaxial.steel01(
        user_name="Aluminum",
        Fy=2.55e8 if angle_degrees in (0, 90) else 1.3e8,
        E0=aluminum_e, b=0.000001,
    )
    alum_g = aluminum_e / (2.0 * (1.0 + aluminum_nu))
    pile_area = math.pi * (pile_outer_radius**2 - pile_inner_radius**2)
    pile_i = math.pi * (pile_outer_radius**4 - pile_inner_radius**4) / 4.0
    pile_section = model.section.fiber.section(
        user_name="pile_section", GJ=alum_g * 2.0 * pile_i,
    )
    pile_section.add_circular_patch(
        material="Aluminum",
        int_rad=pile_inner_radius,
        ext_rad=pile_outer_radius,
        num_subdiv_circ=48,
        num_subdiv_rad=4,
        y_center=0.0,
        z_center=0.0,
        start_ang=0.0,
        end_ang=360.0,
    )

    # Keep the thesis transformation vector fixed in global coordinates.
    transformation = model.transformation.transformation3d(
        transf_type="PDelta",
        vecxz_x=-1.0,
        vecxz_y=0.0,
        vecxz_z=0.0,
    )
    pile_element = model.element.beam.disp(
        ndof=6, section=pile_section, transformation=transformation, numIntgrPts=5,
    )
    structure_damping = model.damping.uniform(
        dampingRatio=0.07, freql=2.2, freq2=15.0,
    )
    structure_region = model.region.element(damping=structure_damping)
    above_density = 909.0 / pile_area  # 0.909 tonne/m line mass
    left_soil = model.meshpart.line.single_line(
        user_name="pile_left_soil", element=pile_element, region=structure_region,
        x0=-3.809, y0=0.0, z0=-14.3, x1=-3.809, y1=0.0, z1=0.0,
        number_of_lines=19, merge_points=True, density=aluminum_density,
    )
    left_free = model.meshpart.line.single_line(
        user_name="pile_left_free", element=pile_element, region=structure_region,
        x0=-3.809, y0=0.0, z0=0.0, x1=-3.809, y1=0.0, z1=cap_base_z,
        number_of_lines=6, merge_points=True, density=above_density,
    )
    left_cap = model.meshpart.line.single_line(
        user_name="pile_left_cap", element=pile_element, region=structure_region,
        x0=-3.809, y0=0.0, z0=cap_base_z, x1=-3.809, y1=0.0, z1=5.6,
        number_of_lines=2, merge_points=True, density=above_density,
    )

    # The right pile has the same three segments on the other side of the cap.
    right_soil = model.meshpart.line.single_line(
        user_name="pile_right_soil", element=pile_element, region=structure_region,
        x0=3.809, y0=0.0, z0=-14.3, x1=3.809, y1=0.0, z1=0.0,
        number_of_lines=19, merge_points=True, density=aluminum_density,
    )
    right_free = model.meshpart.line.single_line(
        user_name="pile_right_free", element=pile_element, region=structure_region,
        x0=3.809, y0=0.0, z0=0.0, x1=3.809, y1=0.0, z1=cap_base_z,
        number_of_lines=6, merge_points=True, density=above_density,
    )
    right_cap = model.meshpart.line.single_line(
        user_name="pile_right_cap", element=pile_element, region=structure_region,
        x0=3.809, y0=0.0, z0=cap_base_z, x1=3.809, y1=0.0, z1=5.6,
        number_of_lines=2, merge_points=True, density=above_density,
    )
    # --8<-- [end:piles]

    #########################################################################
    # cap
    #########################################################################
    # --8<-- [start:cap]
    # Solid cap, not a line beam and carrying no lumped mass.
    cap_material = model.material.nd.elastic_isotropic(
        user_name="cap_mat", E=aluminum_e, nu=aluminum_nu, rho=aluminum_density,
    )
    cap_element = model.element.brick.std(
        ndof=3, material=cap_material,
        b1=0.0, b2=0.0, b3=-aluminum_density * gravity,
        lumped=True,
    )
    cap_part = model.meshpart.volume.uniform_rectangular_grid(
        user_name="cap", element=cap_element, region=structure_region,
        x_min=-5.72, x_max=5.72,
        y_min=-3.12, y_max=3.12,
        z_min=cap_base_z, z_max=cap_top_z,
        nx=11, ny=6, nz=3,
    )
    left_soil.transform.rotate_z(angle=angle_degrees)
    left_free.transform.rotate_z(angle=angle_degrees)
    left_cap.transform.rotate_z(angle=angle_degrees)
    right_soil.transform.rotate_z(angle=angle_degrees)
    right_free.transform.rotate_z(angle=angle_degrees)
    right_cap.transform.rotate_z(angle=angle_degrees)
    cap_part.transform.rotate_z(angle=angle_degrees)
    # --8<-- [end:cap]

    #########################################################################
    # interfaces
    #########################################################################
    # --8<-- [start:interfaces]
    # The thesis interface diameter is 1.181 m, larger than the physical pile diameter.
    interface_radius = 1.181 / 2.0
    # Only the two deeper soil grids transfer force to the piles; the top 1 m does not.
    left_soil_interface = model.interface.beam_solid_interface(
        name="pile_soil_interface_left", beam_part=left_soil,
        solid_parts=["soil_grid_1", "soil_grid_2"],
        radius=interface_radius, n_peri=8, n_long=3,
        penalty_param=1.0e9, g_penalty=True,
        write_connectivity=True, write_interface=True,
    )
    right_soil_interface = model.interface.beam_solid_interface(
        name="pile_soil_interface_right", beam_part=right_soil,
        solid_parts=["soil_grid_1", "soil_grid_2"],
        radius=interface_radius, n_peri=8, n_long=3,
        penalty_param=1.0e9, g_penalty=True,
        write_connectivity=True, write_interface=True,
    )
    left_cap_interface = model.interface.beam_solid_interface(
        name="pile_cap_interface_left", beam_part=left_cap,
        solid_parts=["cap"], radius=interface_radius, n_peri=8, n_long=3,
        penalty_param=1.0e9, g_penalty=True,
        write_connectivity=True, write_interface=True,
    )
    right_cap_interface = model.interface.beam_solid_interface(
        name="pile_cap_interface_right", beam_part=right_cap,
        solid_parts=["cap"], radius=interface_radius, n_peri=8, n_long=3,
        penalty_param=1.0e9, g_penalty=True,
        write_connectivity=True, write_interface=True,
    )

    #########################################################################
    # assembly
    #########################################################################

    model.assembler.create_section(
        meshparts=[
            "pile_left_soil", "pile_left_free", "pile_left_cap",
            "pile_right_soil", "pile_right_free", "pile_right_cap", "cap",
        ],
        num_partitions=1,
        partition_algorithm="kd-tree",
        merge_points=True,
    )
    model.assembler.create_section(
        meshparts=["soil_grid_1", "soil_grid_2", "soil_grid_3"],
        num_partitions=32,
        partition_algorithm="kd-tree",
        merge_points=True,
    )
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
    # --8<-- [end:interfaces]


    # ########################################################################
    # constraints
    # ########################################################################

    model.constraint.mp.laminar_boundary(dofs=[1, 2, 3], bounds=(-27.9, 0.0), direction=3)
    model.constraint.sp.fix_macro_z_min(dofs=[1, 1, 1], tol=1.0e-3)


    #########################################################################
    # gravity
    #########################################################################
    # --8<-- [start:gravity]

    # Settle under self-weight before starting the explicit dynamic solution.
    gravity_settings = dict(
        constraint_handler=model.analysis.constraint.transformation(),
        numberer=model.analysis.numberer.parallelrcm(),
        system=model.analysis.system.mumps(icntl14=400, icntl7=7),
        test=model.analysis.test.energyincr(tol=1.0e-3, max_iter=20, print_flag=2),
        algorithm=model.analysis.algorithm.modifiednewton(factor_once=True),
        integrator=model.analysis.integrator.newmark(gamma=0.6, beta=0.3025),
    )
    gravity_elastic = model.analysis.transient(
        name="gravity_elastic", num_steps=100, dt=1.0, **gravity_settings,
    )
    gravity_plastic = model.analysis.transient(
        name="gravity_plastic", num_steps=500, dt_min=0.001, dt_max=0.1,
        **gravity_settings,
    )
    # --8<-- [end:gravity]

    #########################################################################
    # excitation
    #########################################################################
    # --8<-- [start:excitation]
    # Reset the clock while keeping gravity state, then apply uniform x excitation.
    motion_series = model.time_series.path(
        dt=motion_dt, filePath=str(motion_path), factor=gravity,
    )
    uniform_x = model.pattern.uniform_excitation(dof=1, time_series=motion_series)
    # --8<-- [end:excitation]

    #########################################################################
    #    recorders
    #########################################################################
    recorder_dt = 0.02
    pile_recorder_dt = 0.01
    response_recorder = model.recorder.vtkhdf(
        file_base_name="rotated_bent_response.vtkhdf",
        resp_types=["disp", "vel", "accel"],
        delta_t=recorder_dt,
    )
    left_pile_force = model.recorder.beam_force(
        meshparts=["pile_left_soil", "pile_left_free", "pile_left_cap"],
        force_type="globalForce",
        file_prefix="pile_left_force",
        output_format="xml",
        include_time=True,
        delta_t=pile_recorder_dt,
        precision=16,
    )
    right_pile_force = model.recorder.beam_force(
        meshparts=["pile_right_soil", "pile_right_free", "pile_right_cap"],
        force_type="globalForce",
        file_prefix="pile_right_force",
        output_format="xml",
        include_time=True,
        delta_t=pile_recorder_dt,
        precision=16,
    )
    interface_recorder = model.recorder.embedded_beam_solid_interface(
        interface=[
            left_soil_interface, right_soil_interface,
            left_cap_interface, right_cap_interface,
        ],
        dt=recorder_dt,
    )

    ###########################################################################
    # Explicit shaking: one structural rank and 32 soil ranks per case.
    # No retry or substepping: changing the step would change explicit stability.
    ###########################################################################
    # --8<-- [start:dynamic]
    dynamic_dt = 4.0e-5
    dynamic_analysis = model.analysis.transient(
        name="dynamic",
        constraint_handler=model.analysis.constraint.transformation(),
        numberer=model.analysis.numberer.parallelplain(),
        system=model.analysis.system.mpidiagonal(),
        test=model.analysis.test.normdispincr(tol=1e-8, max_iter=1),
        algorithm=model.analysis.algorithm.linear(),
        integrator=model.analysis.integrator.explicitdifference(),
        dt=dynamic_dt,
        num_steps=round(final_time / dynamic_dt),
        max_retries=0,
        initialize=True,
    )
    # --8<-- [end:dynamic]

    #########################################################################
    # process
    ##########################################################################
    # --8<-- [start:gravity-process]
    model.process.add_step(model.actions.update_material_stage_to_elastic(), "Elastic gravity stage")
    model.process.add_step(gravity_elastic, "Gravity elastic (100 steps, dt=1.0)")
    model.process.add_step(model.actions.update_material_stage_to_plastic(), "Plastic gravity stage")
    model.process.add_step(gravity_plastic, "Gravity plastic (500 ramped steps)")
    model.process.add_step(uniform_x, "Uniform global-x base excitation")
    model.process.add_step(response_recorder, "Record displacement, velocity, acceleration")
    model.process.add_step(left_pile_force, "Record left pile end forces")
    model.process.add_step(right_pile_force, "Record right pile end forces")
    model.process.add_step(interface_recorder, "Record pile-soil and pile-cap interfaces")
    model.process.add_step(model.actions.set_time(0.0), "Reset time, keeping gravity state")
    model.process.add_step(dynamic_analysis, "Run the 50 s dynamic analysis")
    # --8<-- [end:gravity-process]

    #########################################################################
    # export
    #########################################################################
    tcl_file = case_dir / "model.tcl"
    model.export_to_tcl(filename=str(tcl_file.resolve()), progress_callback=lambda *_: None)
    return tcl_file


def postprocess_results(context):
    """Reduce remote histories and plot validation without archiving raw fields."""
    spec = importlib.util.spec_from_file_location(
        "rotated_postprocess", context.workspace / POSTPROCESS
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = Path(context.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    numerical = module.extract_reduced_results(
        context.workspace / "build",
        context.workspace / "motions" / MOTION_FILE,
        output / "rotated_bent_numerical.h5",
        motion_dt=0.0127,
    )
    return module.generate_validation_plots(
        numerical, context.workspace / EXPERIMENT_FILE, output
    )


# --8<-- [start:workflow]
def build_workflow():
    """Build four cases sequentially, then solve them in parallel."""
    workflow = fm.Workflow("rotated-two-pile-bent")
    workflow.add(
        "build",
        tasks=[
            fm.tasks.Python("angle_000", build_model, kwargs={"angle_degrees": 0}),
            fm.tasks.Python("angle_030", build_model, kwargs={"angle_degrees": 30}),
            fm.tasks.Python("angle_060", build_model, kwargs={"angle_degrees": 60}),
            fm.tasks.Python("angle_090", build_model, kwargs={"angle_degrees": 90}),
        ],
    )
    workflow.add(
        "solve",
        parallel=True,
        tasks=[
            fm.tasks.OpenSees("angle_000", "build/angle_000/model.tcl", ranks=RANKS_PER_CASE),
            fm.tasks.OpenSees("angle_030", "build/angle_030/model.tcl", ranks=RANKS_PER_CASE),
            fm.tasks.OpenSees("angle_060", "build/angle_060/model.tcl", ranks=RANKS_PER_CASE),
            fm.tasks.OpenSees("angle_090", "build/angle_090/model.tcl", ranks=RANKS_PER_CASE),
        ],
    )
    workflow.add(
        "postprocess", tasks=[fm.tasks.Python("responses", postprocess_results)]
    )
    workflow.outputs(
        "postprocess/responses/*",
        "**/stdout.log",
        "build/*/model.tcl",
        "motions/**/*",
        "solve/**/*",
    )
    return workflow
# --8<-- [end:workflow]


# --8<-- [start:submission]
if __name__ == "__main__":
    job = fm.submit(
        function=build_workflow,
        platform="tacc",
        settings={
            "app_id": "amnp95-femora-workflow-stampede3",
            "system": "stampede3",
            "queue": "skx",
            "allocation": "DesignSafe-SimCenter",
            "nodes": 3,
            "cores_per_node": 48,
            "minutes": 2880,
        },
        files={
            POSTPROCESS: Path(__file__).with_name(POSTPROCESS),
            EXPERIMENT_FILE: (
                Path(__file__).resolve().parents[1]
                / "inputs/validation/rotated_two_pile_bent"
                / EXPERIMENT_FILE
            ),
            f"motions/{MOTION_FILE}": motions_dir() / MOTION_FILE,
        },
    )
    print(f"Job UUID: {job.id}")
# --8<-- [end:submission]
