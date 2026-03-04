"""Module for managing and proxying spatial transformations.

This module re-exports key classes related to spatial transformation management
and mesh part transformation proxies for convenient access within the Femora
project.
"""
from .spatial_transform_manager import SpatialTransformManager
from .meshpart_transform_proxy import MeshPartTransform

__all__ = ["SpatialTransformManager", "MeshPartTransform"]