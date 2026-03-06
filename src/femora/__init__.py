"""Femora: Fast Efficient Meshing for OpenSees based Resilient Analysis.

This package provides tools for creating and managing meshes for OpenSees simulations.
When imported as `import femora as fm`, the module itself acts as a MeshMaker instance,
allowing direct access to all MeshMaker methods and properties.

Example:
    >>> import femora as fm
    >>> # Create a material definition
    >>> material_properties = {"name": "Concrete01", "fc": -4000, "fpc": -5000}
    >>> concrete_material = fm.material.create_material(
    ...     material_type="Concrete01",
    ...     properties=material_properties,
    ...     tag=1
    ... )
    >>> print(concrete_material.tag)
    1
    >>> # Access a lazily loaded property
    >>> print(fm.mask)
    <MeshMask instance at ...>
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
    """Lazily retrieves module-level attributes.

    This method provides lazy access for certain module-level properties (e.g., `mask`),
    avoiding their evaluation at module import time. For other attributes, it raises
    an `AttributeError` if the attribute is not explicitly defined or exported.

    Args:
        name: The name of the attribute to retrieve.

    Returns:
        The value of the requested attribute.

    Raises:
        AttributeError: If the attribute does not exist or is not supported for lazy
            retrieval.

    Example:
        >>> import femora as fm
        >>> # The 'mask' attribute is lazily loaded the first time it's accessed
        >>> mask_instance = fm.mask
        >>> print(type(mask_instance).__name__)
        MeshMask
        >>> # Attempting to access a non-existent attribute raises an error
        >>> try:
        ...     fm.non_existent_attribute
        ... except AttributeError as e:
        ...     print(e)
        module 'femora' has no attribute 'non_existent_attribute'
    """
    if name == 'mask':
        return _instance.mask
    raise AttributeError(f"module 'femora' has no attribute {name!r}")