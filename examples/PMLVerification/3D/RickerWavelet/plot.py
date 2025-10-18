# %%
import numpy as np
import glob
import h5py
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

os.chdir(os.path.dirname(__file__))

def read_vtk_data(file_pattern, max_time, coord=[0., 0., 0.], res_type="acceleration"):
    """Read and process VTK HDF files."""
    files = sorted(glob.glob(file_pattern))
    for filename in files:
        try:
            with h5py.File(filename, "r") as f:
                points = f["VTKHDF"]["Points"][()]
                if points.size == 0:
                    continue

                # Find the closest point to coord
                distances = np.linalg.norm(points - np.array(coord), axis=1)
                closest_index = np.argmin(distances)
                if distances[closest_index] > 1e-3:
                    continue

                data = f["VTKHDF"]["PointData"][res_type][()]
                offsets = f["VTKHDF"]["Steps"]["PointDataOffsets"][res_type][()]
                data = data[offsets + closest_index]

                time = f["VTKHDF"]["Steps"]["Values"][()]
                index = np.where(time < max_time)[0]

                return time[index], data[index]
        except Exception:
            continue
    return None, None


if __name__ == "__main__":
    # Parameters
    colors = [
        (0.050980392156862744, 0.16078431372549018, 0.4666666666666666, 1.0),
        (0.9784313725490196, 0.12137254901960784, 0.301960784313724, 1.0),
        (0.0, 0.2784313725490196, 0.10588235294117643, 1.0),
        (0.615686274509804, 0.27450980392156865, 0.0, 1.0),
        (0.5147058823529411, 0.141078431372549, 0.38431372549019527, 1.0),
        (0.025490196078431372, 0.2196078431372549, 0.28627450980392155, 1.0),
        (0.33333333333333337, 0.21764705882352942, 0.2333333333333333, 1.0),
        (0.4892156862745098, 0.19990196078431371, 0.2039215686274502, 1.0),
        (0.7970588235294118, 0.19794117647058823, 0.150980392156862, 1.0),
        (0.307843137254902, 0.27647058823529413, 0.052941176470588214, 1.0),
    ]
    mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)

    boundaryConditionType = "Extended"  # "PML" or "Fixed", "Extended"
    file_pattern = os.path.join(boundaryConditionType, "*.vtkhdf")

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

    max_time = 2  # read full time series up to this time
    res_type = "acceleration"

    # Read data for all observation points
    data = []
    for i, op in enumerate(ops):
        t, a = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op, res_type=res_type)
        if t is None or a is None:
            print(f"Warning: Could not locate the requested point/field for observation point {i+1} under '{boundaryConditionType}/'.")
            continue
        data.append((i, op, t, np.array(a) / 9.81))  # convert to g

    if not data:
        print(f"No valid observation points found in '{boundaryConditionType}/'.")
    else:
        # Plot: rows = number of valid points, columns = X/Y/Z
        nrows = len(data)
        fig_height = max(2.0 + 1.4 * nrows, 4.0)
        fig, ax = plt.subplots(nrows, 3, figsize=(9.5, fig_height), dpi=300, sharex=True, sharey=True)

        # Ensure ax is 2D
        if nrows == 1:
            ax = np.array([ax])

        for row, (orig_idx, op, t, a) in enumerate(data):
            color = colors[orig_idx % len(colors)]

            # X
            ax[row, 0].plot(t, a[:, 0], lw=1.2, color=color)
            if row == nrows - 1:
                ax[row, 0].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 0].set_ylabel("Acc X (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 0].grid(True, linestyle='--', alpha=0.7)
            ax[row, 0].text(
                0.98, 0.95, f"Observation point {orig_idx+1}",
                transform=ax[row, 0].transAxes,
                ha='right', va='top',
                fontsize=12, fontname="Times New Roman",
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
            )

            # Y
            ax[row, 1].plot(t, a[:, 1], lw=1.2, color=color)
            if row == nrows - 1:
                ax[row, 1].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 1].set_ylabel("Acc Y (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 1].grid(True, linestyle='--', alpha=0.7)
            ax[row, 1].text(
                0.98, 0.95, f"Observation point {orig_idx+1}",
                transform=ax[row, 1].transAxes,
                ha='right', va='top',
                fontsize=12, fontname="Times New Roman",
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
            )

            # Z
            ax[row, 2].plot(t, a[:, 2], lw=1.2, color=color)
            if row == nrows - 1:
                ax[row, 2].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 2].set_ylabel("Acc Z (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[row, 2].grid(True, linestyle='--', alpha=0.7)
            ax[row, 2].text(
                0.98, 0.95, f"Observation point {orig_idx+1}",
                transform=ax[row, 2].transAxes,
                ha='right', va='top',
                fontsize=12, fontname="Times New Roman",
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
            )

        # Ticks font
        for axi in ax.ravel():
            axi.tick_params(axis='both', which='major', labelsize=10)
            for label in axi.get_xticklabels() + axi.get_yticklabels():
                label.set_fontname("Times New Roman")

        plt.tight_layout()
        plt.savefig(f'{boundaryConditionType}.pdf', format='pdf', bbox_inches='tight')
        plt.show()