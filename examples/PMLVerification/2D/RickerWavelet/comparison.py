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
    ]
    mpl.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)

    boundary_conditions = ["Extended", "PML", "Fixed"]
    styles = {
        "Extended": {"linestyle": "-", "color": "blue", "linewidth": 1.0},
        "PML": {"linestyle": "-", "color": "red", "linewidth": 1.2},
        "Fixed": {"linestyle": "--", "color": "black", "linewidth": 1.0, "alpha": 0.7},
    }
    
    op1 = [51.0, 1.5, 0.0]
    op2 = [0.0,  1.5,  -51.0]
    op3 = [51.0, 1.5, -51.0]
    ops = [op1, op2, op3]

    max_time = 2.
    
    all_data_acc = []
    all_data_disp = []

    for i, op in enumerate(ops):
        op_data_acc = {}
        op_data_disp = {}
        for bc_type in boundary_conditions:
            file_pattern = os.path.join(bc_type, "*.vtkhdf")
            
            # Read acceleration
            t_acc, acc = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op, res_type="acceleration")
            if t_acc is not None and acc is not None:
                op_data_acc[bc_type] = (t_acc, np.array(acc) / 9.81)  # convert to g
            else:
                print(f"Warning: Could not locate acceleration data for OP {i+1} under '{bc_type}/'.")

            # Read displacement
            t_disp, disp = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op, res_type="displacement")
            if t_disp is not None and disp is not None:
                op_data_disp[bc_type] = (t_disp, np.array(disp))
            else:
                print(f"Warning: Could not locate displacement data for OP {i+1} under '{bc_type}/'.")

        if op_data_acc:
            all_data_acc.append((i, op, op_data_acc))
        if op_data_disp:
            all_data_disp.append((i, op, op_data_disp))

    # Plot Accelerations
    if not all_data_acc:
        print("No valid acceleration data found.")
    else:
        nrows = len(all_data_acc)
        fig, ax = plt.subplots(nrows, 2, figsize=(8, 2.5 * nrows), dpi=300, sharex=True, sharey="row")

        if nrows == 1:
            ax = np.array([ax])

        for row, (orig_idx, op, op_data) in enumerate(all_data_acc):
            for bc_type, (t, a) in op_data.items():
                style = styles.get(bc_type, {})
                ax[row, 0].plot(t, a[:, 0], label=bc_type, **style)
                ax[row, 1].plot(t, a[:, 2], label=bc_type, **style)

            for col, direction in enumerate(["X", "Z"]):
                ax[row, col].grid(True, linestyle='--', alpha=0.7)
                if row == nrows - 1:
                    ax[row, col].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax[row, col].set_ylabel(f"Acc {direction} (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax[row, col].text(
                    0.98, 0.95, f"Point {orig_idx+1}",
                    transform=ax[row, col].transAxes, ha='right', va='top', fontsize=12, fontname="Times New Roman",
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
                )

        for axi in ax.ravel():
            axi.tick_params(axis='both', which='major', labelsize=10)
            for label in axi.get_xticklabels() + axi.get_yticklabels():
                label.set_fontname("Times New Roman")
        
        handles, labels = ax[0,0].get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        fig.legend(unique_labels.values(), unique_labels.keys(), loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=len(styles), fontsize=12, frameon=False)

        plt.tight_layout(rect=[0, 0, 1, 1])
        plt.savefig('comparison_acceleration.pdf', format='pdf', bbox_inches='tight')
        plt.show()

    # Plot Displacements
    if not all_data_disp:
        print("No valid displacement data found.")
    else:
        nrows = len(all_data_disp)
        fig_disp, ax_disp = plt.subplots(nrows, 2, figsize=(8, 2.5 * nrows), dpi=300, sharex=True, sharey="row")

        if nrows == 1:
            ax_disp = np.array([ax_disp])

        for row, (orig_idx, op, op_data) in enumerate(all_data_disp):
            for bc_type, (t, d) in op_data.items():
                style = styles.get(bc_type, {})
                ax_disp[row, 0].plot(t, d[:, 0], label=bc_type, **style)
                ax_disp[row, 1].plot(t, d[:, 2], label=bc_type, **style)

            for col, direction in enumerate(["X", "Z"]):
                ax_disp[row, col].grid(True, linestyle='--', alpha=0.7)
                if row == nrows - 1:
                    ax_disp[row, col].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[row, col].set_ylabel(f"Disp {direction} (m)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[row, col].text(
                    0.98, 0.95, f"Point {orig_idx+1}",
                    transform=ax_disp[row, col].transAxes, ha='right', va='top', fontsize=12, fontname="Times New Roman",
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
                )

        for axi in ax_disp.ravel():
            axi.tick_params(axis='both', which='major', labelsize=10)
            for label in axi.get_xticklabels() + axi.get_yticklabels():
                label.set_fontname("Times New Roman")
        
        handles, labels = ax_disp[0,0].get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        fig_disp.legend(unique_labels.values(), unique_labels.keys(), loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=len(styles), fontsize=12, frameon=False)

        plt.tight_layout(rect=[0, 0, 1, 1])
        plt.savefig('comparison_displacement.pdf', format='pdf', bbox_inches='tight')
        plt.show()
