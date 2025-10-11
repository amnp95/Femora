"""
femora: Fast Efficient Meshing for OpenSees based Resilient Analysis
===================================================================

This package provides tools for creating and managing meshes for OpenSees simulations.

When imported as `import femora as fm`, the module itself acts as a MeshMaker instance,
allowing for direct access to all MeshMaker methods and properties.

Example usage:
-------------
```python
import femora as fm

# Create materials
material = fm.material.create_material(...)

# Create elements
element = fm.element.create_element(...)

# Create mesh parts
fm.meshPart.create_mesh_part(...)

# Assemble the mesh
fm.assembler.Assemble()
```
"""

from .components.MeshMaker import MeshMaker
from .components.Actions.action import ActionManager

# Create a MeshMaker instance to be used when importing the module
_instance = MeshMaker()

# Create an independent ActionManager instance
_action_manager = ActionManager()

# Export all attributes from the MeshMaker instance to the module level
for attr_name in dir(_instance):
    if attr_name.startswith('_'):
        continue
    # Avoid evaluating lazy properties at import time (e.g., mask)
    if attr_name == 'mask':
        continue
    globals()[attr_name] = getattr(_instance, attr_name)

# Make the instance's properties directly accessible from the module level
material = _instance.material
element = _instance.element
meshPart = _instance.meshPart
assembler = _instance.assembler
constraint = _instance.constraint
damping = _instance.damping
region = _instance.region
analysis = _instance.analysis
timeSeries = _instance.timeSeries
pattern = _instance.pattern
recorder = _instance.recorder
process = _instance.process
drm = _instance.drm
mesh_part = _instance.meshPart
transformation = _instance.transformation
section = _instance.section
interface = _instance.interface
mass = _instance.mass
spatial_transform = _instance.spatial_transform

set_results_folder = MeshMaker.set_results_folder



# Add actions as a separate direct property
actions = _action_manager

# Also expose the underlying MeshMaker class and instance
MeshMaker = MeshMaker
get_instance = MeshMaker.get_instance


def __getattr__(name):
    """
    Lazy attribute access for module-level conveniences.

    This avoids evaluating certain properties (like `mask`) at import time.
    """
    if name == 'mask':
        return _instance.mask
    raise AttributeError(f"module 'femora' has no attribute {name!r}")