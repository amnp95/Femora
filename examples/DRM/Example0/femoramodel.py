import os

import femora as fm
from femora.utils.paths import motions_dir

# Run from this example folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# -------------------------------------------------------------------
# Example0 (DRM folder): Same layer profile as DRM/Example2, but using
# uniform excitation + laminar boundary conditions (site-response style)
# instead of DRM absorbing layers and H5DRM loading.
# -------------------------------------------------------------------

# Layer properties (same as examples/DRM/Example2)
layers = [
    {"layer": 1, "rho": 2142.0500, "vp": 669.0500, "vs": 353.1000, "xi_s": 0.0296, "xi_p": 0.0148, "thickness": 8},
    {"layer": 2, "rho": 2146.2000, "vp": 785.2500, "vs": 414.4000, "xi_s": 0.0269, "xi_p": 0.0134, "thickness": 8},
    {"layer": 3, "rho": 2150.3500, "vp": 886.0500, "vs": 467.6000, "xi_s": 0.0249, "xi_p": 0.0125, "thickness": 8},
    {"layer": 4, "rho": 2154.4500, "vp": 976.4000, "vs": 515.3000, "xi_s": 0.0234, "xi_p": 0.0117, "thickness": 8},
    {"layer": 5, "rho": 2158.6000, "vp": 1059.0500, "vs": 558.9500, "xi_s": 0.0221, "xi_p": 0.0111, "thickness": 8},
    {"layer": 6, "rho": 2162.7500, "vp": 1135.6500, "vs": 599.4000, "xi_s": 0.0211, "xi_p": 0.0105, "thickness": 8},
]


# Mesh parameters (same geometry as DRM/Example2)
x_min, x_max = -64.0, 64.0
y_min, y_max = -64.0, 64.0
z_base = -48.0
dx = 4.0
dy = 4.0
dz = 4.0

nx = int((x_max - x_min) / dx)
ny = int((y_max - y_min) / dy)


# Build layers bottom -> top (same ordering as DRM/Example2 loop)
index = 0
for layer in layers[::-1]:
    rho = layer["rho"]
    vp = layer["vp"]
    vs = layer["vs"]
    xi_s = layer["xi_s"]
    thickness = layer["thickness"]

    vp_vs_ratio = (vp / vs) ** 2
    nu = (vp_vs_ratio - 2) / (2 * (vp_vs_ratio - 1))
    E = 2 * rho * (vs**2) * (1 + nu)

    # Keep same units conversion used in DRM/Example2
    E = E / 1000.0
    rho = rho / 1000.0

    mat = fm.material.create_material(
        "nDMaterial",
        "ElasticIsotropic",
        user_name=f"Layer{layer['layer']}",
        E=E,
        nu=nu,
        rho=rho,
    )
    ele = fm.element.create_element(
        element_type="stdBrick",
        ndof=3,
        material=mat,
        b1=0,
        b2=0,
        b3=0,
    )

    damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=3, f2=15)
    reg = fm.region.create_region("elementRegion", damping=damp)

    z_min = z_base + index * thickness
    z_max = z_min + thickness
    nz = int(thickness / dz)

    fm.meshPart.create_mesh_part(
        "Volume mesh",
        "Uniform Rectangular Grid",
        user_name=f"Layer{layer['layer']}",
        element=ele,
        region=reg,
        **{
            "X Min": x_min,
            "X Max": x_max,
            "Y Min": y_min,
            "Y Max": y_max,
            "Z Min": z_min,
            "Z Max": z_max,
            "Nx Cells": nx,
            "Ny Cells": ny,
            "Nz Cells": nz,
        },
    )
    index += 1


mesh_parts = [f"Layer{layer['layer']}" for layer in layers]

# Use single-partition assembly by default so it runs out-of-the-box
fm.assembler.create_section(mesh_parts, num_partitions=32, merge_points=True)
fm.assembler.Assemble()


# -------------------------------------------------------------------
# Boundary conditions (laminar, like SiteResponse examples)
# -------------------------------------------------------------------
fm.constraint.mp.create_laminar_boundary(bounds=(z_base + 0.1, 0.0), dofs=[1, 2, 3], direction=3)
fm.constraint.sp.fixMacroZmin(dofs=[1, 1, 1], tol=1e-3)


# -------------------------------------------------------------------
# Uniform excitation input (reuse SiteResponse/Example5 frequency sweep)
# -------------------------------------------------------------------
_MOTIONS = motions_dir()
acc_path = str(_MOTIONS / "kobe.acc")
time_path = str(_MOTIONS / "kobe.time")

timeseries = fm.timeSeries.create_time_series(
    series_type="path",
    filePath=acc_path,
    fileTime=time_path,
    factor=9.81,
)

pattern = fm.pattern.create_pattern(pattern_type="uniformexcitation", dof=1, time_series=timeseries)


# -------------------------------------------------------------------
# Recorder + explicit transient analysis
# -------------------------------------------------------------------
fm.set_results_folder("Results")
recorder = fm.recorder.vtkhdf(
    file_base_name="result.vtkhdf",
    resp_types=["accel", "disp"],
    delta_t=0.02,
)

final_time = 50.0
dynamic = fm.actions.tcl(
f"""
constraints Plain
numberer    ParallelPlain
system      MPIDiagonal
algorithm   Linear
integrator  Explicitdifference
analysis    Transient
initialize
set dt [getCriticalTimeStep -safetyFactor 0.8]
if {{$pid == 0}} {{puts "Critical time step: $dt"}}
while {{[getTime] < {final_time}}} {{
\tif {{$pid == 0}} {{puts "Time : [getTime]/{final_time}"}}
\tset Ok [analyze 1 $dt]
}}
wipeAnalysis
"""
)

fm.process.add_step(pattern, description="Uniform excitation (frequency sweep)")
fm.process.add_step(recorder, description="VTK-HDF recorder")
fm.process.add_step(dynamic, description="Explicit transient analysis")

fm.export_to_tcl("model.tcl")

