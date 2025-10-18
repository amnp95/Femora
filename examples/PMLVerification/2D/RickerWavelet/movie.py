import numpy as np
import glob
import h5py
import os
import pyvista as pv



boundaryConditionType = "Extended"  # "PML" or "Fixed", "Extended"
# boundaryConditionType = "Fixed"  # "PML" or "Fixed", "Extended"
boundaryConditionType = "PML"  # "PML" or "Fixed
dirname = os.path.dirname(__file__)
os.chdir(dirname)
diname = os.path.join(dirname, boundaryConditionType)

# filter files with *.vtkhdf extension
file_pattern = os.path.join(diname, "*.vtkhdf")

# get list of all files matching the pattern
file_list = glob.glob(file_pattern)

# sort the list by filename
file_list.sort()

# create a PyVista plotter


bounds = (-90, 90, -90, 90, -90, 0)


meshes = []
displacements = []
accelerations = []
stride = 1 
max_time = 2.0
magnification = 8.0
# loop over all files and add them to the plotter
for file in file_list:
    # read the file using PyVista
    mesh = pv.read(file)
    mesh = pv.UnstructuredGrid(mesh)
    npoints = mesh.n_points
    mesh = mesh.clip_box(bounds, invert=False, crinkle=True)
    if not mesh.is_empty:
        meshes.append(mesh)
        f = h5py.File(file, "r")
        time = f["VTKHDF"]["Steps"]["Values"][()]
        nsteps = time < max_time
        nsteps = np.sum(nsteps)
        disp = f["VTKHDF"]["PointData"]["displacement"][()]
        acc  = f["VTKHDF"]["PointData"]["acceleration"][()]
        f.close()
        disp = disp.reshape((-1, npoints, 3))
        acc  = acc.reshape((-1, npoints, 3))

        ids  = mesh.point_data["vtkOriginalPointIds"]
        disp = disp[:nsteps:stride, ids, :]
        acc  = acc[:nsteps:stride, ids, :]

        # create magnitude from acceleration
        acc = np.linalg.norm(acc, axis=2)

        displacements.append(disp)
        accelerations.append(acc)

# create an animation by updating the mesh in the plotter
nframes = displacements[0].shape[0]
plotter = pv.Plotter()
plotter.open_movie(f"{boundaryConditionType}.mp4", framerate=120, quality=10, 
                    codec="libx264", 
                    format="FFMPEG",
                    output_params=["-pix_fmt", "yuv420p"])
clim_max = np.max([np.max(acc) for acc in accelerations])
clim_min = np.min([np.min(acc) for acc in accelerations])
clim = (clim_min, clim_max)
coords = []
# # add the meshes first
for i, mesh in enumerate(meshes):
    mesh.point_data["acceleration"] = accelerations[i][0, :]
    actor = plotter.add_mesh(mesh, scalars="acceleration", clim=clim, cmap="jet", show_scalar_bar=True)
    coords.append(mesh.points.copy())

plotter.camera_position = 'xz'
plotter.show(auto_close=False) 
plotter.write_frame()


for frame in range(nframes):
    print(f"Frame {frame+1}/{nframes}")
    for i, mesh in enumerate(meshes):
        mesh.point_data["acceleration"] = accelerations[i][frame, :]
        mesh.points = coords[i] + displacements[i][frame, :] * magnification
    plotter.write_frame()

plotter.close()


