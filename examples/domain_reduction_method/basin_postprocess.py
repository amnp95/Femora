"""Basin response reduction and documentation mesh rendering."""

import argparse
import csv
from pathlib import Path
import femora as fm


def generate_results(results_root, output_dir, final_time=2.0):
    """Reduce results on TACC; this is a numerical check, not validation."""
    import json
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    results_root = Path(results_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    center_rows = []
    figure, axes = plt.subplots(3, 3, figsize=(15, 9), sharex=True, squeeze=False)
    probes = [("center", (0, 0, 0)), ("edge", (48, 0, 0)), ("outside", (60, 0, 0))]
    for column, site in enumerate((1, 2, 3)):
        axes[0, column].set_title(f"Site {site}")
        for material in ("elastic", "plastic", "no_basin"):
            case = f"site{site}_{material}"
            response = results_root / case / "results" / "basin_response*.vtkhdf"
            with fm.results.open(str(response)) as results:
                time = np.asarray(results.times, dtype=float)
                if len(time) < 2 or not np.isfinite(time).all() or np.any(np.diff(time) <= 0):
                    raise ValueError(f"{case}: invalid recorded time vector")
                if time[-1] < final_time - 0.011:
                    raise ValueError(f"{case}: incomplete run, last recorded time {time[-1]}")
                summary[case] = {"samples": len(time), "last_time_s": float(time[-1]), "probes": {}}
                for axis, (name, coordinate) in zip(axes[:, column], probes):
                    point = results.nearest_point(coordinate)
                    if np.linalg.norm(np.asarray(point.coordinate) - coordinate) > 1.0e-6:
                        raise ValueError(f"{case}: missing requested probe {coordinate}")
                    acceleration = np.asarray(results.point_history("acceleration", point), dtype=float)[:, :3]
                    displacement = np.asarray(results.point_history("displacement", point), dtype=float)[:, :3]
                    if not np.isfinite(acceleration).all() or not np.isfinite(displacement).all():
                        raise ValueError(f"{case}: nonfinite results at {name}")
                    if name == "center":
                        # Preserve native timestamps when adaptive steps differ.
                        center_rows.extend(
                            (case, float(t), *a)
                            for t, a in zip(time, acceleration)
                        )
                    np.savetxt(output_dir / f"{case}_{name}.csv",
                               np.column_stack((time, acceleration, displacement)), delimiter=",",
                               header="time_s,ax_m_per_s2,ay_m_per_s2,az_m_per_s2,ux_m,uy_m,uz_m", comments="")
                    summary[case]["probes"][name] = {
                        "coordinate_m": list(point.coordinate),
                        "peak_acceleration_m_per_s2": float(np.abs(acceleration).max()),
                        "peak_displacement_m": float(np.abs(displacement).max()),
                    }
                    axis.plot(time, acceleration[:, 0], label=material.replace("_", " "))
                    axis.set_ylabel(f"{name}\nax (m/s2)")
                    axis.grid(alpha=0.2)
    with (output_dir / "center_acceleration_all_cases.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(["case", "time_s", "ax_m_per_s2", "ay_m_per_s2", "az_m_per_s2"])
        writer.writerows(center_rows)
    axes[0, 0].legend()
    for axis in axes[-1]:
        axis.set_xlabel("Time (s)")
    figure.tight_layout()
    figure.savefig(output_dir / "surface_acceleration.png", dpi=180)
    plt.close(figure)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_dir


def render_mesh(output_dir):
    """Render the layered mesh figure without launching a simulation."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    import numpy as np
    import pyvista as pv
    from basin import LAYERS

    # A separate presentation script keeps the model's interactive preview simple.
    colors = ["#cfb781", "#b7c79f", "#80b5ac", "#709da9", "#738aa3", "#8c829e"]
    basin_color = "#bd6348"
    background = "#f6f4ee"
    ink = "#293e45"
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    plotter = pv.Plotter(off_screen=True, window_size=(1200, 1100))
    plotter.set_background(background)
    z_top = 0.0
    for layer, color in zip(LAYERS, colors):
        name, density, vp, vs, damping, thickness = layer
        z_bottom = z_top - thickness
        grid = pv.RectilinearGrid(
            np.linspace(-64.0, 64.0, 33), np.linspace(-64.0, 64.0, 33),
            np.linspace(z_bottom, z_top, 3),
        ).cast_to_unstructured_grid()
        centers = grid.cell_centers().points
        inside = np.linalg.norm(centers - [0.0, 0.0, 70.0], axis=1) <= 85.0
        # Keep whole cells so the cutaway shows the real brick edges.
        host = grid.extract_cells(~inside).clip(normal="y", origin=(0, 0, 0), crinkle=True)
        plotter.add_mesh(host, color=color, show_edges=True, edge_color="#626963", line_width=0.4)
        if inside.any():
            basin = grid.extract_cells(inside).clip(normal="y", origin=(0, 0, 0), crinkle=True)
            plotter.add_mesh(basin, color=basin_color, show_edges=True, edge_color="#794f42", line_width=0.4)
        z_top = z_bottom
    plotter.view_isometric()
    plotter.camera.parallel_projection = False
    plotter.camera.zoom(1.12)
    image = plotter.screenshot(return_img=True)
    plotter.close()

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": ink})
    figure, axes = plt.subplots(1, 2, figsize=(16, 7.4), facecolor=background,
                                gridspec_kw={"width_ratios": [1.05, 1]})
    axes[0].imshow(image)
    axes[0].axis("off")
    axes[0].set_title("01   PERSPECTIVE CUTAWAY", loc="left", fontsize=15, pad=10)
    section = axes[1]
    section.set_facecolor(background)
    # y = 0 lies on two cell faces; both adjacent columns have |y_center| = 2 m.
    # Color each rectangle using the same cell-center rule as the model.
    for row in range(12):
        z_bottom = -4.0 * (row + 1)
        for column in range(32):
            x_left = -64.0 + 4.0 * column
            distance = np.linalg.norm([x_left + 2.0, 2.0, z_bottom + 2.0 - 70.0])
            color = basin_color if distance <= 85.0 else colors[row // 2]
            section.add_patch(Rectangle((x_left, z_bottom), 4, 4, facecolor=color,
                                       edgecolor="#606961", linewidth=0.22))
    section.set_xlim(-83, 82)
    section.set_ylim(-70, 16)
    section.set_aspect("equal")
    section.axis("off")
    section.set_title("02   CENTER SECTION  /  y = 0 m", loc="left", fontsize=15, pad=10)
    section.text(-64, 5, "Ground surface", fontsize=10, color=ink)
    section.annotate("Soft basin", xy=(0, -8), xytext=(28, 9), fontsize=11, color=ink,
                     arrowprops={"arrowstyle": "-", "color": ink, "linewidth": 0.8})
    dimension = {"arrowstyle": "|-|", "color": "#6b7c7d", "linewidth": 0.8}
    section.annotate("", xy=(-64, -56), xytext=(64, -56), arrowprops=dimension)
    section.text(0, -62, "128 m", ha="center", fontsize=11)
    section.annotate("", xy=(-73, 0), xytext=(-73, -48), arrowprops=dimension)
    section.text(-79, -24, "48 m", ha="center", va="center", rotation=90, fontsize=11)
    for depth in (0, -8, -16, -24, -32, -40, -48):
        section.text(67, depth, f"{depth} m", va="center", fontsize=9, color="#647578")

    legend = [Patch(facecolor=basin_color, label="Basin")]
    for index, color in enumerate(colors, start=1):
        legend.append(Patch(facecolor=color, label=f"Layer {index}"))
    figure.legend(handles=legend, loc="lower center", ncol=7, frameon=False,
                  bbox_to_anchor=(0.5, 0.055), handlelength=1.3, columnspacing=1.7)
    figure.text(0.5, 0.022, "Actual 4 m bricks  |  Muted mesh edges  |  Absorbing extension omitted",
                ha="center", fontsize=10, color="#647578")
    figure.subplots_adjust(left=0.025, right=0.975, bottom=0.16, top=0.91, wspace=0.04)
    figure.savefig(destination / "mesh.png", dpi=180, facecolor=background)
    plt.close(figure)
    print(f"Rendered {destination / 'mesh.png'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", action="store_true", help="Render the documentation mesh figure")
    parser.add_argument("--results-root", type=Path, default=Path("build"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--final-time", type=float, default=2.0)
    args = parser.parse_args()
    if args.mesh:
        output = args.output or Path(__file__).resolve().parents[2] / "website/docs/assets/examples/basin"
        render_mesh(output)
    else:
        generate_results(args.results_root, args.output or Path("example_outputs/basin/responses"), args.final_time)
