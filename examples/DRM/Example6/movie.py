# %%
import pyvista as pv
import h5py
import os
from tqdm import tqdm
from glob import glob
from itertools import cycle
import numpy as np
import matplotlib.pyplot as plt

# Directory change for file management
os.chdir(os.path.dirname(__file__))
filenames = sorted(glob("./Results/result*.vtkhdf"))  # Find all matching files
if not filenames:
    raise FileNotFoundError(
        "No VTKHDF result files found. Expected files like './Results/result*.vtkhdf'."
    )

stride = 2  # Skip frames to make it faster
output_movie = "movie.mp4"
frame_rate = 50  # Movie frame rate

# Create a PyVista plotter for the movie but do not use a graphical display
pl = pv.Plotter(off_screen=True)

# Preload all meshes and displacements
meshes = []
displacements = []
dispoffsets = []
points = []

# Color cycle for meshes
color_cycle = cycle(plt.cm.tab20.colors)

# Reading files and storing the data
for filename in tqdm(filenames, desc="Reading files"):
    mesh = pv.read(filename)
    meshes.append(mesh)
    points.append(mesh.points.copy())  # Store original points

    with h5py.File(filename, "r") as f:
        disp = f["VTKHDF"]["PointData"]["displacement"][()]
        dispoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["displacement"][()]
        displacements.append(disp)
        dispoffsets.append(dispoffset)

# Set up movie output using PyVista's built-in movie recording functionality
pl.open_movie(output_movie, framerate=frame_rate)

# Add meshes to the plotter
for mesh in meshes:
    pl.add_mesh(mesh, show_edges=True, opacity=1.0, color=next(color_cycle))
pl.write_frame()  # Write the first frame

# Update and render frames
for i in tqdm(range((len(dispoffsets[0]) - 1) // stride), desc=f"Rendering frames"):
    for mesh, disp, dispoffset, point in zip(meshes, displacements, dispoffsets, points):
        ii = dispoffset[i * stride]
        jj = dispoffset[i * stride + 1]
        mesh.points = point + disp[ii:jj, :] * 5.0  # Scale factor for visualization
    pl.write_frame()

# Close the movie when done
pl.close()
