# %%
import numpy as np
import glob
import h5py
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patheffects as pe
import argparse
# Work from the script directory so relative paths match the example layout
os.chdir(os.path.dirname(__file__))


def read_vtk_data(file_pattern, max_time, coord=(0.0, 0.0, 0.0), res_type="acceleration"):
    """Read and process VTK HDF files for the closest point to coord.

    Returns (time[:], data[:]) or (None, None) if not found.
    """
    files = sorted(glob.glob(file_pattern))
    for filename in files:
        try:
            with h5py.File(filename, "r", swmr=True) as f:
                points = f["VTKHDF"]["Points"][()]
                if points.size == 0:
                    continue

                # Find the closest point to coord
                distances = np.linalg.norm(points - np.array(coord), axis=1)
                closest_index = np.argmin(distances)
                # Require close match so we don't pick a random node
                if distances[closest_index] > 1e-3:
                    continue

                data = f["VTKHDF"]["PointData"][res_type][()]
                offsets = f["VTKHDF"]["Steps"]["PointDataOffsets"][res_type][()]
                data = data[offsets + closest_index]

                time = f["VTKHDF"]["Steps"]["Values"][()]
                index = np.where(time < max_time)[0]
                return time[index], data[index]
        except Exception:
            # Try next file if this one doesn't have the requested info
            continue
    return None, None


def read_sw4_series(point_index, max_time):
    """Read SW4 acceleration time series from text files for a given point index.

    Looks for SW4/P{point_index}/A_x.txt, A_y.txt, A_z.txt and optional DT_NPTS.txt.
    Returns (t, a) in SI units (m/s^2), or (None, None) if not found.
    """
    base = os.path.join("SW4", f"P{point_index}")
    ax_path = os.path.join(base, "A_x.txt")
    ay_path = os.path.join(base, "A_y.txt")
    az_path = os.path.join(base, "A_z.txt")
    if not (os.path.exists(ax_path) and os.path.exists(ay_path) and os.path.exists(az_path)):
        return None, None

    try:
        ax = np.loadtxt(ax_path)
        ay = np.loadtxt(ay_path)
        az = np.loadtxt(az_path)
    except Exception:
        return None, None

    # Determine dt: prefer DT_NPTS.txt if present, else fallback to known dt
    dt = None
    meta_path = os.path.join(base, "DT_NPTS.txt")
    if os.path.exists(meta_path):
        try:
            vals = np.loadtxt(meta_path).ravel()
            # Accept either "dt npts" in one line or a vector with dt first
            if vals.size >= 1:
                dt = float(vals[0])
        except Exception:
            dt = None
    if dt is None:
        dt = 1.077828176e-02  # fallback dt used in this example set

    n = min(ax.shape[0], ay.shape[0], az.shape[0])
    ax, ay, az = ax[:n], ay[:n], az[:n]
    t = np.arange(0.0, n * dt, dt)
    # Time window
    mask = t < max_time
    t = t[mask]
    a = np.zeros((t.shape[0], 3))
    a[:, 0] = ax[: t.shape[0]]
    a[:, 1] = ay[: t.shape[0]]
    a[:, 2] = az[: t.shape[0]]
    return t, a


def _resample_uniform(t, y):
    """Resample y(t) to a uniform time grid using linear interpolation.

    Returns tu, yu, dt where tu is uniform time, yu matches y's trailing dims.
    """
    t = np.asarray(t).ravel()
    if t.size < 2:
        return t, y, None
    dt_min = np.min(np.diff(t))
    # Guard against zero/negative dt due to possible duplicates
    dt_min = float(dt_min) if dt_min > 0 else float(np.mean(np.diff(t)[np.diff(t) > 0]))
    if not np.isfinite(dt_min) or dt_min <= 0:
        # fallback: treat as already uniform
        dt_min = float(np.diff(t).mean())
    tu = np.arange(t[0], t[-1] + 1e-12, dt_min)
    y = np.asarray(y)
    if y.ndim == 1:
        yu = np.interp(tu, t, y)
    else:
        yu = np.zeros((tu.shape[0],) + y.shape[1:], dtype=float)
        for j in range(y.shape[1]):
            yu[:, j] = np.interp(tu, t, y[:, j])
    return tu, yu, dt_min


def compute_psa_spectrum(t, a_g, periods, zeta=0.05):
    """Compute pseudo-acceleration response spectrum (PSA) for each component.

    Parameters:
    - t: time vector (s)
    - a_g: ground acceleration time history in g, shape (n, 3)
    - periods: array of periods (s)
    - zeta: damping ratio

    Returns: psa_g: array shape (len(periods), 3) in g
    """
    t = np.asarray(t).ravel()
    ag_si = np.asarray(a_g, dtype=float) * 9.81  # convert to m/s^2
    tu, agu, dt = _resample_uniform(t, ag_si)
    if dt is None or not np.isfinite(dt) or dt <= 0:
        return np.zeros((len(periods), ag_si.shape[1]))

    beta = 1/4  # average acceleration
    gamma = 1/2
    n = agu.shape[0]
    ncomp = agu.shape[1] if agu.ndim > 1 else 1
    psa = np.zeros((len(periods), ncomp), dtype=float)

    # Precompute Newmark constants that depend on dt only
    a0 = 1.0 / (beta * dt * dt)
    a1 = gamma / (beta * dt)
    a2 = 1.0 / (beta * dt)
    a3 = 0.5 / beta - 1.0
    a4 = gamma / beta - 1.0
    a5 = dt * (gamma / (2.0 * beta) - 1.0)

    # Loop over components
    for j in range(ncomp):
        p = -agu[:, j]  # effective external force p(t) = -ag(t)

        # For each period
        for k, T in enumerate(periods):
            # avoid zero or extremely small periods
            T_eff = max(float(T), 1e-3)
            omega = 2.0 * np.pi / T_eff
            c = 2.0 * zeta * omega  # m=1
            k_s = omega * omega

            k_eff = k_s + a0 + a1 * c

            # initialize
            u = 0.0
            v = 0.0
            a_rel = p[0] - c * v - k_s * u  # a = (p - c v - k u)/m, m=1
            umax = 0.0

            for i in range(n - 1):
                # effective load at i+1
                p_hat = (
                    p[i + 1]
                    + (a0 * u + a2 * v + a3 * a_rel)
                    + c * (a1 * u + a4 * v + a5 * a_rel)
                )
                u_new = p_hat / k_eff
                v_new = a1 * (u_new - u) - a4 * v - a5 * a_rel
                a_new = a0 * (u_new - u) - a2 * v - a3 * a_rel

                u, v, a_rel = u_new, v_new, a_new
                # track max relative displacement
                if abs(u) > umax:
                    umax = abs(u)

            psa[k, j] = (2.0 * np.pi / T_eff) ** 2 * umax  # omega^2 * max|u|

    # convert to g
    return psa / 9.81


def make_time_history_figure(all_data, styles, boundary_conditions, save_path='comparison.pdf'):
    """Create and save the time-history comparison figure (3xN layout)."""
    # Transposed layout: 3 rows (X,Y,Z components) by N columns (observation points)
    ncols = len(all_data)  # number of observation points
    nrows = 3  # X, Y, Z
    fig_height = max(2.0 + 1.4 * nrows, 4.0)
    fig_width = max(8.0, 4.8 * ncols)
    fig, ax = plt.subplots(nrows, ncols, figsize=(fig_width, fig_height), dpi=300, sharex=True, sharey="row")
    if ncols == 1:
        ax = np.array(ax).reshape(nrows, 1)

    # Plot data: iterate over columns (points), plot each component in its row
    for col, (orig_idx, _op, op_data) in enumerate(all_data):
        for bc_type, (t, a) in op_data.items():
            style = styles.get(bc_type, {})
            lines = []
            lines.append(ax[0, col].plot(t, a[:, 0], **style)[0])  # X
            lines.append(ax[1, col].plot(t, a[:, 1], **style)[0])  # Y
            lines.append(ax[2, col].plot(t, a[:, 2], **style)[0])  # Z

            # Add an outline to emphasized lines to keep them visible when overlapping
            if bc_type != "SW4":
                for ln in lines:
                    ln.set_path_effects([
                        pe.Stroke(linewidth=ln.get_linewidth() + 1.2, foreground="white"),
                        pe.Normal(),
                    ])

    # Common settings: grids, labels
    for row_idx, direction in enumerate(["X", "Y", "Z"]):
        for col in range(ncols):
            ax[row_idx, col].grid(True, linestyle='--', alpha=0.7)
            if row_idx == nrows - 1:
                ax[row_idx, col].set_xlabel("Time (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            if col == 0:
                ax[row_idx, col].set_ylabel(f"Acc {direction} (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")

    # Column titles on the top row: OP1, OP2, ...
    for col in range(ncols):
        ax[0, col].set_title(f"OP{col+1}", fontsize=12, fontweight='bold', fontname="Times New Roman")

    # Ticks font
    for axi in ax.ravel():
        axi.tick_params(axis='both', which='major', labelsize=10)
        for label in axi.get_xticklabels() + axi.get_yticklabels():
            label.set_fontname("Times New Roman")

    # Legend with rounded box frame
    handles = [plt.Line2D([0], [0], **styles[bc]) for bc in boundary_conditions]
    labels = boundary_conditions
    leg = fig.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 1.02),
        ncol=len(labels),
        fontsize=12,
        frameon=True,
        fancybox=True,
        framealpha=1.0,
    )
    frame = leg.get_frame()
    try:
        frame.set_boxstyle("round,pad=0.3,rounding_size=0.5")
    except Exception:
        frame.set_boxstyle("round")
    frame.set_edgecolor('black')
    frame.set_linewidth(1.0)
    frame.set_facecolor('white')

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(save_path, format='pdf', bbox_inches='tight')
    return fig


def make_psa_figure(all_data, styles, boundary_conditions, periods=None, zeta=0.05, save_path='comparison_psa.pdf', logx=True, logy=True):
    """Create and save the PSA comparison figure (3xN layout)."""
    if periods is None:
        periods = np.linspace(0.05, 5.0, 160)

    ncols = len(all_data)
    nrows = 3
    # fig2_height = max(2.0 + 1.4 * nrows, 4.0)
    # fig2_width = max(5.0, 4.8 * ncols)
    fig2_height = 8.0
    fig2_width = 5.0
    fig2, ax2 = plt.subplots(nrows, ncols, figsize=(fig2_width, fig2_height), dpi=300, sharex=True, sharey="row")
    if ncols == 1:
        ax2 = np.array(ax2).reshape(nrows, 1)

    for col, (_orig_idx, _op, op_data) in enumerate(all_data):
        for bc_type, (t_bc, a_bc_g) in op_data.items():
            base = styles.get(bc_type, {})
            # Force PSA plotting to solid lines, same alpha and thickness; keep colors
            plot_kwargs = dict(base)
            plot_kwargs.update({
                "linestyle": "-",
                "linewidth": 1.0,
                "alpha": 1.0,
            })
            psa = compute_psa_spectrum(t_bc, a_bc_g, periods, zeta=zeta)  # (nT,3) in g
            psa_plot = np.maximum(psa, 1e-6)
            lines = []
            lines.append(ax2[0, col].plot(periods, psa_plot[:, 0], **plot_kwargs)[0])  # X
            lines.append(ax2[1, col].plot(periods, psa_plot[:, 1], **plot_kwargs)[0])  # Y
            lines.append(ax2[2, col].plot(periods, psa_plot[:, 2], **plot_kwargs)[0])  # Z

            if bc_type != "SW4":
                for ln in lines:
                    ln.set_path_effects([
                        pe.Stroke(linewidth=ln.get_linewidth() + 1.2, foreground="white"),
                        pe.Normal(),
                    ])

    # Axes styling for spectra figure
    for row_idx, direction in enumerate(["X", "Y", "Z"]):
        for col in range(ncols):
            ax2[row_idx, col].grid(True, linestyle='--', alpha=0.7)
            if row_idx == nrows - 1:
                ax2[row_idx, col].set_xlabel("Period (s)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            if col == 0:
                ax2[row_idx, col].set_ylabel(f"PSA {direction} (g)", fontsize=12, fontweight='bold', fontname="Times New Roman")
            if logy:
                ax2[row_idx, col].set_yscale('log')
            if logx:
                ax2[row_idx, col].set_xscale('log')

    # Column titles OP1, OP2, ... on spectra figure
    for col in range(ncols):
        ax2[0, col].set_title(f"OP{col+1}", fontsize=12, fontweight='bold', fontname="Times New Roman")

    # Tick font for spectra
    for axi in ax2.ravel():
        axi.tick_params(axis='both', which='major', labelsize=10)
        for label in axi.get_xticklabels() + axi.get_yticklabels():
            label.set_fontname("Times New Roman")

    # Legend with rounded box for spectra
    handles2 = [plt.Line2D([0], [0], **styles[bc]) for bc in boundary_conditions]
    labels2 = boundary_conditions
    leg2 = fig2.legend(
        handles2, labels2, loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=len(labels2), fontsize=12,
        frameon=True, fancybox=True, framealpha=1.0,
    )
    frame2 = leg2.get_frame()
    try:
        frame2.set_boxstyle("round,pad=0.3,rounding_size=0.5")
    except Exception:
        frame2.set_boxstyle("round")
    frame2.set_edgecolor('black')
    frame2.set_linewidth(1.0)
    frame2.set_facecolor('white')

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    fig2.savefig(save_path, format='pdf', bbox_inches='tight')
    return fig2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare boundary conditions: time histories and PSA.")
    parser.add_argument("--figure", choices=["time", "psa", "both"], default="both", help="Which figure(s) to generate")
    parser.add_argument("--no-show", action="store_true", help="Do not display figures interactively")
    parser.add_argument("--psa-zeta", type=float, default=0.05, help="Damping ratio for PSA")
    parser.add_argument("--psa-logx", action="store_true", help="Use logarithmic x-axis for PSA")
    parser.add_argument("--psa-lin-x", dest="psa_logx", action="store_false", help="Use linear x-axis for PSA")
    args = parser.parse_args()
    # Visual parameters
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

    # Boundary condition datasets to compare
    boundary_conditions = ["SW4", "Results"]
    # Styling: SW4 is the neutral baseline; PML and Fixed are emphasized with strong, contrasting visuals
    styles = {
        # Neutral, slightly thinner baseline so differences stand out
        "SW4": {"linestyle": "-", 
        "color": "black", 
        "linewidth": 1, 
        "alpha": 1.0, 
        "zorder": 1
        },
        # High-contrast red with markers
        "Regular": {
            "linestyle": "--",
            "color": "r",
            "linewidth": 1.0,
            # "marker": "o",
            "markevery": 15,
            "markersize": 3.8,
            # "alpha": 0.2,
            "zorder": 3,
        },
        # High-contrast blue with different markers
        "nonlinearbasin": {
            "linestyle": "-.",
            "color": "b",
            "linewidth": 0.5,
            # "marker": "s",
            "markevery": 18,
            "markersize": 3.8,
            # "alpha": 0.5,
            "zorder": 2,
            "alpha": 0.3
        },
        "Results": {
            "linestyle": ":",
            "color": "g",
            "linewidth": 1,
            "markevery": 20,
            "markersize": 4,
            "zorder": 4,
            "alpha": 0.7
        }
    }

    # Observation points: align with SW4 directories (P0, P1, ...) and their coordinates in the model
    # For this example, SW4 provides P0 only, corresponding to coord (0, 0, 0)
    ops = [(0.0, 0.0, 0.0),
           (0.0, 0.0, -20.0)]

    # Controls
    max_time = 18.0
    res_type = "acceleration"

    # Gather data for all points and boundary conditions
    all_data = []  # list of (point_index, coord, {bc_type: (t, a_g)})
    for i, op in enumerate(ops):
        op_data = {}
        for bc_type in boundary_conditions:
            if bc_type == "SW4":
                t, a = read_sw4_series(i, max_time)
                if t is not None and a is not None:
                    op_data[bc_type] = (t, a / 9.81)  # convert to g
                else:
                    print(f"Warning: Could not locate SW4 data for P{i}.")
            else:
                file_pattern = os.path.join(bc_type, "*.vtkhdf")
                t, a = read_vtk_data(file_pattern=file_pattern, max_time=max_time, coord=op, res_type=res_type)
                if t is not None and a is not None:
                    op_data[bc_type] = (t, np.array(a) / 9.81)  # convert to g
                else:
                    print(f"Warning: Could not locate {bc_type} data for point {i+1} at coord {op}.")
        if op_data:
            all_data.append((i, op, op_data))

    if not all_data:
        print("No valid observation points found for any dataset.")
        exit(1)
    figs = []
    figs.append(make_time_history_figure(all_data, styles, boundary_conditions, save_path='comparison.pdf'))
    styles = {
        # Neutral, slightly thinner baseline so differences stand out
        "SW4": {"linestyle": "-", 
        "color": "black", 
        "linewidth": 2, 
        "alpha": 1.0, 
        "zorder": 1
        },
        # High-contrast red with markers
        "Regular": {
            "linestyle": "-",
            "color": "r",
            "linewidth": 1,
            # "marker": "o",
            "markevery": 15,
            "markersize": 3.8,
            # "alpha": 0.2,
            "zorder": 3,
        },
        # High-contrast blue with different markers
        "nonlinearbasin": {
            "linestyle": "-",
            "color": "b",
            "linewidth": 1,
            # "marker": "s",
            "markevery": 18,
            "markersize": 3.8,
            # "alpha": 0.5,
            "zorder": 2,
        },
        "Results": {
            "linestyle": "-",
            "color": "g",
            "linewidth": 1,
            "markevery": 20,
            "markersize": 4,
            "zorder": 4,
        }
    }
    figs.append(make_psa_figure(all_data, styles, boundary_conditions, periods=None, zeta=args.psa_zeta, save_path='comparison_psa.pdf', logx=True, logy=True))

    plt.show()

# %%
