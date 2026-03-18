import femora as fm
import pyvista as pv
import numpy as np
import os

# change the direcotto the current file
os.chdir(os.path.dirname(os.path.abspath(__file__)))
fm.set_results_folder("Results")

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
# softMat_E = softMat_E / 1000.
# softMat_rho = softMat_rho / 1000.
# sofmat = fm.material.create_material("nDMaterial", "ElasticIsotropic",
#                                 user_name=f"softMaterial",
#                                 E=softMat_E, nu=softMat_nu, rho=softMat_rho)

sofmat = fm.material.nd.pressure_independ_multi_yield(
    user_name="softMaterial",
    nd=3,
    rho=softMat_rho,
    refShearModul=softMat_G,
    refBulkModul=softMat_K,
    cohesi=softMat_Cohesion,
    peakShearStra=softMat_peakStrain,
    updatewithsigmav0 = True
)

softele = fm.element.create_element(element_type="stdBrick",
                                ndof=3,
                                material=sofmat,
                                b1=0,
                                b2=0,
                                b3=0,
                                lumped=True)
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
                                    lumped=True)

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
fm.meshPart.create_mesh_part("General mesh", "External mesh",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        mesh=boxwithhole)

if BASIN:
    fm.meshPart.create_mesh_part("General mesh", "External mesh",
                                        user_name=f"basin{layer}",
                                        element=softele,
                                        region=softMat_reg,
                                        mesh=semihemisphere)
else:
    fm.meshPart.create_mesh_part("General mesh", "External mesh",
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
fm.meshPart.create_mesh_part("General mesh", "External mesh",
                        user_name=f"Layer{layer}",
                        element=ele,
                        region=reg,
                        mesh=boxwithhole)


if BASIN:
    fm.meshPart.create_mesh_part("General mesh", "External mesh",
                                            user_name=f"basin{layer}",
                                            element=softele,
                                            region=softMat_reg,
                                            mesh=semihemisphere)
else:
    fm.meshPart.create_mesh_part("General mesh", "External mesh",
                                            user_name=f"basin{layer}",
                                            element=ele,
                                            region=reg,
                                            mesh=semihemisphere)
# =========================================================
# plotting if you want to see the mesh
# =========================================================
PLOTTING = False
if PLOTTING:
    pl = pv.Plotter()
    pl.add_mesh(fm.meshPart.get_mesh_part("basin1").mesh, show_edges=True, color="red", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("basin2").mesh, show_edges=True, color="blue", opacity=1.0)
    pl.show_axes_all()
    pl.show_grid()
    # pl.export_html("basin.html")
    pl.show()

    pl = pv.Plotter()
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer1").mesh, show_edges=True, color="red", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer2").mesh, show_edges=True, color="blue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer3").mesh, show_edges=True, color="green", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer4").mesh, show_edges=True, color="yellow", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer5").mesh, show_edges=True, color="orange", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer6").mesh, show_edges=True, color="purple", opacity=1.0)
    pl.show_axes_all()
    pl.show_grid()
    # pl.export_html("layers.html")
    pl.show()

    pl = pv.Plotter()
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer1").mesh, show_edges=True, color="royalblue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer2").mesh, show_edges=True, color="royalblue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer3").mesh, show_edges=True, color="royalblue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer4").mesh, show_edges=True, color="royalblue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer5").mesh, show_edges=True, color="royalblue", opacity=1.0)      
    pl.add_mesh(fm.meshPart.get_mesh_part("Layer6").mesh, show_edges=True, color="royalblue", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("basin1").mesh, show_edges=True, color="red", opacity=1.0)
    pl.add_mesh(fm.meshPart.get_mesh_part("basin2").mesh, show_edges=True, color="red", opacity=1.0)
    pl.show_axes_all()
    pl.show_grid()
    # pl.export_html("layers_basin.html")
    pl.show()



# create a list of mesh parts
layers = ["Layer1", "Layer2", 
              "Layer3", "Layer4", 
              "Layer5", "Layer6", "basin1", "basin2"]

fm.assembler.create_section(layers, num_partitions=32)


fm.assembler.Assemble()
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
constraints Transformation
numberer ParallelRCM
system Mumps -ICNTL14 400 -ICNTL7 7
algorithm ModifiedNewton -factoronce
test EnergyIncr 0.001 20 2
integrator Newmark 0.6 0.30250000000000005
analysis Transient
set AnalysisStep 0
while { $AnalysisStep < 30} {
	if {$pid==0} {puts "$AnalysisStep/30"}
	set Ok [analyze 1 1.0]
	incr AnalysisStep 1
}
wipeAnalysis
""")


elasitc_state = fm.actions.updateMaterialStageToElastic()
plastic_state = fm.actions.updateMaterialStageToPlastic()

reset = fm.actions.seTime(pseudo_time=0.0)

dynamic_analysis = fm.actions.tcl("""
constraints Transformation
numberer ParallelPlain
system MPIDiagonal
algorithm Linear -factorOnce
integrator Explicitdifference
analysis Transient
initialize
while {[getTime] < 20.000000} {
	if {$pid == 0} {puts "Time : [getTime]/20.000000"}

	set Ok [analyze 1 0.0002]

}
wipeAnalysis
""")

fm.process.add_step(elasitc_state, description="Update material state to elastic")
fm.process.add_step(gravity_analysis,  description="Gravity Analysis Step (Elastic)")
fm.process.add_step(plastic_state, description="Update material state to plastic")
fm.process.add_step(gravity_analysis,  description="Gravity Analysis Step (Plastic)")
fm.process.add_step(h5pattern, description="DRM load pattern")
fm.process.add_step(recorder, description="VTK-HDF recorder")
fm.process.add_step(reset, description="Reset time to zero")
fm.process.add_step(dynamic_analysis, description="Transient analysis")                    


fm.export_to_tcl("model.tcl")



fm.assembler.plot(show_edges=True, scalars="Core")
