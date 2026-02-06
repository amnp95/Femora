from typing import Dict, List, Union
from ..Material.materialBase import Material
from ..section.section_base import Section, SectionManager
from ..transformation.transformation import GeometricTransformation, GeometricTransformationManager
from .elementBase import Element, ElementRegistry


class DispBeamColumnElement(Element):
    """Represents a displacement-based beam-column element for OpenSees.

    This element uses a distributed plasticity formulation based on
    displacement shape functions. It is suitable for nonlinear analysis
    where plasticity is expected to spread along the element's length.

    Attributes:
        _section (Section): The resolved section object for the element.
        _transformation (GeometricTransformation): The resolved geometric
            transformation object for the element.
        params (dict): A dictionary holding additional optional parameters
            like 'numIntgrPts' and 'massDens'.

    Example:
        >>> import femora as fm
        >>> # Assuming section (tag 1) and transformation (tag 1) are registered
        >>> element = fm.DispBeamColumnElement(
        ...     ndof=6,
        ...     section=1, # Using a tag assuming it's registered
        ...     transformation=1, # Using a tag assuming it's registered
        ...     numIntgrPts=5,
        ...     massDens=0.5
        ... )
        >>> print(element.params['numIntgrPts'])
        5
        >>> tcl_command = element.to_tcl(tag=101, nodes=[1, 2])
        >>> print(tcl_command)
        element dispBeamColumn 101 1 2 5 1 1 -mass 0.5
    """

    def __init__(self, ndof: int, section: Union[Section, int, str],
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """Initializes a Displacement-Based Beam-Column Element.

        Args:
            ndof: Number of degrees of freedom. Must be 3 for 2D or 6 for 3D.
            section: The section object, its unique tag (int), or its name (str).
            transformation: The geometric transformation object, its unique tag (int),
                or its name (str).
            **kwargs: Additional optional parameters.
                numIntgrPts (int, optional): Number of integration points along
                    the element. Defaults to 2 if not provided in `to_tcl`.
                massDens (float, optional): Element mass density per unit length.
                    Defaults to 0.0 if not provided in `to_tcl`.

        Raises:
            ValueError: If `ndof` is not 3 or 6.
            ValueError: If `section` or `transformation` is None.
            ValueError: If any provided `kwargs` parameters are invalid.
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
        """Resolves a section object from various input types.

        Args:
            section_input: The input for the section, which can be a Section
                object, an integer tag, or a string name.

        Returns:
            Section: The resolved Section object.

        Raises:
            ValueError: If the `section_input` type is invalid or the section
                cannot be found in the `SectionManager`.
        """
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager.get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolves a geometric transformation object from various input types.

        Args:
            transf_input: The input for the transformation, which can be a
                GeometricTransformation object, an integer tag, or a string name.

        Returns:
            GeometricTransformation: The resolved GeometricTransformation object.

        Raises:
            ValueError: If the `transf_input` type is invalid or the
                transformation cannot be found in the `GeometricTransformationManager`.
        """
        if isinstance(transf_input, GeometricTransformation):
            return transf_input
        if isinstance(transf_input, (int, str)):
            return GeometricTransformationManager.get_transformation(transf_input)
        raise ValueError(f"Invalid transformation input type: {type(transf_input)}")

    def __str__(self):
        """Generates the OpenSees element string representation for display.

        Returns:
            str: A string representing the element's key properties for display.
        """
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        return f"{self._section.tag} {self._transformation.tag} {params_str}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generates the OpenSees TCL command for creating the element.

        Args:
            tag: The unique integer tag for this element in the OpenSees model.
            nodes: A list of two integer node tags [i-node, j-node]
                connected by this element.

        Returns:
            str: The OpenSees TCL command string.

        Raises:
            ValueError: If `nodes` does not contain exactly two node tags.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.DispBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5, massDens=0.5
            ... )
            >>> tcl_command = element.to_tcl(tag=101, nodes=[1, 2])
            >>> print(tcl_command)
            element dispBeamColumn 101 1 2 5 1 1 -mass 0.5
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
        """Returns a list of valid parameter names for this element type.

        Returns:
            list[str]: A list of strings representing the parameter names.
        """
        return ["numIntgrPts", "massDens"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns a list of descriptions for the valid parameters of this element type.

        Returns:
            list[str]: A list of strings describing each parameter.
        """
        return [
            "Number of integration points along the element",
            "Element mass density per unit length (optional)"
        ]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates a dictionary of element parameters.

        Args:
            **kwargs: Arbitrary keyword arguments representing element parameters.
                Expected parameters are 'numIntgrPts' (int) and 'massDens' (float).

        Returns:
            dict: A dictionary containing the validated parameters.

        Raises:
            ValueError: If any parameter is invalid (e.g., wrong type, out of range).

        Example:
            >>> validated = DispBeamColumnElement.validate_element_parameters(
            ...     numIntgrPts=4, massDens=1.2
            ... )
            >>> print(validated)
            {'numIntgrPts': 4, 'massDens': 1.2}
            >>> try:
            ...     DispBeamColumnElement.validate_element_parameters(numIntgrPts=0)
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
        """Retrieves the current values for a specified list of parameters.

        Args:
            keys: A list of parameter names to retrieve values for.
                Can include 'section' and 'transformation' to get their user names.

        Returns:
            dict: A dictionary mapping parameter names to their current values.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1, name "Rect") and transformation (tag 1, name "Linear") exist
            >>> element = fm.DispBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5, massDens=0.5
            ... )
            >>> values = element.get_values(
            ...     ['numIntgrPts', 'massDens', 'section', 'transformation']
            ... )
            >>> print(values['numIntgrPts'])
            5
            >>> # Actual output for 'section' and 'transformation' depends on their
            >>> # internal 'user_name' attribute if available.
        """
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
        """Updates the element's parameters, section, or transformation.

        Args:
            values: A dictionary where keys are parameter names (e.g., 'numIntgrPts',
                'massDens', 'section', 'transformation') and values are the new
                values. 'section' and 'transformation' can be a Section/Transformation
                object, tag, or name.

        Raises:
            ValueError: If any provided parameter value is invalid.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.DispBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5, massDens=0.5
            ... )
            >>> element.update_values({'numIntgrPts': 10, 'massDens': 0.8})
            >>> print(element.params['numIntgrPts'])
            10
            >>> # Assuming a new section (tag 2) is registered
            >>> # element.update_values({'section': 2})
        """
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
        """Returns a list of possible degrees of freedom for this element type.

        Returns:
            list[str]: A list containing string representations of valid DOF counts.
        """
        return ["3", "6"]

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.params.get("massDens", 0.0)


class ForceBeamColumnElement(Element):
    """Represents a force-based beam-column element for OpenSees (nonlinearBeamColumn).

    This element utilizes a force-based formulation with distributed plasticity,
    making it suitable for rigorous nonlinear analysis, especially for members
    where plasticity is expected to spread.

    Attributes:
        _section (Section): The resolved section object for the element.
        _transformation (GeometricTransformation): The resolved geometric
            transformation object for the element.
        params (dict): A dictionary holding additional optional parameters
            like 'numIntgrPts', 'massDens', 'maxIters', and 'tol'.

    Example:
        >>> import femora as fm
        >>> # Assuming section (tag 1) and transformation (tag 1) are registered
        >>> element = fm.ForceBeamColumnElement(
        ...     ndof=6,
        ...     section=1, # Using a tag assuming it's registered
        ...     transformation=1, # Using a tag assuming it's registered
        ...     numIntgrPts=5,
        ...     massDens=0.5,
        ...     maxIters=20,
        ...     tol=1e-8
        ... )
        >>> print(element.params['numIntgrPts'])
        5
        >>> tcl_command = element.to_tcl(tag=201, nodes=[3, 4])
        >>> print(tcl_command)
        element nonlinearBeamColumn 201 3 4 5 1 1 -mass 0.5 -iter 20 1e-08
    """

    def __init__(self, ndof: int, section: Union[Section, int, str],
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """Initializes a Force-Based Beam-Column Element.

        Args:
            ndof: Number of degrees of freedom. Must be 3 for 2D or 6 for 3D.
            section: The section object, its unique tag (int), or its name (str).
            transformation: The geometric transformation object, its unique tag (int),
                or its name (str).
            **kwargs: Additional optional parameters.
                numIntgrPts (int, optional): Number of integration points along
                    the element. Defaults to 2 if not provided in `to_tcl`.
                massDens (float, optional): Element mass density per unit length.
                    Defaults to 0.0 if not provided in `to_tcl`.
                maxIters (int, optional): Maximum number of iterations for
                    element compatibility. Defaults to 1 if not provided in `to_tcl`.
                tol (float, optional): Tolerance for satisfaction of element
                    compatibility. Defaults to 1e-16 if not provided in `to_tcl`.

        Raises:
            ValueError: If `ndof` is not 3 or 6.
            ValueError: If `section` or `transformation` is None.
            ValueError: If any provided `kwargs` parameters are invalid.
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
        """Resolves a section object from various input types.

        Args:
            section_input: The input for the section, which can be a Section
                object, an integer tag, or a string name.

        Returns:
            Section: The resolved Section object.

        Raises:
            ValueError: If the `section_input` type is invalid or the section
                cannot be found in the `SectionManager`.
        """
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager.get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolves a geometric transformation object from various input types.

        Args:
            transf_input: The input for the transformation, which can be a
                GeometricTransformation object, an integer tag, or a string name.

        Returns:
            GeometricTransformation: The resolved GeometricTransformation object.

        Raises:
            ValueError: If the `transf_input` type is invalid or the
                transformation cannot be found in the `GeometricTransformationManager`.
        """
        if isinstance(transf_input, GeometricTransformation):
            return transf_input
        if isinstance(transf_input, (int, str)):
            return GeometricTransformationManager.get_transformation(transf_input)
        raise ValueError(f"Invalid transformation input type: {type(transf_input)}")

    def __str__(self):
        """Generates the OpenSees element string representation for display.

        Returns:
            str: A string representing the element's key properties for display.
        """
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        return f"{self._section.tag} {self._transformation.tag} {params_str}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generates the OpenSees TCL command for creating the element.

        Args:
            tag: The unique integer tag for this element in the OpenSees model.
            nodes: A list of two integer node tags [i-node, j-node]
                connected by this element.

        Returns:
            str: The OpenSees TCL command string.

        Raises:
            ValueError: If `nodes` does not contain exactly two node tags.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ForceBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5,
            ...     massDens=0.5, maxIters=20, tol=1e-8
            ... )
            >>> tcl_command = element.to_tcl(tag=201, nodes=[3, 4])
            >>> print(tcl_command)
            element nonlinearBeamColumn 201 3 4 5 1 1 -mass 0.5 -iter 20 1e-08
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
        """Returns a list of valid parameter names for this element type.

        Returns:
            list[str]: A list of strings representing the parameter names.
        """
        return ["numIntgrPts", "massDens", "maxIters", "tol"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns a list of descriptions for the valid parameters of this element type.

        Returns:
            list[str]: A list of strings describing each parameter.
        """
        return [
            "Number of integration points along the element",
            "Element mass density per unit length (optional)",
            "Maximum number of iterations for element compatibility (optional)",
            "Tolerance for satisfaction of element compatibility (optional)"
        ]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates a dictionary of element parameters.

        Args:
            **kwargs: Arbitrary keyword arguments representing element parameters.
                Expected parameters are 'numIntgrPts' (int), 'massDens' (float),
                'maxIters' (int), and 'tol' (float).

        Returns:
            dict: A dictionary containing the validated parameters.

        Raises:
            ValueError: If any parameter is invalid (e.g., wrong type, out of range).

        Example:
            >>> validated = ForceBeamColumnElement.validate_element_parameters(
            ...     numIntgrPts=4, massDens=1.2, maxIters=10, tol=1e-6
            ... )
            >>> print(validated)
            {'numIntgrPts': 4, 'massDens': 1.2, 'maxIters': 10, 'tol': 1e-06}
            >>> try:
            ...     ForceBeamColumnElement.validate_element_parameters(maxIters=0)
            ... except ValueError as e:
            ...     print(e)
            Maximum iterations must be positive
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
        """Retrieves the current values for a specified list of parameters.

        Args:
            keys: A list of parameter names to retrieve values for.
                Can include 'section' and 'transformation' to get their user names.

        Returns:
            dict: A dictionary mapping parameter names to their current values.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ForceBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5,
            ...     massDens=0.5, maxIters=20, tol=1e-8
            ... )
            >>> values = element.get_values(
            ...     ['numIntgrPts', 'massDens', 'maxIters', 'tol']
            ... )
            >>> print(values['numIntgrPts'])
            5
        """
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
        """Updates the element's parameters, section, or transformation.

        Args:
            values: A dictionary where keys are parameter names (e.g., 'numIntgrPts',
                'massDens', 'maxIters', 'tol', 'section', 'transformation') and
                values are the new values. 'section' and 'transformation' can be
                a Section/Transformation object, tag, or name.

        Raises:
            ValueError: If any provided parameter value is invalid.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ForceBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, numIntgrPts=5
            ... )
            >>> element.update_values({'numIntgrPts': 10, 'maxIters': 30})
            >>> print(element.params['numIntgrPts'])
            10
            >>> print(element.params['maxIters'])
            30
        """
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
        """Returns a list of possible degrees of freedom for this element type.

        Returns:
            list[str]: A list containing string representations of valid DOF counts.
        """
        return ["3", "6"]

    def get_mass_per_length(self) -> float:
        """Retrieve mass density per unit length if defined"""
        return self.params.get("massDens", 0.0)


class ElasticBeamColumnElement(Element):
    """Represents an elastic beam-column element for OpenSees.

    This element uses an elastic formulation based on section properties.
    It is suitable for linear-elastic analyses or as a component in a
    more complex model where certain regions remain elastic.

    Attributes:
        _section (Section): The resolved section object for the element.
        _transformation (GeometricTransformation): The resolved geometric
            transformation object for the element.
        params (dict): A dictionary holding additional optional parameters
            like 'massDens' and 'cMass'.

    Example:
        >>> import femora as fm
        >>> # Assuming section (tag 1) and transformation (tag 1) are registered
        >>> element = fm.ElasticBeamColumnElement(
        ...     ndof=6,
        ...     section=1, # Using a tag assuming it's registered
        ...     transformation=1, # Using a tag assuming it's registered
        ...     massDens=0.5,
        ...     cMass=True
        ... )
        >>> print(element.params['cMass'])
        True
        >>> tcl_command = element.to_tcl(tag=301, nodes=[5, 6])
        >>> print(tcl_command)
        element elasticBeamColumn 301 5 6 1 1 -mass 0.5 -cMass
    """

    def __init__(self, ndof: int, section: Union[Section, int, str],
                 transformation: Union[GeometricTransformation, int, str], **kwargs):
        """Initializes an Elastic Beam-Column Element.

        Args:
            ndof: Number of degrees of freedom. Must be 3 for 2D or 6 for 3D.
            section: The section object, its unique tag (int), or its name (str).
            transformation: The geometric transformation object, its unique tag (int),
                or its name (str).
            **kwargs: Additional optional parameters.
                massDens (float, optional): Element mass density per unit length.
                    Defaults to 0.0 if not provided in `to_tcl`.
                cMass (bool, optional): If True, use a consistent mass matrix
                    instead of a lumped mass matrix. Defaults to False.

        Raises:
            ValueError: If `ndof` is not 3 or 6.
            ValueError: If `section` or `transformation` is None.
            ValueError: If any provided `kwargs` parameters are invalid.
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
        """Resolves a section object from various input types.

        Args:
            section_input: The input for the section, which can be a Section
                object, an integer tag, or a string name.

        Returns:
            Section: The resolved Section object.

        Raises:
            ValueError: If the `section_input` type is invalid or the section
                cannot be found in the `SectionManager`.
        """
        if isinstance(section_input, Section):
            return section_input
        if isinstance(section_input, (int, str)):
            return SectionManager.get_section(section_input)
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    @staticmethod
    def _resolve_transformation(transf_input: Union[GeometricTransformation, int, str]) -> GeometricTransformation:
        """Resolves a geometric transformation object from various input types.

        Args:
            transf_input: The input for the transformation, which can be a
                GeometricTransformation object, an integer tag, or a string name.

        Returns:
            GeometricTransformation: The resolved GeometricTransformation object.

        Raises:
            ValueError: If the `transf_input` type is invalid or the
                transformation cannot be found in the `GeometricTransformationManager`.
        """
        if isinstance(transf_input, GeometricTransformation):
            return transf_input
        if isinstance(transf_input, (int, str)):
            return GeometricTransformationManager.get_transformation(transf_input)
        raise ValueError(f"Invalid transformation input type: {type(transf_input)}")

    def __str__(self):
        """Generates the OpenSees element string representation for display.

        Returns:
            str: A string representing the element's key properties for display.
        """
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params and key != "cMass")
        return f"{self._section.tag} {self._transformation.tag} {params_str}"

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generates the OpenSees TCL command for creating the element.

        Args:
            tag: The unique integer tag for this element in the OpenSees model.
            nodes: A list of two integer node tags [i-node, j-node]
                connected by this element.

        Returns:
            str: The OpenSees TCL command string.

        Raises:
            ValueError: If `nodes` does not contain exactly two node tags.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ElasticBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, massDens=0.5, cMass=True
            ... )
            >>> tcl_command = element.to_tcl(tag=301, nodes=[5, 6])
            >>> print(tcl_command)
            element elasticBeamColumn 301 5 6 1 1 -mass 0.5 -cMass
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
        """Returns a list of valid parameter names for this element type.

        Returns:
            list[str]: A list of strings representing the parameter names.
        """
        return ["massDens", "cMass"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns a list of descriptions for the valid parameters of this element type.

        Returns:
            list[str]: A list of strings describing each parameter.
        """
        return [
            "Element mass density per unit length (optional)",
            "Use consistent mass matrix instead of lumped (optional)"
        ]

    @staticmethod
    def get_possible_dofs():
        """Returns a list of possible degrees of freedom for this element type.

        Returns:
            list[str]: A list containing string representations of valid DOF counts.
        """
        return ["3", "6"]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, bool]]:
        """Validates a dictionary of element parameters.

        Args:
            **kwargs: Arbitrary keyword arguments representing element parameters.
                Expected parameters are 'massDens' (float) and 'cMass' (bool).

        Returns:
            dict: A dictionary containing the validated parameters.

        Raises:
            ValueError: If any parameter is invalid (e.g., wrong type, out of range).

        Example:
            >>> validated = ElasticBeamColumnElement.validate_element_parameters(
            ...     massDens=1.5, cMass=True
            ... )
            >>> print(validated)
            {'massDens': 1.5, 'cMass': True}
            >>> try:
            ...     ElasticBeamColumnElement.validate_element_parameters(massDens=-1)
            ... except ValueError as e:
            ...     print(e)
            Mass density must be non-negative
        """
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
        """Retrieves the current values for a specified list of parameters.

        Args:
            keys: A list of parameter names to retrieve values for.
                Can include 'section' and 'transformation' to get their user names.

        Returns:
            dict: A dictionary mapping parameter names to their current values.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ElasticBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, massDens=0.5, cMass=True
            ... )
            >>> values = element.get_values(['massDens', 'cMass'])
            >>> print(values['massDens'])
            0.5
            >>> print(values['cMass'])
            True
        """
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
        """Updates the element's parameters, section, or transformation.

        Args:
            values: A dictionary where keys are parameter names (e.g., 'massDens',
                'cMass', 'section', 'transformation') and values are the new
                values. 'section' and 'transformation' can be a Section/Transformation
                object, tag, or name.

        Raises:
            ValueError: If any provided parameter value is invalid.

        Example:
            >>> import femora as fm
            >>> # Assuming section (tag 1) and transformation (tag 1) exist
            >>> element = fm.ElasticBeamColumnElement(
            ...     ndof=6, section=1, transformation=1, massDens=0.5, cMass=False
            ... )
            >>> element.update_values({'massDens': 0.7, 'cMass': True})
            >>> print(element.params['massDens'])
            0.7
            >>> print(element.params['cMass'])
            True
        """
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