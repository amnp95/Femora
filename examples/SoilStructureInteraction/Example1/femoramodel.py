import femora as fm
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==========================================================
# Soil 
# ==========================================================
Vs1 = 190.0  # Shear wave velocity in m/s
rho1 = 19.9 * 1000 / 9.81  # Density in kg/m^3
nu1 = 0.3  # Poisson's ratio
G1 = rho1 * Vs1 ** 2  # Shear modulus in Pa
E1 = 2 * G1 * (1 + nu1)  # Young's modulus in Pa

Vs2 = 240.0  # Shear wave velocity in m/s
rho2 = 19.1 * 1000 / 9.81  # Density in kg/m^3
nu2 = 0.3  # Poisson's ratio
G2 = rho2 * Vs2 ** 2  # Shear modulus in Pa
E2 = 2 * G2 * (1 + nu2)  # Young's modulus in Pa


# damping frequncy damping
f1 = 0.01  # in Hz
f2 =  100.0 # in Hz
damp = 0.03  # 3% damping
damping = fm.damping.frequencyRayleigh(f1=f1, f2=f2, dampingFactor=damp)
region = fm.region.elementRegion(damping=damping)

soil_mat1 = fm.material.nd.elastic_isotropic(
    user_name="soil_mat1",
    E=E1, # Young's modulus in Pa
    nu=nu1, # Poisson's ratio
    rho = rho1 # Density in kg/m^3
)

soil_mat2 = fm.material.nd.elastic_isotropic(
    user_name="soil_mat2",
    E=E2, # Young's modulus in Pa
    nu=nu2, # Poisson's ratio   
    rho = rho2 # Density in kg/m^3
)

Xmin = -8.0; Xmax = 8.0; 
Ymin = -3.0; Ymax = 3.0;
Zmin = -8.0; Zmax = 0.0;
Nx = 12;
Ny = 5;
Nz1 = 7;
Nz2 = 5;


soilele1 = fm.element.brick.std(
    name="soil_brick1",
    material=soil_mat1,
    ndof=3
)
soilele2 = fm.element.brick.std(
    name="soil_brick2",
    material=soil_mat2,
    ndof=3
)

ratio = 0.85
dimesions = [
    (Xmin, 0.0, Ymin, 0.0, Zmin, Zmax, ratio, ratio, ratio),
    (0.0, Xmax, Ymin, 0.0, Zmin, Zmax, 1./ratio, ratio, ratio),
    (Xmin, 0.0, 0.0, Ymax, Zmin, Zmax, ratio, 1./ratio, ratio),
    (0.0, Xmax, 0.0, Ymax, Zmin, Zmax, 1./ratio, 1./ratio, ratio),
]
soil = []

for i in range(4):
    xmin, xmax, ymin, ymax, zmin, zmax, xratio, yratio, zratio = dimesions[i]
    fm.mesh_part.volume.geometric_rectangular_grid(
        user_name="soil_grid_"+str(i),
        element=soilele2,
        region=region,
        x_min = xmin,
        x_max = xmax,
        y_min = ymin,
        y_max = ymax,
        z_min = zmin,
        z_max = zmax-2.0,
        nx = Nx,
        ny = Ny,
        nz = Nz1,
        x_ratio = xratio,
        y_ratio = yratio,
        z_ratio = zratio)
    fm.mesh_part.volume.geometric_rectangular_grid(
        user_name="soil_grid_"+str(i)+"_top",
        element=soilele1,
        region=None,
        x_min = xmin,
        x_max = xmax,
        y_min = ymin,
        y_max = ymax,
        z_min = zmax-2.0,
        z_max = zmax,
        nx = Nx,
        ny = Ny,
        nz = Nz2,
        x_ratio = xratio,
        y_ratio = yratio,
        z_ratio = 1.0)
    soil.append("soil_grid_"+str(i))
    soil.append("soil_grid_"+str(i)+"_top")



# ==========================================================
# Beam 
# ==========================================================
# transformation
transf = fm.transformation.transformation3d(
    transf_type="PDelta",
    vecxz_x=-1,
    vecxz_y=0,
    vecxz_z=0,
)

# Pile section definition
diameter = 1.  # pile diameter in meters
radius  = diameter / 2.0
pi      = 3.141593
Epile   = 1e10  # Young's modulus for the pile material in Pa
nu      = 0.3  # Poisson's ratio for the pile material
Gpile   = Epile / (2 * (1 + nu))  # Shear modulus
Area    = (diameter ** 2) * pi / 4.0  # Cross-sectional area
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
    user_name="pile",
    element=pile_ele,
    region=None,
    x0 = 0.0,
    y0 = 0.0,
    z0 = -5.0,
    x1 = 0.0,
    y1 = 0.0,
    z1 = 2.0,
    number_of_lines = 16,
    merge_points = True,
)
# # ==========================================================
# # interface 
# # ==========================================================
fm.interface.beam_solid_interface(
    name = "pile_soil_interface",
    beam_part = "pile",
    solid_parts = None,  # No solid part specified
    radius = radius,  # Interface radius
    n_peri = 8,
    n_long = 3,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
)
# ==========================================================
# Mass
# ==========================================================
# Add a lumped mass at the top of the pile in the x direction
lumpedMass = 25000.0 # Mass value in tons
fm.mass.meshpart.closest_point(
    meshpart_name="pile",
    xyz= (0.0, 0.0, 2.0),  # Point at the top of the pile
    mass_vec= (lumpedMass, 0.0, 0.0),  # Mass vector in the x direction
    combine="override",  # Override existing mass if any
)



# ==========================================================
# Assembly
# ==========================================================
mesh = soil + ["pile"]
fm.assembler.create_section(
    meshparts=mesh,
    num_partitions=0,
    partition_algorithm="kd-tree",
    merging_points=False,
)
fm.assembler.Assemble()


# ==========================================================
# create DRM
# ==========================================================
soil = [
    {"h": 2,  "vs": Vs1, "rho": rho1, "damping": damp, "damping_type":"rayleigh", "f1": f1, "f2": f2},
    {"h": 6,  "vs": Vs2, "rho": rho2, "damping": damp, "damping_type":"rayleigh", "f1": f1, "f2": f2},
    # {"h": 10, "vs": 300, "rho": 19.9*1000/9.81, "damping": damp, "damping_type":"rayleigh", "f1": 2.76, "f2": 13.84},
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
surface = TimeHistory.load(acc_file="ricker_surface.acc",
                            time_file="ricker_surface.time",
                            unit_in_g=True,
                            gravity=9.81)


# Create transfer function instance
# initialize the transfer function with the soil layers and rock properties
# the f_max is the maximum frequency of the transfer function
tf = TransferFunction(soil, rock, f_max=180.0)

incident = tf._deconvolve(time_history=surface)
incident.plot()



# Create DRM pattern
# for creating the DRM pattern we need to provide the mesh (pyvista mesh),
# the properties of the DRM pattern (shape, time history, filename)
# the mesh is the final that we assembled above lest extraxted mesh from the assembled model
mesh = fm.assembler.get_mesh()

# now we can create the DRM pattern using the transfer function and the mesh
# since we our mesh is box shaped we can use the box shape for the DRM pattern
# to the date of this writing the DRM pattern is only supported for box shaped meshes
# the box shape mesh should be representation of the soil box should start at z=0 and extend to the depth  with negative z values
tf.createDRM(mesh, props={"shape":"box"}, time_history=incident, filename="drmload.h5drm")

h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])

# ==========================================================
# PML Layer
# ==========================================================
ABSORBING_LAYER = "PML" ; # "", "PML", "Rayleigh"
# ABSORBING_LAYER = "Rayleigh"
# ABSORBING_LAYER = "Fixed"
if ABSORBING_LAYER in ["PML", "Rayleigh"]:
    fm.drm.addAbsorbingLayer(numLayers=2,
                        numPartitions=0,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=True,
                        type=ABSORBING_LAYER,
                        )

h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
fm.set_results_folder(f"Results_{ABSORBING_LAYER}")
fm.drm.set_pattern(h5pattern)
rcm = fm.analysis.numberer.rcm()
system = fm.analysis.system.bandGeneral()
fm.drm.createDefaultProcess(
    finalTime=6.0, 
    dT=0.001,
    vtkhdfrecorder_file=f"result",
    vtkhdfrecorder_resp_types=["disp", "vel", "accel"],
    vtkhdfrecorder_delta_t=0.005,
    GravityElasticOptions={
        "numberer": rcm,
        "system": system,
    }
    , 
    GravityPlasticOptions={
        "numberer": rcm,
        "system": system,
    }, 
    DynamicAnalysisOptions={
        "numberer": rcm,
        "system": system,
    }
)
fm.export_to_tcl(filename="model.tcl")
# fm.gui()
fm.assembler.plot(show_edges=True, scalars="MaterialTag")


