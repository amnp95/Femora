"""Read the standalone frame's VTKHDF results and plot its responses."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from femora.results import BuildingResults

# Match the model script's output folder. The model need not be rebuilt.
case = Path("example_outputs/frame_earthquake_nonlinear")
show_plots = True

# --8<-- [start:read-results]
with BuildingResults.open(
    str(case / "results/response*.vtkhdf"),
    metadata=case / "building.structure.h5",
) as results:
    displacement = results.floor_displacement("x", relative_to_base=True)
    drift = results.interstory_drift("x")
    shear = results.base_shear("x")
    # --8<-- [end:read-results]

    pushover = results.metadata["abscissa"] == "load_factor"

    # --8<-- [start:export-results]
    responses = ["floor_displacement", "interstory_drift", "base_shear"]
    results.export_csv(case / "processed", responses=responses)

    summary = results.summary(responses=responses)
    summary.to_csv(case / "processed/summary.csv", index=False)
    # --8<-- [end:export-results]

    if not pushover:
        # Add ground acceleration once; it is zero after the supplied input ends.
        ground = np.loadtxt(case / "ground_motion.csv", delimiter=",", skiprows=1)
        time = np.unique(np.r_[ground[:, 0], results.raw.times])
        motion = np.interp(time, ground[:, 0], ground[:, 1], left=0, right=0)
        acceleration = results.floor_acceleration(
            "x",
            basis="absolute",
            ground_motion=(time, motion),
        )
        acceleration.to_csv(case / "processed/floor_absolute_acceleration.csv")

# Responses are DataFrames: select a floor, plot it, or export it directly.
if pushover:
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(displacement.iloc[:, -1] * 1000, shear.iloc[:, 0] / 1000)
    axis.set(xlabel="Roof displacement (mm)", ylabel="Base shear (MN)", title="Pushover")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(case / "pushover.png", dpi=180)
else:
    figure, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(acceleration.index, acceleration.iloc[:, -1])
    axes[0].set_ylabel("Roof absolute acceleration (m/s^2)")
    (drift * 100).plot(ax=axes[1])
    axes[1].set_ylabel("Interstory drift (%)")
    axes[1].legend(title="Story")
    axes[2].plot(shear.index, shear.iloc[:, 0] / 1000)
    axes[2].set(xlabel="Time (s)", ylabel="Base shear (MN)")
    for axis in axes:
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(case / "earthquake.png", dpi=180)

print(f"Plots and processed CSVs: {case.resolve()}")
if show_plots:
    plt.show()
else:
    plt.close("all")
