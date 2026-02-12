import femora as fm
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))



# Get rotation angle from command line argument
if len(sys.argv) != 2:
    print("Usage: python femoramodel.py <rotation_angle>")
    print("Example: python femoramodel.py 30")
    sys.exit(1)

try:
    rotation_angle = float(sys.argv[1])
    print(f"Using rotation angle: {rotation_angle} degrees")
except ValueError:
    print("Error: Rotation angle must be a number")
    print("Example: python femoramodel.py 30")
    sys.exit(1)


# ==========================================================
# Soil 
# ==========================================================
soil_mat = fm.material.nd.pressure_depend_multi_yield(
    user_name="Soil",
    nd=3,
    rho=1.66,
    refShearModul=100000.0,
    refBulkModul=300000.0,
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




def GK_to_E_nu(G, K):
    E = (9 * K * G) / (3 * K + G)
    nu = (3 * K - 2 * G) / (2 * (3 * K + G))
    return E, nu

refShearModul = 100000.0
refBulkModul  = 300000.0

E, nu = GK_to_E_nu(refShearModul, refBulkModul)
print(f"E = {E}")
print(f"nu = {nu}")
soil_mat_Elastic = fm.material.nd.elastic_isotropic(E=E, nu=nu, rho=1.66)







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


soilele_elastic = fm.element.brick.std(
    name="soil_brick",
    material=soil_mat_Elastic,
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

Zmin = -14.3; Zmax = -1;
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



Zmin = -1; Zmax = 0.0;
Nz = int((Zmax - Zmin) / (dz*1.0))
fm.mesh_part.volume.uniform_rectangular_grid(
    user_name="soil_crust",
    element=soilele_elastic,
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
#rotation_angle = 30
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

# pile_section = fm.section.elastic(
#     user_name="pile_section",
#     E=alum_E,
#     A=3.14*(0.4953**2 - 0.449072**2),
#     Iz=I,
#     Iy=I,
#     G=alum_G,
#     J=J,
# )


transf = fm.transformation.transformation3d(
    transf_type="Linear",
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
    rho = 2.7*1.0 # Density in ton/m^3
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
# Assembly
# ==========================================================
# fm.assembler.create_section(
#     meshparts=["soil_grid_1", "soil_grid_2", "pile1", "pile2", "bent_grid"],
#     num_partitions=8,
#     partition_algorithm="kd-tree",
#     merging_points=True
# )
fm.assembler.create_section(
    meshparts=["pile1", "pile2", "bent_grid"],
    num_partitions=2,
    partition_algorithm="kd-tree",
    merging_points=True)

fm.assembler.create_section(
    meshparts=["soil_grid_1", "soil_grid_2", "soil_crust"],
    num_partitions=4,
    partition_algorithm="kd-tree",
    merging_points=True)
fm.assembler.Assemble(merge_points=True)

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
recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="result.vtkhdf",resp_types=["disp", "vel", "accel", "stress3D6", "strain3D6"], delta_t=0.02)

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





#beam_recorder = 

import numpy as np
mesh =fm.assembler.get_mesh()
# pile1_points = mesh.point_data["MeshPartTag_pointdata"] == pile1.tag
# pile2_points = mesh.point_data["MeshPartTag_pointdata"] == pile2.tag
# pile1_points = np.where(pile1_points)[0] + 1
# pile2_points = np.where(pile2_points)[0] + 1
pile1_elements = mesh.cell_data["MeshPartTag_celldata"] == pile1.tag
pile2_elements = mesh.cell_data["MeshPartTag_celldata"] == pile2.tag
pile1_elements = np.where(pile1_elements)[0] + 1
pile2_elements = np.where(pile2_elements)[0] + 1


beam_recorder = fm.actions.tcl(f"""
recorder Element -xml Results_{rotation_angle}/pile1_recorder$pid.xml -time  -dT 0.02 -ele {" ".join(map(str, pile1_elements))} force
recorder Element -xml Results_{rotation_angle}/pile2_recorder$pid.xml -time  -dT 0.02 -ele {" ".join(map(str, pile2_elements))} force
""")











# dynamic analysis
#test = fm.analysis.test.normdispincr(tol=5.0e-2, max_iter=5, print_flag=2)
#dynamic = fm.analysis.create_default_transient_analysis(username="dynamic", 
#                                                        final_time=50.0, dt=0.0127,
#                                                        options={"test": test}
#                                                        )

dynamic = fm.actions.tcl("""

constraints Penalty 1.e12 1.e12
numberer ParallelRCM
system Mumps -ICNTL14 400 -ICNTL7 7
algorithm ModifiedNewton -factoronce
#test FixedNumIter 3 2
test NormDispIncr 0.001 5 2 2
integrator Newmark 0.5 0.25
analysis Transient 
set dt 0.01
set numSublevels 3 
set numSubSteps 2

# Adaptive single global step with recursive subdivision up to numSublevels
# Usage: doAdaptiveStep <dt> <level> <maxLevels> <numSubSteps>
proc doAdaptiveStep {dt level maxLevels numSubSteps} {
    # Try one step
    set ok [analyze 1 $dt]
    if {$ok >= 0} {return $ok}
    # If failed and we can still subdivide
    if {$level >= $maxLevels} {return $ok}
    if {$numSubSteps < 2} {return $ok} ;# nothing to subdivide
    set subDt [expr {$dt / double($numSubSteps)}]
    for {set i 0} {$i < $numSubSteps} {incr i} {
        set ok [doAdaptiveStep $subDt [expr {$level+1}] $maxLevels $numSubSteps]
        if {$ok < 0} {return $ok}
    }
    return 0
}

set endTime 50.0
set baseDt $dt
set currentTest "Disp"

while {[getTime] < $endTime} {
    if {$pid == 0} {puts "Time : [getTime]"}
    # Prevent overshooting end time
    set remain [expr {$endTime - [getTime]}]
    if {$remain < $baseDt} {set dt $remain} else {set dt $baseDt}

    set ok [doAdaptiveStep $dt 1 $numSublevels $numSubSteps]
 
    if {$ok < 0} {
        if {$pid == 0} {puts "losening the criteria"}
    
        test NormDispIncr 0.01 5 2 2
        set currentTest "DispLoosen"
        set ok [doAdaptiveStep $dt 1 $numSublevels $numSubSteps]
    }


   if {$ok < 0} {
        if {$pid == 0} {puts "changing to fixed iterations"}

        test FixedNumIter 3  2
        set currentTest "Fixed"
        set ok [doAdaptiveStep $dt 1 $numSublevels $numSubSteps]
    }
    if {$currentTest != "Disp"} {

        if {$pid == 0} {puts "reverting to the disp test"}

        test NormDispIncr 0.001 5 2 2
        set currentTest "Disp"
    }

     if {$ok < 0} {
        if {$pid == 0} {puts "**********failed analysis*********"}
        break
    }
        
}

wipeAnalysis     

        """)







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
fm.process.add_step(beam_recorder, description="Beam Recorder")
fm.process.add_step(embedded_recorder, description="Embedded Beam-Solid Interface Recorder")
fm.process.add_step(reset,       description="Reset pseudo time")
fm.process.add_step(dynamic,     description="Dynamic Analysis Step")

# fm.export_to_tcl(filename=f"model_{int(rotation_angle)}.tcl")
#print(fm.assembler.get_mesh().cell_data.keys())
fm.assembler.plot(show_edges=True, scalars="ElementTag")
