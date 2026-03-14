import femora as fm
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==========================================================
# Soil 
# ==========================================================
soil_mat = fm.material.nd.elastic_isotropic(
    user_name="soil_mat",
    E=2e8, # Young's modulus in Pa
    nu=0.4, # Poisson's ratio
    rho = 2100.0 # Density in kg/m^3
)
dx   = 0.5; dy = dx ; dz = dx
Xmin = -8.0; Xmax = 8.0; 
Ymin = -3.0; Ymax = 3.0;
Zmin = -8.0; Zmax = 0.0;
Nx = int((Xmax - Xmin) / dx)
Ny = int((Ymax - Ymin) / dy)
Nz = int((Zmax - Zmin) / dz)
soilele = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat,
    ndof=3
)

fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="soil_grid",
    element=soilele,
    region=None,
    **{
    "X Min": Xmin, "X Max": Xmax,
    "Y Min": Ymin, "Y Max": Ymax,
    "Z Min": Zmin, "Z Max": Zmax,
    "Nx Cells": Nx, "Ny Cells": Ny, "Nz Cells": Nz,
    })


# ==========================================================
# Beam 
# ==========================================================
# transformation
transf = fm.transformation.transformation3d(
    transf_type="PDelta",
    vecxz_x=0,
    vecxz_y=1,
    vecxz_z=0,
)

# Pile section definition
diameter = 1.5  # pile diameter in meters
radius  = diameter / 2.0
pi      = 3.141593
Epile   = 1e10  # Young's modulus for the pile material in Pa
nu      = 0.3  # Poisson's ratio for the pile material
Gpile   = Epile / (2 * (1 + nu))  # Shear modulus
Area    = (diameter ** 2) * pi / 2.0  # Cross-sectional area
Iy      = (diameter ** 4) * pi / 64.0  # Moment of inertia about y-axis
Iz      = (diameter ** 4) * pi / 64.0  # Moment of inertia about z-axis
Jpile   = (diameter ** 4) * pi / 32.0  # Polar moment of inertia

pile_sec = fm.section.elastic(
    user_name="pile_section",
    E=Epile,
    nu=nu,
    G=Gpile,
    A=Area,
    Iy=Iy,
    Iz=Iz,
    J=Jpile,
)

pile_ele = fm.element.beam.disp(
    ndof=6,
    section=pile_sec,
    transformation=transf,
    numIntgrPts=5,
)


fm.mesh_part.line.single_line(
    user_name="pile1",
    element=pile_ele,
    region=None,
    x0 = -2.5,
    y0 = 0.0,
    z0 = -5.0,
    x1 = -2.5,
    y1 = 0.0,
    z1 = 3.0,
    number_of_lines = 16,
    merge_points = True,
)


fm.mesh_part.line.single_line(
    user_name="pile2",
    element=pile_ele,
    region=None,
    x0 = 2.5,
    y0 = 0.0,
    z0 = -5.0,
    x1 = 2.5,
    y1 = 0.0,
    z1 = 3.0,
    number_of_lines = 16,
    merge_points = True,
)

fm.mesh_part.line.single_line(
    user_name="pile3",
    element=pile_ele,
    region=None,
    x0 = 0.0,
    y0 = 0.0,
    z0 = -5.0,
    x1 = 0.0,
    y1 = 0.0,
    z1 = 3.0,
    number_of_lines = 16,
    merge_points = True,
)


fm.mesh_part.line.single_line(
    user_name="beam1",
    element=pile_ele,
    region=None,
    x0 = -2.5,
    y0 = 0.0,
    z0 = 3.0,
    x1 = 0.0,
    y1 = 0.0,
    z1 = 3.0,
    number_of_lines = 16,
    merge_points = True,
)

fm.mesh_part.line.single_line(
    user_name="beam2",
    element=pile_ele,
    region=None,
    x0 = 2.5,
    y0 = 0.0,
    z0 = 3.0,
    x1 = 0.0,
    y1 = 0.0,
    z1 = 3.0,
    number_of_lines = 16,
    merge_points = True,
)
# # ==========================================================
# # interface 
# # ==========================================================
fm.interface.beam_solid_interface(
    name = "pile_soil_interface1",
    beam_part = "pile1",
    solid_parts = None,  # No solid part specified
    radius = radius,  # Interface radius
    n_peri = 8,
    n_long = 3,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
    write_connectivity = True,
    write_interface = True,  # Write interface file
)

fm.interface.beam_solid_interface(
    name = "pile_soil_interface2",
    beam_part = "pile2",
    solid_parts = None,  # No solid part specified
    radius = radius,  # Interface radius
    n_peri = 8,
    n_long = 3,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
    write_connectivity = True,
    write_interface = True,
)

# fm.interface.beam_solid_interface(
#     name = "pile_soil_interface3",
#     beam_part = "pile3",
#     solid_parts = None,  # No solid part specified
#     radius = radius,  # Interface radius
#     n_peri = 8,
#     n_long = 5,
#     penalty_param = 1.0e12,  # Penalty parameter
#     g_penalty = True,  # Use geometric penalty
# )
# ==========================================================
# Mass
# ==========================================================
# Add a lumped mass at center of the beam in the x direction
lumpedMass = 25000.0
fm.mass.meshpart.closest_point(
    meshpart_name="beam1",
    xyz= (0.0, 0.0, 3.0),  # Point at the top of the pile
    mass_vec= (lumpedMass, 0.0, 0.0),  # Mass vector in the x direction
    combine="override",  # Override existing mass if any
)



# ==========================================================
# Assembly
# ==========================================================
fm.assembler.create_section(
    meshparts=["soil_grid", "pile1", "pile2", "beam1", "beam2"],
    num_partitions=4,
    partition_algorithm="kd-tree",
    merge_points=True,
)
fm.assembler.Assemble()

# ==========================================================
# PML Layer
# ==========================================================
ABSORBING_LAYER = "PML" ; # "", "PML", "Rayleigh"
ABSORBING_LAYER = "Rayleigh"
ABSORBING_LAYER = "Fixed"

fm.set_results_folder(f"Results_{ABSORBING_LAYER}")


if ABSORBING_LAYER in ["PML", "Rayleigh"]:
    fm.drm.addAbsorbingLayer(numLayers=4,
                        numPartitions=4,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type=ABSORBING_LAYER,
                        )

h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='rickter.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
fm.drm.set_pattern(h5pattern)
fm.drm.createDefaultProcess(
    finalTime=4, 
    dT=0.001,
    vtkhdfrecorder_file=f"result",
    vtkhdfrecorder_resp_types=["disp", "vel", "accel"],
    vtkhdfrecorder_delta_t=0.005,
)

recorder = fm.recorder.embedded_beam_solid_interface(
    interface=["pile_soil_interface1", "pile_soil_interface2"],
    dt=0.005
    )
fm.process.insert_step(index=-2,
                       component= recorder,
                       description="Recorder for embedded beam-solid interface",)


fm.export_to_tcl(filename="model.tcl")
# fm.gui()
fm.assembler.plot(show_edges=True, scalars="Core")


