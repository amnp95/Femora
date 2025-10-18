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




if __name__ == "__main__":
    # Parameters
    # Publication plotting style (match ricker_load.py)
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
    boundaryConditionType = "Fixed"  # "PML" or "Fixed", "Extended"
    boundaryConditionType = "PML"  # "PML" or "Fixed", "Extended"


    file_pattern = os.path.join(boundaryConditionType, "*.vtkhdf")
    op3 = [51.0, 1.5, -51.0]
    op2 = [0.0,  1.5,  -51.0]
    op1 = [51.0, 1.5, 0.0]
    max_time = 2  # read full time series
    res_type = "acceleration"

    # Read data
    t1, a1 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op1, res_type=res_type)
    t2, a2 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op2, res_type=res_type)
    t3, a3 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op3, res_type=res_type)
    if a1 is None or a2 is None or a3 is None:
        print("Could not locate the requested point/field in any VTK-HDF file under 'Extended/'.")
    else:
        # convert to g
        a1, a2, a3 = np.array(a1)/9.81, np.array(a2)/9.81, np.array(a3)/9.81

        # plot in a (3,2) for each observation point for x and z acceleration
        fig, ax = plt.subplots(3, 2, figsize=(6.5, 7.5), dpi=300, sharex=True, sharey=True)
        nrows = ax.shape[0]
        for i, (t, a, target_coord) in enumerate(zip([t1, t2, t3], [a1, a2, a3], [op1, op2, op3])):
            color = colors[i % len(colors)]
            # X component
            ax[i, 0].plot(t, a[:, 0], lw=1.2, color=color)
            if i == nrows - 1:
                ax[i, 0].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[i, 0].set_ylabel("Acc X (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[i, 0].grid(True, linestyle='--', alpha=0.7)
            ax[i, 0].text(
                0.98, 0.95, f"Observation point {i+1}",
                transform=ax[i, 0].transAxes,
                ha='right', va='top',
                fontsize=12, fontname="Times New Roman",
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
            )

            # Z component
            ax[i, 1].plot(t, a[:, 2], lw=1.2, color=color)
            if i == nrows - 1:
                ax[i, 1].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[i, 1].set_ylabel("Acc Z (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            ax[i, 1].grid(True, linestyle='--', alpha=0.7)
            ax[i, 1].text(
                0.98, 0.95, f"Observation point {i+1}",
                transform=ax[i, 1].transAxes,
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
        # Save publication-quality PDF
        plt.savefig(f'{boundaryConditionType}.pdf', format='pdf', bbox_inches='tight')
        plt.savefig(f'{boundaryConditionType}.png', format='png', bbox_inches='tight')
        plt.savefig(f'{boundaryConditionType}.svg', format='svg', bbox_inches='tight')
        plt.show()


        # Plot displacement figures as well
        res_type_disp = "displacement"
        t1_disp, d1 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op1, res_type=res_type_disp)
        t2_disp, d2 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op2, res_type=res_type_disp)
        t3_disp, d3 = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op3, res_type=res_type_disp)

        if d1 is None or d2 is None or d3 is None:
            print("Could not locate the requested point/field in any VTK-HDF file for displacement under 'Extended/'.")
        else:
            fig_disp, ax_disp = plt.subplots(3, 2, figsize=(6.5, 7.5), dpi=300, sharex=True, sharey=True)
            for i, (t, d, target_coord) in enumerate(zip([t1_disp, t2_disp, t3_disp], [d1, d2, d3], [op1, op2, op3])):
                color = colors[i % len(colors)]
                # X component
                ax_disp[i, 0].plot(t, d[:, 0], lw=1.2, color=color)
                if i == 2:
                    ax_disp[i, 0].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[i, 0].set_ylabel("Disp X (m)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[i, 0].grid(True, linestyle='--', alpha=0.7)
                ax_disp[i, 0].text(
                    0.98, 0.95, f"Observation point {i+1}",
                    transform=ax_disp[i, 0].transAxes,
                    ha='right', va='top',
                    fontsize=12, fontname="Times New Roman",
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
                )

                # Z component
                ax_disp[i, 1].plot(t, d[:, 2], lw=1.2, color=color)
                if i == 2:
                    ax_disp[i, 1].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[i, 1].set_ylabel("Disp Z (m)", fontsize=12, fontweight='bold', fontname="Times New Roman")
                ax_disp[i, 1].grid(True, linestyle='--', alpha=0.7)
                ax_disp[i, 1].text(
                    0.98, 0.95, f"Observation point {i+1}",
                    transform=ax_disp[i, 1].transAxes,
                    ha='right', va='top',
                    fontsize=12, fontname="Times New Roman",
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.6, alpha=0.9)
                )

            for axi in ax_disp.ravel():
                axi.tick_params(axis='both', which='major', labelsize=10)
                for label in axi.get_xticklabels() + axi.get_yticklabels():
                    label.set_fontname("Times New Roman")

            plt.tight_layout()
            # plt.savefig(f'{boundaryConditionType}_displacement.pdf', format='pdf', bbox_inches='tight')
            # plt.savefig(f'{boundaryConditionType}_displacement.png', format='png', bbox_inches='tight')
            plt.savefig(f'{boundaryConditionType}_displacement.svg', format='svg', bbox_inches='tight')
            plt.show()