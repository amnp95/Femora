"""Elastic/plastic basin: build, inspect, and export; with optional TACC workflow."""

from pathlib import Path

import numpy as np
import pyvista as pv
from femora import Model
import femora as fm

# --8<-- [start:settings]
BASIN_MATERIAL = "elastic"  # Options: "elastic", "plastic", "no_basin".
# Units: m, kN, tonne, s; stresses and moduli are in kPa.
# Both cases use the elastic legacy density, not Example6's 1.3 tonne/m3.
BASIN_DENSITY = 1.8
FINAL_TIME = 27.4  # Shared duration within all three SW4 reference windows.
DYNAMIC_DT = 0.01  # Initial implicit step; check convergence and time-step sensitivity.
RECORDER_DT = 0.02
NO_PHYSICAL_DAMPING = False  # Disable basin/host damping only; retain absorber damping.
# Shared scratch inputs are accessible from compute nodes; Corral is not.
DRM_ROOT = Path("/scratch/08189/amnp95/drm_inputs")
# Top to bottom: name, density, Vp, Vs, viscous damping ratio, thickness.
LAYERS = [
    ("layer_1", 2.14205, 669.05, 353.10, 0.0296, 8.0),
    ("layer_2", 2.14620, 785.25, 414.40, 0.0269, 8.0),
    ("layer_3", 2.15035, 886.05, 467.60, 0.0249, 8.0),
    ("layer_4", 2.15445, 976.40, 515.30, 0.0234, 8.0),
    ("layer_5", 2.15860, 1059.05, 558.95, 0.0221, 8.0),
    ("layer_6", 2.16275, 1135.65, 599.40, 0.0211, 8.0),
]
# --8<-- [end:settings]

def build_model(drm_file=None, output_dir=Path("example_outputs/basin"),
                material=BASIN_MATERIAL, final_time=FINAL_TIME,
                no_physical_damping=NO_PHYSICAL_DAMPING):
    """Build the selected material and export its OpenSees model."""
    if not np.isfinite(final_time) or final_time <= 0:
        raise ValueError("final_time must be positive and finite")
    if material not in ("elastic", "plastic", "no_basin"):
        raise ValueError('material must be "elastic", "plastic", or "no_basin"')
    if drm_file is not None and not drm_file.is_file():
        raise FileNotFoundError(drm_file)

    # Keep each case's Tcl and recorder files in its own output folder.
    output = output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    model = Model(model_name=f"basin_{material}", model_path=str(output))
    model.set_results_folder((output / "results").as_posix())

    # --8<-- [start:basin-material]
    # 1. Define the soft basin material from Vs = 150 and Vp = 300 m/s.
    # G = rho*Vs^2 and K = rho*(Vp^2 - 4*Vs^2/3); both cases start equally stiff.
    basin_g = BASIN_DENSITY * 150.0**2
    basin_k = BASIN_DENSITY * (300.0**2 - 4.0 * 150.0**2 / 3.0)
    if material == "elastic":
        basin_material = model.material.nd.elastic_isotropic(
            user_name="basin", E=2.0 * basin_g * (1.0 + 1.0 / 3.0), nu=1.0 / 3.0, rho=BASIN_DENSITY,
        )
    elif material == "plastic":
        basin_material = model.material.nd.pressure_independ_multi_yield(
            user_name="basin", nd=3, rho=BASIN_DENSITY,
            refShearModul=basin_g, refBulkModul=basin_k,
            cohesi=8.0, peakShearStra=0.1,
        )
    if material != "no_basin":
        # Both basin cases share viscous damping; plasticity adds hysteresis.
        basin_damping = None if no_physical_damping else model.damping.frequency_rayleigh(damping_factor=0.03, f1=3.0, f2=15.0)
        basin_region = model.region.element(user_name="basin", damping=basin_damping)
        # stdBrick expects body force per volume: density times gravity, in kN/m^3.
        basin_element = model.element.brick.std(ndof=3, material=basin_material, lumped=False, b3=-9.81 * BASIN_DENSITY)
    # --8<-- [end:basin-material]

    # --8<-- [start:mesh]
    # 2. Build the six host layers, walking downward from the surface.
    # Each 8 m layer contains two 4 m brick rows.
    # Cell-center selection makes a stepped, conforming basin/host boundary.
    part_names = []
    z_top = 0.0
    for name, density, vp, vs, damping_ratio, thickness in LAYERS:
        z_bottom = z_top - thickness
        # Convert each layer's wave speeds into elastic stiffness and Poisson ratio.
        shear_modulus = density * vs**2
        poisson_ratio = (vp**2 - 2.0 * vs**2) / (2.0 * (vp**2 - vs**2))
        layer_material = model.material.nd.elastic_isotropic(
            user_name=name, E=2.0 * shear_modulus * (1.0 + poisson_ratio),
            nu=poisson_ratio, rho=density,
        )
        # A region assigns this layer's damping to its host bricks.
        damping = None if no_physical_damping else model.damping.frequency_rayleigh(damping_factor=damping_ratio, f1=3.0, f2=15.0)
        region = model.region.element(user_name=name, damping=damping)
        element = model.element.brick.std(ndof=3, material=layer_material, lumped=False, b3=-9.81 * density)
        # 33 points span each horizontal direction: 32 cells across 128 m.
        # StructuredGrid produces hexahedral corner ordering required by stdBrick.
        # RectilinearGrid would produce voxels with a different node order.
        x, y, z = np.meshgrid(
            np.linspace(-64.0, 64.0, 33), np.linspace(-64.0, 64.0, 33),
            np.linspace(z_bottom, z_top, 3),
            indexing="ij",
        )
        grid = pv.StructuredGrid(x, y, z).cast_to_unstructured_grid()
        # The sphere center lies above ground; its intersection with soil is a bowl.
        # Classify whole bricks rather than cutting curved, non-brick cells.
        centers = grid.cell_centers().points
        inside_basin = np.linalg.norm(centers - [0.0, 0.0, 70.0], axis=1) <= 85.0
        # Outside the bowl, retain the layer's elastic material.
        host_mesh = grid.extract_cells(~inside_basin)
        model.meshpart.general.external_mesh(user_name=name, element=element, region=region, mesh=host_mesh)
        part_names.append(name)
        # Inside the bowl, replace host bricks with the shared basin material.
        # Only the upper two layers contain basin cells; no cells are duplicated.
        if inside_basin.any():
            basin_name = f"basin_{name}"
            basin_mesh = grid.extract_cells(inside_basin)
            # Preserve the extracted geometry in the baseline, but give these
            # cells the same material, density, and damping as this host layer.
            if material == "no_basin":
                basin_element = element
                basin_region = region
            model.meshpart.general.external_mesh(
                user_name=basin_name, element=basin_element, region=basin_region, mesh=basin_mesh,
            )
            part_names.append(basin_name)
        # Start the next layer at the bottom of the current one.
        z_top = z_bottom
    # --8<-- [end:mesh]

    if drm_file is None:
        print(f"Geometry built in {output}. Supply --drm to export the analysis.")
    else:
        # --8<-- [start:boundary]
        # 3. Partition the physical soil and add absorbing rows at sides and bottom.
        # 32 physical + 64 absorbing partitions = 96 MPI ranks.
        model.assembler.create_section(meshparts=part_names, num_partitions=32, partition_algorithm="kd-tree")
        model.interface.boundary.absorber(
            num_layers=8, num_partitions=64, partition_algo="kd-tree",
            geometry="Rectangular", boundary_type="Rayleigh",
            rayleigh_damping=0.95, match_damping=False,
        )
        # Merge shared nodes so layers and basin transfer forces continuously.
        model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)
        # Fix only the outer absorber faces; leave the ground surface free.
        model.constraint.sp.fix_macro_x_min(dofs=[1, 1, 1], tol=0.01)
        model.constraint.sp.fix_macro_x_max(dofs=[1, 1, 1], tol=0.01)
        model.constraint.sp.fix_macro_y_min(dofs=[1, 1, 1], tol=0.01)
        model.constraint.sp.fix_macro_y_max(dofs=[1, 1, 1], tol=0.01)
        model.constraint.sp.fix_macro_z_min(dofs=[1, 1, 1], tol=0.01)
        # --8<-- [end:boundary]

        # --8<-- [start:analysis]
        # 4. Define the analyses, loading, and recorders without running them yet.
        # Static gravity establishes equilibrium without startup inertia.
        # ICNTL14 increases Mumps workspace allowance; ICNTL7 selects ordering.
        # Hold the body-force loading fixed and correct equilibrium for 10 steps.
        gravity_elastic = model.analysis.static(
            name="gravity_elastic", constraint_handler=model.analysis.constraint.transformation(),
            numberer=model.analysis.numberer.parallelrcm(), system=model.analysis.system.mumps(icntl14=400, icntl7=7),
            test=model.analysis.test.energyincr(tol=1.0e-8, max_iter=30, print_flag=0),
            algorithm=model.analysis.algorithm.modifiednewton(factor_once=True),
            integrator=model.analysis.integrator.loadcontrol(incr=0.0),
            num_steps=10, max_retries=0,
        )
        gravity_reequilibrate = model.analysis.static(
            name="gravity_reequilibrate", constraint_handler=model.analysis.constraint.transformation(),
            numberer=model.analysis.numberer.parallelrcm(), system=model.analysis.system.mumps(icntl14=400, icntl7=7),
            test=model.analysis.test.energyincr(tol=1.0e-5, max_iter=30, print_flag=0),
            algorithm=model.analysis.algorithm.modifiednewton(factor_once=False),
            integrator=model.analysis.integrator.loadcontrol(incr=0.0),
            num_steps=10, max_retries=0,
        )
        # The DRM file supplies the incoming layered-background wave field.
        # Identity transformation preserves its coordinates and physical units.
        drm = model.pattern.h5drm(
            filepath=drm_file.resolve().as_posix(), factor=1.0, crd_scale=1.0,
            distance_tolerance=0.01, do_coordinate_transformation=1,
            transform_matrix=[1, 0, 0, 0, 1, 0, 0, 0, 1], origin=[0, 0, 0],
        )
        # Record motion and soil tensors for response plots and stress-strain checks.
        recorder = model.recorder.vtkhdf(
            file_base_name="basin_response.vtkhdf",
            resp_types=["disp", "vel", "accel", "stress3D6", "strain3D6"], delta_t=RECORDER_DT,
        )
        # Implicit Newmark uses Mumps and reuses the tangent factorization per analysis.
        # Retry once, then halve failed steps up to three levels. The exporter
        # resets factor-once reuse whenever dt changes, including on return.
        dynamic = model.analysis.transient(
            name="basin_response", constraint_handler=model.analysis.constraint.plain(),
            numberer=model.analysis.numberer.parallelrcm(), system=model.analysis.system.mumps(icntl14=400, icntl7=7),
            test=model.analysis.test.energyincr(tol=1.0e-4, max_iter=8, print_flag=0),
            algorithm=model.analysis.algorithm.modifiednewton(factor_once=True),
            integrator=model.analysis.integrator.newmark(gamma=0.5, beta=0.25),
            dt=DYNAMIC_DT, final_time=final_time, initialize=True, max_retries=1,
            num_sublevels=3, num_substeps=2,
        )
        # 5. Put the full execution sequence together here, for both material cases.
        # Elastic materials ignore stage updates. Re-equilibrate after the switch,
        # reset the clock while keeping the gravity state, then apply the DRM wave.
        model.process.add_step(model.actions.update_material_stage_to_elastic(), "Elastic initialization")
        model.process.add_step(gravity_elastic, "Equilibrate self-weight")
        model.process.add_step(model.actions.update_material_stage_to_plastic(), "Enable plastic material stage")
        model.process.add_step(gravity_reequilibrate, "Re-equilibrate before dynamic loading")
        model.process.add_step(model.actions.set_time(0.0), "Reset the dynamic clock")
        model.process.add_step(drm, "Apply the layered background wave field")
        model.process.add_step(recorder, "Record physical and absorbing domain responses")
        model.process.add_step(dynamic, "Run implicit basin response")
        # 6. Export only; the workflow's OpenSees task executes this Tcl remotely.
        model.export_to_tcl(str(output / "model.tcl"), progress_callback=lambda *_: None)
        print(f"Exported {output / 'model.tcl'}; launch with 96 MPI ranks.")
        return output / "model.tcl"
        # --8<-- [end:analysis]

def build_case(context, material, site, final_time):
    """Use the staged scratch record for this site's material case."""
    drm_file = DRM_ROOT / f"HaywardFault_SW4_DRM_Site{site}.h5drm"
    return build_model(
        drm_file=drm_file, output_dir=context.output_dir,
        material=material, final_time=final_time,
    )


def postprocess_results(context, final_time):
    """Keep all plotting and result inspection in the companion file."""
    import importlib.util

    # Bundled companion files are staged in the workspace, not on sys.path.
    path = context.workspace / "basin_postprocess.py"
    spec = importlib.util.spec_from_file_location("basin_postprocess", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load basin postprocessor from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_results(context.workspace / "build", context.output_dir, final_time)


# --8<-- [start:workflow]
def build_workflow():
    final_time = FINAL_TIME
    workflow = fm.Workflow("basin-comparison")
    # Build sequentially; solve the three material cases together at each site.
    workflow.add("build", parallel=False, tasks=[
        fm.tasks.Python("site1_elastic", build_case,
                        kwargs={"site": 1, "material": "elastic", "final_time": final_time}),
        fm.tasks.Python("site1_plastic", build_case,
                        kwargs={"site": 1, "material": "plastic", "final_time": final_time}),
        fm.tasks.Python("site1_no_basin", build_case,
                        kwargs={"site": 1, "material": "no_basin", "final_time": final_time}),
        fm.tasks.Python("site2_elastic", build_case,
                        kwargs={"site": 2, "material": "elastic", "final_time": final_time}),
        fm.tasks.Python("site2_plastic", build_case,
                        kwargs={"site": 2, "material": "plastic", "final_time": final_time}),
        fm.tasks.Python("site2_no_basin", build_case,
                        kwargs={"site": 2, "material": "no_basin", "final_time": final_time}),
        fm.tasks.Python("site3_elastic", build_case,
                        kwargs={"site": 3, "material": "elastic", "final_time": final_time}),
        fm.tasks.Python("site3_plastic", build_case,
                        kwargs={"site": 3, "material": "plastic", "final_time": final_time}),
        fm.tasks.Python("site3_no_basin", build_case,
                        kwargs={"site": 3, "material": "no_basin", "final_time": final_time}),
    ])
    # Three concurrent 96-rank solves fill six 48-core SKX nodes.
    for site in (1, 2, 3):
        workflow.add(
            f"solve_site{site}",
            parallel=True,
            tasks=[
                fm.tasks.OpenSees(
                    f"site{site}_{material}",
                    f"build/site{site}_{material}/model.tcl",
                    ranks=96,
                )
                for material in ("elastic", "plastic", "no_basin")
            ],
        )
    workflow.add("postprocess", parallel=False, tasks=[
        fm.tasks.Python("responses", postprocess_results, kwargs={"final_time": final_time}),
    ])
    # Download compact products; raw VTKHDF remains in the remote workspace.
    workflow.outputs("postprocess/responses/*", "**/stdout.log", "**/stderr.log",
                     "build/*/model.tcl")
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
            "nodes": 6,
            "cores_per_node": 48,
            "minutes": 240,
        },
        files={
            "basin_postprocess.py": Path(__file__).with_name("basin_postprocess.py"),
        },
    )
    print(f"Job UUID: {job.id}")
# --8<-- [end:submission]
