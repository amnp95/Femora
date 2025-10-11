"""Mask subsystem for post-assembly mesh queries.

Exposes:
- MeshIndex: immutable snapshot of the assembled mesh for fast queries
- NodeMask, ElementMask: typed masks with common filters and conversions
- MaskManager: entrypoint tied to the assembled mesh state
"""

from .mask_base import MeshIndex, NodeMask, ElementMask
from .mask_manager import MaskManager

__all__ = [
    "MeshIndex",
    "NodeMask",
    "ElementMask",
    "MaskManager",
]



