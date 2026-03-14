from __future__ import annotations

import os
from pathlib import Path

__all__ = ["motions_dir"]


def motions_dir() -> Path:
    """
    Return the directory containing shared example input motions.

    Resolution order:
    1) Environment override via `FEMORA_MOTIONS_DIR`
    2) Repository-local default: `<repo>/examples/inputs/motions`

    Notes:
    - This helper is intended for *example scripts* shipped in this repository.
    - If Femora is installed from a wheel (no repo checkout), the repo-local
      default may not exist. In that case, set `FEMORA_MOTIONS_DIR`.
    """
    override = os.getenv("FEMORA_MOTIONS_DIR")
    if override:
        p = Path(override).expanduser()
        return p.resolve() if p.exists() else p

    # Package file: <repo>/src/femora/utils/paths.py  -> repo root is parents[3]
    repo_root = Path(__file__).resolve().parents[3]
    default = repo_root / "examples" / "inputs" / "motions"
    if default.exists():
        return default

    raise FileNotFoundError(
        "Could not locate the shared motions folder.\n"
        "Expected it at `examples/inputs/motions` (repo checkout), or set the\n"
        "environment variable `FEMORA_MOTIONS_DIR` to the motions directory."
    )

