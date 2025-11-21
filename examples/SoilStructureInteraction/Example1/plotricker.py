import numpy as np
import matplotlib.pyplot as plt
import os
os.chdir(os.path.dirname(__file__))
import h5py

time = np.loadtxt("ricker_surface.time")
acc = np.loadtxt("ricker_surface.acc")



f = h5py.File("drmload.h5drm", "r")
xyz = f["DRM_Data"]["xyz"][()]
acc_drm = f["DRM_Data"]["acceleration"][()]
disp_drm = f["DRM_Data"]["displacement"][()]
data_location_ = f["DRM_Data"]["data_location"][()]
dt = f["DRM_Metadata"]["dt"][()]
print(xyz.shape)
print(acc_drm.shape)
point = [8.0, 3.0, 0.0]
distances = np.linalg.norm(xyz - point, axis=1)
closest_index = np.argmin(distances)
print(f"Closest point to {point}: {xyz[closest_index]}, Index: {closest_index}, Distance: {distances[closest_index]}")
data_location = data_location_[closest_index]
acc_drm_point = acc_drm[data_location,:]

# Setup for publication quality plot
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.figsize': (10, 6),
    'lines.linewidth': 1.5
})

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
time_axis = np.arange(0, acc_drm_point.shape[0]*dt, dt)

# Plot surface motion
ax.plot(time_axis, acc_drm_point, color="#e74c3c", linestyle="-", label="Surface Motion", alpha=0.9)

point = [8.0, 3.0, -5.0]
distances = np.linalg.norm(xyz - point, axis=1)
closest_index = np.argmin(distances)
print(f"Closest point to {point}: {xyz[closest_index]}, Index: {closest_index}, Distance: {distances[closest_index]}")
data_location = data_location_[closest_index]
acc_drm_point = acc_drm[data_location,:]

# Plot incident motion
ax.plot(time_axis, acc_drm_point, color="b", linestyle="--", label="Incident Motion", alpha=0.9)

ax.set_title("DRM Acceleration Time History")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Acceleration ($m/s^2$)")
ax.grid(True, which='major', linestyle='--', alpha=0.7)
ax.grid(True, which='minor', linestyle=':', alpha=0.4)
ax.minorticks_on()
ax.legend(frameon=True, fancybox=True, framealpha=0.9, loc='best')

plt.tight_layout()
plt.savefig("drm_acceleration_history.png", dpi=300, bbox_inches='tight')
plt.savefig("drm_acceleration_history.pdf", bbox_inches='tight')
plt.show()
