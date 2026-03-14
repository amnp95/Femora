
"""Femora components package.

This file also provides a small compatibility alias so legacy imports using
`femora.components.Partitioner` continue to work after the package was renamed
to `femora.components.partitioner`.
"""

from __future__ import annotations

import sys


def _install_partitioner_case_alias() -> None:
	try:
		from . import partitioner as _partitioner_pkg
		from .partitioner import partitioner as _partitioner_mod
	except Exception:
		return

	sys.modules.setdefault(__name__ + ".Partitioner", _partitioner_pkg)
	sys.modules.setdefault(__name__ + ".Partitioner.partitioner", _partitioner_mod)


_install_partitioner_case_alias()

