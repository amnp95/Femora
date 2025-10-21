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
Ymin = -8.0; Ymax = 8.0;
Zmin = -8.0; Zmax = 0.0;
Nx = 8
Ny = 8
Nz = 10
soilele = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat,
    ndof=3
)

ratio = 0.8
dimesions = [
    (Xmin, 0.0, Ymin, 0.0, Zmin, Zmax, ratio, ratio, ratio),
    (0.0, Xmax, Ymin, 0.0, Zmin, Zmax, 1./ratio, ratio, ratio),
    (Xmin, 0.0, 0.0, Ymax, Zmin, Zmax, ratio, 1./ratio, ratio),
    (0.0, Xmax, 0.0, Ymax, Zmin, Zmax, 1./ratio, 1./ratio, ratio),
]

for i in range(4):
    xmin, xmax, ymin, ymax, zmin, zmax, xratio, yratio, zratio = dimesions[i]
    fm.mesh_part.volume.geometric_rectangular_grid(
        user_name="soil_grid_"+str(i),
        element=soilele,
        region=None,
        x_min = xmin,
        x_max = xmax,
        y_min = ymin,
        y_max = ymax,
        z_min = zmin,
        z_max = zmax,
        nx = Nx,
        ny = Ny,
        nz = Nz,
        x_ratio = xratio,
        y_ratio = yratio,
        z_ratio = zratio)


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
diameter = 1.0  # pile diameter in meters
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


pile_head = (0.0, 0.0, 1.0)
pile_bottom = (0.0, 0.0, -5.0)

pml_region = fm.region.elementRegion()

fm.mesh_part.line.single_line(
    user_name="pile",
    element=pile_ele,
    region=pml_region,
    x0 = pile_bottom[0],
    y0 = pile_bottom[1],
    z0 = pile_bottom[2],
    x1 = pile_head[0],
    y1 = pile_head[1],
    z1 = pile_head[2],
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
    n_long = 4,
    penalty_param = 1.0e12,  # Penalty parameter
    g_penalty = True,  # Use geometric penalty
    write_connectivity=True,
    write_interface=True,
)
# ==========================================================
# Assembly
# ==========================================================
fm.assembler.create_section(
    meshparts=[f"soil_grid_{i}" for i in range(len(dimesions))],
    num_partitions=0,
    partition_algorithm="kd-tree",
    merging_points=True,
    tolerance=5e-2
)
fm.assembler.create_section(
    meshparts=["pile"],
    num_partitions=0,
    partition_algorithm="kd-tree",
    merging_points=False,
)
fm.assembler.Assemble(merge_points=True)
# fm.assembler.plot(show_edges=True, 
#                   render_lines_as_tubes=True, 
#                   sperate_beams_solid =True, 
#                   opacity_solids =0.5,
#                   color="royalblue",
#                   tube_radius=4.0)

# ==========================================================
# Boundary Conditions   
# ==========================================================
fm.constraint.sp.fixMacroXmax(dofs=[1,1,1], tol=1e-6)
fm.constraint.sp.fixMacroXmin(dofs=[1,1,1], tol=1e-6)
fm.constraint.sp.fixMacroYmax(dofs=[1,1,1], tol=1e-6)
fm.constraint.sp.fixMacroYmin(dofs=[1,1,1], tol=1e-6)
fm.constraint.sp.fixMacroZmin(dofs=[1,1,1], tol=1e-6)

# ==========================================================
# Static Load
# ==========================================================
load = 1.e6 # N
time_series = fm.timeSeries.linear(factor=1.0)
mask = fm.mask.nodes.near_point(point=pile_head, radius=1e-4)
pattern = fm.pattern.plain(time_series=time_series, factor=1.0)
pattern.add_load.node(node_mask=mask, values=[load, 0.0, 0.0])

# ==========================================================================
# recorder
# ==========================================================================
fm.set_results_folder("Results")
soil_recorder = fm.recorder.vtkhdf(file_base_name="result", resp_types = ["disp", "accel", "vel"])
interface_recorder = fm.recorder.embedded_beam_solid_interface(interface="pile_soil_interface",
                                                          resp_type= ["displacement", "localDisplacement", "axialDisp", "radialDisp", "tangentialDisp", "globalForce", "localForce", "axialForce", "radialForce", "tangentialForce", "solidForce", "beamForce", "beamLocalForce"])

pile_recorder = fm.recorder.beam_force(mesh_parts=["pile"], 
                                       force_type = "globalForce", 
                                       file_prefix="pile_force",
                                       include_time=True,
                                       delta_t = None,
                                       output_format="xml",
                                       )

# ==========================================================
# Analysis
# ==========================================================
analysis = """
set steps  100
set loadincr [expr 1.0 / $steps] 
constraints Penalty 1.e15 1.e15
numberer RCM
system BandGeneral
algorithm ModifiedNewton -factoronce
test NormDispIncr 0.001 5 2 2
integrator LoadControl $loadincr
analysis Static
for {set i 0} {$i < $steps} {incr i} {
    if {$pid == 0} {puts "step $i"}
    set ok [analyze 1]
    if {$ok != 0} {
        puts "analysis failed at step $i"
        break
    }
}
"""
analysis = fm.actions.tcl(command=analysis)


# ===========================================================================
# Simulation steps
# ===========================================================================
fm.process.add_step(component=pattern, description="Lateral loading")
fm.process.add_step(component=soil_recorder, description="Domain recorder")
fm.process.add_step(component=interface_recorder, description="Pile-soil interface recorder")
fm.process.add_step(component=pile_recorder, description="Pile recorder")
fm.process.add_step(component=analysis, description="Static analysis")

fm.export_to_tcl(filename="model.tcl")







