import numpy as np
import glob
import h5py
import os
import pyvista as pv


boundaryConditionType = "Extended"  # "PML" or "Fixed", "Extended"
# boundaryConditionType = "Fixed"  # "PML" or "Fixed", "Extended"
boundaryConditionType = "PML"  # "PML" or "Fixed"
dirname = os.path.dirname(__file__)
os.chdir(dirname)
diname = os.path.join(dirname, boundaryConditionType)

# filter files with *.vtkhdf extension
file_pattern = os.path.join(diname, "*.vtkhdf")

# get list of all files matching the pattern
file_list = sorted(glob.glob(file_pattern))

# observation points (copied from plot.py) - these are the points we want to
# check for presence in a given vtkhdf file. If a file contains at least one
# of these points we keep it. This speeds up reading and ensures we only
# process files that actually have data for the observation points.
depth = -51
op1 = [0, 0, 0]
op2 = [0, 51, 0]
op3 = [51.0, 0, 0]
op4 = [51.0, 51.0, 0]
op5 = [0, 0, depth]
op6 = [0, 51, depth]
op7 = [51.0, 0, depth]
op8 = [51.0, 51.0, depth]
ops = [op1, op2, op3, op4, op5, op6, op7, op8]


# helper: check whether a file contains any of the observation points
def file_has_any_obs_point(filename, obs_points, tol=1e-3):
    try:
        with h5py.File(filename, "r") as f:
            pts = f["VTKHDF"]["Points"][()]
            if pts.size == 0:
                return False
            # compute distances from each obs point to all file points
            for op in obs_points:
                d = np.linalg.norm(pts - np.array(op), axis=1)
                if np.min(d) <= tol:
                    return True
    except Exception:
        return False
    return False


def file_obs_indices(filename, obs_points, tol=1e-3):
    """Return indices of obs_points present in filename (within tol)."""
    inds = []
    try:
        with h5py.File(filename, "r") as f:
            pts = f["VTKHDF"]["Points"][()]
            if pts.size == 0:
                return inds
            for i, op in enumerate(obs_points):
                d = np.linalg.norm(pts - np.array(op), axis=1)
                if np.min(d) <= tol:
                    inds.append(i)
    except Exception:
        return []
    return inds


# Select files in a single pass. If a file contains one or more observation
# points, select it and mark those points as covered. Stop when all points
# are covered.
selected_files = []
covered = [False] * len(ops)

for f in file_list:
    inds = file_obs_indices(f, ops)
    # keep only indices not yet covered
    new_inds = [ii for ii in inds if not covered[ii]]
    if new_inds:
        selected_files.append(f)
        for ii in new_inds:
            covered[ii] = True
    if all(covered):
        break

if not selected_files:
    # fallback: keep the original list to preserve previous behaviour
    filtered = file_list
else:
    filtered = selected_files

print(f"Selected {len(filtered)} files out of {len(file_list)} total files.")



bounds = (-90, 90, -90, 90, -90, 0)


meshes = []
displacements = []
accelerations = []
stride = 1
max_time = 2.0
magnification = 8.0
# loop over filtered files and add them to the plotter
for file in filtered:
    # read the file using PyVista
    mesh = pv.read(file)
    mesh = pv.UnstructuredGrid(mesh)
    npoints = mesh.n_points
    mesh = mesh.clip_box(bounds, invert=False, crinkle=True)
    if not mesh.is_empty:
        meshes.append(mesh)
        with h5py.File(file, "r") as f:
            time = f["VTKHDF"]["Steps"]["Values"][()]
            nsteps = time < max_time
            nsteps = np.sum(nsteps)
            disp = f["VTKHDF"]["PointData"]["displacement"][()]
            acc = f["VTKHDF"]["PointData"]["acceleration"][()]

        disp = disp.reshape((-1, npoints, 3))
        acc = acc.reshape((-1, npoints, 3))

        ids = mesh.point_data["vtkOriginalPointIds"]
        disp = disp[:nsteps:stride, ids, :]
        acc = acc[:nsteps:stride, ids, :]

        # create magnitude from acceleration
        acc = np.linalg.norm(acc, axis=2)

        displacements.append(disp)
        accelerations.append(acc)

if not displacements:
    raise RuntimeError("No mesh data found in the selected files.")

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
# add the meshes first
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


