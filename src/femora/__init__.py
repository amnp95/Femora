"""femora: Fast Efficient Meshing for OpenSees based Resilient Analysis.

This package provides tools for creating and managing meshes for OpenSees
simulations.

When imported as `import femora as fm`, the module itself acts as a MeshMaker
instance, allowing for direct access to all MeshMaker methods and properties.
This design simplifies API usage by flattening the object hierarchy for common
operations.

Attributes:
    material (MaterialManager): Manages the creation and retrieval of material
        properties for the simulation.
    element (ElementManager): Manages the creation and retrieval of element
        definitions.
    meshPart (MeshPartManager): Manages geometric mesh parts, including nodes
        and elements.
    assembler (Assembler): Provides methods for assembling the OpenSees model
        based on defined components.
    constraint (ConstraintManager): Manages boundary conditions and constraints
        for the model.
    damping (DampingManager): Manages damping properties and definitions.
    region (RegionManager): Manages geometric regions and their properties.
    analysis (AnalysisManager): Configures and runs the OpenSees analysis.
    timeSeries (TimeSeriesManager): Manages time series definitions for loads
        and ground motions.
    pattern (PatternManager): Manages load patterns and their application.
    recorder (RecorderManager): Manages output recorders for simulation results.
    process (ProcessManager): Manages simulation processes (e.g., parallel
        processing setup).
    drm (DRMManager): Manages Domain Reduction Method (DRM) functionalities.
    mesh_part (MeshPartManager): Alias for `meshPart`.
    transformation (TransformationManager): Manages coordinate transformations.
    section (SectionManager): Manages cross-section properties for elements.
    interface (InterfaceManager): Manages interface elements or properties.
    mass (MassManager): Manages mass properties for nodes or elements.
    spatial_transform (SpatialTransformManager): Manages spatial transformation
        definitions.
    set_results_folder (function): A static method from MeshMaker to set the
        global results directory.
    actions (ActionManager): An independent manager for tracking and replaying
        user actions.
    MeshMaker (type): The underlying MeshMaker class used to create the module-
        level instance.
    get_instance (function): A static method from MeshMaker to retrieve the
        current MeshMaker instance.

Example:
    >>> import femora as fm
    >>> # Create a material
    >>> material_obj = fm.material.create_material(
    ...     'ElasticIsotropic', tag=1, E=200e9, nu=0.3
    ... )
    >>> # Create an element
    >>> element_obj = fm.element.create_element(
    ...     'truss', tag=1, iNode=1, jNode=2, A=0.1, matTag=1
    ... )
    >>> # Create a mesh part (simplified example)
    >>> fm.meshPart.create_mesh_part(name='Column', node_tags=[1, 2, 3])
    >>> # Assemble the mesh
    >>> fm.assembler.Assemble()
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


def __getattr__(name: str):
    """Provides lazy attribute access for module-level conveniences.

    This method is called when an attribute is not found through the normal
    lookup procedures. It specifically handles the lazy loading of the 'mask'
    property from the internal MeshMaker instance, avoiding its evaluation
    at module import time.

    Args:
        name: The name of the attribute being accessed.

    Returns:
        The value of the requested attribute if it's 'mask' from the internal
        MeshMaker instance.

    Raises:
        AttributeError: If the requested attribute is not 'mask' and does not
            exist on the module.
    """
    if name == 'mask':
        return _instance.mask
    raise AttributeError(f"module 'femora' has no attribute {name!r}")