from typing import Dict, List, Union
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.core.element_base import Element, ElementRegistry

class ForceBeamColumnElement(Element):
    """
    Force-Based Beam-Column Element for OpenSees (nonlinearBeamColumn).
    Uses force-based formulation with distributed plasticity.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 numIntgrPts: int = 5, 
                 massDens: float = 0.0,
                 maxIters: int = 10,
                 tol: float = 1e-12,
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
            maxIters (int, optional): Maximum number of iterations for element compatibility. 
                Defaults to 10.
            tol (float, optional): Tolerance for satisfaction of element compatibility. 
                Defaults to 1e-12.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
            ``element nonlinearBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens> <-iter $maxIters $tol>``

        Example:
            ```python
            element = ForceBeamColumnElement(ndof=3, section=1, transformation=1, numIntgrPts=5, maxIters=10, tol=1e-12)
            ```
        """
        # Validate DOF requirement (typically 6 for 3D, 3 for 2D)
        if ndof not in [3, 6]:
            raise ValueError(f"ForceBasedBeamColumnElement requires 3 (2D) or 6 (3D) DOFs, but got {ndof}")
        
        # Resolve section - REQUIRED for beam elements
        if section is None:
            raise ValueError("ForceBasedBeamColumnElement requires a section")
        self._section = self._resolve_section(section)
        
        # Resolve transformation - REQUIRED for beam elements  
        if transformation is None:
            raise ValueError("ForceBasedBeamColumnElement requires a geometric transformation")
        self._transformation = self._resolve_transformation(transformation)
        
        # Validate parameters
        if numIntgrPts < 1:
            raise ValueError("Number of integration points must be positive")
        if massDens < 0:
            raise ValueError("Mass density must be non-negative")
        if maxIters < 1:
            raise ValueError("Max iterations must be positive")
        if tol <= 0:
            raise ValueError("Tolerance must be positive")
            
        # Material should be None for beam elements (they use sections)
        super().__init__('nonlinearBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation, **kwargs)
        
        self.numIntgrPts = numIntgrPts
        self.massDens = massDens
        self.maxIters = maxIters
        self.tol = tol

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
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens} {self.maxIters} {self.tol}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """
        Generate the OpenSees TCL command
        
        Example: element nonlinearBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens> <-iter $maxIters $tol>
        """
        if len(nodes) != 2:
            raise ValueError("Force-based beam-column element requires 2 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        
        # Required parameters
        cmd_parts = [f"element nonlinearBeamColumn {tag} {nodes_str}"]
        
        # Add number of integration points
        cmd_parts.append(str(self.numIntgrPts))
            
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if self.massDens != 0.0:
            cmd_parts.extend(["-mass", str(self.massDens)])
            
        # Add iteration parameters (always outputting to be safe given explicit defaults)
        cmd_parts.extend(["-iter", str(self.maxIters), str(self.tol)])
        
        return " ".join(cmd_parts)
    
    @classmethod
    def get_parameters(cls) -> List[str]:
        return ["numIntgrPts", "massDens", "maxIters", "tol"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Force-Based Beam-Column Element"""
        return [
            "Number of integration points along the element",
            "Element mass density per unit length (optional)",
            "Maximum number of iterations for element compatibility (optional)",
            "Tolerance for satisfaction of element compatibility (optional)"
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
        
        # Validate maxIters
        if "maxIters" in kwargs:
            try:
                max_iters = int(kwargs["maxIters"])
                if max_iters < 1:
                    raise ValueError("Maximum iterations must be positive")
                validated_params["maxIters"] = max_iters
            except (ValueError, TypeError):
                raise ValueError("Invalid maxIters. Must be a positive integer")
        
        # Validate tol
        if "tol" in kwargs:
            try:
                tol = float(kwargs["tol"])
                if tol <= 0:
                    raise ValueError("Tolerance must be positive")
                validated_params["tol"] = tol
            except (ValueError, TypeError):
                raise ValueError("Invalid tol. Must be a positive number")
        
        return validated_params

    @staticmethod
    def get_possible_dofs():
        return ["3", "6"]
    
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        values = {}
        for key in keys:
             if hasattr(self, key): values[key] = getattr(self, key)
        return values
        
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        if "numIntgrPts" in values:
            val = int(values["numIntgrPts"])
            if val < 1: raise ValueError("Positive numIntgrPts required")
            self.numIntgrPts = val
        if "massDens" in values:
            val = float(values["massDens"])
            if val < 0: raise ValueError("Non-negative massDens required")
            self.massDens = val
        if "maxIters" in values:
            val = int(values["maxIters"])
            if val < 1: raise ValueError("Positive maxIters required")
            self.maxIters = val
        if "tol" in values:
            val = float(values["tol"])
            if val <= 0: raise ValueError("Positive tol required")
            self.tol = val

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.massDens

ElementRegistry.register_element_type('NonlinearBeamColumn', ForceBeamColumnElement)
ElementRegistry.register_element_type('ForceBasedBeamColumn', ForceBeamColumnElement)
