import os

import femora as fm

os.chdir(os.path.dirname(__file__))
fm.set_results_folder("Results")

# -------------------------------------------------------------------
# IMPORTANT:
# This example's soil layering + domain bounds now match DRM/Example2.
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

# Domain bounds + mesh size (same as DRM/Example2)
x_min, x_max = -64.0, 64.0
y_min, y_max = -64.0, 64.0
z_base = -48.0
dx = 4.0
dy = 4.0
dz = 4.0

nx = int((x_max - x_min) / dx)
ny = int((y_max - y_min) / dy)

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


# Create assembly Sections
fm.assembler.create_section(meshparts=[f"Layer{layer['layer']}" for layer in layers], num_partitions=32)


# Assemble the mesh parts
fm.assembler.Assemble()

# ===================================================================
# creating the DRM pattern
# ===================================================================

# The soil profile used for DRM load generation should match the mesh layering above.
# TransferFunction expects a layered profile with thickness (h), Vs, rho, and damping definition.
soil = [
    {"h": 8, "vs": 353.1000, "rho": 2142.0500, "damping": 0.0296, "damping_type": "rayleigh", "f1": 3, "f2": 15},
    {"h": 8, "vs": 414.4000, "rho": 2146.2000, "damping": 0.0269, "damping_type": "rayleigh", "f1": 3, "f2": 15},
    {"h": 8, "vs": 467.6000, "rho": 2150.3500, "damping": 0.0249, "damping_type": "rayleigh", "f1": 3, "f2": 15},
    {"h": 8, "vs": 515.3000, "rho": 2154.4500, "damping": 0.0234, "damping_type": "rayleigh", "f1": 3, "f2": 15},
    {"h": 8, "vs": 558.9500, "rho": 2158.6000, "damping": 0.0221, "damping_type": "rayleigh", "f1": 3, "f2": 15},
    {"h": 8, "vs": 599.4000, "rho": 2162.7500, "damping": 0.0211, "damping_type": "rayleigh", "f1": 3, "f2": 15},
]

# the rock layer is defined as a single layer with the properties below
# we just assume a hard rock layer with high shear wave velocity and density
# to represent the rigid base condition to create a high impedance contrast
rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}

import numpy as np
from femora.tools.transferFunction import TransferFunction, TimeHistory
from femora.utils.paths import motions_dir

# Create transfer function instance (soil profile matches the mesh above)
tf = TransferFunction(soil, rock, f_max=50.0)

# Load a surface Ricker wavelet and deconvolve to obtain consistent bedrock motion
_MOTIONS = motions_dir()
surface = TimeHistory.load(
    acc_file=str(_MOTIONS / "ricker_surface.acc"),
    time_file=str(_MOTIONS / "ricker_surface.time"),
    unit_in_g=True,
    gravity=9.81,
)

record = tf._deconvolve(time_history=surface)


# Create DRM pattern
# for creating the DRM pattern we need to provide the mesh (pyvista mesh),
# the properties of the DRM pattern (shape, time history, filename)
# the mesh is the final that we assembled above lest extraxted mesh from the assembled model
mesh = fm.assembler.get_mesh()

# now we can create the DRM pattern using the transfer function and the mesh
# since we our mesh is box shaped we can use the box shape for the DRM pattern
# to the date of this writing the DRM pattern is only supported for box shaped meshes
# the box shape mesh should be representation of the soil box should start at z=0 and extend to the depth  with negative z values
tf.createDRM(mesh, props={"shape":"box"}, time_history=record, filename="drmload.h5drm")

h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
# ===================================================================
# ===================================================================
fm.drm.addAbsorbingLayer(numLayers=2,
                        numPartitions=32,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type="Rayleigh",
                        )
fm.drm.set_pattern(h5pattern)
fm.drm.createDefaultProcess(finalTime=30, dT=0.01)

resultdirectoryname = "Results"
fm.process.insert_step(index=0, component=fm.actions.tcl(f"file mkdir {resultdirectoryname}"), description="making result directory")

fm.export_to_tcl(filename="model.tcl")

