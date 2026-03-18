import femora as fm
import os

# change the direcotto the current file
os.chdir(os.path.dirname(os.path.abspath(__file__)))
fm.set_results_folder("Results")

# Layer properties as a dictionary
layers = [
    {"layer": 1, "rho": 2142.0500, "vp": 669.0500, "vs": 353.1000, "xi_s": 0.0296, "xi_p": 0.0148, "thickness": 8},
    {"layer": 2, "rho": 2146.2000, "vp": 785.2500, "vs": 414.4000, "xi_s": 0.0269, "xi_p": 0.0134, "thickness": 8},
    {"layer": 3, "rho": 2150.3500, "vp": 886.0500, "vs": 467.6000, "xi_s": 0.0249, "xi_p": 0.0125, "thickness": 8},
    {"layer": 4, "rho": 2154.4500, "vp": 976.4000, "vs": 515.3000, "xi_s": 0.0234, "xi_p": 0.0117, "thickness": 8},
    {"layer": 5, "rho": 2158.6000, "vp": 1059.0500, "vs": 558.9500, "xi_s": 0.0221, "xi_p": 0.0111, "thickness": 8},
    {"layer": 6, "rho": 2162.7500, "vp": 1135.6500, "vs": 599.4000, "xi_s": 0.0211, "xi_p": 0.0105, "thickness": 8}
]


pi = 3.1415926
f1 = 15; # Hz
f2 = 3; # Hz
w1 = 2*pi*f1
w2 = 2*pi*f2


index = 0
for layer in layers[::-1]:
    rho = layer["rho"]
    vp = layer["vp"]
    vs = layer["vs"]
    xi_s = layer["xi_s"]
    xi_p = layer["xi_p"]
    thickness = layer["thickness"]
    vp_vs_ratio = (vp / vs) ** 2
    nu  = (vp_vs_ratio - 2) / (2 * (vp_vs_ratio - 1))
    E = 2 * rho * (vs ** 2) * (1 + nu)
    E = E / 1000
    rho = rho / 1000
    mat = fm.material.create_material("nDMaterial", "ElasticIsotropic",
                                user_name=f"Layer{layer['layer']}",
                                E=E, nu=nu, rho=rho)
    ele = fm.element.create_element(element_type="stdBrick",
                                    ndof=3,
                                    material=mat,
                                    b1=0,
                                    b2=0,
                                    b3=0)

    damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=3, f2=15)
    # reg = fm.region.create_region("elementRegion", damping=damp)

    zmin = -48 + index * thickness
    zmax = zmin + thickness
    dx = 4.0
    dy = 4.0
    dz = 4.0
    Nx = int(128 / dx)
    Ny = int(128 / dy)
    Nz = int(thickness / dz)
    reg = fm.region.create_region("elementRegion", damping=damp)
    fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                            user_name=f"Layer{layer['layer']}",
                            element=ele,
                            region=reg,
                            **{'X Min': -64, 'X Max': 64,
                                'Y Min': -64, 'Y Max': 64,
                                'Z Min': zmin, 'Z Max': zmax,
                                'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz})
    index += 1


# create a list of mesh parts
mesh_parts = []
for layer in layers:
    mesh_parts.append(f"Layer{layer['layer']}")

fm.assembler.create_section(mesh_parts, num_partitions=32, partition_algorithm = "metis")

fm.assembler.Assemble()
# fm.addAbsorbingLayer(numLayers=10,
#                         numPartitions=8,
#                         partitionAlgo="kd-tree",
#                         geometry="Rectangular",
#                         rayleighDamping=0.95,
#                         matchDamping=False,
#                         type="Rayleigh",
#                         )
fm.drm.addAbsorbingLayer(numLayers=4,
                        numPartitions=64,
                        partitionAlgo="kd-tree",
                        geometry="Rectangular",
                        rayleighDamping=0.95,
                        matchDamping=False,
                        type="PML",
                        )
h5pattern = fm.pattern.create_pattern( 'h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
fm.drm.set_pattern(h5pattern)
fm.drm.createDefaultProcess(finalTime=20, dT=0.01)
fm.export_to_tcl(filename="model.tcl")

# fm.export_to_vtk("mesh.vtk")
# fm.gui()
