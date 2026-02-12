from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Any
from femora.components.Material.materialBase import Material, MaterialManager
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager


class Element(ABC):
    """Base abstract class for all OpenSees finite elements.

    This class provides a foundation for creating and managing finite element
    objects in structural analysis. It handles automatic tag assignment, element
    registration, and dependency management for materials, sections, and
    geometric transformations.

    Attributes:
        tag: The unique sequential identifier for this element.
        element_type: The type of element (e.g., 'quad', 'truss', 'beam').
        _ndof: Number of degrees of freedom for the element.
        element_params: Dictionary of element-specific parameters.
        _material: Primary material assigned to this element.
        _materials: List of all materials assigned to this element.
        _section: Section assigned to this element (for section-based elements).
        _transformation: Geometric transformation assigned to this element (for beam elements).

    Example:
        >>> from femora.components.element.elementBase import Element
        >>> class TrussElement(Element):
        ...     def __init__(self, material, A: float):
        ...         super().__init__('truss', ndof=2, material=material, A=A)
        ...     @classmethod
        ...     def get_parameters(cls):
        ...         return ['A']
        ...     @classmethod
        ...     def get_possible_dofs(cls):
        ...         return ['ux', 'uy']
        ...     @classmethod
        ...     def get_description(cls):
        ...         return ['Cross-sectional area']
        ...     @classmethod
        ...     def validate_element_parameters(cls, **kwargs):
        ...         return kwargs
        ...     def get_values(self, keys):
        ...         return {k: self.element_params.get(k) for k in keys}
        ...     def update_values(self, values):
        ...         self.element_params.update(values)
        ...     def to_tcl(self, tag, nodes):
        ...         return f"element truss {tag} {nodes[0]} {nodes[1]} {self.element_params['A']} {self._material.tag}"
        >>> # Create material first
        >>> # truss = TrussElement(material=my_material, A=0.5)
        >>> # print(truss.tag)
    """
    _elements = {}  # Dictionary mapping tags to elements
    _element_to_tag = {}  # Dictionary mapping elements to their tags
    _next_tag = 1  # Track the next available tag

    def __init__(self, element_type: str,
                 ndof: int,
                 material: Union[Material, List[Material], None] = None,
                 section: Section = None,
                 transformation: GeometricTransformation = None,
                 **element_params
                 ):
        """Initializes the Element with flexible dependency support.

        Child classes handle validation of materials, sections, and transformations.

        Args:
            element_type: The type of element (e.g., 'quad', 'truss').
            ndof: Number of degrees of freedom for the element.
            material: Material(s) for the element. Can be a single Material,
                a list of Materials, or None.
            section: Section for section-based elements. Defaults to None.
            transformation: Transformation for beam elements. Defaults to None.
            **element_params: Element-specific parameters (thickness, body forces, etc.).
        """
        self.element_type = element_type
        self._ndof = ndof
        self.element_params = element_params

        # Store dependencies without validation (child classes handle validation)
        self._material = material
        self._section = section
        self._transformation = transformation

        # Handle multiple materials for list case
        if isinstance(material, list):
            self._materials = material
            self._material = material[0] if material else None  # Primary material
        else:
            self._materials = [material] if material else []

        # Assign the next available tag
        self.tag = self._next_tag
        Element._next_tag += 1

        # Register this element in both mapping dictionaries
        Element._elements[self.tag] = self
        Element._element_to_tag[self] = self.tag

    @classmethod
    def _retag_elements(cls):
        """Retags all elements sequentially from 1 to n based on their current order.

        This method rebuilds the element tracking dictionaries with new sequential
        tags while preserving the original creation order.
        """
        # Get all current elements sorted by their tags
        sorted_elements = sorted(cls._elements.items(), key=lambda x: x[0])

        # Clear existing mappings
        cls._elements.clear()
        cls._element_to_tag.clear()

        # Reassign tags sequentially
        for new_tag, (old_tag, element) in enumerate(sorted_elements, start=1):
            element.tag = new_tag
            cls._elements[new_tag] = element
            cls._element_to_tag[element] = new_tag

        # Update next available tag
        cls._next_tag = len(sorted_elements) + 1

    @classmethod
    def delete_element(cls, tag: int) -> None:
        """Deletes an element by its tag and retags remaining elements.

        This method removes an element from all tracking dictionaries and
        resequences all remaining elements to maintain sequential numbering.

        Args:
            tag: The tag of the element to delete.
        """
        if tag in cls._elements:
            element = cls._elements[tag]
            # Remove from both dictionaries
            del cls._elements[tag]
            del cls._element_to_tag[element]
            # Retag remaining elements
            cls._retag_elements()

    @classmethod
    def get_element_by_tag(cls, tag: int) -> Optional['Element']:
        """Gets an element by its tag.

        Args:
            tag: The tag to look up.

        Returns:
            The element with the given tag, or None if not found.
        """
        return cls._elements.get(tag)

    @classmethod
    def get_tag_by_element(cls, element: 'Element') -> Optional[int]:
        """Gets an element's tag.

        Args:
            element: The element to look up.

        Returns:
            The tag for the given element, or None if not found.
        """
        return cls._element_to_tag.get(element)

    @classmethod
    def set_tag_start(cls, start_number: int):
        """Sets the starting number for element tags and retags all existing elements.

        This method changes the starting tag number and adjusts all existing
        element tags by the appropriate offset.

        Args:
            start_number: The first tag number to use.
        """
        if not cls._elements:
            cls._next_tag = start_number
        else:
            offset = start_number - 1
            # Create new mappings with offset tags
            new_elements = {(tag + offset): element for tag, element in cls._elements.items()}
            new_element_to_tag = {element: (tag + offset) for element, tag in cls._element_to_tag.items()}

            # Update all element tags
            for element in cls._elements.values():
                element.tag += offset

            # Replace the mappings
            cls._elements = new_elements
            cls._element_to_tag = new_element_to_tag
            cls._next_tag = max(cls._elements.keys()) + 1

    @classmethod
    def get_all_elements(cls) -> Dict[int, 'Element']:
        """Retrieves all created elements.

        Returns:
            A dictionary of all elements, keyed by their unique tags.
        """
        return cls._elements

    @classmethod
    def clear_all_elements(cls):
        """Clears all elements and resets tag counter.

        This method removes all registered elements and resets the tag counter to 1.
        """
        cls._elements.clear()
        cls._element_to_tag.clear()
        cls._next_tag = 1

    def assign_material(self, material: Union[Material, List[Material]]):
        """Assigns a material to the element.

        Note: Child classes may override this to add validation.

        Args:
            material: The material(s) to assign. Can be a single Material
                or a list of Materials.
        """
        if isinstance(material, list):
            self._materials = material
            self._material = material[0] if material else None
        else:
            self._material = material
            self._materials = [material] if material else []

    def assign_section(self, section: Section):
        """Assigns a section to the element.

        Note: Child classes may override this to add validation.

        Args:
            section: The section to assign.
        """
        self._section = section

    def assign_transformation(self, transformation: GeometricTransformation):
        """Assigns a geometric transformation to the element.

        Note: Child classes may override this to add validation.

        Args:
            transformation: The transformation to assign.
        """
        self._transformation = transformation

    def assign_ndof(self, ndof: int):
        """Assigns the number of DOFs for the element.

        Args:
            ndof: Number of DOFs for the element.
        """
        self._ndof = ndof

    def get_material(self) -> Optional[Material]:
        """Retrieves the primary assigned material.

        Returns:
            The primary material assigned to this element, or None if not assigned.
        """
        return self._material

    def get_materials(self) -> List[Material]:
        """Retrieves all assigned materials.

        Returns:
            List of all materials assigned to this element.
        """
        return self._materials.copy()

    def get_section(self) -> Optional[Section]:
        """Retrieves the assigned section.

        Returns:
            The section assigned to this element, or None if not assigned.
        """
        return self._section

    def get_transformation(self) -> Optional[GeometricTransformation]:
        """Retrieves the assigned geometric transformation.

        Returns:
            The transformation assigned to this element, or None if not assigned.
        """
        return self._transformation

    def get_element_params(self) -> Dict[str, Any]:
        """Retrieves element-specific parameters.

        Returns:
            Dictionary of element-specific parameters.
        """
        return self.element_params.copy()

    def update_element_params(self, **new_params):
        """Updates element-specific parameters.

        Args:
            **new_params: New parameter values to update.
        """
        self.element_params.update(new_params)

    def get_ndof(self) -> int:
        """Gets the number of degrees of freedom for this element.

        Returns:
            Number of DOFs.
        """
        return self._ndof

    # Abstract methods for element implementation
    @classmethod
    @abstractmethod
    def get_parameters(cls) -> List[str]:
        """Gets the list of parameters for this element type.

        Subclasses must implement this method to define their parameter names.

        Returns:
            List of parameter names required for this element type.
        """
        pass

    @classmethod
    @abstractmethod
    def get_possible_dofs(cls) -> List[str]:
        """Gets the list of possible DOFs for this element type.

        Subclasses must implement this method to define which degrees of freedom
        are supported by the element.

        Returns:
            List of possible DOFs (e.g., ['ux', 'uy', 'uz', 'rx', 'ry', 'rz']).
        """
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> List[str]:
        """Gets the list of parameter descriptions for this element type.

        Subclasses must implement this method to provide parameter descriptions.
        The descriptions should correspond to the parameters from get_parameters()
        in the same order.

        Returns:
            List of parameter descriptions.
        """
        pass

    @classmethod
    @abstractmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Checks if the element input parameters are valid.

        Subclasses must implement this method to validate element-specific
        parameters before element creation.

        Args:
            **kwargs: Element parameters to validate.

        Returns:
            Dictionary of parameters with valid values.

        Raises:
            ValueError: If any parameter is invalid.
        """
        pass

    @abstractmethod
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters.

        Args:
            keys: List of parameter names to retrieve.

        Returns:
            Dictionary of parameter values for the requested keys.
        """
        pass

    @abstractmethod
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates element parameters.

        Args:
            values: Dictionary of parameter names and values to update.
        """
        pass

    @abstractmethod
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Converts the element to a TCL command string for OpenSees.

        Subclasses must implement this method to generate the appropriate
        TCL command for use with OpenSees.

        Args:
            tag: The tag of the element.
            nodes: List of node tags for the element.

        Returns:
            TCL command string representation of the element.
        """
        pass

    def __str__(self) -> str:
        """Returns string representation of the element.

        Returns:
            String showing element type, tag, and DOF count.
        """
        return f"{self.element_type} Element (Tag: {self.tag}, DOF: {self._ndof})"

    def __repr__(self) -> str:
        """Returns detailed string representation of the element.

        Returns:
            Detailed string showing all element properties and dependencies.
        """
        return f"Element(type='{self.element_type}', tag={self.tag}, ndof={self._ndof}, " \
               f"material={'Yes' if self._material else 'No'}, " \
               f"section={'Yes' if self._section else 'No'}, " \
               f"transformation={'Yes' if self._transformation else 'No'})"

    def get_section_tag(self) -> Optional[int]:
        """Gets the tag of the assigned section.

        Returns:
            The tag of the section, or 0 if not assigned.
        """
        return self._section.tag if self._section else 0

    def get_material_tag(self) -> Optional[int]:
        """Gets the tag of the primary assigned material.

        Returns:
            The tag of the primary material, or 0 if not assigned.
        """
        return self._material.tag if self._material else 0


    def get_mass_per_length(self) -> float:
        """Gets the mass per length of the element (useful for beam elements).
        

        Returns:
            The mass per length value, or 0.0 if not specified.
        """
        return 0.0
    
    def get_density(self) -> float:
        """Gets the density of the element.

        Returns:
            The density value, or 0.0 if not specified.
        """
        return 0.0

    



class ElementRegistry:
    """A singleton registry to manage element types and their creation.

    This class provides a centralized system for registering element classes
    and creating element instances dynamically with full dependency resolution.
    It automatically resolves material, section, and transformation references
    to their corresponding objects.

    Attributes:
        _instance: The singleton instance of ElementRegistry.
        _element_types: Class-level dictionary mapping element type names
            to their element classes.
        beam: Property providing access to beam element types.
        brick: Property providing access to brick element types.
        quad: Property providing access to quad element types.

    Example:
        >>> from femora.components.element.elementBase import ElementRegistry
        >>> # Register a custom element type
        >>> # ElementRegistry.register_element_type('my_truss', MyTrussElement)
        >>> # Create an element with automatic dependency resolution
        >>> # elem = ElementRegistry.create_element(
        >>> #     element_type='my_truss',
        >>> #     material='steel_material',  # Resolved automatically
        >>> #     A=0.5
        >>> # )
        >>> # Get available element types
        >>> types = ElementRegistry.get_element_types()
        >>> print(len(types) > 0)
        True
    """
    _instance = None
    _element_types = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ElementRegistry, cls).__new__(cls)
        return cls._instance

    @property
    def beam(self):
        """Provides access to beam element types.

        Returns:
            BeamElements accessor for creating beam elements.
        """
        from femora.core.element_manager import _BeamElements
        return _BeamElements

    @property
    def brick(self):
        """Provides access to brick element types.

        Returns:
            BrickElements accessor for creating brick elements.
        """
        from femora.core.element_manager import _BrickElements
        return _BrickElements
    @property
    def quad(self):
        """Provides access to quad element types.

        Returns:
            QuadElements accessor for creating quad elements.
        """
        from femora.core.element_manager import _QuadElements
        return _QuadElements

    @classmethod
    def register_element_type(cls, name: str, element_class: Type[Element]):
        """Registers a new element type for easy creation.

        Args:
            name: The name of the element type.
            element_class: The class of the element to register.
        """
        cls._element_types[name] = element_class

    @classmethod
    def unregister_element_type(cls, name: str):
        """Unregisters an element type.

        Args:
            name: The name of the element type to remove.
        """
        if name in cls._element_types:
            del cls._element_types[name]

    @classmethod
    def get_element_types(cls) -> List[str]:
        """Gets available element types.

        Returns:
            List of registered element type names.
        """
        return list(cls._element_types.keys())

    @classmethod
    def is_element_type_registered(cls, name: str) -> bool:
        """Checks if an element type is registered.

        Args:
            name: The element type name to check.

        Returns:
            True if registered, False otherwise.
        """
        return name in cls._element_types

    @classmethod
    def create_element(cls,
                       element_type: str,
                       **kwargs) -> Element:
        """Creates a new element of a specific type with full dependency resolution.

        This method automatically resolves material, section, and transformation
        references (by name or tag) to their corresponding objects before
        creating the element.

        Args:
            element_type: Type of element to create.
            **kwargs: All element parameters including ndof, material, section,
                transformation, and element-specific parameters.

        Returns:
            A new element instance.

        Raises:
            KeyError: If the element type is not registered.
            ValueError: If dependencies cannot be resolved.
        """
        if element_type not in cls._element_types:
            raise KeyError(f"Element type '{element_type}' not registered. "
                          f"Available types: {list(cls._element_types.keys())}")

        # Resolve dependencies
        resolved_kwargs = kwargs.copy()

        if 'material' in resolved_kwargs:
            resolved_kwargs['material'] = cls._resolve_materials(resolved_kwargs['material'])

        if 'section' in resolved_kwargs:
            resolved_kwargs['section'] = cls._resolve_section(resolved_kwargs['section'])

        if 'transformation' in resolved_kwargs:
            resolved_kwargs['transformation'] = cls._resolve_transformation(resolved_kwargs['transformation'])

        return cls._element_types[element_type](**resolved_kwargs)

    @classmethod
    def _resolve_materials(cls, material):
        """Resolves material references to actual Material objects.

        This method converts material identifiers (names or tags) to Material
        objects, supporting both single materials and lists of materials.

        Args:
            material: Material reference (str, int, Material, or list of these).

        Returns:
            Resolved material object(s) or None.

        Raises:
            ValueError: If a material reference cannot be resolved or has
                invalid type.
        """
        if material is None:
            return None

        if isinstance(material, list):
            # List of materials
            resolved_materials = []
            for i, mat in enumerate(material):
                if isinstance(mat, (str, int)):
                    resolved_mat = MaterialManager.get_material(mat)
                    if resolved_mat is None:
                        raise ValueError(f"Material {mat} at index {i} not found")
                    resolved_materials.append(resolved_mat)
                elif isinstance(mat, Material):
                    resolved_materials.append(mat)
                else:
                    raise ValueError(f"Invalid material type at index {i}: {type(mat)}")
            return resolved_materials

        elif isinstance(material, (str, int)):
            # Single material by reference
            resolved_material = MaterialManager.get_material(material)
            if resolved_material is None:
                raise ValueError(f"Material '{material}' not found")
            return resolved_material

        elif isinstance(material, Material):
            # Already a Material object
            return material

        else:
            raise ValueError(f"Invalid material type: {type(material)}")

    @classmethod
    def _resolve_section(cls, section):
        """Resolves section references to actual Section objects.

        This method converts section identifiers (names or tags) to Section objects.

        Args:
            section: Section reference (str, int, Section, or None).

        Returns:
            Resolved section object or None.

        Raises:
            ValueError: If a section reference cannot be resolved or has
                invalid type.
        """
        if section is None:
            return None

        if isinstance(section, (str, int)):
            resolved_section = SectionManager.get_section(section)
            if resolved_section is None:
                raise ValueError(f"Section '{section}' not found")
            return resolved_section
        elif isinstance(section, Section):
            return section
        else:
            raise ValueError(f"Invalid section type: {type(section)}")

    @classmethod
    def _resolve_transformation(cls, transformation):
        """Resolves transformation references to actual GeometricTransformation objects.

        This method converts transformation identifiers (names or tags) to
        GeometricTransformation objects.

        Args:
            transformation: Transformation reference (str, int,
                GeometricTransformation, or None).

        Returns:
            Resolved transformation object or None.

        Raises:
            ValueError: If a transformation reference cannot be resolved or
                has invalid type.
        """
        if transformation is None:
            return None

        if isinstance(transformation, (str, int)):
            resolved_transformation = GeometricTransformationManager.get_transformation(transformation)
            if resolved_transformation is None:
                raise ValueError(f"Transformation '{transformation}' not found")
            return resolved_transformation
        elif isinstance(transformation, GeometricTransformation):
            return transformation
        else:
            raise ValueError(f"Invalid transformation type: {type(transformation)}")

    @classmethod
    def get_element(cls, tag: int) -> Optional[Element]:
        """Gets an element by its tag.

        Args:
            tag: The tag of the element to retrieve.

        Returns:
            The element with the given tag, or None if not found.
        """
        return Element.get_element_by_tag(tag)

    @classmethod
    def get_element_count(cls) -> int:
        """Gets the total number of registered elements.

        Returns:
            Number of elements currently registered.
        """
        return len(Element.get_all_elements())

    @classmethod
    def clear_all_elements(cls):
        """Clears all elements.

        This method removes all registered elements and resets the element
        tag counter.
        """
        Element.clear_all_elements()


# Import existing element implementations
from femora.components.element import ssp_brick
from femora.components.element import ssp_quad
from femora.components.element import std_brick
from femora.components.element import pml_3d
from femora.components.element import asd_embedded_node
from femora.components.element import zero_length_contact
from femora.components.element import disp_beam_column
from femora.components.element import force_beam_column
from femora.components.element import elastic_beam_column
