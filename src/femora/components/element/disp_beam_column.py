from typing import Dict, List, Union
from femora.components.section.section_base import Section, SectionManager
from femora.components.transformation.transformation import GeometricTransformation, GeometricTransformationManager
from femora.core.element_base import Element, ElementRegistry

class DispBeamColumnElement(Element):
    """Represents a displacement-based beam-column element for OpenSees.

    This element type uses distributed plasticity with a displacement-based
    formulation, suitable for simulating flexural and axial behavior
    under various loading conditions.

    Attributes:
        numIntgrPts (int): The number of integration points along the element's length.
        massDens (float): The element's mass density per unit length.
        _section (Section): The resolved Section object associated with this element.
        _transformation (GeometricTransformation): The resolved GeometricTransformation object.

    Example:
        >>> import femora as fm
        >>> # Assuming `Section` and `GeometricTransformation` objects exist
        >>> element = fm.DispBeamColumnElement(ndof=3, section=1,
        ...     transformation=2, numIntgrPts=5, massDens=0.1)
        >>> print(element.numIntgrPts)
        5
    """
    
    def __init__(self, ndof: int, section: Union[Section, int, str], 
                 transformation: Union[GeometricTransformation, int, str], 
                 numIntgrPts: int = 5, 
                 massDens: float = 0.0,
                 **kwargs):
        """Initializes a Displacement-Based Beam-Column Element.

        Args:
            ndof: The number of degrees of freedom per node (3 for 2D, 6 for 3D).
            section: The cross-section definition. Can be a Section object,
                its integer tag, or its string name.
            transformation: The geometric transformation. Can be a
                GeometricTransformation object, its integer tag, or its
                string name.
            numIntgrPts: Optional. The number of integration points along
                the element. Defaults to 5.
            massDens: Optional. The element's mass density per unit length.
                Defaults to 0.0.
            **kwargs: Additional keyword arguments passed to the base Element class.

        Raises:
            ValueError: If `ndof` is not 3 or 6, if `section` or
                `transformation` is missing, or if `numIntgrPts` or
                `massDens` are invalid.

        Notes:
            This element corresponds to the `dispBeamColumn` element in OpenSees.
            The typical OpenSees command syntax is:
            `element dispBeamColumn $tag $iNode $jNode $numIntgrPts $secTag $transfTag <-mass $massDens>`

        Example:
            >>> import femora as fm
            >>> # Assuming section and transformation with tags 1 and 2 exist
            >>> element = fm.DispBeamColumnElement(ndof=3, section=1,
            ...     transformation=2, numIntgrPts=5, massDens=0.1)
            >>> print(element.numIntgrPts)
            5
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
        """Resolves a section object from various input types.

        This internal helper method converts a section tag (int), name (str),
        or a Section object itself into a Section object.

        Args:
            section_input: The input representing the section, which can be
                a Section object, its integer tag, or its string name.

        Returns:
            The resolved `Section` object.

        Raises:
            ValueError: If the `section_input` type is invalid or if the
                section cannot be found.
        """
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager.get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolves a geometric transformation object from various input types.

        This internal helper method converts a transformation tag (int),
        name (str), or a GeometricTransformation object itself into a
        GeometricTransformation object.

        Args:
            transf_input: The input representing the transformation, which
                can be a GeometricTransformation object, its integer tag,
                or its string name.

        Returns:
            The resolved `GeometricTransformation` object.

        Raises:
            ValueError: If the `transf_input` type is invalid or if the
                transformation cannot be found.
        """
        if isinstance(transf_input, GeometricTransformation):
            return transf_input
        if isinstance(transf_input, (int, str)):
            return GeometricTransformationManager.get_transformation(transf_input)
        raise ValueError(f"Invalid transformation input type: {type(transf_input)}")

    def __str__(self):
        """Generates a string representation of the element's properties.

        Returns:
            A string containing the section tag, transformation tag, number
            of integration points, and mass density, separated by spaces.
        """
        return f"{self._section.tag} {self._transformation.tag} {self.numIntgrPts} {self.massDens}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generates the OpenSees TCL command string for this element.

        This method constructs the OpenSees `element dispBeamColumn` command
        using the element's properties and provided global tag and node list.

        Args:
            tag: The unique integer tag to assign to this element in OpenSees.
            nodes: A list containing the two integer tags of the connected
                start (i) and end (j) nodes.

        Returns:
            A string representing the full OpenSees TCL command to create
            the displacement-based beam-column element.

        Raises:
            ValueError: If `nodes` does not contain exactly two node tags.

        Example:
            >>> import femora as fm
            >>> # Assuming setup for a 2D element
            >>> element_instance = fm.DispBeamColumnElement(ndof=3, section=1, transformation=2)
            >>> tcl_command = element_instance.to_tcl(tag=101, nodes=[1, 2])
            >>> print(tcl_command)
            element dispBeamColumn 101 1 2 5 1 2
            >>> # With mass density
            >>> element_instance_mass = fm.DispBeamColumnElement(ndof=3, section=1, transformation=2, massDens=0.5)
            >>> tcl_command_mass = element_instance_mass.to_tcl(tag=102, nodes=[3, 4])
            >>> print(tcl_command_mass)
            element dispBeamColumn 102 3 4 5 1 2 -mass 0.5
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
        """Returns a list of parameter names specific to this element type.

        These parameters define the unique properties of a displacement-based
        beam-column element beyond standard element attributes.

        Returns:
            A list of strings, where each string is the name of a parameter
            (e.g., "numIntgrPts", "massDens").

        Example:
            >>> import femora as fm
            >>> params = fm.DispBeamColumnElement.get_parameters()
            >>> print(params)
            ['numIntgrPts', 'massDens']
        """
        return ["numIntgrPts", "massDens"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns a list of descriptions for the element's specific parameters.

        The order of descriptions corresponds to the order of parameters
        returned by `get_parameters`.

        Returns:
            A list of strings, each describing a parameter of this element type.

        Example:
            >>> import femora as fm
            >>> descriptions = fm.DispBeamColumnElement.get_description()
            >>> print(descriptions[0])
            Number of integration points along the element
        """
        return [
            "Number of integration points along the element",
            "Element mass density per unit length (optional)"
        ]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the element-specific parameters.

        This method checks the provided keyword arguments against the expected
        types and ranges for `numIntgrPts` and `massDens`.

        Args:
            **kwargs: Keyword arguments representing element parameters
                to be validated (e.g., `numIntgrPts`, `massDens`).

        Returns:
            A dictionary containing the validated parameters and their
            converted values.

        Raises:
            ValueError: If any parameter is invalid (e.g., wrong type,
                out of range).

        Example:
            >>> import femora as fm
            >>> validated = fm.DispBeamColumnElement.validate_element_parameters(
            ...     numIntgrPts=10, massDens=0.15)
            >>> print(validated)
            {'numIntgrPts': 10, 'massDens': 0.15}
            >>> # Example with invalid input
            >>> try:
            ...     fm.DispBeamColumnElement.validate_element_parameters(numIntgrPts=-1)
            ... except ValueError as e:
            ...     print(e)
            Number of integration points must be positive
        """
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
        """Retrieves the current values for specified element parameters.

        This method allows fetching values for both direct attributes and
        associated section/transformation names.

        Args:
            keys: A list of strings, where each string is a parameter name
                (e.g., "numIntgrPts", "massDens", "section", "transformation").

        Returns:
            A dictionary where keys are the requested parameter names and
            values are their current settings. For "section" and
            "transformation", their user_name or tag is returned.

        Example:
            >>> import femora as fm
            >>> # Define mock classes for demonstration without full Femora setup
            >>> class MockSection:
            ...     def __init__(self, tag, name): self.tag = tag; self.user_name = name
            >>> class MockTransformation:
            ...     def __init__(self, tag, name): self.tag = tag; self.user_name = name
            >>>
            >>> element_instance = fm.DispBeamColumnElement(ndof=3,
            ...     section=MockSection(1, 'concrete_rect'),
            ...     transformation=MockTransformation(2, 'p_delta_2d'),
            ...     numIntgrPts=7, massDens=0.2)
            >>> values = element_instance.get_values(['numIntgrPts', 'section', 'massDens'])
            >>> print(values)
            {'numIntgrPts': 7, 'section': 'concrete_rect', 'massDens': 0.2}
        """
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
        """Updates the element's parameters with new values.

        This method allows modifying element-specific properties, as well as
        changing the associated section or geometric transformation.

        Args:
            values: A dictionary where keys are parameter names (e.g.,
                "numIntgrPts", "massDens", "section", "transformation")
                and values are their new settings.

        Raises:
            ValueError: If any provided parameter value is invalid.

        Example:
            >>> import femora as fm
            >>> # Assuming initial element setup
            >>> element_instance = fm.DispBeamColumnElement(ndof=3, section=1, transformation=2, numIntgrPts=5)
            >>> print(element_instance.numIntgrPts)
            5
            >>> element_instance.update_values({'numIntgrPts': 10, 'massDens': 0.1})
            >>> print(element_instance.numIntgrPts)
            10
            >>> print(element_instance.massDens)
            0.1
            >>> # Update section (actual check requires deeper integration, but demonstrates usage)
            >>> # element_instance.update_values({'section': 3})
        """
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
    def get_possible_dofs() -> List[str]:
        """Returns a list of possible degrees of freedom (DOF) values.

        For displacement-based beam-column elements, common DOF values are
        3 (for 2D analysis) and 6 (for 3D analysis).

        Returns:
            A list of strings representing the supported DOF counts.

        Example:
            >>> import femora as fm
            >>> dofs = fm.DispBeamColumnElement.get_possible_dofs()
            >>> print(dofs)
            ['3', '6']
        """
        return ["3", "6"]

    def get_mass_per_length(self) -> float:
        """Retrieves the element's mass density per unit length.

        Returns:
            The floating-point value of the mass density per unit length.

        Example:
            >>> import femora as fm
            >>> element_instance = fm.DispBeamColumnElement(ndof=3, section=1, transformation=2, massDens=0.25)
            >>> mass = element_instance.get_mass_per_length()
            >>> print(mass)
            0.25
        """
        return self.massDens

ElementRegistry.register_element_type('DispBeamColumn', DispBeamColumnElement)