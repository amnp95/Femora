## Ground motion inputs

This folder contains **shared input motions** used by multiple example models.

- **`FrequencySweep.acc` / `FrequencySweep.time`**: frequency-sweep input motion.
- **`kobe.acc` / `kobe.time`**: Kobe earthquake record (acceleration + time vector).
- **`ricker_surface.acc` / `ricker_surface.time`**: Ricker wavelet surface motion used for deconvolution examples.

Examples reference these files by locating the repository root (via `pyproject.toml`) and building an absolute path to this folder.

