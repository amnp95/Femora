"""
Enhanced Section Base Architecture for FEMORA with Material Resolution
Following the established patterns in the codebase with improved material handling
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Any
from femora.components.Material.materialBase import Material, MaterialManager


class Section(ABC):
    """
    Base abstract class for all sections with sequential tagging and material handling
    """
    _sections = {}      # Class-level dictionary to track all sections
    _sec_tags = {}      # Class-level dictionary to track section tags  
    _names = {}         # Class-level dictionary to track section names
    _next_tag = 1       # Class variable to track the next tag to assign
    _start_tag = 1      # Class variable to track the starting tag number

    def __init__(self, section_type: str, section_name: str, user_name: str):
        """
        Initialize a new section with a sequential tag
        
        Args:
            section_type (str): The type of section (e.g., 'Elastic', 'Fiber', 'Aggregator')
            section_name (str): The specific section name for OpenSees
            user_name (str): User-specified name for the section
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
        """
        Resolve material from different input types
        
        Args:
            material_input: Can be:
                - int: material tag
                - str: material name
                - Material: material object
                - None: no material required
                
        Returns:
            Material object or None
            
        Raises:
            ValueError: If material cannot be found or is invalid type
        """
        if material_input is None:
            return None
            
        if isinstance(material_input, Material):
            return material_input
            
        if isinstance(material_input, (int, str)):
            try:
                return MaterialManager.get_material(material_input)
            except (KeyError, TypeError) as e:
                raise ValueError(f"Material not found: {material_input}. Error: {str(e)}")
                
        raise ValueError(f"Invalid material input type: {type(material_input)}. "
                        f"Expected Material object, int (tag), str (name), or None")

    @staticmethod
    def resolve_materials_dict(materials_input: Dict[str, Union[int, str, Material]]) -> Dict[str, Material]:
        """
        Resolve a dictionary of materials from different input types
        
        Args:
            materials_input: Dictionary mapping keys to material inputs
            
        Returns:
            Dictionary mapping keys to Material objects
        """
        resolved_materials = {}
        for key, material_input in materials_input.items():
            resolved_materials[key] = Section.resolve_material(material_input)
        return resolved_materials

    def assign_material(self, material_input: Union[int, str, Material, None]) -> None:
        """
        Assign a material to this section
        
        Args:
            material_input: Material to assign (tag, name, object, or None)
        """
        self.material = self.resolve_material(material_input)

    def get_material(self) -> Optional[Material]:
        """
        Get the material assigned to this section
        
        Returns:
            Material object or None if no material assigned
        """
        return self.material

    def has_material(self) -> bool:
        """
        Check if this section has a material assigned
        
        Returns:
            True if material is assigned, False otherwise
        """
        return self.material is not None

    @classmethod
    def delete_section(cls, tag: int) -> None:
        """Delete a section by its tag and retag remaining sections"""
        if tag in cls._sections:
            section_to_delete = cls._sections[tag]
            cls._names.pop(section_to_delete.user_name)
            cls._sec_tags.pop(section_to_delete)
            cls._sections.pop(tag)
            cls.retag_all()

    @classmethod
    def retag_all(cls):
        """Retag all sections sequentially"""
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
        """Retrieve all created sections"""
        return cls._sections

    @classmethod
    def get_section_by_tag(cls, tag: int) -> 'Section':
        """Retrieve a specific section by its tag"""
        if tag not in cls._sections:
            raise KeyError(f"No section found with tag {tag}")
        return cls._sections[tag]

    @classmethod
    def get_section_by_name(cls, name: str) -> 'Section':
        """Retrieve a specific section by its user-specified name"""
        if name not in cls._names:
            raise KeyError(f"No section found with name {name}")
        return cls._names[name]

    @classmethod
    def clear_all_sections(cls):
        """Clear all sections and reset tags"""
        cls._sections.clear()
        cls._sec_tags.clear()
        cls._names.clear()
        cls._next_tag = cls._start_tag

    @classmethod
    def set_start_tag(cls, start_number: int):
        """
        Set the starting tag number for section tagging.
        Args:
            start_number (int): The tag number to start from.
        """
        cls._start_tag = start_number
        cls._next_tag = start_number
        cls.retag_all()

    @classmethod
    @abstractmethod
    def get_parameters(cls) -> List[str]:
        """Get the list of parameters for this section type"""
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> List[str]:
        """Get the list of parameter descriptions for this section type"""
        pass

    @classmethod
    @abstractmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for this section type for GUI display"""
        pass

    @classmethod
    @abstractmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate section input parameters"""
        pass

    @abstractmethod
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        pass

    @abstractmethod
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        pass

    @abstractmethod
    def to_tcl(self) -> str:
        """Convert the section to a TCL string representation for OpenSees"""
        pass

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section (for dependency tracking)"""
        if self.material is not None:
            return [self.material]
        return []

    def __str__(self) -> str:
        """String representation of the section"""
        material_info = f", Material: {self.material.user_name}" if self.material else ", No Material"
        return (f"Section '{self.user_name}' (Tag: {self.tag}, Type: {self.section_name}"
                f"{material_info})")


class SectionRegistry:
    """Registry to manage section types and their creation"""
    _section_types = {}

    @classmethod
    def register_section_type(cls, name: str, section_class: Type[Section]):
        """Register a new section type for easy creation"""
        cls._section_types[name] = section_class

    @classmethod
    def get_section_types(cls):
        """Get available section types"""
        return list(cls._section_types.keys())

    @classmethod
    def create_section(cls, section_type: str, user_name: str = "Unnamed", **kwargs) -> Section:
        """Create a new section of a specific type"""
        if section_type not in cls._section_types:
            raise KeyError(f"Section type {section_type} not registered")
        
        return cls._section_types[section_type](user_name=user_name, **kwargs)


class SectionManager:
    """
    Singleton class for managing sections - following the same pattern as MaterialManager
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SectionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the singleton instance"""
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
        """Create a new section with the given parameters"""
        return SectionRegistry.create_section(
            section_type=section_type,
            user_name=user_name,
            **section_params
        )

    @staticmethod
    def get_section(identifier: Union[int, str]) -> Section:
        """Get section by either tag or name"""
        if isinstance(identifier, int):
            return Section.get_section_by_tag(identifier)
        elif isinstance(identifier, str):
            return Section.get_section_by_name(identifier)
        else:
            raise TypeError("Identifier must be either tag (int) or name (str)")

    def get_all_sections(self) -> Dict[int, Section]:
        """Get all registered sections"""
        return Section.get_all_sections()

    def delete_section(self, identifier: Union[int, str]) -> None:
        """Delete a section by its identifier"""
        if isinstance(identifier, str):
            section = Section.get_section_by_name(identifier)
            Section.delete_section(section.tag)
        elif isinstance(identifier, int):
            Section.delete_section(identifier)
        else:
            raise TypeError("Identifier must be either tag (int) or name (str)")

    def clear_all_sections(self) -> None:
        """Clear all registered sections and reset tags"""
        Section.clear_all_sections()

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of SectionManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_start_tag(self, start_number: int):
        """
        Set the starting tag number for section tagging.
        Args:
            start_number (int): The tag number to start from.
        """
        Section.set_start_tag(start_number)