## DRM examples

This directory contains examples that demonstrate **Domain Reduction Method (DRM)** workflows in Femora.

Each subdirectory (`Example0`, `Example1`, …) is a self-contained example with its own `femoramodel.py` (and supporting scripts/plots) illustrating different aspects of DRM modelling and loading.

### Layered soil profile (used across the examples)
The layered domain is built from the same 6-layer profile in `Example0`/`Example1`/`Example2` (and reused as the background profile for the basin/SSI cases).

| Layer | Thickness (m) | ρ | Vₚ (m/s) | Vₛ (m/s) | ξₛ | ξₚ |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 2142.0500 | 669.0500 | 353.1000 | 0.0296 | 0.0148 |
| 2 | 8 | 2146.2000 | 785.2500 | 414.4000 | 0.0269 | 0.0134 |
| 3 | 8 | 2150.3500 | 886.0500 | 467.6000 | 0.0249 | 0.0125 |
| 4 | 8 | 2154.4500 | 976.4000 | 515.3000 | 0.0234 | 0.0117 |
| 5 | 8 | 2158.6000 | 1059.0500 | 558.9500 | 0.0221 | 0.0111 |
| 6 | 8 | 2162.7500 | 1135.6500 | 599.4000 | 0.0211 | 0.0105 |

### Structure
- **`Example0`**: Builds a layered soil column and drives it with **uniform excitation** under **laminar boundary conditions** (site-response style). It serves as the baseline for the layer profile used across the DRM studies.
- **`Example1`**: Generates a **DRM load inside Femora** using a transfer function (Ricker surface wavelet is deconvolved to bedrock motion). The script writes an **`h5drm`** file (created DRM load) and runs the model with absorbing boundaries.
- **`Example2`**: Runs the same layered domain using a pre-generated **H5DRM load** (`drmload.h5drm`). This example focuses on the “consume existing DRM load + simulate” workflow (absorbing layers are configured in the script).
- **`Example3`**: Extends the layered domain with a **semi-hemispherical elastic basin** (3D geometry created with external mesh parts) and runs a DRM-driven simulation.
- **`Example4`**: Builds on `Example3` by adding a **mat foundation** and a coupled **embedded-node interface** setup for the building/soil interaction, while keeping the basin as **soft elastic**.
- **`Example5`**: Builds on the mat-foundation case by adding the full **SSI building system** (mat + **dowels** + **pile cap/piles**) and using **embedded beam interfaces** to couple structural elements to the soil; basin response remains elastic.
- **`Example6`**: Repeats `Example3` but switches the basin material to a **nonlinear (plastic)** constitutive model.
- **`Example7`**: Repeats `Example4` but switches the basin material to a **nonlinear (plastic)** constitutive model, preserving the mat + embedded-node interface coupling.
- **`Example8`**: Repeats `Example5` but switches the basin material to a **nonlinear (plastic)** constitutive model, preserving the full SSI system with embedded beam interfaces.

### Running an example
From the repository root, run any example like this:

1. Change into the example directory (so `model.tcl` is written locally):
   - `cd examples/DRM/ExampleX`
2. Generate the OpenSees input (`model.tcl`):
   - `python femoramodel.py`
3. Run OpenSeesMP with MPI (from the same directory):
   - `ibrun/mpirun/mpi.exe -n $num_required_cores OpenSeesMP model.tcl`

Prerequisites / expected inputs:
- Some examples require DRM load inputs (for example an `h5drm` file). If an input file is needed, the README assumes you generate it from the related example (or place the required file into the run directory).

Outputs and helper scripts:
- Most examples write results under a `Results/` folder.
- Each example may include additional helper scripts (plots, movies, comparisons) to visualize or post-process the outputs; use the files in that example directory as needed.

