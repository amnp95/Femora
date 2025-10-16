# %%
import femora as fm
Vs = 300 # m/s
nu = 0.3
rho = 2000 # kg/m3
boundaryConditionType = "Extended" ; # "PML" or "Fixed", "Extended"
# boundaryConditionType = "Fixed" ; # "PML" or "Fixed", "Extended"
# boundaryConditionType = "PML" ; # "PML" or "Fixed", "Extended"

# calculate elastic parameters
G = rho*Vs**2
E = 2*G*(1+nu)

# convert to MPa
E /= 1000.
rho /= 1000.


mat = fm.material.nd.elastic_isotropic(user_name="elastic_material",
                                  E=E,
                                  nu=nu,
                                  rho=rho)

brick = fm.element.brick.std(ndof=3,
                     material=mat,
                     b1 = 0.0,
                     b2 = 0.0,
                     b3 = 0.0
                     )

dx = 3.0  # element size in x direction
dy = dx  # element size in y direction
dz = dx  # element size in z direction


# maximum delta x for the Ricker wavelet
max_interested_frequency = 10.0  # Hz
velocity                 = Vs  # m/s
wavelength               = velocity/max_interested_frequency
point_per_wavelength     = 10.0
max_dx                   = wavelength/point_per_wavelength
if dx > max_dx:
    print("Warning: The element size is too large for the desired frequency content.")
    print("The maximum element size should be: ", max_dx)
    print("Current element size is: ", dx)
    exit()


if boundaryConditionType == "Extended":
    additional_length = 510.0
else:
    additional_length = 90.0


Xmin = - additional_length
Xmax =   additional_length
Ymin = - additional_length
Ymax =   additional_length
Zmin = - additional_length
Zmax = 0.0
eps = 1e-6
Nx = int(((Xmax - Xmin) + eps)/dx)
Ny = int(((Ymax - Ymin) + eps)/dy)
Nz = int(((Zmax - Zmin) + eps)/dz)

fm.mesh_part.volume.uniform_rectangular_grid(user_name="inner_meshpart",
                                             element = brick,
                                             region = fm.region.get_region(0),
                                             x_min = Xmin, x_max = Xmax,
                                             y_min = Ymin, y_max = Ymax,
                                             z_min = Zmin, z_max = Zmax,
                                             nx = Nx, ny = Ny, nz = Nz
                                             )


# number of elements in the PML
n_elements_pml = 12
thickness_pml = n_elements_pml * dx



Damping = fm.damping.frequencyRayleigh(f1=0.2, f2=20.0, dampingFactor=0.95)
PMLRegion = fm.region.elementRegion(damping=Damping)


# right side PML 
Xref     = Xmax
Yref     = 0.0
Zref     = 0.0

normal_x = 1.0
normal_y = 0.0
normal_z = 0.0





right_absorbing_layer = fm.element.brick.pml3d(ndof=9,
                                               material=mat,
                                               PML_Thickness = thickness_pml,
                                               meshType="General",
                                               meshTypeParameters = [Xref, Yref, Zref, normal_x, normal_y, normal_z],
                                               )

fm.mesh_part.volume.uniform_rectangular_grid(user_name="right_pml_meshpart",
                                             element = right_absorbing_layer,
                                             region = PMLRegion,
                                             x_min = Xmax, 
                                             x_max = Xmax + thickness_pml,
                                             y_min = Ymin, 
                                             y_max = Ymax,
                                             z_min = Zmin,
                                             z_max = Zmax,
                                             nx = n_elements_pml, 
                                             ny = Ny,
                                             nz = Nz
                                                )

# right-bottom corner PML
Xref     = Xmax
Yref     = Ymin
Zref     = Zmin
normal_x = 1.0
normal_y = 0.0
normal_z = -1.0


# normalized normal vector
norm = (normal_x**2 + normal_y**2 + normal_z**2)**0.5
normal_x /= norm
normal_y /= norm
normal_z /= norm

right_corner_absorbing_layer = fm.element.brick.pml3d(ndof=9,
                                                  material=mat,
                                                  PML_Thickness = thickness_pml,
                                                  meshType="General",
                                                  meshTypeParameters = [
                                                      Xref, Yref, Zref, normal_x, normal_y, normal_z],
                                                    )
fm.mesh_part.volume.uniform_rectangular_grid(user_name="right_bottom_pml_meshpart",
                                             element = right_corner_absorbing_layer,
                                                region = PMLRegion,
                                                x_min = Xmax, 
                                                x_max = Xmax + thickness_pml,
                                                y_min = Ymin ,
                                                y_max = Ymax,
                                                z_min = Zmin - thickness_pml,
                                                z_max = Zmin,
                                                nx = n_elements_pml,
                                                ny = Ny,
                                                nz = n_elements_pml
                                                )



# bottom side PML
Xref     = 0.0
Yref     = 0.0
Zref     = Zmin
normal_x = 0.0
normal_y = 0.0
normal_z = -1.0

bottom_absorbing_layer = fm.element.brick.pml3d(ndof=9,
                                               material=mat,
                                                  PML_Thickness = thickness_pml,
                                                    meshType="General",
                                                    meshTypeParameters = [
                                                        Xref, Yref, Zref, normal_x, normal_y, normal_z],
                                                )

fm.mesh_part.volume.uniform_rectangular_grid(user_name="bottom_pml_meshpart",
                                             element = bottom_absorbing_layer,
                                                region = PMLRegion,
                                                x_min = Xmin, 
                                                x_max = Xmax,
                                                y_min = Ymin ,
                                                y_max = Ymax,
                                                z_min = Zmin - thickness_pml,
                                                z_max = Zmin,
                                                nx = Nx,
                                                ny = Ny,
                                                nz = n_elements_pml
                                                )


# left side PML
Xref     = Xmin
Yref     = 0.0
Zref     = 0.0
normal_x = -1.0
normal_y = 0.0
normal_z = 0.0

left_absorbing_layer = fm.element.brick.pml3d(ndof=9,
                                              material=mat,
                                              PML_Thickness = thickness_pml,
                                              meshType="General",
                                              meshTypeParameters = [
                                                Xref, Yref, Zref, 
                                                normal_x, normal_y, normal_z],
                                            )

fm.mesh_part.volume.uniform_rectangular_grid(user_name="left_pml_meshpart",
                                             element = left_absorbing_layer,
                                                region = PMLRegion,
                                                x_min = Xmin - thickness_pml, 
                                                x_max = Xmin,
                                                y_min = Ymin ,
                                                y_max = Ymax,
                                                z_min = Zmin,
                                                z_max = Zmax,
                                                nx = n_elements_pml,
                                                ny = Ny,
                                                nz = Nz
                                                )


# left-bottom corner PML
Xref     = Xmin
Yref     = 0.0
Zref     = Zmin

normal_x = -1.0
normal_y = 0.0
normal_z = -1.0
# normalized normal vector
norm = (normal_x**2 + normal_y**2 + normal_z**2)**0.5
normal_x /= norm
normal_y /= norm
normal_z /= norm

left_corner_absorbing_layer = fm.element.brick.pml3d(ndof=9,
                                                   material=mat,
                                                    PML_Thickness = thickness_pml,
                                                    meshType="General",
                                                    meshTypeParameters = [
                                                    Xref, Yref, Zref, normal_x, normal_y, normal_z],
                                                )

fm.mesh_part.volume.uniform_rectangular_grid(user_name="left_bottom_pml_meshpart",
                                             element = left_corner_absorbing_layer,
                                                region = PMLRegion,
                                                x_min = Xmin - thickness_pml, 
                                                x_max = Xmin,
                                                y_min = Ymin ,
                                                y_max = Ymax,
                                                z_min = Zmin - thickness_pml,
                                                z_max = Zmin,
                                                nx = n_elements_pml,
                                                ny = Ny,
                                                nz = n_elements_pml
                                                )

# %%
# assembling the mesh
fm.assembler.clear_assembly_sections()
fm.assembler.create_section(meshparts=["inner_meshpart"], num_partitions= 2, merging_points=True)
if boundaryConditionType == "PML":
    # fm.assembler.create_section(meshparts=["right_pml_meshpart", 
    #                                 "right_bottom_pml_meshpart", 
    #                                 "bottom_pml_meshpart",
    #                                     "left_pml_meshpart",
    #                                     "left_bottom_pml_meshpart",
    #                                 ], num_partitions= 2, merging_points=True)
    fm.assembler.create_section(meshparts=["right_pml_meshpart", "right_bottom_pml_meshpart"], num_partitions= 2, merging_points=True)
    fm.assembler.create_section(meshparts=["bottom_pml_meshpart"], num_partitions= 2, merging_points=True)
    fm.assembler.create_section(meshparts=["left_pml_meshpart", "left_bottom_pml_meshpart"], num_partitions= 2, merging_points=True)
    
fm.assembler.Assemble(merge_points=False)
# %%
# ==========================================================================
# boundary conditions
# =========================================================================
# define boundary conditions
fm.constraint.sp.fixMacroYmin(dofs=[0,1,0,0,0,0,0,0,0], tol=1e-3)
fm.constraint.sp.fixMacroYmax(dofs=[0,1,0,0,0,0,0,0,0], tol=1e-3)
fm.constraint.sp.fixMacroXmin(dofs=[1,1,1,1,1,1,1,1,1], tol=1e-3)
fm.constraint.sp.fixMacroXmax(dofs=[1,1,1,1,1,1,1,1,1], tol=1e-3)
fm.constraint.sp.fixMacroZmin(dofs=[1,1,1,1,1,1,1,1,1], tol=1e-3)

# ==========================================================================
# mp constraints
# ==========================================================================
if boundaryConditionType == "PML":
    fm.constraint.mp.create_equal_dof_between_meshparts(meshpart_master="inner_meshpart",
                                                        meshpart_slave="right_pml_meshpart",
                                                        dofs=[1,2,3])
    fm.constraint.mp.create_equal_dof_between_meshparts(meshpart_master="inner_meshpart",
                                                        meshpart_slave="right_bottom_pml_meshpart",
                                                        dofs=[1,2,3])
    fm.constraint.mp.create_equal_dof_between_meshparts(meshpart_master="inner_meshpart",
                                                        meshpart_slave="bottom_pml_meshpart",
                                                        dofs=[1,2,3])
    fm.constraint.mp.create_equal_dof_between_meshparts(meshpart_master="inner_meshpart",
                                                        meshpart_slave="left_pml_meshpart",
                                                        dofs=[1,2,3])
    fm.constraint.mp.create_equal_dof_between_meshparts(meshpart_master="inner_meshpart",
                                                        meshpart_slave="left_bottom_pml_meshpart",
                                                        dofs=[1,2,3])
    



# ==========================================================================
# loading
# ==========================================================================

# time series for the Ricker wavelet
time_series = fm.timeSeries.path(filePath="LoadForce.txt", fileTime="LoadTime.txt")

# apply load at the center of the model

# create a mask for the nodes at the center of the model
mask = fm.mask.nodes.along_line(point1=[0.0, -dy/2, 0.0], 
                               point2=[0.0, dy/2, 0.0], 
                               radius=1e-1)

# apply the load
pattern = fm.pattern.plain(time_series=time_series, factor=1.0)
pattern.add_load.node(node_mask=mask, values=[0.0, 0.0, -1.0])


# ==========================================================================
# recorder
# ==========================================================================
fm.set_results_folder(boundaryConditionType)
recorder = fm.recorder.vtkhdf(file_base_name="result", resp_types = ["disp", "accel"])

# ==========================================================================
# analysis 
# ==========================================================================
analysis = """
domainChange
constraints Penalty 1.0e12 1.0e12;
numberer    ParallelRCM;
system      Mumps -ICNTL14 400;
test        EnergyIncr 1.0e-4 10;
integrator  Newmark 0.5 0.25;
algorithm   Linear -factorOnce
analysis    Transient;
set dt 0.002

set steps [expr 4./$dt]
for {set i 0} {$i < $steps} {incr i} {
    
    if {$pid == 0} {puts "step $i"}
    
    set ok [analyze 1 $dt]
    if {$ok != 0} {
        puts "analysis failed at step $i"
        break
    }
}

"""
analysis = fm.actions.tcl(command=analysis)


# ===========================================================================
# simulation steps
# ===========================================================================
fm.process.add_step(component=pattern, description="Ricker wavelet loading")
fm.process.add_step(component=recorder, description="VTK recorder")
fm.process.add_step(component=analysis, description="Transient analysis")


# print mesh infomaton  
mk = fm.MeshMaker()
mk.print_info()

# fm.gui()
fm.assembler.plot(scalars="Core")
# export the model to a tcl file
fm.export_to_tcl("model.tcl")






