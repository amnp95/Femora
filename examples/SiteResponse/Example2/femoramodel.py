import os

import femora as fm
from femora.utils.paths import motions_dir

os.chdir(os.path.dirname(__file__))



# create one damping for all the meshParts
uniformDamp = fm.damping.frequencyRayleigh(f1 = 2.76, f2 = 13.84, dampingFactor=0.03)
region = fm.region.elementRegion(damping=uniformDamp)

# defining the mesh parts
Xmin = 0.0 ;Xmax = 1.0
Ymin = 0.0 ;Ymax = 1.0
Zmin = -18.;Zmax = 0.0
dx   = 1.0; dy   = 1.0
Nx = int((Xmax - Xmin)/dx)
Ny = int((Ymax - Ymin)/dy)


layers_properties = [
    {"user_name": "Dense Ottawa1",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 2.6, "dz": 1.3}, 
    {"user_name": "Dense Ottawa2",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 2.4, "dz": 1.2},
    {"user_name": "Dense Ottawa3",  "G": 145.0e6, "gamma": 19.9,  "nu": 0.3, "thickness": 5.0, "dz": 1.0},
    {"user_name": "Loose Ottawa",   "G": 75.0e6,  "gamma": 19.1,  "nu": 0.3, "thickness": 6.0, "dz": 0.5}, 
    {"user_name": "Dense Montrey",  "G": 42.0e6,  "gamma": 19.8,  "nu": 0.3, "thickness": 2.0, "dz": 0.5} 
]


for layer in layers_properties:
    name = layer["user_name"]
    nu   = layer["nu"]
    rho  = layer["gamma"] * 1000 / 9.81        # Density in kg/m^3
    Vs   = (layer["G"] / rho) ** 0.5           # Shear wave velocity in m/s
    E    = 2 * layer["G"] * (1 + layer["nu"])  # Young's modulus in Pa
    E    = E / 1000.                           # Convert to kPa
    rho  = rho / 1000.                         # Convert to kg/m^3

    print(f"Layer: {name}, Vs: {Vs}")


    # Define the material
    fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name=name, E=E, nu=nu, rho=rho)

    # Define the element
    ele = fm.element.create_element(element_type="stdBrick", ndof=3, material=name, b1=0.0, b2=0.0, b3=-9.81 * rho)

    fm.meshPart.create_mesh_part(category="Volume mesh", mesh_part_type="Uniform Rectangular Grid", 
                                 user_name=name, element=ele, region=region,
                                **{
                                    'X Min': Xmin, 'X Max': Xmax,
                                    'Y Min': Ymin, 'Y Max': Ymax,
                                    'Z Min': Zmin, 'Z Max': Zmin + layer["thickness"],
                                    'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(layer["thickness"] / layer["dz"])
                                })
    Zmin += layer["thickness"]


# #  Create assembly Sections
fm.assembler.create_section(meshparts=[layer["user_name"] for layer in layers_properties], num_partitions=0)


# Assemble the mesh parts
fm.assembler.Assemble()

# Create a TimeSeries for the uniform excitation
timeseries = fm.timeSeries.create_time_series(series_type="path",
                                              filePath=str(motions_dir() / "FrequencySweep.acc"),
                                              fileTime=str(motions_dir() / "FrequencySweep.time"),
                                              factor= 9.81)

# Create a pattern for the uniform excitation
kobe = fm.pattern.create_pattern(pattern_type="uniformexcitation",dof=1, time_series=timeseries)


# boundary conditions
fm.constraint.mp.create_laminar_boundary(bounds=(-17.9,0),dofs=[1,2,3], direction=3)
fm.constraint.sp.fixMacroZmin(dofs=[1,1,1],tol=1e-3)


# Create a recorder for the whole model
mkdir = fm.actions.tcl("file mkdir Results")
recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="Results/result.vtkhdf",resp_types=["accel", "disp"], delta_t=0.001)

# gravity analysis
newmark_gamma = 0.6
newnark_beta = (newmark_gamma + 0.5)**2 / 4
system = fm.analysis.system.bandGeneral()
numberer = fm.analysis.numberer.rcm()
dampNewmark = fm.analysis.integrator.newmark(gamma=newmark_gamma, beta=newnark_beta)
gravity = fm.analysis.create_default_transient_analysis(username="gravity", 
                                                        dt=1.0, num_steps=30,
                                                        options={"system": system,
                                                                 "numberer": numberer,
                                                                 "integrator": dampNewmark})

# dynamic analysis
dynamic = fm.analysis.create_default_transient_analysis(username="dynamic", 
                                                        final_time=50.0, dt=0.001,
                                                        options={"system": system,
                                                                 "numberer": numberer})


reset = fm.actions.seTime(pseudo_time=0.0)

# Add the recorder and gravity analysis step to the process
fm.process.add_step(gravity,  description="Gravity Analysis Step")
fm.process.add_step(kobe,     description="Uniform Excitation (Kobe record)")
fm.process.add_step(mkdir,    description="Create Results Directory")
fm.process.add_step(recorder, description="Recorder of the whole model")
fm.process.add_step(reset,    description="Reset pseudo time")
fm.process.add_step(dynamic,  description="Dynamic Analysis Step")
fm.export_to_tcl("mesh.tcl")


# fm.gui()
