from typing import Dict, List, Union
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.core.element_base import Element, ElementRegistry

class DispBeamColumnElement(Element):
    """
    Displacement-Based Beam-Column Element for OpenSees.
    Uses distributed plasticity with displacement-based formulation.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 numIntgrPts: int = 5, 
                 massDens: float = 0.0,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom (3 for 2D, 6 for 3D).
            section (Union[Section, int, str]): Section object, tag, or name.
            transformation (Union[GeometricTransformation, int, str]): 
                Transformation object, tag, or name.
            numIntgrPts (int, optional): Number of integration points along the element. 
                Defaults to 5.
            massDens (float, optional): Element mass density per unit length. 
                Defaults to 0.0.

        Raises:
            ValueError: If ndof is invalid, section/transformation missing, or
                parameters are invalid.

        OpenSees command syntax:
            ``element dispBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens>``

        Example:
            ```python
            element = DispBeamColumnElement(ndof=3, section=1, transformation=1, numIntgrPts=5)
            ```
        """
        # Validate DOF requirement (typically 6 for 3D, 3 for 2D)
        if ndof not in [3, 6]:
            raise ValueError(f"DisplacementBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")
        
        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)
        
        # Resolve transformation - REQUIRED for beam elements  
        if transformation is None:
            raise ValueError("DisplacementBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)
        
        # Validate parameters
        if numIntgrPts < 1:
            raise ValueError("Number of integration points must be positive")
        if massDens < 0:
            raise ValueError("Mass density must be non-negative")
            
        # Material should be None for beam elements (they use sections)
        super().__init__('dispBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation, **kwargs)
        
        self.numIntgrPts = numIntgrPts
        self.massDens = massDens

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
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command
        
        Example: element dispBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens>
        """
        if len(nodes) != 2:
            raise ValueError("Displacement-based beam-column element requires 2 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        
        # Required parameters
        cmd_parts = [f"element dispBeamColumn {tag} {nodes_str}"]
        
        # Add number of integration points
        cmd_parts.append(str(self.numIntgrPts))
            
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])
            
        return " ".join(cmd_parts)
    
    @classmethod 
    def get_parameters(cls) -> List[str]:
        """Parameters for Displacement-Based Beam-Column Element"""
        return ["numIntgrPts", "massDens"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Displacement-Based Beam-Column Element"""
        return [
            "Number of integration points along the element",
            "Element mass density per unit length (optional)"
        ]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate element parameters"""
        validated_params = {}
        
        # Validate numIntgrPts
        if "numIntgrPts" in kwargs:
            try:
                num_pts = int(kwargs["numIntgrPts"])
                if num_pts < 1:
                    raise ValueError("Number of integration points must be positive")
                validated_params["numIntgrPts"] = num_pts
            except (ValueError, TypeError):
                raise ValueError("Invalid numIntgrPts. Must be a positive integer")
        
        # Validate massDens
        if "massDens" in kwargs:
            try:
                mass_dens = float(kwargs["massDens"])
                if mass_dens < 0:
                    raise ValueError("Mass density must be non-negative")
                validated_params["massDens"] = mass_dens
            except (ValueError, TypeError):
                raise ValueError("Invalid massDens. Must be a non-negative number")
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        for key in keys:
            if hasattr(self, key):
                values[key] = getattr(self, key)
            elif key == "section":
                values[key] = self._section.user_name
            elif key == "transformation":
                values[key] = self._transformation.user_name if hasattr(self._transformation, 'user_name') else str(self._transformation.tag)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update element parameters"""
        # Extract section and transformation updates
        section_update = values.pop("section", None)
        transformation_update = values.pop("transformation", None)
        
        # Update parameters
        if values:
            validated_params = self.validate_element_parameters(**values)
            for key, val in validated_params.items():
                setattr(self, key, val)
        
        # Update section if provided
        if section_update:
            self._section = self._resolve_section(section_update)
            
        # Update transformation if provided  
        if transformation_update:
            self._transformation = self._resolve_transformation(transformation_update)

    @staticmethod
    def get_possible_dofs():
        return ["3", "6"]

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.massDens

ElementRegistry.register_element_type('DispBeamColumn', DispBeamColumnElement)
