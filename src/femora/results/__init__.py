# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Open, query, and visualize recorder output independently of a model."""

from .base import (
    CELL_FRAME,
    CELL_HISTORY,
    MESH,
    POINT_FRAME,
    POINT_HISTORY,
    ResultReader,
)
from .exceptions import ResultError, ResultFormatError, UnsupportedResultOperation
from .readers import VTKHDFResultReader
from .registry import reader_registry
from .result_set import PointSelection, ResultSet, open_results
from .visualization import DeformationRenderer
from .building import BuildingResults


reader_registry.register(
    "vtkhdf",
    VTKHDFResultReader,
    suffixes=".vtkhdf",
    replace=True,
)


def register_reader(name, reader, *, suffixes=(), replace=False):
    """Register a result reader for explicit and optional suffix dispatch."""
    reader_registry.register(
        name,
        reader,
        suffixes=suffixes,
        replace=replace,
    )


open = open_results

__all__ = [
    "BuildingResults",
    "CELL_FRAME",
    "CELL_HISTORY",
    "DeformationRenderer",
    "MESH",
    "POINT_FRAME",
    "POINT_HISTORY",
    "PointSelection",
    "ResultError",
    "ResultFormatError",
    "ResultReader",
    "ResultSet",
    "UnsupportedResultOperation",
    "VTKHDFResultReader",
    "open",
    "open_results",
    "register_reader",
    "reader_registry",
]
