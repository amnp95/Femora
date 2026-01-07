"""Public API for the mass management module.

This module provides an interface for managing mass properties within the
Femora project, exporting the primary `MassManager` class.
"""
from .mass_manager import MassManager

__all__ = ["MassManager"]