import femora as fm
import os
from math import sqrt
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ==========================================================
# Soil 
# ==========================================================

Gref = 100000.0  # Reference shear modulus in kPa
Bref = 300000.0  # Reference bulk modulus in kPa
Rho = 1.66  # Density in ton/m^3
Vs  = sqrt(Gref/Rho)  # Shear wave velocity in m/s
print(f"Shear wave velocity: {Vs} m/s")

soil_mat = fm.material.nd.pressure_depend_multi_yield(
    user_name="Soil",
    nd=3,
    rho=Rho,
    refShearModul=Gref,
    refBulkModul=Bref,
    frictionAng=37.0,
    peakShearStra=0.1,
    refPress=80.0,
    pressDependCoe=0.5,
    PTAng=20.0,
    contrac=0.05,
    dilat1=0.6,
    dilat2=3.0,
    liquefac1=5.0,
    liquefac2=0.003,
    liquefac3=1.0,
)
dx   = 1.0; dy = dx ; dz = dx
Xmin = -15.0; Xmax = 15.0; 
Ymin = -15.0; Ymax = 15.0;
Nx = int((Xmax - Xmin) / dx)
Ny = int((Ymax - Ymin) / dy)
soilele = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat,
    ndof=3,
    b1=0.0,
    b2=0.0,
    b3=-9.81*1.66,  # Gravity load in z-direction
)


Zmin = -28.0; Zmax = -14.3;
Nz = int((Zmax - Zmin) / (dz*1.75))
fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="soil_grid_1",
    element=soilele,
    region=None,
    **{
    "X Min": Xmin, "X Max": Xmax,
    "Y Min": Ymin, "Y Max": Ymax,
    "Z Min": Zmin, "Z Max": Zmax,
    "Nx Cells": Nx, "Ny Cells": Ny, "Nz Cells": Nz,
})

Zmin = -14.3; Zmax = 0.0;
Nz = int((Zmax - Zmin) / (dz*1.0))
fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="soil_grid_2",
    element=soilele,
    region=None,
    **{
    "X Min": Xmin, "X Max": Xmax,
    "Y Min": Ymin, "Y Max": Ymax,
    "Z Min": Zmin, "Z Max": Zmax,
    "Nx Cells": Nx, "Ny Cells": Ny, "Nz Cells": Nz,
})

# ==========================================================
# Pile
# ==========================================================
rotation_angle = 30
alum_fy = 1.3e5
alum_E = 6.89e7
alum_nu = 0.33
alum_G  = alum_E / (2 * (1 + alum_nu))  # Shear modulus
I       = 3.14* (0.4953**4 - 0.449072**4)/4.0
J       = 2.0 * I  # Polar moment of inertia
alumHardening_ratio = 0.000001
fm.material.uniaxial.steel01(
    user_name="Aluminum",
    Fy=alum_fy,
    E0=alum_E,
    b=alumHardening_ratio
)

pile_section = fm.section.fiber(
    user_name="pile_section",
    GJ=alum_G*J,
)
pile_section.add_circular_patch(
    material="Aluminum",
    int_rad=0.449072,
    ext_rad=0.4953,  
    num_subdiv_circ=48,
    num_subdiv_rad=4,
    y_center=0.0,
    z_center=0.0,
    start_ang=0.0,
    end_ang=360.0,
)


transf = fm.transformation.transformation3d(
    transf_type="PDelta",
    vecxz_x=-1,
    vecxz_y=0,
    vecxz_z=0,
)


pile_ele = fm.element.beam.disp(
    ndof=6,
    section=pile_section,
    transformation=transf,
    numIntgrPts=5,
)

pile1 = fm.mesh_part.line.single_line(
    user_name="pile1",
    element=pile_ele,
    region=None,
    x0 = +3.809,
    y0 = 0.0,
    z0 = -14.3,
    x1 = +3.809,
    y1 = 0.0,
    z1 = 5.6,
    number_of_lines = int(19.9/0.75),
    merge_points = True,
)
pile2 = fm.mesh_part.line.single_line(
    user_name="pile2",
    element=pile_ele,
    region=None,
    x0 = -3.809,
    y0 = 0.0,
    z0 = -14.3,
    x1 = -3.809,
    y1 = 0.0,
    z1 = 5.6,
    number_of_lines = int(19.9/0.75),
    merge_points = True,
)

# # ==========================================================
# # interface 
# # ==========================================================
fm.interface.beam_solid_interface(
    name = "pile_soil_interface1",
    beam_part = "pile1",
    solid_parts = None,  # No solid part specified
    radius = 1.181/2.0,  # Interface radius
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
    radius = 1.181/2.0,  # Interface radius
    n_peri = 8,
    n_long = 3,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
    write_connectivity = True,
    write_interface = True,
)


# ==========================================================
# bent
# ==========================================================
dx   = 1.0; dy = dx ; dz = dx
Xmin = -5.72; Xmax = 5.72; 
Ymin = -3.12; Ymax = 3.12;
Zmin = 3.9; Zmax = 3.9+3.38;
soil_mat = fm.material.nd.elastic_isotropic(
    user_name="bent_mat",
    E=alum_E, # Young's modulus in kPa
    nu=0.33, # Poisson's ratio
    rho = 2.7 # Density in ton/m^3
)
Nx = int((Xmax - Xmin) / dx)
Ny = int((Ymax - Ymin) / dy)
Nz = int((Zmax - Zmin) / dz)
soilele = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat,
    ndof=3,
    b1=0.0,
    b2=0.0,
    b3=-9.81*2.7,
)

bent = fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="bent_grid",
    element=soilele,
    region=None,
    **{
    "X Min": Xmin, "X Max": Xmax,
    "Y Min": Ymin, "Y Max": Ymax,
    "Z Min": Zmin, "Z Max": Zmax,
    "Nx Cells": Nx, "Ny Cells": Ny, "Nz Cells": Nz,
})

# ==========================================================
# Rotate the bent and piles
# ==========================================================

bent.transform.rotate_z(angle=rotation_angle)
pile1.transform.rotate_z(angle=rotation_angle)
pile2.transform.rotate_z(angle=rotation_angle)

# ==========================================================
# Assembly
# ==========================================================
# fm.assembler.create_section(
#     meshparts=["soil_grid_1", "soil_grid_2", "pile1", "pile2", "bent_grid"],
#     num_partitions=8,
#     partition_algorithm="kd-tree",
#     merge_points=True
# )
fm.assembler.create_section(
    meshparts=["pile1", "pile2", "bent_grid"],
    num_partitions=2,
    partition_algorithm="kd-tree",
    merge_points=True)

fm.assembler.create_section(
    meshparts=["soil_grid_1", "soil_grid_2"],
    num_partitions=8,
    partition_algorithm="kd-tree",
    merge_points=True)


fm.assembler.Assemble()

# ===================================================================
# creating the DRM pattern
# ===================================================================

# the soil layers is equivalent to the mesh parts defined above
# this is baisc format that the transfer function will use
soil = [
    {"h": 28,  "vs": Vs, "rho": Rho*1000, "damping": 0.03, "damping_type":"rayleigh", "f1": 0.02, "f2": 20.0},
]

# the rock layer is defined as a single layer with the properties below
# we just assume a hard rock layer with high shear wave velocity and density
# to represent the rigid base condition to create a high impedance contrast
rock = {"vs": 8000, "rho": 2000.0, "damping": 0.00}
                           
from femora.tools.transferFunction import TransferFunction, TimeHistory


# Create TimeHistory instance
# for the DRM pattern we need to provide a time history of the ground motion
# in this case we use a Ricker wavelet based ground motion that we calculate using deconvolution of ricker wavelet
# at the surface of the soil layers to compute the time history of the base motion
record = TimeHistory.load(acc_file="CFG2_ax_base_02g_avg.acc",
                            dt=0.0127,
                            unit_in_g=True,
                            gravity=9.81)
# import matplotlib.pyplot as plt
# plt.plot(record.time, record.acceleration)
# plt.xlabel("Time (s)")
# plt.ylabel("Acceleration (m/s^2)")
# plt.title("Ground Motion Time History")
# plt.grid()
# plt.show()
# exit(0)

# Create transfer function instance
# initialize the transfer function with the soil layers and rock properties
# the f_max is the maximum frequency of the transfer function
tf = TransferFunction(soil, rock, f_max=50.0)


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


# ==========================================================
# Create the Northridge record
# ==========================================================
# Create a TimeSeries for the uniform excitation
timeseries = fm.timeSeries.path(filePath = "CFG2_ax_base_02g_avg.acc",
                                dt = 0.0127,
                                factor = -9.81)

# Create a pattern for the uniform excitation
northridge = fm.pattern.create_pattern(pattern_type="uniformexcitation",dof=1, time_series=timeseries)


# boundary conditions
fm.constraint.mp.create_laminar_boundary(bounds=(-27.9,0),dofs=[1,2,3], direction=3)
fm.constraint.sp.fixMacroZmin(dofs=[1,1,1],tol=1e-3)


# Create a recorder for the whole model

fm.set_results_folder(f"Results_{rotation_angle}")
recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="result.vtkhdf",resp_types=["accel", "disp"], delta_t=0.02)

# gravity analysis
newmark_gamma = 0.6
newnark_beta = (newmark_gamma + 0.5)**2 / 4
elastic_update = fm.actions.updateMaterialStageToElastic()
dampNewmark = fm.analysis.integrator.newmark(gamma=newmark_gamma, beta=newnark_beta)
gravity_elastic = fm.analysis.create_default_transient_analysis(username="gravity_elastic", 
                                                        dt=1.0, num_steps=30,
                                                        options={"integrator": dampNewmark})

plastic_update = fm.actions.updateMaterialStageToPlastic()
gravity_plastic = fm.analysis.create_default_transient_analysis(username="gravity_plastic", 
                                                        dt=0.01, num_steps=100,
                                                        options={"integrator": dampNewmark})


# dynamic analysis
dynamic = fm.analysis.create_default_transient_analysis(username="dynamic", 
                                                        final_time=50.0, dt=0.0127,
                                                        )
embedded_recorder = fm.recorder.embedded_beam_solid_interface(
    interface=["pile_soil_interface1", "pile_soil_interface2"],
    dt=0.0127
    )

reset = fm.actions.seTime(pseudo_time=0.0)

# Add the recorder and gravity analysis step to the process
fm.process.add_step(elastic_update, description="Update Material Stage to Elastic")
fm.process.add_step(gravity_elastic,     description="Gravity Analysis Step")
fm.process.add_step(plastic_update, description="Update Material Stage to Plastic")
fm.process.add_step(gravity_plastic,     description="Gravity Analysis Step")
fm.process.add_step(northridge,  description="Uniform Excitation (Northridge record)")
fm.process.add_step(recorder,    description="Recorder of the whole model")
fm.process.add_step(embedded_recorder, description="Embedded Beam-Solid Interface Recorder")
fm.process.add_step(reset,       description="Reset pseudo time")
fm.process.add_step(dynamic,     description="Dynamic Analysis Step")

fm.export_to_tcl(filename="model.tcl")
fm.assembler.plot(show_edges=True, scalars="Core")
