## Ground motion inputs

This folder contains **shared ground-motion time histories** used across multiple examples.

### What’s in here
- **`FrequencySweep.acc` / `FrequencySweep.time`**: Frequency-sweep input motion.
- **`kobe.acc` / `kobe.time`**: Kobe earthquake record (acceleration + time vector).
- **`ricker_surface.acc` / `ricker_surface.time`**: Ricker wavelet surface motion used for deconvolution examples.

### File format
Each motion is stored as a pair of files with the same basename:
- **`<name>.time`**: time values (typically one column).
- **`<name>.acc`**: acceleration values at the corresponding times (typically one column).

General expectations:
- **Length match**: `len(time) == len(acc)`.
- **Ordering**: time values should be **monotonically increasing**.
- **Units**: examples may assume specific units (e.g., seconds for time and \(m/s^2\) or \(g\) for acceleration). If you add a new record, keep units consistent with the example you’re using, or document unit assumptions alongside the record.

### Naming convention (recommended)
- Keep paired files together and use the same basename: `MyMotion.time` + `MyMotion.acc`.
- Prefer descriptive basenames (event name, component, processing tag), e.g. `kobe_NS.acc`.

### How examples locate this folder
Many examples resolve paths by finding the repository root (often via `pyproject.toml`) and then building an absolute path to this directory.

### Adding a new motion
- Add both `*.time` and `*.acc` files.
- Ensure the two files have the same number of samples and consistent sampling.
- If the record has special assumptions (units, filtering, scaling, component direction), add a short note here or include a small sidecar text file near the record.
