"""Enhanced Section Base Architecture for FEMORA with Material Resolution
Following the established patterns in the codebase with improved material handling
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Any
from femora.components.Material.materialBase import Material, MaterialManager


class Section(ABC):
    """Base abstract class for all sections with sequential tagging and material handling.

    This class provides a common interface and management for different types
    of structural sections within the Femora framework, including material
    resolution, section assignment, and global tracking.

    Attributes:
        tag (int): The unique integer identifier for this section.
        section_type (str): The general type of the section (e.g., 'Elastic', 'Fiber').
        section_name (str): The specific name of the section as used by OpenSees.
        user_name (str): A user-defined, unique name for this section.
        material (Optional[Material]): The material object assigned to this
            section, or None if no material is directly assigned.

    Example:
        >>> from femora.components.section.section_base import Section
        >>> # Dummy Material and MaterialManager for example
        >>> class MockMaterial:
        ...     def __init__(self, tag, user_name):
        ...         self.tag = tag
        ...         self.user_name = user_name
        >>> class MockMaterialManager:
        ...     _materials = {}
        ...     @classmethod
        ...     def get_material(cls, identifier):
        ...         if identifier in cls._materials:
        ...             return cls._materials[identifier]
        ...         raise KeyError(f"Material {identifier} not found")
        ...     @classmethod
        ...     def add_material(cls, material):
        ...         cls._materials[material.tag] = material
        ...         cls._materials[material.user_name] = material
        >>> # Assume Material and MaterialManager are correctly imported
        >>> # or mocked as above for demonstration.
        >>> class ConcreteSection(Section):
        ...     def __init__(self, user_name: str, material, depth: float):
        ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
        ...         self.assign_material(material)
        ...         self.depth = depth
        ...     def get_parameters(cls): return ["depth"]
        ...     def get_description(cls): return ["Section depth"]
        ...     def get_help_text(cls): return "A concrete section."
        ...     def validate_section_parameters(cls, **kwargs): return kwargs
        ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
        ...     def update_values(self, values): pass
        ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
        >>> mat1 = MockMaterial(1, "C30")
        >>> MockMaterialManager.add_material(mat1)
        >>> s1 = ConcreteSection(user_name="MyWall", material=mat1, depth=0.3)
        >>> print(s1.tag)
        1
        >>> print(s1.user_name)
        MyWall
        >>> print(s1.get_material().user_name)
        C30
    """
    _sections = {}      # Class-level dictionary to track all sections
    _sec_tags = {}      # Class-level dictionary to track section tags
    _names = {}         # Class-level dictionary to track section names
    _next_tag = 1       # Class variable to track the next tag to assign
    _start_tag = 1      # Class variable to track the starting tag number

    def __init__(self, section_type: str, section_name: str, user_name: str):
        """Initializes a new section with a sequential tag.

        Args:
            section_type: The general type of section (e.g., 'Elastic', 'Fiber', 'Aggregator').
            section_name: The specific section name as used by OpenSees.
            user_name: A user-specified unique name for the section.

        Raises:
            ValueError: If `user_name` already exists for another section.
        """
        if user_name in self._names:
            raise ValueError(f"Section name '{user_name}' already exists")

        self.tag = Section._next_tag
        Section._next_tag += 1

        self.section_type = section_type
        self.section_name = section_name
        self.user_name = user_name

        # Initialize material as None by default (sections without materials)
        self.material = None

        # Register this section
        self._sections[self.tag] = self
        self._sec_tags[self] = self.tag
        self._names[user_name] = self

    @staticmethod
    def resolve_material(material_input: Union[int, str, Material, None]) -> Optional[Material]:
        """Resolves a material object from various input types.

        This static method handles converting a material tag (int), material name (str),
        or a Material object itself into a consistent Material object.

        Args:
            material_input: The input to resolve. Can be:
                - An integer representing the material's tag.
                - A string representing the material's user-defined name.
                - A Material object instance.
                - None, indicating no material is required.

        Returns:
            The resolved Material object or None if `material_input` was None.

        Raises:
            ValueError: If the material cannot be found for the given tag or name,
                or if `material_input` is of an unsupported type.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and MockMaterialManager are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class MockMaterialManager:
            ...     _materials = {}
            ...     @classmethod
            ...     def get_material(cls, identifier):
            ...         if identifier in cls._materials:
            ...             return cls._materials[identifier]
            ...         raise KeyError(f"Material {identifier} not found")
            ...     @classmethod
            ...     def add_material(cls, material):
            ...         cls._materials[material.tag] = material
            ...         cls._materials[material.user_name] = material
            >>> mat_c30 = MockMaterial(tag=100, user_name="C30")
            >>> mat_s235 = MockMaterial(tag=101, user_name="S235")
            >>> MockMaterialManager.add_material(mat_c30)
            >>> MockMaterialManager.add_material(mat_s235)
            >>> resolved_by_tag = Section.resolve_material(100)
            >>> resolved_by_name = Section.resolve_material("S235")
            >>> resolved_by_object = Section.resolve_material(mat_c30)
            >>> print(resolved_by_tag.user_name)
            C30
            >>> print(resolved_by_name.tag)
            101
            >>> print(resolved_by_object.tag)
            100
            >>> print(Section.resolve_material(None))
            None
            >>> try:
            ...     Section.resolve_material("NonExistentMaterial")
            ... except ValueError as e:
            ...     print(e)
            Material not found: NonExistentMaterial. Error: 'NonExistentMaterial'
        """
        if material_input is None:
            return None

        if isinstance(material_input, Material):
            return material_input

        if isinstance(material_input, (int, str)):
            try:
                # Assuming MaterialManager is properly configured to resolve
                return MaterialManager.get_material(material_input)
            except (KeyError, TypeError) as e:
                raise ValueError(f"Material not found: {material_input}. Error: {str(e)}")

        raise ValueError(f"Invalid material input type: {type(material_input)}. "
                         f"Expected Material object, int (tag), str (name), or None")

    @staticmethod
    def resolve_materials_dict(materials_input: Dict[str, Union[int, str, Material]]) -> Dict[str, Material]:
        """Resolves a dictionary of material inputs into a dictionary of Material objects.

        This method iterates through a dictionary where values can be material tags,
        names, or objects, and resolves each into a Material object.

        Args:
            materials_input: A dictionary where keys are arbitrary identifiers
                and values are material inputs (int, str, or Material).

        Returns:
            A dictionary where keys are the same as `materials_input` and values
            are the resolved Material objects.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and MockMaterialManager are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class MockMaterialManager:
            ...     _materials = {}
            ...     @classmethod
            ...     def get_material(cls, identifier):
            ...         if identifier in cls._materials:
            ...             return cls._materials[identifier]
            ...         raise KeyError(f"Material {identifier} not found")
            ...     @classmethod
            ...     def add_material(cls, material):
            ...         cls._materials[material.tag] = material
            ...         cls._materials[material.user_name] = material
            >>> mat_c30 = MockMaterial(tag=100, user_name="C30")
            >>> mat_s235 = MockMaterial(tag=101, user_name="S235")
            >>> MockMaterialManager.add_material(mat_c30)
            >>> MockMaterialManager.add_material(mat_s235)
            >>> input_dict = {
            ...     "concrete": 100,
            ...     "steel": "S235"
            ... }
            >>> resolved_dict = Section.resolve_materials_dict(input_dict)
            >>> print(resolved_dict["concrete"].user_name)
            C30
            >>> print(resolved_dict["steel"].tag)
            101
        """
        resolved_materials = {}
        for key, material_input in materials_input.items():
            resolved_materials[key] = Section.resolve_material(material_input)
        return resolved_materials

    def assign_material(self, material_input: Union[int, str, Material, None]) -> None:
        """Assigns a material to this section.

        The input material can be an integer tag, a string name, or a Material object.
        It uses `resolve_material` to convert the input into a Material object and
        assigns it to the `material` attribute.

        Args:
            material_input: The material to assign. Can be an integer tag,
                a string name, a Material object, or None to clear the material.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and MockMaterialManager are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class MockMaterialManager:
            ...     _materials = {}
            ...     @classmethod
            ...     def get_material(cls, identifier):
            ...         if identifier in cls._materials:
            ...             return cls._materials[identifier]
            ...         raise KeyError(f"Material {identifier} not found")
            ...     @classmethod
            ...     def add_material(cls, material):
            ...         cls._materials[material.tag] = material
            ...         cls._materials[material.user_name] = material
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> s = ConcreteSection(user_name="ColumnBase")
            >>> mat_c30 = MockMaterial(tag=1, user_name="C30")
            >>> MockMaterialManager.add_material(mat_c30)
            >>> s.assign_material(mat_c30)
            >>> print(s.get_material().user_name)
            C30
            >>> s.assign_material(None)
            >>> print(s.get_material())
            None
        """
        self.material = self.resolve_material(material_input)

    def get_material(self) -> Optional[Material]:
        """Retrieves the material object assigned to this section.

        Returns:
            The Material object assigned to the section, or None if no
            material has been assigned.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and ConcreteSection are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str, material=None):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...         self.assign_material(material)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> mat_s235 = MockMaterial(tag=2, user_name="S235")
            >>> s = ConcreteSection(user_name="Beam", material=mat_s235)
            >>> print(s.get_material().user_name)
            S235
            >>> s_no_mat = ConcreteSection(user_name="NoMat")
            >>> print(s_no_mat.get_material())
            None
        """
        return self.material

    def has_material(self) -> bool:
        """Checks if this section has a material assigned.

        Returns:
            True if a material is assigned to the section, False otherwise.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and ConcreteSection are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str, material=None):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...         self.assign_material(material)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> mat_s235 = MockMaterial(tag=2, user_name="S235")
            >>> s = ConcreteSection(user_name="Beam", material=mat_s235)
            >>> print(s.has_material())
            True
            >>> s_no_mat = ConcreteSection(user_name="NoMat")
            >>> print(s_no_mat.has_material())
            False
        """
        return self.material is not None

    @classmethod
    def delete_section(cls, tag: int) -> None:
        """Deletes a section by its tag and automatically retags remaining sections.

        When a section is deleted, all existing sections are re-numbered
        sequentially starting from `_start_tag` to maintain tag continuity.

        Args:
            tag: The unique integer tag of the section to delete.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> s1 = ConcreteSection(user_name="C1") # tag 1
            >>> s2 = ConcreteSection(user_name="C2") # tag 2
            >>> s3 = ConcreteSection(user_name="C3") # tag 3
            >>> print([s.tag for s in Section.get_all_sections().values()])
            [1, 2, 3]
            >>> Section.delete_section(2) # Delete s2
            >>> print([s.tag for s in Section.get_all_sections().values()])
            [1, 2]
            >>> print(Section.get_section_by_name("C1").tag)
            1
            >>> print(Section.get_section_by_name("C3").tag) # s3 is now tag 2
            2
        """
        if tag in cls._sections:
            section_to_delete = cls._sections[tag]
            cls._names.pop(section_to_delete.user_name)
            cls._sec_tags.pop(section_to_delete)
            cls._sections.pop(tag)
            cls.retag_all()

    @classmethod
    def retag_all(cls):
        """Retags all registered sections sequentially.

        This method reassigns tags to all sections currently managed by the class,
        starting from `_start_tag` and incrementing by one for each section.
        It is typically called after a section deletion or when the starting tag
        number is changed.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> Section.clear_all_sections()
            >>> s1 = ConcreteSection(user_name="Alpha") # tag 1
            >>> s2 = ConcreteSection(user_name="Beta")  # tag 2
            >>> s3 = ConcreteSection(user_name="Gamma") # tag 3
            >>> print([s.tag for s in Section.get_all_sections().values()])
            [1, 2, 3]
            >>> # Manually change tag of s2 for demonstration of re-tagging
            >>> s2.tag = 99 # This breaks sequential order
            >>> Section._sections.pop(2) # Remove old entry
            >>> Section._sections[99] = s2 # Add new entry
            >>> Section._sec_tags.pop(s2)
            >>> Section._sec_tags[s2] = 99
            >>> Section.retag_all() # Re-tagging
            >>> print([s.tag for s in Section.get_all_sections().values()])
            [1, 2, 3]
            >>> print(Section.get_section_by_name("Beta").tag)
            2
        """
        sorted_sections = sorted(
            [(tag, section) for tag, section in cls._sections.items()],
            key=lambda x: x[0]
        )

        cls._sections.clear()
        cls._sec_tags.clear()

        for new_tag, (_, section) in enumerate(sorted_sections, start=cls._start_tag):
            section.tag = new_tag
            cls._sections[new_tag] = section
            cls._sec_tags[section] = new_tag

        cls._next_tag = cls._start_tag + len(cls._sections)

    @classmethod
    def get_all_sections(cls) -> Dict[int, 'Section']:
        """Retrieves a dictionary of all created sections.

        The dictionary maps section tags to their respective Section objects.

        Returns:
            A dictionary of all active sections, where keys are integer tags
            and values are Section instances.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> Section.clear_all_sections()
            >>> s1 = ConcreteSection(user_name="Column1")
            >>> s2 = ConcreteSection(user_name="Beam1")
            >>> all_secs = Section.get_all_sections()
            >>> print(len(all_secs))
            2
            >>> print(all_secs[s1.tag].user_name)
            Column1
        """
        return cls._sections

    @classmethod
    def get_section_by_tag(cls, tag: int) -> 'Section':
        """Retrieves a specific section by its unique integer tag.

        Args:
            tag: The unique integer tag of the section to retrieve.

        Returns:
            The Section object corresponding to the given tag.

        Raises:
            KeyError: If no section with the specified tag exists.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> Section.clear_all_sections()
            >>> s1 = ConcreteSection(user_name="ColumnA")
            >>> retrieved_s = Section.get_section_by_tag(s1.tag)
            >>> print(retrieved_s.user_name)
            ColumnA
            >>> try:
            ...     Section.get_section_by_tag(999)
            ... except KeyError as e:
            ...     print(e)
            'No section found with tag 999'
        """
        if tag not in cls._sections:
            raise KeyError(f"No section found with tag {tag}")
        return cls._sections[tag]

    @classmethod
    def get_section_by_name(cls, name: str) -> 'Section':
        """Retrieves a specific section by its user-specified name.

        Args:
            name: The unique user-specified name of the section to retrieve.

        Returns:
            The Section object corresponding to the given name.

        Raises:
            KeyError: If no section with the specified name exists.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> Section.clear_all_sections()
            >>> s1 = ConcreteSection(user_name="Footing_Section")
            >>> retrieved_s = Section.get_section_by_name("Footing_Section")
            >>> print(retrieved_s.tag)
            1
            >>> try:
            ...     Section.get_section_by_name("NonExistent")
            ... except KeyError as e:
            ...     print(e)
            'No section found with name NonExistent'
        """
        if name not in cls._names:
            raise KeyError(f"No section found with name {name}")
        return cls._names[name]

    @classmethod
    def clear_all_sections(cls):
        """Clears all registered sections and resets the tagging system.

        This method removes all sections from internal tracking dictionaries
        and resets `_next_tag` to `_start_tag`. Use with caution as it
        removes all section definitions.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> s1 = ConcreteSection(user_name="W1")
            >>> s2 = ConcreteSection(user_name="W2")
            >>> print(len(Section.get_all_sections()))
            2
            >>> Section.clear_all_sections()
            >>> print(len(Section.get_all_sections()))
            0
            >>> s3 = ConcreteSection(user_name="W3")
            >>> print(s3.tag) # Tagging restarts from _start_tag (default 1)
            1
        """
        cls._sections.clear()
        cls._sec_tags.clear()
        cls._names.clear()
        cls._next_tag = cls._start_tag

    @classmethod
    def set_start_tag(cls, start_number: int):
        """Sets the starting tag number for section tagging.

        This affects subsequent section creation and re-tagging operations.
        It also triggers an immediate re-tagging of all existing sections.

        Args:
            start_number: The integer tag number from which new sections should
                start being assigned.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume ConcreteSection is defined as in Section example
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> Section.clear_all_sections()
            >>> s1 = ConcreteSection(user_name="P1") # Tag 1
            >>> Section.set_start_tag(100)
            >>> s2 = ConcreteSection(user_name="P2") # Tag 101
            >>> print(s1.tag) # s1 is retagged
            100
            >>> print(s2.tag)
            101
        """
        cls._start_tag = start_number
        cls._next_tag = start_number
        cls.retag_all()

    @classmethod
    @abstractmethod
    def get_parameters(cls) -> List[str]:
        """Abstract method to get the list of parameters for this section type.

        Each concrete section implementation must define the parameters relevant
        to its definition (e.g., 'width', 'depth', 'fibers').

        Returns:
            A list of strings, where each string is the name of a parameter
            for this section type.
        """
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> List[str]:
        """Abstract method to get the list of parameter descriptions for this section type.

        Each concrete section implementation must provide a concise description
        for each parameter returned by `get_parameters`.

        Returns:
            A list of strings, where each string is a description corresponding
            to a parameter in `get_parameters`.
        """
        pass

    @classmethod
    @abstractmethod
    def get_help_text(cls) -> str:
        """Abstract method to get the formatted help text for this section type for GUI display.

        This method should return a user-friendly string explaining the section type
        and its usage, often used in a graphical user interface.

        Returns:
            A string containing comprehensive help information for the section.
        """
        pass

    @classmethod
    @abstractmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Abstract method to validate section input parameters.

        This method should be implemented by concrete section classes to
        check if the provided parameters are valid for creating or updating
        an instance of that section type.

        Args:
            **kwargs: Arbitrary keyword arguments representing section parameters.

        Returns:
            A dictionary of validated parameters, possibly with default values applied.
        """
        pass

    @abstractmethod
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Abstract method to retrieve values for specific parameters of this section instance.

        Args:
            keys: A list of strings, where each string is the name of a parameter
                whose value is to be retrieved.

        Returns:
            A dictionary mapping parameter names to their current values for
            this section instance.
        """
        pass

    @abstractmethod
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Abstract method to update section parameters.

        This method should be implemented to allow modifying the properties
        of an existing section instance.

        Args:
            values: A dictionary where keys are parameter names and values are
                the new values to assign to those parameters.
        """
        pass

    @abstractmethod
    def to_tcl(self) -> str:
        """Abstract method to convert the section to a TCL string representation for OpenSees.

        Each concrete section must provide a method to generate the corresponding
        TCL command string that OpenSees can interpret to define the section.

        Returns:
            A string representing the TCL command to define this section in OpenSees.
        """
        pass

    def get_materials(self) -> List[Material]:
        """Gets all materials used directly by this section instance.

        This method is primarily for dependency tracking and typically returns
        the single material assigned via `assign_material`. More complex sections
        (e.g., Fiber sections) would override this to return multiple materials.

        Returns:
            A list of Material objects directly associated with this section.
            Returns an empty list if no material is assigned.

        Example:
            >>> from femora.components.section.section_base import Section
            >>> # Assume MockMaterial and ConcreteSection are defined as in Section example
            >>> class MockMaterial:
            ...     def __init__(self, tag, user_name):
            ...         self.tag = tag
            ...         self.user_name = user_name
            ...     def __eq__(self, other): return self.tag == other.tag
            ...     def __hash__(self): return hash(self.tag)
            >>> class ConcreteSection(Section):
            ...     def __init__(self, user_name: str, material=None):
            ...         super().__init__("Concrete", "ConcreteSection1D", user_name)
            ...         self.assign_material(material)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A concrete section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section ConcreteSection {self.tag}"
            >>> mat_c30 = MockMaterial(tag=1, user_name="C30")
            >>> s_with_mat = ConcreteSection(user_name="Col", material=mat_c30)
            >>> s_no_mat = ConcreteSection(user_name="Beam")
            >>> print([m.user_name for m in s_with_mat.get_materials()])
            ['C30']
            >>> print(s_no_mat.get_materials())
            []
        """
        if self.material is not None:
            return [self.material]
        return []

    def __str__(self) -> str:
        """Provides a human-readable string representation of the section.

        Returns:
            A string detailing the section's user name, tag, type, and
            assigned material (if any).
        """
        material_info = f", Material: {self.material.user_name}" if self.material else ", No Material"
        return (f"Section '{self.user_name}' (Tag: {self.tag}, Type: {self.section_name}"
                f"{material_info})")


class SectionRegistry:
    """Registry to manage section types and their creation.

    This class provides a centralized mechanism for registering concrete
    `Section` subclasses and creating instances of those registered types
    dynamically.

    Attributes:
        _section_types (Dict[str, Type[Section]]): A class-level dictionary
            mapping section type names (strings) to their corresponding
            `Section` class objects.

    Example:
        >>> from femora.components.section.section_base import Section, SectionRegistry
        >>> class CustomSection(Section):
        ...     def __init__(self, user_name: str, area: float):
        ...         super().__init__("Custom", "MyCustomSection", user_name)
        ...         self.area = area
        ...     def get_parameters(cls): return ["area"]
        ...     def get_description(cls): return ["Section area"]
        ...     def get_help_text(cls): return "A custom section type."
        ...     def validate_section_parameters(cls, **kwargs): return kwargs
        ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
        ...     def update_values(self, values): pass
        ...     def to_tcl(self): return f"section CustomSection {self.tag} {self.area}"
        >>> SectionRegistry.register_section_type("Custom", CustomSection)
        >>> section_types = SectionRegistry.get_section_types()
        >>> print("Custom" in section_types)
        True
        >>> my_custom_section = SectionRegistry.create_section(
        ...     section_type="Custom",
        ...     user_name="MyUniqueCustomSection",
        ...     area=10.5
        ... )
        >>> print(my_custom_section.user_name)
        MyUniqueCustomSection
        >>> print(my_custom_section.area)
        10.5
    """
    _section_types = {}

    @classmethod
    def register_section_type(cls, name: str, section_class: Type[Section]):
        """Registers a new section type for easy creation.

        This allows new `Section` subclasses to be added to the registry
        and subsequently created via their string name.

        Args:
            name: The string identifier for the section type (e.g., "Elastic", "Fiber").
            section_class: The `Section` subclass to register.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry
            >>> class SquareSection(Section):
            ...     def __init__(self, user_name: str, side: float):
            ...         super().__init__("Square", "SquareSection", user_name)
            ...         self.side = side
            ...     def get_parameters(cls): return ["side"]
            ...     def get_description(cls): return ["Side length"]
            ...     def get_help_text(cls): return "A square section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Square {self.tag} {self.side}"
            >>> SectionRegistry.register_section_type("Square", SquareSection)
            >>> print("Square" in SectionRegistry.get_section_types())
            True
        """
        cls._section_types[name] = section_class

    @classmethod
    def get_section_types(cls) -> List[str]:
        """Retrieves a list of all available registered section type names.

        Returns:
            A list of strings, where each string is the name of a registered
            section type.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry
            >>> class CircleSection(Section):
            ...     def __init__(self, user_name: str, radius: float):
            ...         super().__init__("Circle", "CircleSection", user_name)
            ...         self.radius = radius
            ...     def get_parameters(cls): return ["radius"]
            ...     def get_description(cls): return ["Radius"]
            ...     def get_help_text(cls): return "A circular section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Circle {self.tag} {self.radius}"
            >>> SectionRegistry.register_section_type("Circle", CircleSection)
            >>> types = SectionRegistry.get_section_types()
            >>> print("Circle" in types)
            True
        """
        return list(cls._section_types.keys())

    @classmethod
    def create_section(cls, section_type: str, user_name: str = "Unnamed", **kwargs) -> Section:
        """Creates a new section of a specific type.

        This method instantiates a `Section` object based on the registered
        `section_type` and passes `user_name` and any additional `kwargs`
        to its constructor.

        Args:
            section_type: The string name of the section type to create (must be registered).
            user_name: Optional. A user-defined unique name for the new section.
                Defaults to "Unnamed".
            **kwargs: Additional keyword arguments specific to the constructor
                of the target `Section` subclass.

        Returns:
            An instance of the specified `Section` subclass.

        Raises:
            KeyError: If the `section_type` is not registered.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry
            >>> class RectSection(Section):
            ...     def __init__(self, user_name: str, width: float, height: float):
            ...         super().__init__("Rectangle", "RectSection", user_name)
            ...         self.width = width
            ...         self.height = height
            ...     def get_parameters(cls): return ["width", "height"]
            ...     def get_description(cls): return ["Width", "Height"]
            ...     def get_help_text(cls): return "A rectangular section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Rect {self.tag} {self.width} {self.height}"
            >>> SectionRegistry.register_section_type("Rectangle", RectSection)
            >>> my_rect = SectionRegistry.create_section(
            ...     section_type="Rectangle",
            ...     user_name="FoundationBeam",
            ...     width=0.4,
            ...     height=0.8
            ... )
            >>> print(my_rect.user_name)
            FoundationBeam
            >>> print(my_rect.width)
            0.4
            >>> try:
            ...     SectionRegistry.create_section("NonExistent", "Test")
            ... except KeyError as e:
            ...     print(e)
            'Section type NonExistent not registered'
        """
        if section_type not in cls._section_types:
            raise KeyError(f"Section type {section_type} not registered")

        return cls._section_types[section_type](user_name=user_name, **kwargs)


class SectionManager:
    """Singleton class for managing sections, following the same pattern as MaterialManager.

    This manager provides a convenient high-level interface for creating,
    retrieving, and managing all `Section` instances within the application.
    It leverages `SectionRegistry` for section creation and `Section` class
    methods for global management.

    Attributes:
        _instance (Optional[SectionManager]): The singleton instance of the manager.
        elastic (Type[Section]): Shortcut to the ElasticSection class.
        fiber (Type[Section]): Shortcut to the FiberSection class.
        aggregator (Type[Section]): Shortcut to the AggregatorSection class.
        uniaxial (Type[Section]): Shortcut to the UniaxialSection class.
        wf2d (Type[Section]): Shortcut to the WFSection2d class.
        plate_fiber (Type[Section]): Shortcut to the PlateFiberSection class.
        elastic_membrane_plate (Type[Section]): Shortcut to the ElasticMembranePlateSection class.
        rc (Type[Section]): Shortcut to the RCSection class.
        parallel (Type[Section]): Shortcut to the ParallelSection class.
        bidirectional (Type[Section]): Shortcut to the BidirectionalSection class.
        isolator (Type[Section]): Shortcut to the Isolator2SpringSection class.

    Example:
        >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
        >>> # Dummy section type for example
        >>> class SimpleElasticSection(Section):
        ...     def __init__(self, user_name: str, E: float, I: float):
        ...         super().__init__("Elastic", "SimpleElastic", user_name)
        ...         self.E = E
        ...         self.I = I
        ...     def get_parameters(cls): return ["E", "I"]
        ...     def get_description(cls): return ["Elastic Modulus", "Moment of Inertia"]
        ...     def get_help_text(cls): return "A simple elastic section."
        ...     def validate_section_parameters(cls, **kwargs): return kwargs
        ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
        ...     def update_values(self, values): pass
        ...     def to_tcl(self): return f"section Elastic {self.tag} {self.E} {self.I}"
        >>> SectionRegistry.register_section_type("Elastic", SimpleElasticSection)
        >>> sm = SectionManager.get_instance()
        >>> sm.clear_all_sections() # Clear previous example sections
        >>> s1 = sm.create_section("Elastic", "BeamSection", E=200e9, I=1e-3)
        >>> s2 = sm.create_section("Elastic", "ColumnSection", E=200e9, I=2e-3)
        >>> print(s1.user_name)
        BeamSection
        >>> retrieved_s2 = sm.get_section("ColumnSection")
        >>> print(retrieved_s2.tag)
        2
        >>> sm.delete_section(1)
        >>> print(len(sm.get_all_sections()))
        1
        >>> print(sm.get_all_sections()[1].user_name) # ColumnSection is now tag 1
        ColumnSection
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SectionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initializes the singleton instance of SectionManager.

        This method dynamically imports various concrete section classes from
        `femora.components.section.section_opensees` and sets them as attributes
        of the manager for easy access.
        """
        # Direct access to section_opensees module
        from femora.components.section.section_opensees import ElasticSection, FiberSection, AggregatorSection, UniaxialSection, WFSection2d, PlateFiberSection,ElasticMembranePlateSection , RCSection, ParallelSection,  BidirectionalSection, Isolator2SpringSection
        self.elastic = ElasticSection
        self.fiber = FiberSection
        self.aggregator = AggregatorSection
        self.uniaxial = UniaxialSection
        self.wf2d = WFSection2d
        self.plate_fiber = PlateFiberSection
        self.elastic_membrane_plate = ElasticMembranePlateSection
        self.rc = RCSection
        self.parallel = ParallelSection
        self.bidirectional = BidirectionalSection
        self.isolator = Isolator2SpringSection

    def create_section(self, section_type: str, user_name: str, **section_params) -> Section:
        """Creates a new section with the given parameters using the SectionRegistry.

        Args:
            section_type: The string name of the section type to create.
            user_name: A user-defined unique name for the new section.
            **section_params: Additional keyword arguments required for the
                constructor of the specific section type.

        Returns:
            An instance of the created `Section` subclass.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class SimpleRectSection(Section):
            ...     def __init__(self, user_name: str, width: float, height: float):
            ...         super().__init__("Rectangle", "RectSection", user_name)
            ...         self.width = width
            ...         self.height = height
            ...     def get_parameters(cls): return ["width", "height"]
            ...     def get_description(cls): return ["Width", "Height"]
            ...     def get_help_text(cls): return "A simple rectangular section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {k: getattr(self, k) for k in keys}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Rect {self.tag} {self.width} {self.height}"
            >>> SectionRegistry.register_section_type("Rectangle", SimpleRectSection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections()
            >>> my_section = sm.create_section("Rectangle", "MainBeam", width=0.3, height=0.6)
            >>> print(my_section.user_name)
            MainBeam
            >>> print(my_section.width)
            0.3
        """
        return SectionRegistry.create_section(
            section_type=section_type,
            user_name=user_name,
            **section_params
        )

    @staticmethod
    def get_section(identifier: Union[int, str]) -> Section:
        """Retrieves a section by either its integer tag or user-defined name.

        Args:
            identifier: The unique identifier for the section, which can be
                its integer tag or its string user-defined name.

        Returns:
            The `Section` object matching the identifier.

        Raises:
            TypeError: If the `identifier` is not an int or a string.
            KeyError: If no section is found with the given tag or name.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class DummySection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Dummy", "DummySection", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A dummy section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Dummy {self.tag}"
            >>> SectionRegistry.register_section_type("Dummy", DummySection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections()
            >>> s1 = sm.create_section("Dummy", "SectionA") # Tag 1
            >>> s2 = sm.create_section("Dummy", "SectionB") # Tag 2
            >>> sec_by_tag = SectionManager.get_section(1)
            >>> sec_by_name = SectionManager.get_section("SectionB")
            >>> print(sec_by_tag.user_name)
            SectionA
            >>> print(sec_by_name.tag)
            2
            >>> try:
            ...     SectionManager.get_section(999)
            ... except KeyError as e:
            ...     print(e)
            'No section found with tag 999'
            >>> try:
            ...     SectionManager.get_section([])
            ... except TypeError as e:
            ...     print(e)
            Identifier must be either tag (int) or name (str)
        """
        if isinstance(identifier, int):
            return Section.get_section_by_tag(identifier)
        elif isinstance(identifier, str):
            return Section.get_section_by_name(identifier)
        else:
            raise TypeError("Identifier must be either tag (int) or name (str)")

    def get_all_sections(self) -> Dict[int, Section]:
        """Retrieves a dictionary of all currently registered sections.

        Returns:
            A dictionary where keys are section tags (int) and values are
            `Section` objects.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class DummySection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Dummy", "DummySection", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A dummy section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Dummy {self.tag}"
            >>> SectionRegistry.register_section_type("Dummy", DummySection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections()
            >>> s1 = sm.create_section("Dummy", "FloorBeam")
            >>> s2 = sm.create_section("Dummy", "RoofSlab")
            >>> all_sections = sm.get_all_sections()
            >>> print(len(all_sections))
            2
            >>> print(all_sections[1].user_name)
            FloorBeam
        """
        return Section.get_all_sections()

    def delete_section(self, identifier: Union[int, str]) -> None:
        """Deletes a section by its identifier (tag or name).

        After deletion, all remaining sections are automatically retagged
        sequentially.

        Args:
            identifier: The unique identifier (tag or name) of the section
                to delete.

        Raises:
            TypeError: If the `identifier` is not an int or a string.
            KeyError: If no section is found with the given identifier.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class DummySection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Dummy", "DummySection", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A dummy section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Dummy {self.tag}"
            >>> SectionRegistry.register_section_type("Dummy", DummySection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections()
            >>> s1 = sm.create_section("Dummy", "SecA") # Tag 1
            >>> s2 = sm.create_section("Dummy", "SecB") # Tag 2
            >>> s3 = sm.create_section("Dummy", "SecC") # Tag 3
            >>> print([s.tag for s in sm.get_all_sections().values()])
            [1, 2, 3]
            >>> sm.delete_section("SecB")
            >>> print([s.tag for s in sm.get_all_sections().values()])
            [1, 2]
            >>> print(sm.get_section("SecC").tag) # SecC is now tag 2
            2
            >>> try:
            ...     sm.delete_section(999)
            ... except KeyError as e:
            ...     print(e)
            'No section found with tag 999'
        """
        if isinstance(identifier, str):
            section = Section.get_section_by_name(identifier)
            Section.delete_section(section.tag)
        elif isinstance(identifier, int):
            Section.delete_section(identifier)
        else:
            raise TypeError("Identifier must be either tag (int) or name (str)")

    def clear_all_sections(self) -> None:
        """Clears all registered sections and resets the global tagging system.

        This action removes all section definitions from the manager and
        resets the next available tag to the starting tag number.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class DummySection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Dummy", "DummySection", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A dummy section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Dummy {self.tag}"
            >>> SectionRegistry.register_section_type("Dummy", DummySection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections() # Ensure clean state
            >>> s1 = sm.create_section("Dummy", "Sec1")
            >>> s2 = sm.create_section("Dummy", "Sec2")
            >>> print(len(sm.get_all_sections()))
            2
            >>> sm.clear_all_sections()
            >>> print(len(sm.get_all_sections()))
            0
            >>> s3 = sm.create_section("Dummy", "Sec3")
            >>> print(s3.tag) # Tagging restarts from 1
            1
        """
        Section.clear_all_sections()

    @classmethod
    def get_instance(cls) -> 'SectionManager':
        """Retrieves the singleton instance of the SectionManager.

        If an instance does not already exist, one is created and returned.

        Returns:
            The single `SectionManager` instance.

        Example:
            >>> from femora.components.section.section_base import SectionManager
            >>> sm1 = SectionManager.get_instance()
            >>> sm2 = SectionManager.get_instance()
            >>> print(sm1 is sm2)
            True
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_start_tag(self, start_number: int):
        """Sets the starting tag number for section tagging.

        This method forwards the call to the underlying `Section` class
        to update the global starting tag for all sections managed.

        Args:
            start_number: The integer tag number to start from for new sections
                and re-tagging operations.

        Example:
            >>> from femora.components.section.section_base import Section, SectionRegistry, SectionManager
            >>> # Dummy section type for example
            >>> class DummySection(Section):
            ...     def __init__(self, user_name: str):
            ...         super().__init__("Dummy", "DummySection", user_name)
            ...     def get_parameters(cls): return []
            ...     def get_description(cls): return []
            ...     def get_help_text(cls): return "A dummy section."
            ...     def validate_section_parameters(cls, **kwargs): return kwargs
            ...     def get_values(self, keys): return {}
            ...     def update_values(self, values): pass
            ...     def to_tcl(self): return f"section Dummy {self.tag}"
            >>> SectionRegistry.register_section_type("Dummy", DummySection)
            >>> sm = SectionManager.get_instance()
            >>> sm.clear_all_sections()
            >>> s1 = sm.create_section("Dummy", "Element1") # Tag 1
            >>> sm.set_start_tag(1000)
            >>> s2 = sm.create_section("Dummy", "Element2") # Tag 1001
            >>> print(s1.tag) # s1 is retagged to 1000
            1000
            >>> print(s2.tag)
            1001
        """
        Section.set_start_tag(start_number)