import femora as fm
import pyvista as pv
import numpy as np
import os

from femora.tools.buildings.steel_frame import FEMA_SAC_SteelFrame

# change the direcotto the current file
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# this example is the extension of the example2 which we have semihemispherical basin at the center in this model we are going to use External mesh as a part of the model
# Parameters for the semihemispherical hole
center_x, center_y, center_z = 0, 0, 70  # Center at the top surface
radius = 85.0  # Radius of the semihemisphere

# according to the center of the semihemisphere and it raduis the bounds
# of the mesh is as follows:
#       xmin = center_x - radius = - 85.0
#       xmax = center_x + radius = 85.0
#       ymin = center_y - radius = - 85.0
#       ymax = center_y + radius = 85.0
#       zmin = center_z - radius = - 15.0
#       zmax = center_z + radius = 40.0
# so according to the below values only the layer 1 and layer 2 are intersecting with the semihemisphere

fm.set_results_folder("Results")



model = fm.MeshMaker()
# # =========================================================
# # Define building
# # =========================================================
kip = 4.44822; # kip in kN
inch = 0.0254; # inch in m
lb = 0.453592; # lb in kg
ft = inch*12.0; # ft in m

# Define Building Material ============================
# Create a standard steel material (A992 Gr. 50)
# E = 29000 ksi, nu = 0.3, rho = included in section mass
E = 29000.0*kip/(inch*inch)
steel_density = 490.0*lb/(ft*ft*ft)
steel_density = steel_density / 1000.0
steel_mat = model.material.nd.elastic_isotropic("Steel_A992", E=E, nu=0.3, rho=steel_density)

# Define building floor masses ============================
floor_masses = [24.8544, 24.8544, 24.4296, 24.4296, 24.4296, 24.4296, 24.4296, 24.4296, 24.4296, 26.315999999999995] # in kips
for i in range(len(floor_masses)):
    floor_masses[i] = floor_masses[i] * kip / (ft)

# Define building ============================
building = FEMA_SAC_SteelFrame(
    name_prefix="nine_story_building",
    length_unit_system='m',
    origin=(-13.716, -13.716, -1.0),
    floor_masses=floor_masses
)

# Build the mesh_part =========================
building_mesh_part = building.build(model=model, material=steel_mat, material_density=steel_density)



# =================================================================
# Define foundation
# =================================================================
# Define foundation material ============================
# Create a standard concrete material (A992 Gr. 50)
E = 3000.0*kip/(inch*inch)
concrete_density = 150.0*lb/(ft*ft*ft)
concrete_density = concrete_density / 1000.0
concrete_mat = model.material.nd.elastic_isotropic("Concrete_A992", E=E, nu=0.3, rho=concrete_density)

x_min_foundation = -16
x_max_foundation = 16
y_min_foundation = -16
y_max_foundation = 16
z_min_foundation = -4
z_max_foundation = -1.0

foundation_ele_size = 3.0
nx_foundation = int((x_max_foundation-x_min_foundation)/foundation_ele_size)
ny_foundation = int((y_max_foundation-y_min_foundation)/foundation_ele_size)
nz_foundation = int((z_max_foundation-z_min_foundation)/foundation_ele_size)

fondation_ele = model.element.brick.std(ndof=3, material=concrete_mat, material_density=concrete_density, b1=0, b2=0, b3=0, lumped=False)

model.meshPart.volume.uniform_rectangular_grid(
    user_name="foundation",
    x_min=x_min_foundation,
    x_max=x_max_foundation,
    y_min=y_min_foundation,
    y_max=y_max_foundation,
    z_min=z_min_foundation,
    z_max=z_max_foundation,
    element=fondation_ele,
    nx=nx_foundation,
    ny=ny_foundation,
    nz=nz_foundation
)

# this example is the extension of the example2 which we have semihemispherical basin at the center in this model we are going to use External mesh as a part of the model
# Parameters for the semihemispherical hole
center_x, center_y, center_z = 0, 0, 70  # Center at the top surface
radius = 85.0  # Radius of the semihemisphere

# according to the center of the semihemisphere and it raduis the bounds
# of the mesh is as follows:
#       xmin = center_x - radius = - 85.0
#       xmax = center_x + radius = 85.0
#       ymin = center_y - radius = - 85.0
#       ymax = center_y + radius = 85.0
#       zmin = center_z - radius = - 15.0
#       zmax = center_z + radius = 40.0
# so according to the below values only the layer 1 and layer 2 are intersecting with the semihemisphere

# =========================================================
# Layering and initial information
# =========================================================

# layers [ layer, rho(m/ton), vp(m/s), vs(m/s), xi_s, xi_p, thickness(m) ]
layers = [
    [1, 2.1420500, 669.0500, 353.1000, 0.0296, 0.0148, 8],
    [2, 2.1462000, 785.2500, 414.4000, 0.0269, 0.0134, 8],
    [3, 2.1503500, 886.0500, 467.6000, 0.0249, 0.0125, 8],
    [4, 2.1544500, 976.4000, 515.3000, 0.0234, 0.0117, 8],
    [5, 2.1586000, 1059.0500, 558.9500, 0.0221, 0.0111, 8],
    [6, 2.1627500, 1135.6500, 599.4000, 0.0211, 0.0105, 8]
]

pi = 3.1415926
f1 = 15; # Hz
f2 = 3; # Hz
w1 = 2*pi*f1
w2 = 2*pi*f2

# mesh parameters
xmin = -64
xmax = 64
ymin = -64
ymax = 64
zmin = -48
zmax = zmin
dx = 4.0
dy = 4.0
dz = 4.0
Nx = int((xmax-xmin)/dx)
Ny = int((ymax-ymin)/dy)



# =========================================================
# Defining soft material for the basin
# =========================================================
# using Soft material in the basin
# keeping the ratio of vp/vs = 2.0
BASIN = True
softMat_vs = 150
softMat_vp = 300
softMat_xi_s = 0.03
softMat_xi_p = 0.01
softMat_rho  = 1.3
softMat_vs_vp_ratio   = (softMat_vp / softMat_vs) ** 2
softMat_nu            = (softMat_vs_vp_ratio - 2) / (2 * (softMat_vs_vp_ratio - 1))
softMat_E = 2 * softMat_rho * (softMat_vs ** 2) * (1 + softMat_nu)
softMat_G = softMat_E / (2 * (1 + softMat_nu))
softMat_K = softMat_E / (3 * (1 - 2 * softMat_nu))
softMat_Cohesion = 8.0
softMat_peakStrain = 0.1
sofmat = fm.material.create_material("nDMaterial", "ElasticIsotropic",
                                user_name=f"softMaterial",
                                E=softMat_E, nu=softMat_nu, rho=softMat_rho)

softele = fm.element.create_element(element_type="stdBrick",
                                ndof=3,
                                material=sofmat,
                                b1=0,
                                b2=0,
                                b3=0,
                                lumped=False)
softMat_damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=softMat_xi_s, f1=3, f2=15)
softMat_reg = fm.region.create_region("elementRegion", damping=None)

# =========================================================
# Defining a helpher function
# =========================================================
def helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness):
    vp_vs_ratio = (vp / vs) ** 2
    nu = (vp_vs_ratio - 2) / (2 * (vp_vs_ratio - 1))
    E = 2 * rho * (vs ** 2) * (1 + nu)
    # E = E / 1000.
    # rho = rho / 1000.
    mat = fm.material.create_material("nDMaterial", "ElasticIsotropic",
                                user_name=f"Layer{layer}",
                                E=E, nu=nu, rho=rho)
    ele = fm.element.create_element(element_type="stdBrick",
                                    ndof=3,
                                    material=mat,
                                    b1=0,
                                    b2=0,
                                    b3=0,
                                    lumped=False)

    damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=3, f2=15)
    reg = fm.region.create_region("elementRegion", damping=None)
    return ele, reg


# =========================================================
# layer 6 (bottom layer)
# =========================================================
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[5]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmax = zmin + thickness
Nz = int(thickness/dz)
fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        **{'X Min': xmin, 'X Max': xmax,
                            'Y Min': ymin, 'Y Max': ymax,
                            'Z Min': zmin, 'Z Max': zmax,
                            'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz})

# =========================================================
# layer 5
# =========================================================
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[4]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmin = zmax
zmax = zmin + thickness
Nz = int(thickness/dz)
fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        **{'X Min': xmin, 'X Max': xmax,
                            'Y Min': ymin, 'Y Max': ymax,
                            'Z Min': zmin, 'Z Max': zmax,
                            'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz})

# =========================================================
# layer 4
# =========================================================
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[3]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmin = zmax
zmax = zmin + thickness
Nz = int(thickness/dz)
fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        **{'X Min': xmin, 'X Max': xmax,
                            'Y Min': ymin, 'Y Max': ymax,
                            'Z Min': zmin, 'Z Max': zmax,
                            'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz})

# =========================================================
# layer 3
# =========================================================
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[2]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmin = zmax
zmax = zmin + thickness
Nz = int(thickness/dz)
fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        **{'X Min': xmin, 'X Max': xmax,
                            'Y Min': ymin, 'Y Max': ymax,
                            'Z Min': zmin, 'Z Max': zmax,
                            'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz})

# =========================================================
# layer 2
# =========================================================
# Cause layer 2 is intersecting with the semihemisphere we need to define it by hand
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[1]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmin = zmax
zmax = zmin + thickness
Nz = int(thickness/dz)

x = np.linspace(xmin, xmax, Nx+1)
y = np.linspace(ymin, ymax, Ny+1)
z = np.linspace(zmin, zmax, Nz+1)

x, y, z = np.meshgrid(x, y, z, indexing='ij')
mesh = pv.StructuredGrid(x, y, z).cast_to_unstructured_grid()

cellcenters = mesh.cell_centers()
distances = np.sqrt((cellcenters.points[:, 0] - center_x)**2 +
                    (cellcenters.points[:, 1] - center_y)**2 +
                    (cellcenters.points[:, 2] - center_z)**2)

mask = (distances <= radius)

semihemisphere = mesh.extract_cells(mask)
boxwithhole = mesh.extract_cells(~mask)

# now adding the semihemisphere part and the box part to the femora as
# external mesh part
model.meshPart.create_mesh_part("General mesh", "External mesh",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        mesh=boxwithhole)

# now extracting the foundation part from the boxwithhole
foundation_bounds = [x_min_foundation, x_max_foundation,
                    y_min_foundation, y_max_foundation,
                    z_min_foundation, z_max_foundation]

centers = semihemisphere.cell_centers()

mask = (centers.points[:, 0] >= foundation_bounds[0]) & \
    (centers.points[:, 0] <= foundation_bounds[1]) & \
    (centers.points[:, 1] >= foundation_bounds[2]) & \
    (centers.points[:, 1] <= foundation_bounds[3]) & \
    (centers.points[:, 2] >= foundation_bounds[4]) & \
    (centers.points[:, 2] <= foundation_bounds[5])

semihemisphere = semihemisphere.extract_cells(~mask)


if BASIN:
    model.meshPart.create_mesh_part("General mesh", "External mesh",
                                        user_name=f"basin{layer}",
                                        element=softele,
                                        region=softMat_reg,
                                    mesh=semihemisphere)

else:
    model.meshPart.create_mesh_part("General mesh", "External mesh",
                                        user_name=f"basin{layer}",
                                        element=ele,
                                        region=reg,
                                        mesh=semihemisphere)
# =========================================================
# layer 1
# =========================================================
layer, rho, vp, vs, xi_s, xi_p, thickness = layers[0]
ele, reg = helperfunction(layer, rho, vp, vs, xi_s, xi_p, thickness)
zmin = zmax
zmax = zmin + thickness
Nz = int(thickness/dz)

x = np.linspace(xmin, xmax, Nx+1)
y = np.linspace(ymin, ymax, Ny+1)
z = np.linspace(zmin, zmax, Nz+1)

x, y, z = np.meshgrid(x, y, z, indexing='ij')
mesh = pv.StructuredGrid(x, y, z).cast_to_unstructured_grid()

cellcenters = mesh.cell_centers()
distances = np.sqrt((cellcenters.points[:, 0] - center_x)**2 +
                    (cellcenters.points[:, 1] - center_y)**2 +
                    (cellcenters.points[:, 2] - center_z)**2)

mask = (distances <= radius)

semihemisphere = mesh.extract_cells(mask)
boxwithhole = mesh.extract_cells(~mask)

# now adding the semihemisphere part and the box part to the femora as
# external mesh part
model.meshPart.create_mesh_part("General mesh", "External mesh",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        mesh=boxwithhole)


# now extracting the foundation part from the semihemisphere
foundation_bounds = [x_min_foundation, x_max_foundation,
                    y_min_foundation, y_max_foundation,
                    z_min_foundation, 0.0]

centers = semihemisphere.cell_centers()

mask = (centers.points[:, 0] >= foundation_bounds[0]) & \
    (centers.points[:, 0] <= foundation_bounds[1]) & \
    (centers.points[:, 1] >= foundation_bounds[2]) & \
    (centers.points[:, 1] <= foundation_bounds[3]) & \
    (centers.points[:, 2] >= foundation_bounds[4]) & \
    (centers.points[:, 2] <= foundation_bounds[5])

semihemisphere = semihemisphere.extract_cells(~mask)


if BASIN:
    model.meshPart.create_mesh_part("General mesh", "External mesh",
                                            user_name=f"basin{layer}",
                                            element=softele,
                                            region=softMat_reg,
                                            mesh=semihemisphere)
else:
    model.meshPart.create_mesh_part("General mesh", "External mesh",
                                            user_name=f"basin{layer}",
                                            element=ele,
                                            region=reg,
                                            mesh=semihemisphere)

# ========================================================================
# Interfaces
# ========================================================================
model.interface.node_interface(name="building_foundation_interface",
                               constrained_node="nine_story_building",
                               retained_nodes=["foundation"],
                               K=1e6,
                               rot=True,
                               friction_interface=False)

model.interface.node_interface(name="foundation_soil_interface",
                               constrained_node="foundation",
                               K=1e8,
                               friction_interface=False),

# =========================================================
# Assembly
# =========================================================
# create a list of mesh parts
soil_layers = ["Layer1", "Layer2",
              "Layer3", "Layer4",
              "Layer5", "Layer6",
              "basin1", "basin2"]


foundation_parts = ["foundation"]
building_parts = ["nine_story_building"]



model.assembler.create_section(foundation_parts, num_partitions=1, merge_points=True, partition_algorithm="metis")
model.assembler.create_section(building_parts, num_partitions=4, merge_points=True, partition_algorithm="metis")
model.assembler.create_section(soil_layers, num_partitions=32, merge_points=True, partition_algorithm="metis")



model.assembler.Assemble(merge_points=False)
fm.drm.addAbsorbingLayer(numLayers=5,
                        numPartitions=64,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type="Rayleigh",
                        )


fm.constraint.sp.fixMacroXmax(dofs=[1,1,1,1,1,1,1,1,1], tol = 0.01)
fm.constraint.sp.fixMacroXmin(dofs=[1,1,1,1,1,1,1,1,1], tol = 0.01)
fm.constraint.sp.fixMacroYmax(dofs=[1,1,1,1,1,1,1,1,1], tol = 0.01)
fm.constraint.sp.fixMacroYmin(dofs=[1,1,1,1,1,1,1,1,1], tol = 0.01)
fm.constraint.sp.fixMacroZmin(dofs=[1,1,1,1,1,1,1,1,1], tol = 0.01)             
building.create_rigid_diaphragms(model)



h5pattern = fm.pattern.h5drm(filepath='drmload.h5drm',
                             factor=1.0,
                             crd_scale=1.0,
                             distance_tolerance=0.01,
                             do_coordinate_transformation=1,
                             transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                             origin=[0.0, 0.0, 0.0])




recorder = fm.recorder.vtkhdf(file_base_name="result",
                              resp_types=["disp", "vel", "accel"],
                              delta_t=0.01)

gravity_analysis = fm.actions.tcl("""
if {$pid == 0} {puts [string repeat "=" 120] }
if {$pid == 0} {puts "Starting analysis : Gravity-Elastic"}
if {$pid == 0} {puts [string repeat "=" 120] }
constraints Transformation
numberer ParallelRCM
system Mumps -ICNTL14 200 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test EnergyIncr 0.0001 10 5
integrator Newmark 0.5 0.25
analysis Transient
set AnalysisStep 0
while { $AnalysisStep < 10} {
        if {$pid==0} {puts "$AnalysisStep/10"}
        set Ok [analyze 1 0.01]
        incr AnalysisStep 1
}
wipeAnalysis
""")

reset = fm.actions.seTime(pseudo_time=0.0)

dynamic_analysis = fm.actions.tcl("""
if {$pid == 0} {puts [string repeat "=" 120] }
if {$pid == 0} {puts "Starting analysis : DynamicAnalysis"}
if {$pid == 0} {puts [string repeat "=" 120] }
constraints Transformation
numberer ParallelRCM
system Mumps -ICNTL14 200 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test EnergyIncr 0.0001 10 5
integrator Newmark 0.5 0.25
analysis Transient
while {[getTime] < 25.000000} {
        if {$pid == 0} {puts "Time : [getTime]"}

        set Ok [analyze 1 0.01]

}
wipeAnalysis
""")

fm.process.add_step(gravity_analysis,  description="Gravity Analysis Step (Elastic)")
fm.process.add_step(h5pattern, description="DRM load pattern")
fm.process.add_step(recorder, description="VTK-HDF recorder")
fm.process.add_step(reset, description="Reset time to zero")
fm.process.add_step(dynamic_analysis, description="Transient analysis")                    


fm.export_to_tcl("model.tcl")
fm.assembler.plot(show_edges=True, scalars="Core")
