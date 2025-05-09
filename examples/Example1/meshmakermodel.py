import os
import femora as fm
os.chdir(os.path.dirname(__file__))



# defining the materials
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Dense Ottawa", E=2.0e7, nu=0.3, rho=2.02)
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Loose Ottawa", E=2.0e7, nu=0.3, rho=1.94)
fm.material.create_material(material_category="nDMaterial", material_type="ElasticIsotropic", user_name="Dense Montrey", E=2.0e7, nu=0.3, rho=2.018)

DensOttawaEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Dense Ottawa", b1=0.0, b2=0.0, b3=-9.81 * 2.02)
LooseOttawaEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Loose Ottawa", b1=0.0, b2=0.0, b3=-9.81 * 1.94)
MontreyEle = fm.element.create_element(element_type="stdBrick", ndof=3, material="Dense Montrey", b1=0.0, b2=0.0, b3=-9.81 * 2.018)

# defining the mesh parts
Xmin = -10.0
Xmax = 10.
Ymin = -10.0
Ymax = 10.
Zmin = -18.0
thick1 = 2.6
thick2 = 2.4
thick3 = 5.0 
thick4 = 6.0
thick5 = 2.0
dx = 1.0
dy = 1.0
dz1 = 1.3
dz2 = 1.2
dz3 = 1.0
dz4 = 0.5
dz5 = 0.5
Nx = int((Xmax - Xmin)/dx)
Ny = int((Ymax - Ymin)/dy)

fm.meshPart.create_mesh_part(category="Volume mesh",
                             mesh_part_type="Uniform Rectangular Grid",
                             user_name="DensOttawa1",
                             element=DensOttawaEle,
                             region=fm.region.get_region(0),
                             **{'X Min': Xmin, 'X Max': Xmax, 
                                'Y Min': Ymin, 'Y Max': Ymax, 
                                'Z Min': Zmin, 'Z Max': Zmin + thick1, 
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick1/dz1)})
Zmin += thick1
fm.meshPart.create_mesh_part(category="Volume mesh",
                             mesh_part_type="Uniform Rectangular Grid",
                             user_name="DensOttawa2",
                            element=DensOttawaEle,
                            region=fm.region.get_region(0),
                            **{'X Min': Xmin, 'X Max': Xmax, 
                                'Y Min': Ymin, 'Y Max': Ymax, 
                                'Z Min': Zmin, 'Z Max': Zmin + thick2, 
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick2/dz2)})

Zmin += thick2
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="DensOttawa3",
                                element=DensOttawaEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick3,
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick3/dz3)})
Zmin += thick3
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="LooseOttawa",
                                element=LooseOttawaEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick4,
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick4/dz4)})
Zmin += thick4
fm.meshPart.create_mesh_part(category="Volume mesh",
                                mesh_part_type="Uniform Rectangular Grid",
                                user_name="Montrey",
                                element=MontreyEle,
                                region=fm.region.get_region(0),
                                **{'X Min': Xmin, 'X Max': Xmax,
                                'Y Min': Ymin, 'Y Max': Ymax,
                                'Z Min': Zmin, 'Z Max': Zmin + thick5,  
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': int(thick5/dz5)})



#  Create assembly Sections
fm.assembler.create_section(meshparts=["DensOttawa1", "DensOttawa2", "DensOttawa3"], num_partitions=2)
fm.assembler.create_section(["LooseOttawa"], num_partitions=2)
fm.assembler.create_section(["Montrey"], num_partitions=2)

# Assemble the mesh parts
fm.assembler.Assemble()


# Create a TimeSeries for the uniform excitation
timeseries = fm.timeSeries.create_time_series(series_type="path",filePath="kobe.acc",fileTime="kobe.time")

# Create a pattern for the uniform excitation
kobe = fm.pattern.create_pattern(pattern_type="uniformexcitation",dof=1, time_series=timeseries)


# boundary conditions
fm.constraint.mp.create_laminar_boundary(dofs=[1,2], direction=3)
fm.constraint.sp.fixMacroZmin(dofs=[1,2,3])


# Create a recorder for the whole model
recorder = fm.recorder.create_recorder("vtkhdf", file_base_name="result.vtkhdf",resp_types=["disp", "vel", "accel", "stress3D6", "strain3D6", "stress2D3", "strain2D3"], delta_t=0.02)

# Create a gravity analysis step
gravity = fm.analysis.create_default_transient_analysis(username="gravity", dt=0.01, num_steps=50)


# Add the recorder and gravity analysis step to the process
fm.process.add_step(kobe, description="Uniform Excitation (Kobe record)")
fm.process.add_step(recorder, description="Recorder of the whole model")
fm.process.add_step(gravity, description="Gravity Analysis Step")


fm.export_to_tcl("mesh.tcl")
fm.gui()
