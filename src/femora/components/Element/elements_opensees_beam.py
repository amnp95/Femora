from typing import Dict, List, Union
from ..Material.materialBase import Material
from ..section.section_base import Section, SectionManager
from ..transformation.transformation import GeometricTransformation, GeometricTransformationManager
from .elementBase import Element, ElementRegistry


class DispBeamColumnElement(Element):
    """
    Displacement-Based Beam-Column Element for OpenSees.
    Uses distributed plasticity with displacement-based formulation.

    Parameters
    ----------
    ndof : int
        Number of degrees of freedom (3 for 2D, 6 for 3D).
    section : Section, int, or str
        Section object, tag, or name.
    transformation : GeometricTransformation, int, or str
        Transformation object, tag, or name.
    numIntgrPts : int, optional
        Number of integration points along the element.
    massDens : float, optional
        Element mass density per unit length.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """
        Initialize Displacement-Based Beam-Column Element.

        Parameters
        ----------
        ndof : int
            Number of degrees of freedom (3 for 2D, 6 for 3D).
        section : Section, int, or str
            Section object, tag, or name.
        transformation : GeometricTransformation, int, or str
            Transformation object, tag, or name.
        numIntgrPts : int, optional
            Number of integration points along the element.
        massDens : float, optional
            Element mass density per unit length.
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
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        # Material should be None for beam elements (they use sections)
        super().__init__('dispBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation)
        self.params = kwargs if kwargs else {}

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
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        return f"{self._section.tag} {self._transformation.tag} {params_str}"
    
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
        
        # Add number of integration points (required)
        if "numIntgrPts" in self.params:
            cmd_parts.append(str(self.params["numIntgrPts"]))
        else:
            cmd_parts.append("2")  # Default value
            
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if "massDens" in self.params:
            cmd_parts.extend(["-mass", str(self.params["massDens"])])
            
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
            if key in self.params:
                values[key] = self.params[key]
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
            self.params.update(validated_params)
        
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
        return self.params.get("massDens", 0.0)


class ForceBeamColumnElement(Element):
    """
    Force-Based Beam-Column Element for OpenSees (nonlinearBeamColumn).
    Uses force-based formulation with distributed plasticity.

    Parameters
    ----------
    ndof : int
        Number of degrees of freedom (3 for 2D, 6 for 3D).
    section : Section, int, or str
        Section object, tag, or name.
    transformation : GeometricTransformation, int, or str
        Transformation object, tag, or name.
    numIntgrPts : int, optional
        Number of integration points along the element.
    massDens : float, optional
        Element mass density per unit length.
    maxIters : int, optional
        Maximum number of iterations for element compatibility.
    tol : float, optional
        Tolerance for satisfaction of element compatibility.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """
        Initialize Force-Based Beam-Column Element.

        Parameters
        ----------
        ndof : int
            Number of degrees of freedom (3 for 2D, 6 for 3D).
        section : Section, int, or str
            Section object, tag, or name.
        transformation : GeometricTransformation, int, or str
            Transformation object, tag, or name.
        numIntgrPts : int, optional
            Number of integration points along the element.
        massDens : float, optional
            Element mass density per unit length.
        maxIters : int, optional
            Maximum number of iterations for element compatibility.
        tol : float, optional
            Tolerance for satisfaction of element compatibility.
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
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        # Material should be None for beam elements (they use sections)
        super().__init__('nonlinearBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation)
        self.params = kwargs if kwargs else {}

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
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        return f"{self._section.tag} {self._transformation.tag} {params_str}"
    
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
        
        # Add number of integration points (required)
        if "numIntgrPts" in self.params:
            cmd_parts.append(str(self.params["numIntgrPts"]))
        else:
            cmd_parts.append("2")  # Default value
            
        # Add section and transformation tags
        cmd_parts.extend([str(self._section.tag), str(self._transformation.tag)])
        
        # Add optional mass density
        if "massDens" in self.params:
            cmd_parts.extend(["-mass", str(self.params["massDens"])])
            
        # Add optional iteration parameters
        if "maxIters" in self.params or "tol" in self.params:
            cmd_parts.append("-iter")
            if "maxIters" in self.params:
                cmd_parts.append(str(self.params["maxIters"]))
            else:
                cmd_parts.append("1")  # Default value
            if "tol" in self.params:
                cmd_parts.append(str(self.params["tol"]))
            else:
                cmd_parts.append("1e-16")  # Default value
            
        return " ".join(cmd_parts)
    
    @classmethod 
    def get_parameters(cls) -> List[str]:
        """Parameters for Force-Based Beam-Column Element"""
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

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        for key in keys:
            if key in self.params:
                values[key] = self.params[key]
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
            self.params.update(validated_params)
        
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
        return self.params.get("massDens", 0.0)


class ElasticBeamColumnElement(Element):
    """
    Elastic Beam-Column Element for OpenSees with Section.
    Uses elastic formulation with section properties.

    Parameters
    ----------
    ndof : int
        Number of degrees of freedom (3 for 2D, 6 for 3D).
    section : Section, int, or str
        Section object, tag, or name.
    transformation : GeometricTransformation, int, or str
        Transformation object, tag, or name.
    massDens : float, optional
        Element mass density per unit length.
    cMass : bool, optional
        Use consistent mass matrix instead of lumped.
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """
        Initialize Elastic Beam-Column Element.

        Parameters
        ----------
        ndof : int
            Number of degrees of freedom (3 for 2D, 6 for 3D).
        section : Section, int, or str
            Section object, tag, or name.
        transformation : GeometricTransformation, int, or str
            Transformation object, tag, or name.
        massDens : float, optional
            Element mass density per unit length.
        cMass : bool, optional
            Use consistent mass matrix instead of lumped.
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
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        # Material should be None for beam elements (they use sections)
        super().__init__('elasticBeamColumn', ndof, material=None, 
                         section=self._section, transformation=self._transformation)
        self.params = kwargs if kwargs else {}

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
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params and key != "cMass")
        return f"{self._section.tag} {self._transformation.tag} {params_str}"
    
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
        if "massDens" in self.params:
            cmd_parts.extend(["-mass", str(self.params["massDens"])])
            
        # Add optional consistent mass flag
        if "cMass" in self.params and self.params["cMass"]:
            cmd_parts.append("-cMass")
            
        return " ".join(cmd_parts)
    
    @classmethod 
    def get_parameters(cls) -> List[str]:
        """Parameters for Elastic Beam-Column Element"""
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
        """Retrieve values for specific parameters"""
        values = {}
        for key in keys:
            if key in self.params:
                values[key] = self.params[key]
            elif key == "section":
                values[key] = self._section.user_name
            elif key == "transformation":
                values[key] = self._transformation.user_name if hasattr(self._transformation, 'user_name') else str(self._transformation.tag)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str, bool]]) -> None:
        """Update element parameters"""
        # Extract section and transformation updates
        section_update = values.pop("section", None)
        transformation_update = values.pop("transformation", None)
        
        # Update parameters
        if values:
            validated_params = self.validate_element_parameters(**values)
            self.params.update(validated_params)
        
        # Update section if provided
        if section_update:
            self._section = self._resolve_section(section_update)
            
        # Update transformation if provided  
        if transformation_update:
            self._transformation = self._resolve_transformation(transformation_update)

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.params.get("massDens", 0.0)


# Register the elements with the ElementRegistry
ElementRegistry.register_element_type('DispBeamColumn', DispBeamColumnElement)
ElementRegistry.register_element_type('NonlinearBeamColumn', ForceBeamColumnElement)
ElementRegistry.register_element_type('ForceBasedBeamColumn', ForceBeamColumnElement)
ElementRegistry.register_element_type('ElasticBeamColumn', ElasticBeamColumnElement)