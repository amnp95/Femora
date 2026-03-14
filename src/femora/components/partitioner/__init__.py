"""Femora mesh partitioners.

The canonical partitioner implementation and registry live in
`femora.components.partitioner.partitioner`.
"""

from .partitioner import PartitionerError, PartitionerRegistry

__all__ = [
    "PartitionerError",
    "PartitionerRegistry",
]
