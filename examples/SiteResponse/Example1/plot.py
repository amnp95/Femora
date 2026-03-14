# %%
import numpy as np
import glob
import h5py
import os
import matplotlib.pyplot as plt
from femora.utils.paths import motions_dir

os.chdir(os.path.dirname(__file__))
_MOTIONS = motions_dir()

# Maximum time to plot (seconds)
MAX_TIME = 40.0

def read_vtk_data(file_pattern, max_time,coord=[0., 0., 0.], res_type="acceleration"):
    """Read and process VTK HDF files."""
    files = sorted(glob.glob(file_pattern))
    for filename in files:
        try:
            with h5py.File(filename, "r") as f:
                points = f["VTKHDF"]["Points"][()]
                if points.size == 0:
                    continue

                # Find the closest point to (0, 0, 0)
                distances = np.linalg.norm(points - np.array(coord), axis=1)
                closest_index = np.argmin(distances)
                if distances[closest_index] > 1e-3:
                    continue

                acc = f["VTKHDF"]["PointData"][res_type][()]
                accoffset = f["VTKHDF"]["Steps"]["PointDataOffsets"]["acceleration"][()]
                acc = acc[accoffset + closest_index]

                time = f["VTKHDF"]["Steps"]["Values"][()]
                index = np.where(time < max_time)[0]

                return time[index], acc[index]
        except Exception:
            continue
    return None, None

def compute_transfer_function(surface_time, surface_acc, bedrock_time, bedrock_acc, dt=None):
    """Compute the transfer function using FFT."""
    t_min, t_max = max(surface_time[0], bedrock_time[0]), min(surface_time[-1], bedrock_time[-1])
    dt = dt or min(np.mean(np.diff(surface_time)), np.mean(np.diff(bedrock_time)))
    common_time = np.arange(t_min, t_max, dt)

    surface_interp = np.interp(common_time, surface_time, surface_acc)
    bedrock_interp = np.interp(common_time, bedrock_time, bedrock_acc)
    surface_interp += bedrock_interp

    fft_surface = np.fft.rfft(surface_interp)
    fft_bedrock = np.fft.rfft(bedrock_interp)

    f = np.fft.rfftfreq(len(common_time), d=dt)
    TF = fft_surface / fft_bedrock
    return f, TF

def compute_analytical_transfer_function(E, rho, nu, H, damp, freq_range):
    """Compute the analytical transfer function."""
    G = E / (2 * (1 + nu))
    vs = np.sqrt(G / rho)
    f1 = vs / (4 * H)
    f3 = 5 * f1

    omega1, omega2 = 2 * np.pi * f1, 2 * np.pi * f3
    a0 = 2 * damp * omega1 * omega2 / (omega1 + omega2)
    a1 = 2 * damp / (omega1 + omega2)

    omega = 2 * np.pi * freq_range
    Rdamp = a0 / (2 * omega) + a1 * omega / 2
    TF = 1 / np.sqrt(np.cos(omega * H / vs) ** 2 + (Rdamp * omega * H / vs) ** 2)
    return freq_range, TF

def plot_acceleration(surface_time, surface_acc, bedrock_time, bedrock_acc):
    """Plot acceleration time history."""
    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True, sharey=True)
    fig.subplots_adjust(hspace=0.1)
    labels = ['$a_x$', '$a_y$', '$a_z$']

    surface_correction = np.interp(surface_time, bedrock_time, bedrock_acc)
    surface_acc /= 9.81

    for i in range(3):
        axs[i].plot(surface_time, surface_acc[:, i] + (surface_correction if i == 0 else 0), label='Surface')
        axs[i].plot(bedrock_time, bedrock_acc if i == 0 else np.zeros_like(bedrock_time), label='Bedrock', color='red')
        axs[i].set_ylabel(labels[i])
        axs[i].legend(loc='upper right')
        axs[i].grid()

    axs[2].set_xlabel('Time (s)')
    plt.suptitle('Acceleration Time History')
    plt.show()

def plot_transfer_function(f, TF_num, f_analytical, TF_analytical):
    """Plot transfer function."""
    plt.plot(f, np.abs(TF_num), "b-", label="Numerical")
    plt.plot(f_analytical, TF_analytical, "r--", label="Analytical")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("|TF(f)|")
    plt.legend()
    plt.grid(True)
    plt.show()

# Main execution
surface_time, surface_acc = read_vtk_data("./Results/result*.vtkhdf", MAX_TIME)
bedrock_time = np.loadtxt(_MOTIONS / "FrequencySweep.time")
bedrock_acc = np.loadtxt(_MOTIONS / "FrequencySweep.acc")

if surface_time is not None and surface_acc is not None:
    plot_acceleration(surface_time, surface_acc, bedrock_time, bedrock_acc)

    f, TF_num = compute_transfer_function(surface_time, surface_acc[:, 0], bedrock_time, bedrock_acc)
    mask = (f < 22) & (f > 0)
    f, TF_num = f[mask], TF_num[mask]

    freq_range = np.arange(0.01, 22.01, 0.01)
    f_analytical, TF_analytical = compute_analytical_transfer_function(
        E=1.86e5, rho=15.3 / 9.81, nu=0.5, H=18, damp=0.03, freq_range=freq_range
    )

    plot_transfer_function(f, TF_num, f_analytical, TF_analytical)
