"""Module for defining and managing mesh parts in a DRM analysis application.

This module provides the core `MeshPart` abstract base class, which serves
as the foundation for all mesh entities within the Femora framework. It also
includes `MeshPartRegistry` for registering and creating specific mesh part
types, and `MeshPartManager` for advanced operations like filtering, grouping,
and batch management of mesh parts.

Classes:
    MeshPart: An abstract base class for defining various mesh components.
    MeshPartRegistry: Manages the registration and instanciation of mesh part types.
    MeshPartManager: Provides comprehensive management functionalities for mesh part instances.
"""

import numpy as np
import pyvista as pv
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Type, Union, Optional
from femora.core.element_base import Element
from femora.components.Material.materialBase import Material
from femora.components.Region.regionBase import RegionBase, GlobalRegion
from femora.constants import FEMORA_MAX_NDF
from femora.components.geometry_ops import MeshPartTransform

class MeshPart(ABC):
    """Abstract base class for mesh parts in a structural model.

    This class serves as the foundation for all mesh entities, defining
    common properties and abstract methods that concrete mesh part
    implementations must provide. It handles the assignment of unique tags,
    user-defined names, and associations with elements and regions.

    Attributes:
        category (str): General category of the mesh part (e.g., 'volume mesh', 'surface mesh').
        mesh_type (str): Specific type of mesh (e.g., 'Structured Rectangular Grid').
        user_name (str): The unique user-defined name for this mesh part.
        element (Element): The associated element for the mesh part.
        region (RegionBase): The associated region for the mesh part. Defaults to GlobalRegion.
        mesh (pv.UnstructuredGrid or None): The generated PyVista mesh object. None until `generate_mesh` is called.
        actor (pyvista.Actor or None): The PyVista actor associated with the mesh part for visualization.
        transform (MeshPartTransform): An instance for managing geometric transformations of the mesh part.
        tag (int): The unique integer identifier assigned to this mesh part.

    Example:
        >>> from femora.components.Mesh.meshPartBase import MeshPart
        >>> from femora.components.Element.elementBase import Element
        >>> from femora.components.Material.materialBase import Material
        >>> import pyvista as pv
        >>> # Define a minimal concrete subclass for demonstration
        >>> class ConcreteMeshPart(MeshPart):
        ...     _compatible_elements = ['stdBrick']
        ...     def generate_mesh(self):
        ...         self.mesh = pv.Cube() # Dummy mesh
        ...     @classmethod
        ...     def get_parameters(cls): return []
        ...     @classmethod
        ...     def validate_parameters(cls, **kwargs): return {}
        ...     def update_parameters(self, **kwargs): pass
        >>> dummy_material = Material('steel', 200e9, 0.3)
        >>> dummy_element = Element('stdBrick', 1, dummy_material)
        >>> mesh_part = ConcreteMeshPart('my_volume', dummy_element)
        >>> print(mesh_part.user_name)
        my_volume
        >>> print(mesh_part.tag)
        1
    """
    # Class-level tracking of mesh part names to ensure uniqueness
    _mesh_parts = {}
    _compatible_elements = []  # Base class empty list
    _next_tag = 1
    _tag_map = {}  # user_name -> tag

    def __init__(self, category: str, mesh_type: str, user_name: str, element: Element, region: RegionBase=None):
        """Initializes a MeshPart instance.

        Registers the new mesh part with a unique tag and name, and sets
        up its fundamental properties.

        Args:
            category: General category of the mesh part (e.g., 'volume mesh', 'surface mesh').
            mesh_type: Specific type of mesh (e.g., 'Structured Rectangular Grid').
            user_name: Unique user-defined name for the mesh part.
            element: The associated element for the mesh part.
            region: Optional. The associated region for the mesh part. If None,
                a global region is assigned.

        Raises:
            ValueError: If a mesh part with the same `user_name` already exists.
        """
        # Check for duplicate name
        if user_name in self._mesh_parts:
            raise ValueError(f"Mesh part with name '{user_name}' already exists")
        
        # Set basic properties
        self.category = category
        self.mesh_type = mesh_type
        self.user_name = user_name
        self.element = element
        self.region = region if region is not None else GlobalRegion()  # Use global region if none specified
        
        # Initialize mesh attribute (to be populated by generate_mesh)
        self.mesh = None
        
        # Optional pyvista actor (initially None)
        self.actor = None

        # Instance transform proxy for convenient geometry operations
        self.transform = MeshPartTransform(self)

        # Assign tag and register
        self.tag = MeshPart._next_tag
        MeshPart._tag_map[user_name] = self.tag
        MeshPart._mesh_parts[user_name] = self
        MeshPart._next_tag += 1

    @abstractmethod
    def generate_mesh(self) -> None:
        """Abstract method to generate the PyVista mesh for this part.

        This method should be implemented by concrete subclasses to create
        and assign a `pyvista.UnstructuredGrid` or similar PyVista mesh
        object to the `self.mesh` attribute.

        Args:
            **kwargs: Keyword arguments specific to mesh generation in a subclass.
        """
        pass

    @classmethod
    def get_mesh_parts(cls) -> Dict[str, 'MeshPart']:
        """Retrieves all currently registered mesh parts.

        Returns:
            A dictionary mapping `user_name` (str) to `MeshPart` instances.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts() # Ensure a clean slate for the example
            >>> part1 = ConcreteMeshPart('part_a', dummy_element)
            >>> part2 = ConcreteMeshPart('part_b', dummy_element)
            >>> parts = MeshPart.get_mesh_parts()
            >>> print(len(parts))
            2
            >>> print('part_a' in parts)
            True
        """
        return cls._mesh_parts

    @classmethod
    def delete_mesh_part(cls, user_name: str):
        """Deletes a mesh part by its user name and reassigns tags.

        This method removes the specified mesh part from the internal registry
        and re-indexes the tags of all remaining mesh parts to maintain
        contiguity, ensuring `_next_tag` is correctly updated.

        Args:
            user_name: User name of the mesh part to delete.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> part1 = ConcreteMeshPart('part_a', dummy_element) # tag 1
            >>> part2 = ConcreteMeshPart('part_b', dummy_element) # tag 2
            >>> part3 = ConcreteMeshPart('part_c', dummy_element) # tag 3
            >>> MeshPart.delete_mesh_part('part_b')
            >>> parts = MeshPart.get_mesh_parts()
            >>> print(len(parts))
            2
            >>> print('part_b' in parts)
            False
            >>> part_a_updated = parts['part_a']
            >>> part_c_updated = parts['part_c']
            >>> print(f"part_a tag: {part_a_updated.tag}")
            part_a tag: 1
            >>> print(f"part_c tag: {part_c_updated.tag}")
            part_c tag: 2
        """
        if user_name in cls._mesh_parts:
            del cls._mesh_parts[user_name]
            del cls._tag_map[user_name]
            # Reassign tags to all mesh parts to keep them contiguous
            for idx, (uname, part) in enumerate(sorted(cls._mesh_parts.items()), start=1):
                part.tag = idx
                cls._tag_map[uname] = idx
            cls._next_tag = len(cls._mesh_parts) + 1

    @classmethod
    def clear_all_mesh_parts(cls) -> None:
        """Deletes all mesh parts from the internal registry.

        This method iterates through all registered mesh parts and calls
        `delete_mesh_part` for each, effectively emptying the registry
        and resetting the tag counter.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> part1 = ConcreteMeshPart('part_a', dummy_element)
            >>> part2 = ConcreteMeshPart('part_b', dummy_element)
            >>> print(len(MeshPart.get_mesh_parts()))
            2
            >>> MeshPart.clear_all_mesh_parts()
            >>> print(len(MeshPart.get_mesh_parts()))
            0
        """
        # Create a copy of the keys to avoid modifying dictionary during iteration
        mesh_part_names = list(cls._mesh_parts.keys())
        for user_name in mesh_part_names:
            cls.delete_mesh_part(user_name)

    @classmethod
    @abstractmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """Abstract method to get the list of parameters for this mesh part type.

        Concrete subclasses must implement this to return a list of tuples,
        where each tuple contains the parameter name (str) and its type (str).

        Returns:
            A list of tuples, where each tuple contains (parameter_name, parameter_type_string).
        """
        pass

    @classmethod
    @abstractmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Abstract method to validate the input parameters for this mesh part type.

        Concrete subclasses must implement this to check the validity of provided
        parameters and return a dictionary of validated parameters.

        Args:
            **kwargs: Arbitrary keyword arguments representing parameters to validate.

        Returns:
            A dictionary of validated parameters with their corresponding valid values.
        """
        pass

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """Checks if a given element type is compatible with this mesh part.

        Compatibility is determined by checking if the provided `element` name
        (case-insensitive) is present in the `_compatible_elements` list defined
        by the concrete `MeshPart` subclass.

        Args:
            element: The element type name (e.g., 'stdBrick') to check.

        Returns:
            True if the element type is compatible, False otherwise.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick', 'triShell']
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> print(ConcreteMeshPart.is_elemnt_compatible('stdBrick'))
            True
            >>> print(ConcreteMeshPart.is_elemnt_compatible('trISheLL'))
            True
            >>> print(ConcreteMeshPart.is_elemnt_compatible('lineBeam'))
            False
        """
        return element.lower() in [e.lower() for e in cls._compatible_elements]

    @abstractmethod
    def update_parameters(self, **kwargs) -> None:
        """Abstract method to update the parameters of the mesh part.

        Concrete subclasses must implement this method to allow dynamic
        modification of mesh generation parameters without re-instantiation.

        Args:
            **kwargs: Keyword arguments representing the parameters to update.
        """
        pass

    
    def assign_material(self, material: Material) -> None:
        """Assigns a material to the underlying element of the mesh part.

        This method forwards the material assignment to the `element` associated
        with this mesh part.

        Args:
            material: The `Material` object to assign.

        Raises:
            ValueError: If the associated element's material attribute is currently
                `None`, indicating that a material cannot be assigned (or updated).

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> steel = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, steel) # Element already has steel
            >>> mesh_part = ConcreteMeshPart('my_part', dummy_element)
            >>> print(mesh_part.element.material.name)
            steel
            >>> aluminum = Material('aluminum', 70e9, 0.33)
            >>> mesh_part.assign_material(aluminum)
            >>> print(mesh_part.element.material.name)
            aluminum
        """
        if self.element.material is not None:
            self.element.assign_material(material)
        else:
            raise ValueError("No material to assign to the element")
    
    def assign_actor(self, actor) -> None:
        """Assigns a PyVista actor to the mesh part.

        This allows associating a visualization object directly with the mesh part,
        which can be useful for rendering and interaction in a PyVista scene.

        Args:
            actor: The PyVista actor object to assign.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> mesh_part = ConcreteMeshPart('my_part', dummy_element)
            >>> mesh_part.generate_mesh()
            >>> plotter = pv.Plotter(off_screen=True) # Use off_screen for testing
            >>> actor = plotter.add_mesh(mesh_part.mesh)
            >>> mesh_part.assign_actor(actor)
            >>> print(mesh_part.actor is not None)
            True
            >>> plotter.close()
        """
        self.actor = actor

    def _ensure_mass_array(self):
        """Creates an all-zero 'Mass' point_data array if it doesn't exist.

        The array has shape (n_points, FEMORA_MAX_NDF) and is initialized with
        float32 zeros. It is crucial that every MeshPart carries this 'Mass' array
        so that PyVista correctly merges point data during assembly operations.
        """
        if self.mesh is None:
            return
        if "Mass" not in self.mesh.point_data:
            n_pts = self.mesh.n_points
            self.mesh.point_data["Mass"] = np.zeros((n_pts, FEMORA_MAX_NDF), dtype=np.float32)

    def plot(self, **kwargs) -> None:
        """Plots the mesh part using PyVista.

        A PyVista plotter is initialized, the mesh is added, and then displayed.
        This method also ensures that a 'Mass' array is present in the mesh's
        point data before plotting.

        Args:
            **kwargs: Additional keyword arguments to pass to `pyvista.Plotter.add_mesh()`.

        Raises:
            ValueError: If the mesh has not been generated yet (i.e., `self.mesh` is None).

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> import pyvista as pv
            >>> class ConcreteMeshPart(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> mesh_part = ConcreteMeshPart('my_cube_part', dummy_element)
            >>> mesh_part.generate_mesh()
            >>> # To avoid GUI pop-ups during automated testing, one might run:
            >>> # mesh_part.plot(render=False)
            >>> # For interactive use:
            >>> # mesh_part.plot()
        """
        if self.mesh is None:
            raise ValueError("Mesh not generated yet. Call generate_mesh() first.")
        
        self._ensure_mass_array()
        
        plotter = pv.Plotter()
        plotter.add_mesh(self.mesh, **kwargs)
        plotter.show()

class MeshPartRegistry:
    """A singleton registry for managing different types of mesh parts.

    This class allows for the registration of concrete `MeshPart` subclasses
    under specific categories and types. It provides methods to retrieve
    available mesh part types and to create new instances of registered mesh parts.

    Attributes:
        _instance (MeshPartRegistry): The singleton instance of the registry.
        _mesh_part_types (dict[str, dict[str, Type[MeshPart]]]): A nested dictionary
            storing registered mesh part classes, organized by category and then by name.
            Initial categories include "Volume mesh", "Surface mesh", "Line mesh",
            "Point mesh", and "General mesh".

    Example:
        >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry, MeshPart
        >>> from femora.components.Element.elementBase import Element
        >>> from femora.components.Material.materialBase import Material
        >>> from femora.components.Region.regionBase import GlobalRegion
        >>> import pyvista as pv
        >>> # Define a sample concrete MeshPart for registration
        >>> class SimpleVolumeMesh(MeshPart):
        ...     _compatible_elements = ['stdBrick']
        ...     def __init__(self, user_name, element, region=None, width=1.0):
        ...         super().__init__('Volume mesh', 'Simple Box', user_name, element, region)
        ...         self.width = width
        ...     def generate_mesh(self):
        ...         self.mesh = pv.Cube(x_length=self.width, y_length=self.width, z_length=self.width)
        ...     @classmethod
        ...     def get_parameters(cls):
        ...         return [('width', 'float')]
        ...     @classmethod
        ...     def validate_parameters(cls, **kwargs):
        ...         return {'width': float(kwargs.get('width', 1.0))}
        ...     def update_parameters(self, **kwargs):
        ...         if 'width' in kwargs: self.width = float(kwargs['width'])
        >>>
        >>> registry = MeshPartRegistry()
        >>> registry.register_mesh_part_type('Volume mesh', 'Simple Box', SimpleVolumeMesh)
        >>> print('Simple Box' in registry.get_mesh_part_types('Volume mesh'))
        True
        >>> dummy_material = Material('steel', 200e9, 0.3)
        >>> dummy_element = Element('stdBrick', 1, dummy_material)
        >>> global_region = GlobalRegion()
        >>> my_mesh = registry.create_mesh_part('Volume mesh', 'Simple Box', 'my_box_1', dummy_element, global_region, width=2.0)
        >>> print(my_mesh.user_name)
        my_box_1
        >>> print(my_mesh.width)
        2.0
    """
    _instance = None
    _mesh_part_types = {
        "Volume mesh" : {},
        "Surface mesh" : {},
        "Line mesh" : {},
        "Point mesh" : {},
        "General mesh" : {}
    }

    def __new__(cls, *args, **kwargs):
        """Implements the singleton pattern for MeshPartRegistry.

        Ensures that only one instance of MeshPartRegistry exists throughout
        the application.
        """
        if cls._instance is None:
            cls._instance = super(MeshPartRegistry, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    @classmethod
    def register_mesh_part_type(cls, category: str ,name: str, mesh_part_class: Type[MeshPart]):
        """Registers a new concrete `MeshPart` subclass with the registry.

        The mesh part class is registered under a specific category and name,
        making it available for instantiation through the registry.

        Args:
            category: The general category for the mesh part (e.g., 'Volume mesh').
            name: The specific name of the mesh part type (e.g., 'Structured Rectangular Grid').
            mesh_part_class: The `MeshPart` subclass to register.

        Raises:
            KeyError: If the provided `category` is not a recognized category.
            KeyError: If a mesh part type with the given `name` already exists within the `category`.
            TypeError: If `mesh_part_class` is not a subclass of `MeshPart`.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry, MeshPart
            >>> class MyCustomMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> registry = MeshPartRegistry()
            >>> registry.register_mesh_part_type('General mesh', 'Custom Type 1', MyCustomMesh)
            >>> print('Custom Type 1' in registry.get_mesh_part_types('General mesh'))
            True
            >>> # This would raise a KeyError if run:
            >>> # registry.register_mesh_part_type('NonExistentCategory', 'Another Type', MyCustomMesh)
        """
        if category not in cls._mesh_part_types.keys():
            raise KeyError(f"Mesh part category {category} not registered")
        if name in cls._mesh_part_types[category]:
            raise KeyError(f"Mesh part type {name} already registered in {category}")
        if not issubclass(mesh_part_class, MeshPart):
            raise TypeError("Mesh part class must be a subclass of MeshPart")
        
        cls._mesh_part_types[category][name] = mesh_part_class
    
    @classmethod
    def get_mesh_part_types(cls, category: str) -> List[str]:
        """Retrieves a list of registered mesh part types within a specified category.

        Args:
            category: The category to query (e.g., 'Volume mesh').

        Returns:
            A list of strings, where each string is the name of a registered mesh part type.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry, MeshPart
            >>> class TypeA(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> class TypeB(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> registry = MeshPartRegistry()
            >>> registry.register_mesh_part_type('General mesh', 'TypeA', TypeA)
            >>> registry.register_mesh_part_type('General mesh', 'TypeB', TypeB)
            >>> types = registry.get_mesh_part_types('General mesh')
            >>> print(sorted(types))
            ['TypeA', 'TypeB']
            >>> print(registry.get_mesh_part_types('NonExistentCategory'))
            []
        """
        return list(cls._mesh_part_types.get(category, {}).keys())
    
    @classmethod
    def get_mesh_part_categories(cls) -> List[str]:
        """Retrieves a list of all registered mesh part categories.

        Returns:
            A list of strings, where each string is the name of a mesh part category.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry
            >>> registry = MeshPartRegistry()
            >>> categories = registry.get_mesh_part_categories()
            >>> print('Volume mesh' in categories)
            True
            >>> print(len(categories) > 0) # Should have initial categories
            True
        """
        return list(cls._mesh_part_types.keys())
    
    @classmethod
    def create_mesh_part(cls, category: str, mesh_part_type: str, user_name: str, element: Element, region: RegionBase, **kwargs) -> MeshPart:
        """Creates and returns an instance of a registered mesh part.

        This factory method instantiates a `MeshPart` subclass based on its
        registered category and type, passing along the required initialization
        arguments.

        Args:
            category: The category of the mesh part to create.
            mesh_part_type: The specific type name of the mesh part to create.
            user_name: A unique user-defined name for the new mesh part instance.
            element: The `Element` object to associate with the new mesh part.
            region: The `RegionBase` object to associate with the new mesh part.
            **kwargs: Additional keyword arguments specific to the `__init__` method
                of the target `MeshPart` subclass.

        Returns:
            A new instance of the specified `MeshPart` subclass.

        Raises:
            KeyError: If the `mesh_part_type` is not registered within the given `category`.
            ValueError: If a mesh part with the provided `user_name` already exists
                (raised by `MeshPart.__init__`).

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import GlobalRegion
            >>> import pyvista as pv
            >>> class DummyMesh(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def __init__(self, user_name, element, region=None, custom_param=10):
            ...         super().__init__('Volume mesh', 'Dummy', user_name, element, region)
            ...         self.custom_param = custom_param
            ...     def generate_mesh(self): self.mesh = pv.Cube()
            ...     @classmethod
            ...     def get_parameters(cls): return [('custom_param', 'int')]
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return kwargs
            ...     def update_parameters(self, **kwargs): pass
            >>> registry = MeshPartRegistry()
            >>> registry.register_mesh_part_type('Volume mesh', 'Dummy', DummyMesh)
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> global_region = GlobalRegion()
            >>> new_mesh_part = registry.create_mesh_part(
            ...     'Volume mesh', 'Dummy', 'my_dummy_mesh', dummy_element, global_region, custom_param=25
            ... )
            >>> print(new_mesh_part.user_name)
            my_dummy_mesh
            >>> print(new_mesh_part.custom_param)
            25
        """
        if mesh_part_type not in cls._mesh_part_types.get(category, {}):
            raise KeyError(f"Mesh part type {mesh_part_type} not registered in {category}")
        
        return cls._mesh_part_types[category][mesh_part_type](user_name, element, region,**kwargs)
    
    @staticmethod
    def get_mesh_part(user_name: str) -> MeshPart:
        """Retrieves a specific mesh part instance by its user-defined name.

        This static method directly queries the global `MeshPart` registry.

        Args:
            user_name: The unique user-defined name of the mesh part to retrieve.

        Returns:
            The `MeshPart` instance if found, otherwise `None`.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartRegistry, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class TempMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts() # Clean slate for example
            >>> part_a = TempMesh('get_example_part', dummy_element)
            >>> retrieved_part = MeshPartRegistry.get_mesh_part('get_example_part')
            >>> print(retrieved_part is part_a)
            True
            >>> not_found_part = MeshPartRegistry.get_mesh_part('non_existent_part')
            >>> print(not_found_part is None)
            True
        """
        return MeshPart._mesh_parts.get(user_name, None)


class MeshPartManager:
    """Advanced manager class for mesh parts with extended functionality.

    This class provides comprehensive mesh part management capabilities, including
    creation, retrieval, filtering, grouping, validation, and batch operations.
    It acts as a higher-level API, leveraging the `MeshPartRegistry` for core
    registration and instantiation, and providing additional management tools.

    Attributes:
        _instance (MeshPartManager): The singleton instance of the manager.
        _registry (MeshPartRegistry): The underlying registry for mesh part types.
        _last_operation_status (dict): A dictionary storing the success status and
            message of the most recent operation.

    Example:
        >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart, MeshPartRegistry
        >>> from femora.components.Element.elementBase import Element
        >>> from femora.components.Material.materialBase import Material
        >>> from femora.components.Region.regionBase import GlobalRegion
        >>> import pyvista as pv
        >>> # Define a sample concrete MeshPart for registration
        >>> class ManagerTestMesh(MeshPart):
        ...     _compatible_elements = ['stdBrick']
        ...     def __init__(self, user_name, element, region=None):
        ...         super().__init__('Volume mesh', 'Manager Test', user_name, element, region)
        ...     def generate_mesh(self):
        ...         self.mesh = pv.Sphere()
        ...     @classmethod
        ...     def get_parameters(cls): return []
        ...     @classmethod
        ...     def validate_parameters(cls, **kwargs): return {}
        ...     def update_parameters(self, **kwargs): pass
        >>>
        >>> MeshPart.clear_all_mesh_parts() # Ensure clean slate
        >>> manager = MeshPartManager()
        >>> registry = MeshPartRegistry()
        >>> registry.register_mesh_part_type('Volume mesh', 'Manager Test', ManagerTestMesh)
        >>> dummy_material = Material('steel', 200e9, 0.3)
        >>> dummy_element = Element('stdBrick', 1, dummy_material)
        >>> global_region = GlobalRegion()
        >>>
        >>> # Create a mesh part using the manager
        >>> mesh_part_a = manager.create_mesh_part(
        ...     'Volume mesh', 'Manager Test', 'my_sphere_A', dummy_element, global_region
        ... )
        >>> print(mesh_part_a.user_name)
        my_sphere_A
        >>> # Retrieve it
        >>> retrieved_part = manager.get_mesh_part('my_sphere_A')
        >>> print(retrieved_part is mesh_part_a)
        True
        >>> # Check operation status
        >>> print(manager._last_operation_status['success'])
        True
    """
    _instance = None
    
    def __new__(cls):
        """Implements the singleton pattern for MeshPartManager.

        Ensures that only one instance of MeshPartManager exists throughout
        the application.
        """
        if cls._instance is None:
            cls._instance = super(MeshPartManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initializes the MeshPartManager.

        This constructor is called only once due to the singleton pattern
        implemented in `__new__`. It sets up the internal `MeshPartRegistry`
        and initializes the status tracking for operations.
        """
        if not self._initialized:
            self._registry = MeshPartRegistry()
            self._last_operation_status = {"success": True, "message": ""}
            self._initialized = True

    @property
    def line(self):
        """Provides access to the LineMeshManager for line-specific mesh operations.

        Returns:
            The `LineMeshManager` class (not an instance).
        """
        from femora.components.Mesh.meshPartInstance import LineMeshManager
        return LineMeshManager
    
    @property
    def volume(self):
        """Provides access to the VolumeMeshManager for volume-specific mesh operations.

        Returns:
            The `VolumeMeshManager` class (not an instance).
        """
        from femora.components.Mesh.meshPartInstance import VolumeMeshManager
        return VolumeMeshManager
    
    def create_mesh_part(self, category: str, mesh_part_type: str, user_name: str, 
                        element: Element, region: RegionBase=None, **kwargs) -> MeshPart:
        """Creates a new mesh part instance with specified parameters.

        This method acts as a proxy to the `MeshPartRegistry`'s creation functionality,
        allowing the manager to track operation status.

        Args:
            category: Mesh part category (e.g., 'Volume mesh', 'Surface mesh').
            mesh_part_type: Specific type within the category.
            user_name: Unique user-defined name for the mesh part.
            element: The `Element` to associate with this mesh part.
            region: Optional. The `RegionBase` to associate with this mesh part.
                If None, `GlobalRegion` is used.
            **kwargs: Type-specific parameters for mesh part generation, passed directly
                to the `MeshPart` subclass constructor.

        Returns:
            The newly created `MeshPart` instance.

        Raises:
            KeyError: If the category or mesh part type is not registered.
            ValueError: If a mesh part with the provided `user_name` already exists.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart, MeshPartRegistry
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import GlobalRegion
            >>> import pyvista as pv
            >>> class ManagerCreateMesh(MeshPart):
            ...     _compatible_elements = ['stdBrick']
            ...     def __init__(self, user_name, element, region=None, size=1):
            ...         super().__init__('Volume mesh', 'Create Test', user_name, element, region)
            ...         self.size = size
            ...     def generate_mesh(self): self.mesh = pv.Cube(side=self.size)
            ...     @classmethod
            ...     def get_parameters(cls): return [('size', 'int')]
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return kwargs
            ...     def update_parameters(self, **kwargs): pass
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> registry = MeshPartRegistry()
            >>> registry.register_mesh_part_type('Volume mesh', 'Create Test', ManagerCreateMesh)
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> global_region = GlobalRegion()
            >>> new_part = manager.create_mesh_part(
            ...     'Volume mesh', 'Create Test', 'my_created_part', dummy_element, global_region, size=5
            ... )
            >>> print(new_part.user_name)
            my_created_part
            >>> print(new_part.size)
            5
        """
        try:
            mesh_part = self._registry.create_mesh_part(category, mesh_part_type, 
                                                      user_name, element, region, **kwargs)
            self._last_operation_status = {
                "success": True, 
                "message": f"Successfully created {category} mesh part '{user_name}'"
            }
            return mesh_part
        except Exception as e:
            self._last_operation_status = {"success": False, "message": str(e)}
            raise
    
    def get_mesh_part(self, user_name: str) -> Optional[MeshPart]:
        """Retrieves a mesh part instance by its user name.

        Args:
            user_name: User-defined name of the mesh part to retrieve.

        Returns:
            The requested `MeshPart` instance, or `None` if not found.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class DummyMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> part1 = DummyMesh('part_1', dummy_element)
            >>> retrieved = manager.get_mesh_part('part_1')
            >>> print(retrieved is part1)
            True
            >>> not_found = manager.get_mesh_part('non_existent')
            >>> print(not_found is None)
            True
        """
        mesh_part = self._registry.get_mesh_part(user_name)
        if mesh_part:
            self._last_operation_status = {
                "success": True, 
                "message": f"Retrieved mesh part '{user_name}'"
            }
        else:
            self._last_operation_status = {
                "success": False, 
                "message": f"Mesh part '{user_name}' not found"
            }
        return mesh_part
    
    def get_all_mesh_parts(self) -> Dict[str, MeshPart]:
        """Retrieves all registered mesh part instances.

        Returns:
            A dictionary mapping `user_name` (str) to `MeshPart` instances.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class DummyMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> part_x = DummyMesh('mesh_x', dummy_element)
            >>> part_y = DummyMesh('mesh_y', dummy_element)
            >>> all_parts = manager.get_all_mesh_parts()
            >>> print(len(all_parts))
            2
            >>> print('mesh_x' in all_parts and 'mesh_y' in all_parts)
            True
        """
        mesh_parts = MeshPart.get_mesh_parts()
        self._last_operation_status = {
            "success": True, 
            "message": f"Retrieved {len(mesh_parts)} mesh parts"
        }
        return mesh_parts
    
    def get_mesh_parts_by_category(self, category: str) -> Dict[str, MeshPart]:
        """Retrieves mesh part instances filtered by their category.

        Args:
            category: The category name (e.g., 'Volume mesh') to filter by.
                Comparison is case-insensitive.

        Returns:
            A dictionary mapping `user_name` (str) to `MeshPart` instances
            that belong to the specified category.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class VolumePart(MeshPart):
            ...     _compatible_elements = []
            ...     def __init__(self, user_name, element, region=None):
            ...         super().__init__('Volume mesh', 'Vol Type', user_name, element, region)
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> class SurfacePart(MeshPart):
            ...     _compatible_elements = []
            ...     def __init__(self, user_name, element, region=None):
            ...         super().__init__('Surface mesh', 'Surf Type', user_name, element, region)
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> vol_part = VolumePart('vol_1', dummy_element)
            >>> surf_part = SurfacePart('surf_1', dummy_element)
            >>> volume_meshes = manager.get_mesh_parts_by_category('Volume mesh')
            >>> print(len(volume_meshes))
            1
            >>> print('vol_1' in volume_meshes)
            True
            >>> surface_meshes = manager.get_mesh_parts_by_category('surface mesh') # Case-insensitive
            >>> print(len(surface_meshes))
            1
            >>> print('surf_1' in surface_meshes)
            True
        """
        mesh_parts = {name: part for name, part in MeshPart.get_mesh_parts().items() 
                     if part.category.lower() == category.lower()}
        self._last_operation_status = {
            "success": True, 
            "message": f"Retrieved {len(mesh_parts)} mesh parts in category '{category}'"
        }
        return mesh_parts
    
    def get_mesh_parts_by_region(self, region: Union[RegionBase, int]) -> Dict[str, MeshPart]:
        """Retrieves mesh part instances filtered by their associated region.

        Args:
            region: Either a `RegionBase` object or an integer representing the
                tag of the region to filter by.

        Returns:
            A dictionary mapping `user_name` (str) to `MeshPart` instances
            that are associated with the specified region.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> from femora.components.Region.regionBase import RegionBase, GlobalRegion
            >>> class RegionPart(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> MeshPart.clear_all_mesh_parts()
            >>> RegionBase.clear_all_regions() # Ensure clean slate for regions
            >>> manager = MeshPartManager()
            >>> region_a = RegionBase('RegionA') # tag 1
            >>> region_b = RegionBase('RegionB') # tag 2
            >>> part_in_a = RegionPart('part_in_A', Element('stdBrick', 1, dummy_material), region=region_a)
            >>> part_in_b = RegionPart('part_in_B', Element('stdBrick', 2, dummy_material), region=region_b)
            >>> part_global = RegionPart('part_global', Element('stdBrick', 3, dummy_material), region=GlobalRegion())
            >>>
            >>> meshes_in_a = manager.get_mesh_parts_by_region(region_a)
            >>> print(len(meshes_in_a))
            1
            >>> print('part_in_A' in meshes_in_a)
            True
            >>> meshes_in_b_by_tag = manager.get_mesh_parts_by_region(2) # Filter by region tag
            >>> print(len(meshes_in_b_by_tag))
            1
            >>> print('part_in_B' in meshes_in_b_by_tag)
            True
            >>> meshes_in_non_existent = manager.get_mesh_parts_by_region(99)
            >>> print(len(meshes_in_non_existent))
            0
        """
        # Handle case where region is provided as tag number
        if isinstance(region, int):
            region_tag = region
            region = RegionBase.get_region(region_tag)
            if not region:
                self._last_operation_status = {
                    "success": False, 
                    "message": f"Region with tag {region_tag} not found"
                }
                return {}
        
        mesh_parts = {name: part for name, part in MeshPart.get_mesh_parts().items() 
                     if part.region == region}
        self._last_operation_status = {
            "success": True, 
            "message": f"Retrieved {len(mesh_parts)} mesh parts in region '{region.name}'"
        }
        return mesh_parts
    
    def get_mesh_parts_by_element_type(self, element_type: str) -> Dict[str, MeshPart]:
        """Retrieves mesh part instances filtered by the type of their associated element.

        Args:
            element_type: The name of the element type (e.g., 'stdBrick') to filter by.

        Returns:
            A dictionary mapping `user_name` (str) to `MeshPart` instances
            whose associated `Element` matches the specified `element_type`.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class ElementTypePart(MeshPart):
            ...     _compatible_elements = ['stdBrick', 'lineBeam']
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> brick_elem = Element('stdBrick', 1, dummy_material)
            >>> beam_elem = Element('lineBeam', 2, dummy_material)
            >>> part_brick = ElementTypePart('brick_part', brick_elem)
            >>> part_beam = ElementTypePart('beam_part', beam_elem)
            >>>
            >>> brick_meshes = manager.get_mesh_parts_by_element_type('stdBrick')
            >>> print(len(brick_meshes))
            1
            >>> print('brick_part' in brick_meshes)
            True
            >>> beam_meshes = manager.get_mesh_parts_by_element_type('lineBeam')
            >>> print(len(beam_meshes))
            1
            >>> print('beam_part' in beam_meshes)
            True
            >>> unknown_meshes = manager.get_mesh_parts_by_element_type('quadShell')
            >>> print(len(unknown_meshes))
            0
        """
        mesh_parts = {name: part for name, part in MeshPart.get_mesh_parts().items() 
                     if part.element and part.element.element_type == element_type}
        self._last_operation_status = {
            "success": True, 
            "message": f"Retrieved {len(mesh_parts)} mesh parts with element type '{element_type}'"
        }
        return mesh_parts
    
    def delete_mesh_part(self, user_name: str) -> bool:
        """Deletes a mesh part instance by its user-defined name.

        This method removes the mesh part from the global registry and reassigns
        tags to maintain contiguity.

        Args:
            user_name: User-defined name of the mesh part to delete.

        Returns:
            True if the mesh part was successfully deleted, False if it was not found.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class DummyMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> part_to_delete = DummyMesh('to_delete', dummy_element)
            >>> print(manager.get_mesh_part('to_delete') is not None)
            True
            >>> success = manager.delete_mesh_part('to_delete')
            >>> print(success)
            True
            >>> print(manager.get_mesh_part('to_delete') is None)
            True
            >>> failure = manager.delete_mesh_part('non_existent')
            >>> print(failure)
            False
        """
        if user_name in MeshPart.get_mesh_parts():
            MeshPart.delete_mesh_part(user_name)
            self._last_operation_status = {
                "success": True, 
                "message": f"Deleted mesh part '{user_name}'"
            }
            return True
        else:
            self._last_operation_status = {
                "success": False, 
                "message": f"Mesh part '{user_name}' not found"
            }
            return False
    
    def clear_all_mesh_parts(self) -> None:
        """Deletes all mesh part instances from the registry.

        This operation effectively empties the entire mesh part collection managed
        by the application.

        Example:
            >>> from femora.components.Mesh.meshPartBase import MeshPartManager, MeshPart
            >>> from femora.components.Element.elementBase import Element
            >>> from femora.components.Material.materialBase import Material
            >>> class DummyMesh(MeshPart):
            ...     _compatible_elements = []
            ...     def generate_mesh(self): pass
            ...     @classmethod
            ...     def get_parameters(cls): return []
            ...     @classmethod
            ...     def validate_parameters(cls, **kwargs): return {}
            ...     def update_parameters(self, **kwargs): pass
            >>> dummy_material = Material('steel', 200e9, 0.3)
            >>> dummy_element = Element('stdBrick', 1, dummy_material)
            >>> MeshPart.clear_all_mesh_parts()
            >>> manager = MeshPartManager()
            >>> part_a = DummyMesh('a', dummy_element)
            >>> part_b = DummyMesh('b', dummy_element)
            >>> print(len(manager.get_all_mesh_parts()))
            2
            >>> manager.clear_all_mesh_parts()
            >>> print(len(manager.get_all_mesh_parts()))
            0
        """
        count = len(MeshPart.get_mesh_parts())
        MeshPart.clear_all_mesh_parts()
        self._last_operation_status = {
            "success": True, 
            "message": f"Cleared {count} mesh parts"
        }