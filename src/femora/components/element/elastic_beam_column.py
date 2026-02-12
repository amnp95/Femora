from typing import Dict, List, Union
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.core.element_base import Element, ElementRegistry

class ElasticBeamColumnElement(Element):
    """
    Elastic Beam-Column Element for OpenSees with Section.
    Uses elastic formulation with section properties.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 massDens: float = 0.0,
                 cMass: bool = False,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom (3 for 2D, 6 for 3D).
            section (Union[Section, int, str]): Section object, tag, or name.
            transformation (Union[GeometricTransformation, int, str]): 
                Transformation object, tag, or name.
            massDens (float, optional): Element mass density per unit length. 
                Defaults to 0.0.
            cMass (bool, optional): Use consistent mass matrix instead of lumped. 
                Defaults to False.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
            ``element elasticBeamColumn $tag $iNode $jNode $secTag $transfTag <-mass $massDens> <-cMass>``

        Example:
            ```python
            element = ElasticBeamColumnElement(ndof=3, section=1, transformation=1, massDens=10.0)
            ```
        """
        # Validate DOF requirement (typically 6 for 3D, 3 for 2D)
        if ndof not in [3, 6]:
            raise ValueError(f"ElasticBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")
        
        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("ElasticBeamColumnElement requires a section")
        self._section = self._resolve_section(section)
        
        # Resolve transformation - REQUIRED for beam elements  
        if transformation is None:
            raise ValueError("ElasticBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)
        
        # Validate parameters
        if massDens < 0:
            raise ValueError("Mass density must be non-negative")
            
        # Material should be None for beam elements (they use sections)
        super().__init__('elasticBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation, **kwargs)
        
        self.massDens = massDens
        self.cMass = cMass

    @staticmethod
    def _resolve_section(section_input: Union[Section, int, str]) -> Section:
        """Resolve section from different input types"""
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager.get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolve transformation from different input types"""
        if isinstance(transf_input, GeometricTransformation):
            return transf_input
        if isinstance(transf_input, (int, str)):
            return GeometricTransformationManager.get_transformation(transf_input)
        raise ValueError(f"Invalid transformation input type: {type(transf_input)}")

    def __str__(self):
        """Generate the OpenSees element string representation"""
        return f"{self._section.tag} {self._transformation.tag} {self.massDens} {self.cMass}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command
        
        Example: element elasticBeamColumn $tag $iNode $jNode $secTag $transfTag <-mass $massDens> <-cMass>
        """
        if len(nodes) != 2:
            raise ValueError("Elastic beam-column element requires 2 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        
        # Required parameters
        cmd_parts = [f"element elasticBeamColumn {tag} {nodes_str}"]
        
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])
            
        # Add optional consistent mass flag
        if self.cMass:
            cmd_parts.append("-cMass")
            
        return " ".join(cmd_parts)
    
    @classmethod 
    def get_parameters(cls) -> List[str]:
        return ["massDens", "cMass"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Elastic Beam-Column Element"""
        return [
            "Element mass density per unit length (optional)",
            "Use consistent mass matrix instead of lumped (optional)"
        ]
        
    @staticmethod
    def get_possible_dofs():
        return ["3", "6"]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, bool]]:
        """Validate element parameters"""
        validated_params = {}
        
        # Validate massDens
        if "massDens" in kwargs:
            try:
                mass_dens = float(kwargs["massDens"])
                if mass_dens < 0:
                    raise ValueError("Mass density must be non-negative")
                validated_params["massDens"] = mass_dens
            except (ValueError, TypeError):
                raise ValueError("Invalid massDens. Must be a non-negative number")
        
        # Validate cMass flag
        if "cMass" in kwargs:
            if isinstance(kwargs["cMass"], bool):
                validated_params["cMass"] = kwargs["cMass"]
            elif isinstance(kwargs["cMass"], str):
                validated_params["cMass"] = kwargs["cMass"].lower() in ['true', '1', 'yes']
            else:
                try:
                    validated_params["cMass"] = bool(int(kwargs["cMass"]))
                except (ValueError, TypeError):
                    raise ValueError("Invalid cMass. Must be a boolean value")
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str, bool]]:
        values = {}
        for key in keys:
             if hasattr(self, key): values[key] = getattr(self, key)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str, bool]]) -> None:
        """Update element parameters"""
        # Extract section and transformation updates
        section_update = values.pop("section", None)
        transformation_update = values.pop("transformation", None)
        
        # Update parameters
        if values:
            validated_params = self.validate_element_parameters(**values)
            # Update attributes
            if "massDens" in validated_params:
                self.massDens = validated_params["massDens"]
            if "cMass" in validated_params:
                self.cMass = validated_params["cMass"]
        
        # Update section if provided
        if section_update:
            self._section = self._resolve_section(section_update)
            
        # Update transformation if provided  
        if transformation_update:
            self._transformation = self._resolve_transformation(transformation_update)

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.massDens

ElementRegistry.register_element_type('ElasticBeamColumn', ElasticBeamColumnElement)
