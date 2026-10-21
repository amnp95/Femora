"""Edit the settings, export model.tcl, then run it with OpenSees.
Use steel_concentrically_braced_frame_3d_postprocess.py to plot the results.
"""
import os
from pathlib import Path

import numpy as np
from femora import Model
from femora.tools.buildings import SteelConcentricallyBracedFrame3D

# Settings. Units: metres, kN, tonnes, seconds.
# --8<-- [start:settings]
analysis_type = "earthquake"             # "pushover" or "earthquake"
nonlinear = True
calculate_modes = False                 # Requires an OpenSees executable.
plot_modes = True
# --8<-- [end:settings]
opensees = os.environ.get("FEMORA_OPENSEES", "OpenSees")
yield_strength = 150000                  # 150 MPa; use 345000 for stronger steel.
G = 76.923076923e6                       # Shear modulus, kN/m^2, for elastic torsion.
material_density = 7.85                  # tonne/m^3; used for member mass and inertia.
push_control = "displacement"            # "displacement" or "load"
push_steps = 60
roof_drift = 0.01                        # Roof displacement / building height.
target_base_shear = 5000                 # kN, for load control only.
dt = 0.01
final_time = 42.01
damping_ratio = 0.02
reference_frequency = 1.8082838126369407  # Hz, elastic fiber frame's first mode.
output = Path(f"example_outputs/frame_{analysis_type}_{'nonlinear' if nonlinear else 'elastic'}").resolve()
motion_folder = Path(__file__).resolve().parents[1] / "inputs/motions"

if analysis_type not in ("pushover", "earthquake"):
    raise ValueError("Choose pushover or earthquake")
if push_control not in ("displacement", "load"):
    raise ValueError("Choose displacement or load control")
(output / "results").mkdir(parents=True, exist_ok=True)

# Both material choices use the same geometry and floor masses.
# --8<-- [start:geometry]
geometry = dict(
    num_stories=5,
    x_bays=[8, 8, 8],
    y_bays=[8, 8, 8],
    story_heights=[4, 3.5, 3.5, 3.5, 3.5],
    floor_masses=[250, 250, 250, 250, 200],
    column_sections="W14X90",
    beam_sections="W18X35",
    brace_sections="HSS8X8X3/8",
    member_formulation="force_based",
)
# --8<-- [end:geometry]
steel_properties = dict(E=200e6)

# Optional elastic modes. Recalculate when changing the frame geometry.
if calculate_modes:
    # --8<-- [start:modes]
    reference = SteelConcentricallyBracedFrame3D(**geometry)
    modes = reference.get_modes(
        num_modes=6,
        material=dict(type="Elastic", **steel_properties),
        material_density=material_density,
        G=G,
        opensees_exe=opensees,
        plot=plot_modes,
        print_results=True,
    )
    # --8<-- [end:modes]
    reference_frequency = float(modes["frequencies"][0])
    np.savez_compressed(output / "modes.npz", **modes)

# Steel01 supplies yielding and 1% hardening. Brace buckling is not modeled.
# --8<-- [start:materials]
model = Model(model_name="steel_frame", model_path=str(output))
model.set_results_folder((output / "results").as_posix())
if nonlinear:
    steel = model.material.uniaxial.steel01(
        user_name="steel",
        Fy=yield_strength,
        E0=steel_properties["E"],
        b=0.01,
    )

else:
    steel = model.material.uniaxial.elastic(user_name="steel", E=steel_properties["E"])

building = SteelConcentricallyBracedFrame3D(**geometry)
# --8<-- [end:materials]

# --8<-- [start:assembly]
building.build(
    model=model,
    material=steel,
    G=G,
    material_density=material_density,
)

# Fix the base and tie each floor's in-plane motion to its mass node.
model.assembler.create_section(
    meshparts=[building.name_prefix],
    num_partitions=1,
)
model.assembler.assemble(merge_points=True)

building.apply_fixed_base(model)
building.create_rigid_diaphragms(model)
# --8<-- [end:assembly]

# Apply floor gravity loads and establish equilibrium. Positive g means downward.
# --8<-- [start:gravity]
gravity = model.analysis.static(
    name="gravity",
    constraint_handler=model.analysis.constraint.transformation(),
    numberer=model.analysis.numberer.rcm(),
    system=model.analysis.system.bandgeneral(),
    algorithm=model.analysis.algorithm.newton(),
    test=model.analysis.test.energyincr(tol=1e-8, max_iter=30),
    integrator=model.analysis.integrator.loadcontrol(incr=0),
    num_steps=1,
)

model.process.add_step(building.create_gravity_pattern(model, g=9.81))
model.process.add_step(gravity)

model.process.add_step(model.actions.load_const())
model.process.add_step(model.actions.set_time(0))
# --8<-- [end:gravity]

if analysis_type == "pushover":
    # The pattern is a reference load, not a force limit.
    # --8<-- [start:pushover-load]
    lateral = building.create_pushover_pattern(
        model,
        time_series=model.time_series.linear(),
        base_shear=1000,
        direction="x",
        distribution="mass_height",
    )

    model.process.add_step(lateral)
    # --8<-- [end:pushover-load]

    roof_node = lateral.get_loads()[-1].node_mask.to_tags()[0]
    # --8<-- [start:pushover-control]
    if push_control == "displacement":
        integrator = model.analysis.integrator.displacementcontrol(
            node_tag=roof_node,
            dof=1,
            incr=building.total_height * roof_drift / push_steps,
        )
    else:
        integrator = model.analysis.integrator.loadcontrol(
            incr=target_base_shear / (1000 * push_steps),
        )
    # --8<-- [end:pushover-control]

    # --8<-- [start:pushover-analysis]
    response = model.analysis.static(
        name="pushover",
        constraint_handler=model.analysis.constraint.transformation(),
        numberer=model.analysis.numberer.rcm(),
        system=model.analysis.system.bandgeneral(),
        algorithm=model.analysis.algorithm.newton(),
        test=model.analysis.test.energyincr(tol=1e-8, max_iter=30),
        integrator=integrator,
        num_steps=push_steps,
        max_retries=0,
    )
    # --8<-- [end:pushover-analysis]

    recorder = building.get_recorders(
        model,
        file_name="response.vtkhdf",
        abscissa="load_factor",
    )
else:
    # Keep the supplied timestamps and convert Kobe acceleration from g to m/s^2.
    # --8<-- [start:earthquake-load]
    time = np.r_[0, np.loadtxt(motion_folder / "kobe.time")]
    acceleration = np.r_[0, np.loadtxt(motion_folder / "kobe.acc")] * 9.81

    series = model.time_series.path(time=time.tolist(), values=acceleration.tolist())
    model.process.add_step(model.pattern.uniform_excitation(dof=1, time_series=series))
    # --8<-- [end:earthquake-load]

    np.savetxt(
        output / "ground_motion.csv",
        np.column_stack((time, acceleration)),
        delimiter=",",
        header="time_s,acceleration_m_s2",
        comments="",
    )

    # Mass damping avoids stiffness-proportional forces in yielded members.
    # --8<-- [start:damping]
    alpha_m = 2 * damping_ratio * 2 * np.pi * reference_frequency
    model.process.add_step(model.actions.tcl(f"rayleigh {alpha_m} 0 0 0"))
    # --8<-- [end:damping]

    # --8<-- [start:earthquake-analysis]
    response = model.analysis.transient(
        name="earthquake",
        constraint_handler=model.analysis.constraint.transformation(),
        numberer=model.analysis.numberer.rcm(),
        system=model.analysis.system.bandgeneral(),
        algorithm=model.analysis.algorithm.newton(),
        test=model.analysis.test.normdispincr(tol=1e-8, max_iter=30),
        integrator=model.analysis.integrator.newmark(gamma=0.5, beta=0.25),
        dt=dt,
        final_time=final_time,
        initialize=True,
        max_retries=1,
        num_sublevels=3,
        num_substeps=2,
    )
    # --8<-- [end:earthquake-analysis]

    # --8<-- [start:recorder]
    recorder = building.get_recorders(
        model,
        file_name="response.vtkhdf",
        delta_t=dt,
        acceleration_basis="relative",
    )
    # --8<-- [end:recorder]

# One VTKHDF recorder stores motion and global/local member-end forces.
# --8<-- [start:process]
model.process.add_step(recorder)
if analysis_type == "pushover":
    model.process.add_step(model.actions.tcl("record"))
model.process.add_step(response)
model.process.add_step(model.actions.remove_recorders())
# --8<-- [end:process]

# Explicit metadata identifies floors and member roles in a later session.
# --8<-- [start:export]
building.export_metadata(
    model,
    output / "building.structure.h5",
    units=dict(length="m", force="kN", moment="kN*m", acceleration="m/s^2"),
)

model.export_to_tcl(str(output / "model.tcl"))
# --8<-- [end:export]
print(f"Run with OpenSees: {output / 'model.tcl'}")
