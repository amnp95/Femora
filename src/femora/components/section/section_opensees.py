"""
Enhanced OpenSees Section Implementations for FEMORA with Material Resolution
Based on OpenSees section types with validation and parameter management
"""

from typing import List, Dict, Union, Optional, Tuple
from abc import ABC, abstractmethod
import math
from femora.components.section.section_base import Section, SectionRegistry
from femora.components.Material.materialBase import Material
from femora.components.section.section_patch import PatchBase, RectangularPatch
from femora.components.section.section_layer import LayerBase
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle



class ElasticSection(Section):
    """Represents an elastic section in OpenSees.

    This section type defines linear elastic properties without requiring
    external material objects. It is suitable for basic elastic analysis
    or when material properties are defined directly within the section.

    Attributes:
        user_name (str): The user-defined name of the section instance.
        params (dict): A dictionary containing the section's elastic parameters.
        material (None): Elastic sections do not use external material objects.
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """Initializes the ElasticSection.

        Args:
            user_name: The user-defined name of the section instance.
            **kwargs: Keyword arguments for section parameters (E, A, Iz, Iy, G, J).

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> elastic_sec = fm.sections.ElasticSection(
            ...     user_name="W12x40_Beam", E=200000, A=7613, Iz=55.5e6
            ... )
            >>> print(elastic_sec.to_tcl())
            section Elastic 1 200000.0 7613.0 55500000.0; # W12x40_Beam
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Elastic', user_name)
        self.params = kwargs if kwargs else {}
        # Elastic sections don't require external materials
        self.material = None


    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Elastic section.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Elastic {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Elastic section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["E", "A", "Iz", "Iy", "G", "J"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Elastic section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Young's modulus",
            "Cross-sectional area",
            "Moment of inertia about local z-axis",
            "Moment of inertia about local y-axis (optional)",
            "Shear modulus (optional)",
            "Torsional constant (optional)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Elastic section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Elastic Section</b><br>
        Creates a linear elastic section with constant properties.<br><br>
        <b>Required Parameters:</b><br>
        • E: Young's modulus<br>
        • A: Cross-sectional area<br>
        • Iz: Moment of inertia about z-axis<br><br>
        <b>Optional Parameters:</b><br>
        • Iy: Moment of inertia about y-axis (3D)<br>
        • G: Shear modulus<br>
        • J: Torsional constant<br><br>
        <b>Note:</b> This section type does not require external materials.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for an Elastic section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.
        """
        required_params = ['E', 'A', 'Iz']
        optional_params = ['Iy', 'G', 'J']
        validated_params = {}

        # Check required parameters
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"ElasticSection requires the '{param}' parameter")
            try:
                value = float(kwargs[param])
                if value <= 0:
                    raise ValueError(f"'{param}' must be positive")
                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a positive number")

        # Check optional parameters
        for param in optional_params:
            if param in kwargs:
                try:
                    value = float(kwargs[param])
                    if value <= 0:
                        raise ValueError(f"'{param}' must be positive")
                    validated_params[param] = value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for '{param}'. Must be a positive number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If any updated parameter is invalid.
        """
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Elastic sections do not use external materials.

        Returns:
            List[Material]: An empty list.
        """
        return []

    def get_area(self) -> float:
        """Returns the cross-sectional area of the section.

        Returns:
            float: The cross-sectional area.
        """
        return self.params.get("A", 0.0)

    def get_Iz(self) -> float:
        """Returns the moment of inertia about the local z-axis.

        Returns:
            float: The moment of inertia about the z-axis.
        """
        return self.params.get("Iz", 0.0)

    def get_Iy(self) -> float:
        """Returns the moment of inertia about the local y-axis.

        Returns:
            float: The moment of inertia about the y-axis.
        """
        return self.params.get("Iy",0.0)

    def get_J(self) -> float:
        """Returns the torsional constant of the section.

        Returns:
            float: The torsional constant.
        """
        return self.params.get("J", 0.0)


class AggregatorSection(Section):
    """Represents an Aggregator section in OpenSees.

    This section allows combining multiple uniaxial materials, each assigned
    to a different response code (e.g., axial, moment, shear, torsion).
    It can also aggregate with an existing base section.

    Attributes:
        materials (Dict[str, Material]): A dictionary mapping response codes
            (e.g., 'P', 'Mz') to resolved Material objects.
        base_section (Optional[Section]): An optional base section whose
            behavior is aggregated with the uniaxial materials.
        material (Optional[Material]): The primary material, typically the
            first material added to `materials`.
    """

    def __init__(self, user_name: str = "Unnamed",
                 materials: Optional[Dict[str, Union[int, str, Material]]] = None,
                 base_section: Optional[Union[int, str, 'Section']] = None, **kwargs):
        """Initializes the AggregatorSection.

        Args:
            user_name: The user-defined name of the section instance.
            materials: Optional. A dictionary mapping response codes (e.g., 'P', 'Mz')
                to uniaxial materials. Materials can be provided as tags (int),
                names (str), or Material objects.
            base_section: Optional. An existing section to aggregate with. Can be
                provided as a tag (int), name (str), or Section object.
            **kwargs: Additional parameters (currently not used for Aggregator).

        Raises:
            ValueError: If `materials` is not a dictionary or contains invalid response codes.
            ValueError: If `base_section` is provided in an invalid format.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
            >>> concrete = ElasticUniaxialMaterial(user_name="Concrete_4000psi", E=30000, eta=0.0)
            >>> materials_dict = {
            ...     'P': steel,
            ...     'Mz': concrete.tag,
            ...     'Vy': "Steel_A992" # Using existing material name
            ... }
            >>> agg_sec = fm.sections.AggregatorSection(
            ...     user_name="Multi_Response_Section", materials=materials_dict
            ... )
            >>> print(agg_sec.to_tcl())
            section Aggregator 1 1 P 2 Mz 1 Vy; # Multi_Response_Section
        """
        super().__init__('section', 'Aggregator', user_name)

        # Resolve materials dictionary
        self.materials = {}
        if materials:
            self.materials = self.resolve_materials_dict(materials)

        # Resolve base section if provided
        self.base_section = None
        if base_section is not None:
            self.base_section = self.resolve_section(base_section)

        # Set primary material (first material if any)
        if self.materials:
            self.material = next(iter(self.materials.values()))
        else:
            self.material = None



    @staticmethod
    def resolve_section(section_input: Union[int, str, 'Section']) -> 'Section':
        """Resolves a section from different input types.

        Args:
            section_input: The section identifier, which can be an integer tag,
                a string name, or a Section object.

        Returns:
            Section: The resolved Section object.

        Raises:
            ValueError: If the `section_input` type is invalid or the section
                cannot be found.
        """
        if isinstance(section_input, Section):
            return section_input

        if isinstance(section_input, (int, str)):
            from femora.components.section.section_base import SectionManager
            return SectionManager.get_section(section_input)

        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def add_material(self, material_input: Union[int, str, Material], response_code: str):
        """Adds a material to the aggregator section with a specified response code.

        Args:
            material_input: The material to add, as an integer tag, string name,
                or a Material object.
            response_code: The response code this material applies to. Valid codes
                are 'P', 'Mz', 'My', 'Vy', 'Vz', 'T'.

        Raises:
            ValueError: If the `response_code` is invalid.
            ValueError: If the `material_input` cannot be resolved to a Material object.
        """
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {valid_codes}")

        material = self.resolve_material(material_input)
        self.materials[response_code] = material

        # Set as primary material if none exists
        if self.material is None:
            self.material = material

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Aggregator section.

        Returns:
            str: The TCL command string.
        """
        mat_pairs = []
        for code, material in self.materials.items():
            mat_pairs.extend([str(material.tag), code])

        tcl_cmd = f"section Aggregator {self.tag} " + " ".join(mat_pairs)

        if self.base_section:
            tcl_cmd += f" -section {self.base_section.tag}"

        tcl_cmd += f"; # {self.user_name}"
        return tcl_cmd

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section, including those
        from the base section if specified.

        Returns:
            List[Material]: A list of Material objects.
        """
        materials = list(self.materials.values())
        if self.base_section:
            materials.extend(self.base_section.get_materials())
        return materials

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Aggregator section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["materials", "base_section"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Aggregator section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Dictionary of materials mapped to response codes (P, Mz, My, Vy, Vz, T)",
            "Optional base section to aggregate with"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Aggregator section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Aggregator Section</b><br>
        Combines different uniaxial materials for different response quantities.<br><br>
        <b>Response Codes:</b><br>
        • P: Axial force<br>
        • Mz: Moment about z-axis<br>
        • My: Moment about y-axis<br>
        • Vy: Shear force in y-direction<br>
        • Vz: Shear force in z-direction<br>
        • T: Torsion<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for an Aggregator section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If `materials` is not a dictionary or contains invalid response codes.
        """
        validated_params = {}

        if 'materials' in kwargs:
            materials = kwargs['materials']
            if not isinstance(materials, dict):
                raise ValueError("Materials must be a dictionary mapping response codes to materials")

            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            for code in materials.keys():
                if code not in valid_codes:
                    raise ValueError(f"Invalid response code '{code}'. Must be one of: {valid_codes}")

            validated_params['materials'] = materials

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        if 'materials' in keys:
            values['materials'] = str(list(self.materials.keys()))
        if 'base_section' in keys:
            values['base_section'] = self.base_section.user_name if self.base_section else "None"
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Note:
            Updating materials in an AggregatorSection via `update_values` is complex
            and not fully supported by this method due to the nested dictionary structure.
            Use `add_material` or re-initialize for comprehensive material changes.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If `base_section` is updated with an invalid value.
        """
        if 'materials' in values:
            # This would need custom parsing logic for materials
            pass
        if 'base_section' in values and values['base_section'] != "None":
            self.base_section = self.resolve_section(values['base_section'])


class UniaxialSection(Section):
    """Represents a Uniaxial section in OpenSees.

    This section uses a single uniaxial material to define the force-deformation
    behavior for a specific response code (e.g., axial force 'P' or bending moment 'Mz').

    Attributes:
        material (Material): The uniaxial material object assigned to this section.
        response_code (str): The specific response code (e.g., 'P', 'Mz') that
            this material governs.
        params (Dict[str, Union[Material, str]]): A dictionary storing the
            `material` object and `response_code`.
    """

    def __init__(self, user_name: str = "Unnamed",
                 material: Union[int, str, Material] = None,
                 response_code: str = "P", **kwargs):
        """Initializes the UniaxialSection.

        Args:
            user_name: The user-defined name of the section instance.
            material: The uniaxial material for the section, as an integer tag,
                string name, or a Material object.
            response_code: The response code (e.g., 'P', 'Mz') this material represents.
                Valid codes are 'P', 'Mz', 'My', 'Vy', 'Vz', 'T'.
            **kwargs: Additional parameters (currently not used for Uniaxial).

        Raises:
            ValueError: If `material` is None.
            ValueError: If `response_code` is invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
            >>> uniaxial_sec = fm.sections.UniaxialSection(
            ...     user_name="Steel_Axial", material=steel, response_code="P"
            ... )
            >>> print(uniaxial_sec.to_tcl())
            section Uniaxial 1 1 P; # Steel_Axial
        """
        super().__init__('section', 'Uniaxial', user_name)

        # Resolve and store material
        if material is None:
            raise ValueError("UniaxialSection requires a material")
        self.material = self.resolve_material(material)

        # Validate and store response code
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Response code must be one of: {valid_codes}")
        self.response_code = response_code

        # Store in params for consistency
        self.params = {
            'material': self.material,
            'response_code': response_code
        }

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Uniaxial section.

        Returns:
            str: The TCL command string.
        """
        return f"section Uniaxial {self.tag} {self.material.tag} {self.response_code}; # {self.user_name}"

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Returns:
            List[Material]: A list containing the single Material object.
        """
        return [self.material]

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Uniaxial section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["material", "response_code"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Uniaxial section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Uniaxial material to use (tag, name, or object)",
            "Response code (P, Mz, My, Vy, Vz, T)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Uniaxial section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Uniaxial Section</b><br>
        Uses a single uniaxial material for one response quantity.<br><br>
        Specify the material and the response code it represents.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a Uniaxial section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If `response_code` is invalid.
        """
        validated_params = {}

        if 'response_code' in kwargs:
            response_code = kwargs['response_code']
            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            if response_code not in valid_codes:
                raise ValueError(f"Response code must be one of: {valid_codes}")
            validated_params['response_code'] = response_code

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        if 'material' in keys:
            values['material'] = self.material.user_name if self.material else "None"
        if 'response_code' in keys:
            values['response_code'] = self.response_code
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If the `material` or `response_code` update is invalid.
        """
        if 'material' in values:
            self.material = self.resolve_material(values['material'])
            self.params['material'] = self.material
        if 'response_code' in values:
            self.response_code = values['response_code']
            self.params['response_code'] = self.response_code


class FiberElement:
    """Represents a single fiber within a fiber section.

    Each fiber has a defined location (y, z coordinates), a cross-sectional area,
    and an associated material property. It's a fundamental component for fiber-discretized
    section analysis.

    Attributes:
        y_loc (float): The y-coordinate of the fiber.
        z_loc (float): The z-coordinate of the fiber.
        area (float): The cross-sectional area of the fiber.
        material (Material): The material object assigned to this fiber.
    """

    def __init__(self, y_loc: float, z_loc: float, area: float,
                 material: Union[int, str, Material]):
        """Initializes a FiberElement.

        Args:
            y_loc: The y-coordinate of the fiber's centroid.
            z_loc: The z-coordinate of the fiber's centroid.
            area: The cross-sectional area of the fiber. Must be positive.
            material: The material for the fiber, as an integer tag, string name,
                or a Material object.

        Raises:
            ValueError: If coordinates or area are non-numeric, if area is not positive,
                or if the material cannot be resolved.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
            >>> fiber = fm.sections.FiberElement(y_loc=0.0, z_loc=0.1, area=0.001, material=steel)
            >>> print(fiber.to_tcl())
                fiber 0.0 0.1 0.001 1
        """
        # Validate and convert inputs
        try:
            self.y_loc = float(y_loc)
            self.z_loc = float(z_loc)
            self.area = float(area)
        except (ValueError, TypeError):
            raise ValueError("Fiber coordinates and area must be numeric values")

        if self.area <= 0:
            raise ValueError("Fiber area must be positive")

        # Resolve material
        self.material = Section.resolve_material(material)
        if self.material is None:
            raise ValueError("Fiber requires a valid material")

    def plot(self, ax: plt.Axes, material_colors: Dict[str, str],
             scale_factor: float = 1.0, show_fibers: bool = True) -> None:
        """Plots the fiber on the given matplotlib axes.

        Args:
            ax: The matplotlib axes object to draw on.
            material_colors: A dictionary mapping material names to colors for plotting.
            scale_factor: A factor to scale the visual size of the fiber for clarity.
            show_fibers: If False, the fiber will not be plotted.
        """
        if not show_fibers:
            return

        # Get color for this material
        color = material_colors.get(self.material.user_name, 'blue')

        # Calculate fiber size for visualization (proportional to sqrt(area))
        fiber_size = math.sqrt(self.area) * scale_factor

        # Plot fiber as a circle
        circle = Circle((self.y_loc, self.z_loc), fiber_size/2,
                       facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.7)
        ax.add_patch(circle)

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for this fiber.

        Returns:
            str: The TCL command string for a single fiber.
        """
        return f"    fiber {self.y_loc} {self.z_loc} {self.area} {self.material.tag}"

    def __str__(self) -> str:
        """Returns a string representation of the FiberElement.

        Returns:
            str: A descriptive string for the fiber.
        """
        return f"Fiber at ({self.y_loc}, {self.z_loc}) with area {self.area}, material '{self.material.user_name}'"


class WFSection2d(Section):
    """Represents a Wide-Flange (WF) section for 2D problems using fiber discretization.

    This section type simplifies the creation of a fiber-discretized WF section by
    automatically generating fibers based on geometric properties and a single uniaxial material.

    Attributes:
        material (Material): The uniaxial material object assigned to all fibers
            within this WF section.
        params (dict): A dictionary containing the geometric parameters
            (d, tw, bf, tf, Nflweb, Nflflange).
    """

    def __init__(self, user_name: str = "Unnamed",
                 material: Union[int, str, Material] = None, **kwargs):
        """Initializes the WFSection2d.

        Args:
            user_name: The user-defined name of the section instance.
            material: The uniaxial material for the section, as an integer tag,
                string name, or a Material object. This material will be applied to all fibers.
            **kwargs: Keyword arguments for geometric parameters (d, tw, bf, tf, Nflweb, Nflflange).

        Raises:
            ValueError: If `material` is None.
            ValueError: If any required geometric parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
            >>> wf_sec = fm.sections.WFSection2d(
            ...     user_name="W14x68_Section", material=steel,
            ...     d=355.6, tw=10.5, bf=254.0, tf=17.3, Nflweb=8, Nflflange=4
            ... )
            >>> print(wf_sec.to_tcl())
            section WFSection2d 1 355.6 10.5 254.0 17.3 8 4 1; # W14x68_Section
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'WFSection2d', user_name)

        # Resolve and store material
        if material is None:
            raise ValueError("WFSection2d requires a material")
        self.material = self.resolve_material(material)

        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the WFSection2d.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()[:-1]  # Exclude 'material' from params
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section WFSection2d {self.tag} {params_str} {self.material.tag}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the WFSection2d.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["d", "tw", "bf", "tf", "Nflweb", "Nflflange", "material"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the WFSection2d parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Depth of the section",
            "Web thickness",
            "Flange width",
            "Flange thickness",
            "Number of fibers in the web",
            "Number of fibers in each flange",
            "Uniaxial material (tag, name, or object)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the WFSection2d.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>WF Section 2D</b><br>
        Wide-flange section for 2D problems using fiber discretization.<br><br>
        <b>Required Parameters:</b><br>
        • d: Depth of the section<br>
        • tw: Web thickness<br>
        • bf: Flange width<br>
        • tf: Flange thickness<br>
        • Nflweb: Number of fibers in web<br>
        • Nflflange: Number of fibers in each flange<br>
        • material: UniaxialMaterial for all fibers<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a WFSection2d.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.
        """
        required_params = ['d', 'tw', 'bf', 'tf', 'Nflweb', 'Nflflange']
        validated_params = {}

        # Check required parameters
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"WFSection2d requires the '{param}' parameter")

            if param in ['Nflweb', 'Nflflange']:
                # Integer parameters
                try:
                    value = int(kwargs[param])
                    if value <= 0:
                        raise ValueError(f"'{param}' must be a positive integer")
                    validated_params[param] = value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for '{param}'. Must be a positive integer")
            else:
                # Float parameters
                try:
                    value = float(kwargs[param])
                    if value <= 0:
                        raise ValueError(f"'{param}' must be positive")
                    validated_params[param] = value
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid value for '{param}'. Must be a positive number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        for key in keys:
            if key == 'material':
                values[key] = self.material.user_name if self.material else "None"
            else:
                values[key] = self.params.get(key)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If `material` or any geometric parameter update is invalid.
        """
        if 'material' in values:
            self.material = self.resolve_material(values['material'])
            del values['material']

        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Returns:
            List[Material]: A list containing the single Material object if assigned.
        """
        return [self.material] if self.material else []


class PlateFiberSection(Section):
    """Represents a PlateFiber section for shell elements.

    This section type is used with shell elements to define fiber-discretized
    behavior through the plate thickness. It requires an nDMaterial compatible
    with plane-stress conditions.

    Attributes:
        material (Material): The nDMaterial object assigned to the plate fibers.
        params (dict): A dictionary of additional parameters (currently empty).
    """

    def __init__(self, user_name: str = "Unnamed",
                 material: Union[int, str, Material] = None, **kwargs):
        """Initializes the PlateFiberSection.

        Args:
            user_name: The user-defined name of the section instance.
            material: The nDMaterial for plane stress, as an integer tag,
                string name, or a Material object.
            **kwargs: Additional parameters (currently not used for PlateFiber).

        Raises:
            ValueError: If `material` is None.
            ValueError: If the resolved material is not an nDMaterial.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
            >>> plate_material = ElasticIsotropicMaterial(
            ...     user_name="Plate_Steel", E=200000, nu=0.3, rho=7.85e-9
            ... )
            >>> plate_sec = fm.sections.PlateFiberSection(
            ...     user_name="Shell_Section", material=plate_material
            ... )
            >>> print(plate_sec.to_tcl())
            section PlateFiber 1 1; # Shell_Section
        """
        super().__init__('section', 'PlateFiber', user_name)

        # Resolve and store material
        if material is None:
            raise ValueError("PlateFiberSection requires a material")
        self.material = self.resolve_material(material)

        # Validate that material is NDMaterial (plane stress compatible)
        if self.material and hasattr(self.material, 'material_type'):
            if self.material.material_type != 'nDMaterial':
                raise ValueError("PlateFiberSection requires an nDMaterial for plane stress behavior")

        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the PlateFiber section.

        Returns:
            str: The TCL command string.
        """
        return f"section PlateFiber {self.tag} {self.material.tag}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the PlateFiber section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["material"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the PlateFiber section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return ["NDMaterial for plane stress behavior (tag, name, or object)"]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the PlateFiber section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Plate Fiber Section</b><br>
        Used with shell elements for fiber-discretized behavior through plate thickness.<br><br>
        <b>Required Parameters:</b><br>
        • material: NDMaterial compatible with plane stress<br><br>
        <b>Materials:</b> Accepts NDMaterial objects, tags, or names<br>
        <b>Note:</b> Material must be compatible with plane stress conditions
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a PlateFiber section.

        This section type has no additional parameters to validate beyond the material.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: An empty dictionary of validated parameters.
        """
        # No additional parameters to validate beyond material
        return {}

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        if 'material' in keys:
            values['material'] = self.material.user_name if self.material else "None"
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If the `material` update is invalid or not an nDMaterial.
        """
        if 'material' in values:
            self.material = self.resolve_material(values['material'])

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Returns:
            List[Material]: A list containing the single Material object if assigned.
        """
        return [self.material] if self.material else []


class ElasticMembranePlateSection(Section):
    """Represents an ElasticMembranePlateSection for shell elements.

    This section models shell elements with linear elastic membrane and plate
    behavior. It uses built-in properties (E, nu, h, rho) and does not require
    external material objects.

    Attributes:
        params (dict): A dictionary containing the section's elastic properties
            (E, nu, h, rho).
        material (None): Elastic membrane plate sections do not use external
            material objects.
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """Initializes the ElasticMembranePlateSection.

        Args:
            user_name: The user-defined name of the section instance.
            **kwargs: Keyword arguments for section parameters (E, nu, h, rho).

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> membrane_sec = fm.sections.ElasticMembranePlateSection(
            ...     user_name="Membrane_Section", E=200000, nu=0.3, h=0.02, rho=7.85e-9
            ... )
            >>> print(membrane_sec.to_tcl())
            section ElasticMembranePlateSection 1 200000.0 0.3 0.02 7.85e-09; # Membrane_Section
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'ElasticMembranePlateSection', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the ElasticMembranePlateSection.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section ElasticMembranePlateSection {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the ElasticMembranePlateSection.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["E", "nu", "h", "rho"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the ElasticMembranePlateSection parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Young's modulus",
            "Poisson's ratio",
            "Plate thickness",
            "Mass density"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the ElasticMembranePlateSection.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Elastic Membrane Plate Section</b><br>
        Elastic section for membrane-plate behavior in shell elements.<br><br>
        <b>Required Parameters:</b><br>
        • E: Young's modulus<br>
        • nu: Poisson's ratio<br>
        • h: Plate thickness<br>
        • rho: Mass density<br><br>
        <b>Note:</b> This section type does not require external materials.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for an ElasticMembranePlateSection.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.
        """
        required_params = ['E', 'nu', 'h', 'rho']
        validated_params = {}

        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"ElasticMembranePlateSection requires the '{param}' parameter")

            try:
                value = float(kwargs[param])

                # Parameter-specific validations
                if param == 'E' and value <= 0:
                    raise ValueError("Young's modulus 'E' must be positive")
                elif param == 'nu' and not (0 <= value < 0.5):
                    raise ValueError("Poisson's ratio 'nu' must be in range [0, 0.5)")
                elif param == 'h' and value <= 0:
                    raise ValueError("Plate thickness 'h' must be positive")
                elif param == 'rho' and value < 0:
                    raise ValueError("Mass density 'rho' must be non-negative")

                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If any updated parameter is invalid.
        """
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Elastic membrane plate sections do not use external materials.

        Returns:
            List[Material]: An empty list.
        """
        return []


class RCSection(Section):
    """Represents a Reinforced Concrete (RC) section in OpenSees.

    This specialized section allows for individual material definitions for
    core concrete, cover concrete, and steel reinforcement, as well as geometric
    properties of the section.

    Attributes:
        core_material (Material): The uniaxial material object for the core concrete.
        cover_material (Material): The uniaxial material object for the cover concrete.
        steel_material (Material): The uniaxial material object for the steel reinforcement.
        material (Material): The primary material, set to `core_material`.
        params (dict): A dictionary containing the geometric parameters (d, b,
            cover_to_center_of_bar).
    """

    def __init__(self, user_name: str = "Unnamed",
                 core_material: Union[int, str, Material] = None,
                 cover_material: Union[int, str, Material] = None,
                 steel_material: Union[int, str, Material] = None,
                 **kwargs):
        """Initializes the RCSection.

        Args:
            user_name: The user-defined name of the section instance.
            core_material: The uniaxial material for core concrete, as an integer tag,
                string name, or a Material object.
            cover_material: The uniaxial material for cover concrete, as an integer tag,
                string name, or a Material object.
            steel_material: The uniaxial material for steel reinforcement, as an integer tag,
                string name, or a Material object.
            **kwargs: Keyword arguments for geometric parameters (d, b, cover_to_center_of_bar).

        Raises:
            ValueError: If any material (core, cover, steel) is None.
            ValueError: If any required geometric parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> conc_core = ElasticUniaxialMaterial(user_name="Conc_Core", E=30000, eta=0.0)
            >>> conc_cover = ElasticUniaxialMaterial(user_name="Conc_Cover", E=25000, eta=0.0)
            >>> steel_rebar = ElasticUniaxialMaterial(user_name="Rebar", E=200000, eta=0.0)
            >>> rc_sec = fm.sections.RCSection(
            ...     user_name="RC_Column",
            ...     core_material=conc_core,
            ...     cover_material=conc_cover,
            ...     steel_material=steel_rebar,
            ...     d=0.4, b=0.4, cover_to_center_of_bar=0.05
            ... )
            >>> print(rc_sec.to_tcl())
            section RC 1 1 2 3 0.4 0.4 0.05; # RC_Column
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'RC', user_name)

        # Resolve materials
        if core_material is None:
            raise ValueError("RCSection requires a core_material")
        if cover_material is None:
            raise ValueError("RCSection requires a cover_material")
        if steel_material is None:
            raise ValueError("RCSection requires a steel_material")

        self.core_material = self.resolve_material(core_material)
        self.cover_material = self.resolve_material(cover_material)
        self.steel_material = self.resolve_material(steel_material)

        # Set primary material to core material
        self.material = self.core_material

        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the RC section.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()[3:]  # Skip material parameters
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return (f"section RC {self.tag} {self.core_material.tag} {self.cover_material.tag} "
                f"{self.steel_material.tag} {params_str}; # {self.user_name}")

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the RC section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["core_material", "cover_material", "steel_material", "d", "b", "cover_to_center_of_bar"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the RC section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Core concrete material (tag, name, or object)",
            "Cover concrete material (tag, name, or object)",
            "Steel reinforcement material (tag, name, or object)",
            "Section depth",
            "Section width",
            "Cover distance to reinforcement centroid"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the RC section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>RC Section</b><br>
        Specialized reinforced concrete section with separate materials.<br><br>
        <b>Required Parameters:</b><br>
        • core_material: UniaxialMaterial for core concrete<br>
        • cover_material: UniaxialMaterial for cover concrete<br>
        • steel_material: UniaxialMaterial for steel reinforcement<br>
        • d: Section depth<br>
        • b: Section width<br>
        • cover_to_center_of_bar: Cover distance to reinforcement centroid<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for an RC section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required geometric parameter is missing or has an invalid value.
        """
        required_params = ['d', 'b', 'cover_to_center_of_bar']
        validated_params = {}

        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"RCSection requires the '{param}' parameter")

            try:
                value = float(kwargs[param])
                if value <= 0:
                    raise ValueError(f"'{param}' must be positive")
                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a positive number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        for key in keys:
            if key == 'core_material':
                values[key] = self.core_material.user_name if self.core_material else "None"
            elif key == 'cover_material':
                values[key] = self.cover_material.user_name if self.cover_material else "None"
            elif key == 'steel_material':
                values[key] = self.steel_material.user_name if self.steel_material else "None"
            else:
                values[key] = self.params.get(key)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If any material or geometric parameter update is invalid.
        """
        material_updates = {}
        param_updates = {}

        for key, value in values.items():
            if key in ['core_material', 'cover_material', 'steel_material']:
                material_updates[key] = value
            else:
                param_updates[key] = value

        # Update materials
        if 'core_material' in material_updates:
            self.core_material = self.resolve_material(material_updates['core_material'])
            self.material = self.core_material
        if 'cover_material' in material_updates:
            self.cover_material = self.resolve_material(material_updates['cover_material'])
        if 'steel_material' in material_updates:
            self.steel_material = self.resolve_material(material_updates['steel_material'])

        # Update other parameters
        if param_updates:
            validated_params = self.validate_section_parameters(**param_updates)
            self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all unique materials used by this section.

        Returns:
            List[Material]: A list of Material objects.
        """
        materials = []
        if self.core_material:
            materials.append(self.core_material)
        if self.cover_material and self.cover_material not in materials:
            materials.append(self.cover_material)
        if self.steel_material and self.steel_material not in materials:
            materials.append(self.steel_material)
        return materials


class ParallelSection(Section):
    """Combines several existing sections in parallel to sum their force-deformation behaviors.

    This section type is useful for modeling composite sections or for aggregating
    the response of multiple structural components.

    Attributes:
        sections (List[Section]): A list of Section objects that are combined in parallel.
        material (Optional[Material]): The primary material, derived from the first
            material found in the combined sections.
        params (dict): A dictionary of additional parameters (currently empty).
    """

    def __init__(self, user_name: str = "Unnamed",
                 sections: Optional[List[Union[int, str, 'Section']]] = None, **kwargs):
        """Initializes the ParallelSection.

        Args:
            user_name: The user-defined name of the section instance.
            sections: Optional. A list of existing sections to combine in parallel.
                Each item can be an integer tag, a string name, or a Section object.
            **kwargs: Additional parameters (currently not used for ParallelSection).

        Raises:
            ValueError: If any item in the `sections` list cannot be resolved to a Section object.

        Example:
            >>> import femora as fm
            >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
            >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
            >>> elastic_sec = fm.sections.ElasticSection(
            ...     user_name="W12x40_Beam", E=200000, A=7613, Iz=55.5e6
            ... )
            >>> uniaxial_sec = fm.sections.UniaxialSection(
            ...     user_name="Steel_Axial", material=steel, response_code="P"
            ... )
            >>> parallel_sec = fm.sections.ParallelSection(
            ...     user_name="Combined_Section", sections=[elastic_sec, uniaxial_sec]
            ... )
            >>> print(parallel_sec.to_tcl())
            section Parallel 1 1 2; # Combined_Section
        """
        super().__init__('section', 'Parallel', user_name)

        # Resolve sections
        self.sections = []
        if sections:
            for section_input in sections:
                resolved_section = self.resolve_section(section_input)
                self.sections.append(resolved_section)

        # Set primary material to first section's material if available
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

        self.params = kwargs if kwargs else {}

    @staticmethod
    def resolve_section(section_input: Union[int, str, 'Section']) -> 'Section':
        """Resolves a section from different input types.

        Args:
            section_input: The section identifier, which can be an integer tag,
                a string name, or a Section object.

        Returns:
            Section: The resolved Section object.

        Raises:
            ValueError: If the `section_input` type is invalid or the section
                cannot be found.
        """
        if isinstance(section_input, Section):
            return section_input

        if isinstance(section_input, (int, str)):
            from femora.components.section.section_base import SectionManager
            return SectionManager.get_section(section_input)

        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def add_section(self, section_input: Union[int, str, 'Section']) -> None:
        """Adds a section to the parallel combination.

        Args:
            section_input: The section to add, as an integer tag, string name,
                or a Section object.

        Raises:
            ValueError: If the `section_input` cannot be resolved to a Section object.
        """
        resolved_section = self.resolve_section(section_input)
        self.sections.append(resolved_section)

        # Update primary material if none exists
        if self.material is None:
            section_materials = resolved_section.get_materials()
            if section_materials:
                self.material = section_materials[0]

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Parallel section.

        Returns:
            str: The TCL command string.
        """
        section_tags = " ".join(str(sec.tag) for sec in self.sections)
        return f"section Parallel {self.tag} {section_tags}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Parallel section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["sections"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Parallel section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return ["List of existing sections to combine in parallel (tags, names, or objects)"]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Parallel section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Parallel Section</b><br>
        Combines several existing sections in parallel to sum their behaviors.<br><br>
        <b>Required Parameters:</b><br>
        • sections: List of existing sections to combine<br><br>
        <b>Note:</b> Sections can be specified as objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a Parallel section.

        This section type has no additional parameters to validate.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: An empty dictionary of validated parameters.
        """
        # No additional parameters to validate
        return {}

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        if 'sections' in keys:
            values['sections'] = ", ".join(sec.user_name for sec in self.sections)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Note:
            Updating the list of `sections` for a ParallelSection via `update_values`
            is complex due to the potential for nested resolution and is not
            fully supported by this method. Use `add_section` or re-initialize
            for comprehensive changes.

        Args:
            values: A dictionary of parameter names and their new values.
        """
        if 'sections' in values:
            # This would need custom parsing logic for section names/tags
            pass

    def get_materials(self) -> List[Material]:
        """Returns a list of all unique materials used by the combined sections.

        Returns:
            List[Material]: A list of Material objects.
        """
        materials = []
        for section in self.sections:
            for material in section.get_materials():
                if material not in materials:
                    materials.append(material)
        return materials


class BidirectionalSection(Section):
    """Represents a Bidirectional section in OpenSees.

    This section models biaxial moment interaction with axial force using a
    built-in yield surface. It defines its own plasticity parameters and
    does not require external material objects.

    Attributes:
        params (dict): A dictionary containing the section's properties
            (E, Fy, Hiso, Hkin).
        material (None): Bidirectional sections do not use external material objects.
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """Initializes the BidirectionalSection.

        Args:
            user_name: The user-defined name of the section instance.
            **kwargs: Keyword arguments for section parameters (E, Fy, Hiso, Hkin).

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> bidirectional_sec = fm.sections.BidirectionalSection(
            ...     user_name="Biaxial_Section", E=200000, Fy=350, Hiso=1000, Hkin=500
            ... )
            >>> print(bidirectional_sec.to_tcl())
            section Bidirectional 1 200000.0 350.0 1000.0 500.0; # Biaxial_Section
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Bidirectional', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Bidirectional section.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Bidirectional {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Bidirectional section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["E", "Fy", "Hiso", "Hkin"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Bidirectional section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Elastic modulus",
            "Yield strength",
            "Isotropic hardening parameter",
            "Kinematic hardening parameter"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Bidirectional section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Bidirectional Section</b><br>
        Combines biaxial moment interaction with axial force using built-in yield surface.<br><br>
        <b>Required Parameters:</b><br>
        • E: Elastic modulus<br>
        • Fy: Yield strength<br>
        • Hiso: Isotropic hardening parameter<br>
        • Hkin: Kinematic hardening parameter<br><br>
        <b>Note:</b> This section type uses built-in plasticity models.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a Bidirectional section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.
        """
        required_params = ['E', 'Fy', 'Hiso', 'Hkin']
        validated_params = {}

        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"BidirectionalSection requires the '{param}' parameter")

            try:
                value = float(kwargs[param])
                if param in ['E', 'Fy'] and value <= 0:
                    raise ValueError(f"'{param}' must be positive")
                elif param in ['Hiso', 'Hkin'] and value < 0:
                    raise ValueError(f"'{param}' must be non-negative")
                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If any updated parameter is invalid.
        """
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Bidirectional sections do not use external materials.

        Returns:
            List[Material]: An empty list.
        """
        return []


class Isolator2SpringSection(Section):
    """Represents an Isolator2spring section for base isolation systems.

    This section models base isolation systems with bidirectional behavior and
    vertical coupling using built-in isolator behavior. It defines its own
    mechanical properties and does not require external material objects.

    Attributes:
        params (dict): A dictionary containing the section's properties
            (tol, k1, Fy, k2, kv, hb, Pe, Po).
        material (None): Isolator2spring sections do not use external material objects.
    """

    def __init__(self, user_name: str = "Unnamed", **kwargs):
        """Initializes the Isolator2springSection.

        Args:
            user_name: The user-defined name of the section instance.
            **kwargs: Keyword arguments for section parameters (tol, k1, Fy, k2, kv, hb, Pe, Po).

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.

        Example:
            >>> import femora as fm
            >>> isolator_sec = fm.sections.Isolator2SpringSection(
            ...     user_name="Base_Isolator", tol=1e-6, k1=2000, Fy=100, k2=200,
            ...     kv=20000, hb=0.15, Pe=1000, Po=50
            ... )
            >>> print(isolator_sec.to_tcl())
            section Isolator2spring 1 1e-06 2000.0 100.0 200.0 20000.0 0.15 1000.0 50.0; # Base_Isolator
        """
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Isolator2spring', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command for the Isolator2spring section.

        Returns:
            str: The TCL command string.
        """
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Isolator2spring {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Isolator2spring section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["tol", "k1", "Fy", "k2", "kv", "hb", "Pe", "Po"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Isolator2spring section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Tolerance for convergence",
            "Initial stiffness",
            "Yield force",
            "Post-yield stiffness",
            "Vertical stiffness",
            "Isolation height",
            "Buckling load",
            "Vertical load"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Isolator2spring section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Isolator 2Spring Section</b><br>
        Used for modeling base isolation systems with bidirectional behavior.<br><br>
        <b>Required Parameters:</b><br>
        • tol: Tolerance for convergence<br>
        • k1: Initial stiffness<br>
        • Fy: Yield force<br>
        • k2: Post-yield stiffness<br>
        • kv: Vertical stiffness<br>
        • hb: Isolation height<br>
        • Pe: Buckling load<br>
        • Po: Vertical load<br><br>
        <b>Note:</b> This section type uses built-in isolator behavior.
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for an Isolator2spring section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If any required parameter is missing or has an invalid value.
        """
        required_params = ['tol', 'k1', 'Fy', 'k2', 'kv', 'hb', 'Pe', 'Po']
        validated_params = {}

        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Isolator2SpringSection requires the '{param}' parameter")

            try:
                value = float(kwargs[param])

                # Parameter-specific validations
                if param == 'tol' and value <= 0:
                    raise ValueError("Tolerance 'tol' must be positive")
                elif param in ['k1', 'k2', 'kv'] and value <= 0:
                    raise ValueError(f"Stiffness '{param}' must be positive")
                elif param in ['Fy', 'hb'] and value <= 0:
                    raise ValueError(f"'{param}' must be positive")
                elif param in ['Pe', 'Po'] and value < 0:
                    raise ValueError(f"'{param}' must be non-negative")

                validated_params[param] = value
            except (ValueError, TypeError):
                raise ValueError(f"Invalid value for '{param}'. Must be a number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If any updated parameter is invalid.
        """
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Returns a list of all materials used by this section.

        Isolator2spring sections do not use external materials.

        Returns:
            List[Material]: An empty list.
        """
        return []


class FiberSection(Section):
    """Represents a complete Fiber Section implementation for OpenSees.

    This section allows for defining complex cross-sections using individual
    fibers, patches, and layers. Each component can have its own material,
    enabling detailed nonlinear analysis.

    Attributes:
        fibers (List[FiberElement]): A list of individual FiberElement objects
            added to the section.
        patches (List[PatchBase]): A list of PatchBase objects (e.g., RectangularPatch,
            CircularPatch) that generate multiple fibers.
        layers (List[LayerBase]): A list of LayerBase objects (e.g., StraightLayer,
            CircularLayer) that generate multiple fibers along a line or arc.
        GJ (Optional[float]): The linear-elastic torsional stiffness of the section.
        material (Optional[Material]): The primary material, typically the first
            material found among all components.
        params (dict): A dictionary of additional parameters (currently empty).

    Example:
        >>> import femora as fm
        >>> from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
        >>> from femora.components.section.section_patch import RectangularPatch
        >>> from femora.components.section.section_layer import StraightLayer
        >>> steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
        >>> concrete = ElasticUniaxialMaterial(user_name="Concrete_4000psi", E=30000, eta=0.0)
        >>>
        >>> fiber_sec = fm.sections.FiberSection("RC_Beam_Section", GJ=1.5e6)
        >>> fiber_sec.add_rectangular_patch(concrete, 12, 8, -0.15, -0.25, 0.15, 0.25)
        >>> fiber_sec.add_straight_layer(steel, 4, 0.0005, -0.12, -0.22, 0.12, -0.22)
        >>> print(fiber_sec.to_tcl()) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        section Fiber 1 -GJ 1500000.0 {
            patch rect 2 12 8 -0.15 -0.25 0.15 0.25
            layer straight 1 4 0.0005 -0.12 -0.22 0.12 -0.22
        }; # RC_Beam_Section
    """

    def __init__(self, user_name: str = "Unnamed", GJ: Optional[float] = None,
                 components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None, **kwargs):
        """Initializes the FiberSection.

        Args:
            user_name: The user-defined name of the section instance.
            GJ: Optional. The linear-elastic torsional stiffness. Must be a positive number.
            components: Optional. A list of FiberElement, PatchBase, or LayerBase objects
                to initialize the section with.
            **kwargs: Additional parameters (currently not used for FiberSection).

        Raises:
            ValueError: If `GJ` is non-numeric or not positive.
            ValueError: If any item in the `components` list is not a valid fiber section component.
        """
        super().__init__('section', 'Fiber', user_name)

        # Initialize collections
        self.fibers: List[FiberElement] = []
        self.patches: List[PatchBase] = []
        self.layers: List[LayerBase] = []

        # Process components list
        if components is not None:
            for i, component in enumerate(components):
                if isinstance(component, FiberElement):
                    self.fibers.append(component)
                elif isinstance(component, PatchBase):
                    self.patches.append(component)
                elif isinstance(component, LayerBase):
                    self.layers.append(component)
                else:
                    raise ValueError(f"Item {i} in components list is not a valid fiber section component")

        # Handle optional torsional stiffness
        self.GJ = None
        if GJ is not None:
            try:
                self.GJ = float(GJ)
                if self.GJ <= 0:
                    raise ValueError("GJ (torsional stiffness) must be positive")
            except (ValueError, TypeError):
                raise ValueError("GJ must be a positive number")

        # Set primary material to first found material
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

        self.params = kwargs if kwargs else {}

    def add_fiber(self, y_loc: float, z_loc: float, area: float,
                  material: Union[int, str, Material]) -> None:
        """Adds an individual fiber to the section.

        Args:
            y_loc: The y-coordinate of the fiber.
            z_loc: The z-coordinate of the fiber.
            area: The area of the fiber.
            material: The material for the fiber, as an integer tag, string name,
                or a Material object.
        """
        fiber = FiberElement(y_loc, z_loc, area, material)
        self.fibers.append(fiber)

        # Update primary material if none exists
        if self.material is None:
            self.material = fiber.material

    def add_rectangular_patch(self, material: Union[int, str, Material],
                            num_subdiv_y: int, num_subdiv_z: int,
                            y1: float, z1: float, y2: float, z2: float) -> None:
        """Adds a rectangular patch to the section.

        Args:
            material: The material for the patch's fibers, as an integer tag,
                string name, or a Material object.
            num_subdiv_y: Number of subdivisions along the y-axis.
            num_subdiv_z: Number of subdivisions along the z-axis.
            y1: Minimum y-coordinate of the patch.
            z1: Minimum z-coordinate of the patch.
            y2: Maximum y-coordinate of the patch.
            z2: Maximum z-coordinate of the patch.
        """
        from femora.components.section.section_patch import RectangularPatch
        patch = RectangularPatch(material, num_subdiv_y, num_subdiv_z, y1, z1, y2, z2)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_quadrilateral_patch(self, material: Union[int, str, Material],
                             num_subdiv_ij: int, num_subdiv_jk: int,
                             vertices: list) -> None:
        """Adds a quadrilateral patch to the section.

        Args:
            material: The material for the patch's fibers, as an integer tag,
                string name, or a Material object.
            num_subdiv_ij: Number of subdivisions along the first edge (i to j).
            num_subdiv_jk: Number of subdivisions along the second edge (j to k).
            vertices: A list of 4 (y, z) tuples defining the quadrilateral vertices.
        """
        from femora.components.section.section_patch import QuadrilateralPatch
        patch = QuadrilateralPatch(material, num_subdiv_ij, num_subdiv_jk, vertices)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_circular_patch(self, material: Union[int, str, Material],
                         num_subdiv_circ: int, num_subdiv_rad: int,
                         y_center: float, z_center: float, int_rad: float, ext_rad: float,
                         start_ang: float = 0.0, end_ang: float = 360.0) -> None:
        """Adds a circular patch (or annulus) to the section.

        Args:
            material: The material for the patch's fibers, as an integer tag,
                string name, or a Material object.
            num_subdiv_circ: Number of subdivisions in the circumferential direction.
            num_subdiv_rad: Number of subdivisions in the radial direction.
            y_center: The y-coordinate of the circular patch's center.
            z_center: The z-coordinate of the circular patch's center.
            int_rad: The inner radius of the circular patch.
            ext_rad: The outer radius of the circular patch.
            start_ang: Optional. The start angle in degrees for the circular arc (default: 0).
            end_ang: Optional. The end angle in degrees for the circular arc (default: 360).
        """
        from femora.components.section.section_patch import CircularPatch
        patch = CircularPatch(material, num_subdiv_circ, num_subdiv_rad, y_center, z_center, int_rad, ext_rad, start_ang, end_ang)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_straight_layer(self, material: Union[int, str, Material],
                         num_fibers: int, area_per_fiber: float,
                         y1: float, z1: float, y2: float, z2: float) -> None:
        """Adds a straight layer of fibers to the section.

        Args:
            material: The material for the layer's fibers, as an integer tag,
                string name, or a Material object.
            num_fibers: The number of fibers to create along the line.
            area_per_fiber: The cross-sectional area for each fiber in the layer.
            y1: The y-coordinate of the start point of the line.
            z1: The z-coordinate of the start point of the line.
            y2: The y-coordinate of the end point of the line.
            z2: The z-coordinate of the end point of the line.
        """
        from femora.components.section.section_layer import StraightLayer
        layer = StraightLayer(material, num_fibers, area_per_fiber, y1, z1, y2, z2)
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def add_circular_layer(self, material: Union[int, str, Material],
                         num_fibers: int, area_per_fiber: float,
                         y_center: float, z_center: float, radius: float,
                         start_ang: float = 0.0, end_ang: Optional[float] = None) -> None:
        """Adds a circular layer of fibers to the section.

        Args:
            material: The material for the layer's fibers, as an integer tag,
                string name, or a Material object.
            num_fibers: The number of fibers to create along the circular arc.
            area_per_fiber: The cross-sectional area for each fiber in the layer.
            y_center: The y-coordinate of the circular arc's center.
            z_center: The z-coordinate of the circular arc's center.
            radius: The radius of the circular arc.
            start_ang: Optional. The start angle in degrees for the circular arc (default: 0).
            end_ang: Optional. The end angle in degrees for the circular arc. If None,
                defaults to `start_ang + 360`.
        """
        from femora.components.section.section_layer import CircularLayer
        layer = CircularLayer(material, num_fibers, area_per_fiber, y_center, z_center, radius, start_ang, end_ang)
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def to_tcl(self) -> str:
        """Generates the complete OpenSees TCL command for the fiber section,
        including all individual fibers, patches, and layers.

        Returns:
            str: The multi-line TCL command string.
        """
        cmd = f"section Fiber {self.tag}"

        if self.GJ is not None:
            cmd += f" -GJ {self.GJ}"

        cmd += " {\n"

        # Add individual fibers
        for fiber in self.fibers:
            cmd += fiber.to_tcl() + "\n"

        # Add patches
        for patch in self.patches:
            cmd += patch.to_tcl() + "\n"

        # Add layers
        for layer in self.layers:
            cmd += layer.to_tcl() + "\n"

        cmd += f"}}; # {self.user_name}"

        return cmd

    def get_materials(self) -> List[Material]:
        """Returns a list of all unique materials used by this section,
        including those from individual fibers, patches, and layers.

        Returns:
            List[Material]: A list of Material objects.
        """
        materials = []

        # Materials from individual fibers
        for fiber in self.fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)

        # Materials from patches
        for patch in self.patches:
            if patch.material not in materials:
                materials.append(patch.material)

        # Materials from layers
        for layer in self.layers:
            if layer.material not in materials:
                materials.append(layer.material)

        return materials

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Returns the list of parameter names for the Fiber section.

        Returns:
            List[str]: A list of parameter names.
        """
        return ["GJ", "fibers", "patches", "layers"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Returns the list of descriptions for the Fiber section parameters.

        Returns:
            List[str]: A list of parameter descriptions.
        """
        return [
            "Linear-elastic torsional stiffness (optional)",
            "Individual fiber definitions",
            "Patch definitions (rectangular, quadrilateral, circular)",
            "Layer definitions (straight lines, arcs)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Returns the formatted help text for the Fiber section.

        Returns:
            str: HTML formatted help text.
        """
        return """
        <b>Fiber Section</b><br>
        Creates a section using fiber discretization for nonlinear analysis.<br><br>
        Fibers are added programmatically using the add_fiber() method.<br>
        Each fiber has coordinates, area, and a material.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the parameters for a Fiber section.

        Args:
            **kwargs: Keyword arguments containing the section parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters.

        Raises:
            ValueError: If `GJ` is non-numeric or not positive.
        """
        validated_params = {}

        if 'GJ' in kwargs and kwargs['GJ'] is not None:
            try:
                gj = float(kwargs['GJ'])
                if gj <= 0:
                    raise ValueError("GJ must be positive")
                validated_params['GJ'] = gj
            except (ValueError, TypeError):
                raise ValueError("GJ must be a positive number")

        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieves values for specific parameters of the section.

        Args:
            keys: A list of parameter names to retrieve.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary mapping parameter names to their values.
        """
        values = {}
        if 'GJ' in keys:
            values['GJ'] = self.GJ if self.GJ is not None else "None"
        if 'fibers' in keys:
            values['fibers'] = len(self.fibers)
        if 'patches' in keys:
            values['patches'] = len(self.patches)
        if 'layers' in keys:
            values['layers'] = len(self.layers)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Updates the section parameters.

        Note:
            Updating individual fibers, patches, or layers is not supported via
            this method. Use `add_fiber`, `add_rectangular_patch`, etc., or
            `clear_fibers` methods for managing components.

        Args:
            values: A dictionary of parameter names and their new values.

        Raises:
            ValueError: If `GJ` update is invalid.
        """
        if 'GJ' in values:
            if values['GJ'] == "None" or values['GJ'] is None:
                self.GJ = None
            else:
                try:
                    gj = float(values['GJ'])
                    if gj <= 0:
                        raise ValueError("GJ must be positive")
                    self.GJ = gj
                except (ValueError, TypeError):
                    raise ValueError("GJ must be a positive number")

    def clear_fibers(self) -> None:
        """Removes all individual FiberElement objects from the section."""
        self.fibers.clear()

    def clear_patches(self) -> None:
        """Removes all PatchBase objects from the section."""
        self.patches.clear()

    def clear_layers(self) -> None:
        """Removes all LayerBase objects from the section."""
        self.layers.clear()

    def clear_all(self) -> None:
        """Removes all individual fibers, patches, and layers from the section."""
        self.clear_fibers()
        self.clear_patches()
        self.clear_layers()



    def plot(
        self,
        ax: Optional[plt.Axes] = None,
        figsize: 'Tuple[float, float]' = (10, 8),
        show_fibers: bool = True,
        show_patches: bool = True,
        show_layers: bool = True,
        show_patch_outline: bool = True,
        show_fiber_grid: bool = True,
        show_layer_line: bool = True,
        title: Optional[str] = None,
        material_colors: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None,
        dpi: int = 300
    ) -> plt.Figure:
        """Plots the complete fiber section.

        Args:
            ax: Matplotlib axes to plot on. If None, a new figure and axes are created.
            figsize: Figure size if a new figure is created.
            show_fibers: Whether to display individual FiberElement objects.
            show_patches: Whether to display PatchBase objects (e.g., RectangularPatch).
            show_layers: Whether to display LayerBase objects (e.g., StraightLayer).
            show_patch_outline: Whether to show the outer boundary of patches.
            show_fiber_grid: Whether to show the internal fiber grid generated by patches.
            show_layer_line: Whether to show the line defining the layers.
            title: Custom title for the plot. If None, a default title is generated.
            material_colors: A dictionary mapping material names (str) to color strings.
                If None, colors are automatically generated.
            save_path: Optional. The file path to save the figure to (e.g., 'section.png').
            dpi: Dots per inch for the saved figure.

        Returns:
            matplotlib.figure.Figure: The generated matplotlib Figure object.
        """
        # Set default title if none provided
        if title is None:
            title = f"Fiber Section: {self.user_name} (Tag: {self.tag})"
        # Set primary material to first found material
        all_materials = self.get_materials()
        self.material = all_materials[0] if all_materials else None

        # Call the static plotting method
        return self.plot_components(
            fibers=self.fibers,
            patches=self.patches,
            layers=self.layers,
            ax=ax,
            figsize=figsize,
            show_fibers=show_fibers,
            show_patches=show_patches,
            show_layers=show_layers,
            show_patch_outline=show_patch_outline,
            show_fiber_grid=show_fiber_grid,
            show_layer_line=show_layer_line,
            title=title,
            material_colors=material_colors,
            save_path=save_path,
            dpi=dpi
        )


    @staticmethod
    def plot_components(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase],
        ax: Optional[plt.Axes] = None,
        figsize: Tuple[float, float] = (10, 8),
        show_fibers: bool = True,
        show_patches: bool = True,
        show_layers: bool = True,
        show_patch_outline: bool = True,
        show_fiber_grid: bool = True,
        show_layer_line: bool = True,
        title: Optional[str] = None,
        material_colors: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None,
        dpi: int = 300
    ) -> plt.Figure:
        """Static method to plot fiber section components.

        This method is used internally by `FiberSection.plot` but can also be
        called directly to visualize custom collections of fiber components.

        Args:
            fibers: A list of `FiberElement` objects to plot.
            patches: A list of `PatchBase` objects to plot.
            layers: A list of `LayerBase` objects to plot.
            ax: Matplotlib axes to plot on. If None, a new figure and axes are created.
            figsize: Figure size if a new figure is created.
            show_fibers: Whether to display individual FiberElement objects.
            show_patches: Whether to display PatchBase objects.
            show_layers: Whether to display LayerBase objects.
            show_patch_outline: Whether to show the outer boundary of patches.
            show_fiber_grid: Whether to show the internal fiber grid generated by patches.
            show_layer_line: Whether to show the line defining the layers.
            title: Custom title for the plot.
            material_colors: A dictionary mapping material names (str) to color strings.
                If None, colors are automatically generated.
            save_path: Optional. The file path to save the figure to.
            dpi: Dots per inch for the saved figure.

        Returns:
            matplotlib.figure.Figure: The generated matplotlib Figure object.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        if material_colors is None:
            material_colors = FiberSection.generate_material_colors(fibers, patches, layers)

        scale_factor = FiberSection.calculate_scale_factor(fibers)

        if show_fibers:
            for fiber in fibers:
                fiber.plot(ax, material_colors, scale_factor, show_fibers=True)

        if show_patches:
            for patch in patches:
                patch.plot(ax, material_colors, show_patch_outline, show_fiber_grid)

        if show_layers:
            for layer in layers:
                layer.plot(ax, material_colors, show_layer_line, show_fibers)

        ax.set_xlabel('Y Coordinate')
        ax.set_ylabel('Z Coordinate')
        ax.set_aspect('equal')
        # ax.grid(True, alpha=0.3)

        if title is not None:
            ax.set_title(title)

        FiberSection._add_legend_to_axes(ax, material_colors)
        FiberSection._add_section_info_to_axes(ax, fibers, patches, layers)

        fig.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=dpi, bbox_inches='tight')

        return fig

    def _generate_material_colors(self) -> Dict[str, str]:
        """Generates a color mapping for materials in this section.

        Returns:
            Dict[str, str]: A dictionary mapping material user names to color strings.
        """
        return self.generate_material_colors(self.fibers, self.patches, self.layers)

    @staticmethod
    def generate_material_colors(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase]
    ) -> Dict[str, str]:
        """Static method to generate a color mapping for materials from a list of components.

        Args:
            fibers: A list of `FiberElement` objects.
            patches: A list of `PatchBase` objects.
            layers: A list of `LayerBase` objects.

        Returns:
            Dict[str, str]: A dictionary mapping material user names to color strings.
        """
        materials = []
        for fiber in fibers:
            if fiber.material not in materials:
                materials.append(fiber.material)
        for patch in patches:
            if patch.material not in materials:
                materials.append(patch.material)
        for layer in layers:
            if layer.material not in materials:
                materials.append(layer.material)
        colors = [
            'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
            'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan'
        ]
        material_colors = {}
        for i, material in enumerate(materials):
            material_colors[material.user_name] = colors[i % len(colors)]
        return material_colors

    def _calculate_scale_factor(self) -> float:
        """Calculates an appropriate scale factor for fiber visualization based on section dimensions.

        Returns:
            float: The calculated scale factor.
        """
        return self.calculate_scale_factor(self.fibers)

    @staticmethod
    def calculate_scale_factor(fibers: List[FiberElement]) -> float:
        """Static method to calculate an appropriate scale factor for fiber visualization.

        This factor helps visually size the fiber circles relative to the overall
        section dimensions for better readability.

        Args:
            fibers: A list of `FiberElement` objects.

        Returns:
            float: The calculated scale factor. Returns 1.0 if no fibers are present or ranges are zero.
        """
        if not fibers:
            return 1.0
        y_coords = [fiber.y_loc for fiber in fibers]
        z_coords = [fiber.z_loc for fiber in fibers]
        if not y_coords or not z_coords:
            return 1.0
        y_range = max(y_coords) - min(y_coords)
        z_range = max(z_coords) - min(z_coords)
        coord_range = max(y_range, z_range)
        if coord_range == 0:
            return 1.0
        return coord_range / 50.0

    def _add_legend(self, ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Adds a legend showing materials to the plot axes.

        Args:
            ax: The matplotlib axes object to add the legend to.
            material_colors: A dictionary mapping material names to colors.
        """
        self._add_legend_to_axes(ax, material_colors)

    @staticmethod
    def _add_legend_to_axes(ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Static helper method to add a legend showing materials to the plot axes.

        Args:
            ax: The matplotlib axes object to add the legend to.
            material_colors: A dictionary mapping material names to colors.
        """
        if not material_colors:
            return
        legend_elements = [
            mpatches.Patch(color=color, label=material_name)
            for material_name, color in material_colors.items()
        ]
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.)

    def _add_section_info(self, ax: plt.Axes) -> None:
        """Adds section information text (e.g., fiber count) to the plot.

        Args:
            ax: The matplotlib axes object to add the text to.
        """
        self._add_section_info_to_axes(ax, self.fibers, self.patches, self.layers)

    @staticmethod
    def _add_section_info_to_axes(
        ax: plt.Axes,
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase]
    ) -> None:
        """Static helper method to add section information text to the plot.

        Args:
            ax: The matplotlib axes object to add the text to.
            fibers: A list of `FiberElement` objects.
            patches: A list of `PatchBase` objects.
            layers: A list of `LayerBase` objects.
        """
        total_fibers = len(fibers)
        for patch in patches:
            total_fibers += patch.estimate_fiber_count()
        for layer in layers:
            if hasattr(layer, 'num_fibers'):
                total_fibers += layer.num_fibers
        info_text = (
            f"Fibers: {len(fibers)}\n"
            f"Patches: {len(patches)}\n"
            f"Layers: {len(layers)}\n"
            f"Est. Total Fibers: {total_fibers}"
        )
        ax.text(
            1.03, 0.02, info_text, transform=ax.transAxes,
            horizontalalignment='left', verticalalignment='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )





# Register all section types
SectionRegistry.register_section_type('Elastic', ElasticSection)
SectionRegistry.register_section_type('Fiber', FiberSection)
SectionRegistry.register_section_type('Aggregator', AggregatorSection)
SectionRegistry.register_section_type('Uniaxial', UniaxialSection)
SectionRegistry.register_section_type('WFSection2d', WFSection2d)
SectionRegistry.register_section_type('PlateFiber', PlateFiberSection)
SectionRegistry.register_section_type('ElasticMembranePlateSection', ElasticMembranePlateSection)
SectionRegistry.register_section_type('RC', RCSection)
SectionRegistry.register_section_type('Parallel', ParallelSection)
SectionRegistry.register_section_type('Bidirectional', BidirectionalSection)
SectionRegistry.register_section_type('Isolator2spring', Isolator2SpringSection)


def create_example_sections():
    """Creates example sections demonstrating enhanced material handling across all section types.

    This function initializes various material objects and then creates instances
    of each implemented section type, populating them with appropriate materials
    and parameters. It also prints information about the created sections.

    Returns:
        List[Section]: A list of instantiated Section objects.

    Example:
        >>> import femora as fm
        >>> sections = fm.sections.create_example_sections() # doctest: +SKIP
        Created materials:
          Steel: tag=1, name='Steel_A992'
          ...
        1. Elastic Section: Elastic Section 'W12x40_Beam' (Tag: ...)
           Has material: False
        ...
    """
    from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial, ElasticIsotropicMaterial

    # Create materials
    steel = ElasticUniaxialMaterial(user_name="Steel_A992", E=200000, eta=0.0)
    concrete = ElasticUniaxialMaterial(user_name="Concrete_4000psi", E=30000, eta=0.0)
    cover_concrete = ElasticUniaxialMaterial(user_name="Cover_Concrete", E=25000, eta=0.0)
    rebar = ElasticUniaxialMaterial(user_name="Rebar_Grade60", E=200000, eta=0.0)

    # Create NDMaterial for plate sections
    try:
        plate_material = ElasticIsotropicMaterial(user_name="Plate_Steel", E=200000, nu=0.3, rho=7.85e-9)
    except:
        plate_material = None

    print("Created materials:")
    print(f"  Steel: tag={steel.tag}, name='{steel.user_name}'")
    print(f"  Concrete: tag={concrete.tag}, name='{concrete.user_name}'")
    print(f"  Cover Concrete: tag={cover_concrete.tag}, name='{cover_concrete.user_name}'")
    print(f"  Rebar: tag={rebar.tag}, name='{rebar.user_name}'")
    if plate_material:
        print(f"  Plate Material: tag={plate_material.tag}, name='{plate_material.user_name}'")

    sections = []

    # Example 1: Elastic section (no materials required)
    elastic_sec = ElasticSection("W12x40_Beam", E=200000, A=7613, Iz=55.5e6)
    sections.append(elastic_sec)
    print(f"\n1. Elastic Section: {elastic_sec}")
    print(f"   Has material: {elastic_sec.has_material()}")

    # Example 2: Uniaxial section with material object
    uniaxial_sec = UniaxialSection("Steel_Axial", material=steel, response_code="P")
    sections.append(uniaxial_sec)
    print(f"\n2. Uniaxial Section: {uniaxial_sec}")
    print(f"   Material: {uniaxial_sec.material.user_name}")

    # Example 3: WFSection2d with material tag
    wf_sec = WFSection2d("W14x68_Section", material=steel.tag,
                         d=355.6, tw=10.5, bf=254.0, tf=17.3, Nflweb=8, Nflflange=4)
    sections.append(wf_sec)
    print(f"\n3. WF Section 2D: {wf_sec}")
    print(f"   Material: {wf_sec.material.user_name}")

    # Example 4: PlateFiber section with NDMaterial
    if plate_material:
        try:
            plate_sec = PlateFiberSection("Shell_Section", material=plate_material)
            sections.append(plate_sec)
            print(f"\n4. Plate Fiber Section: {plate_sec}")
            print(f"   Material: {plate_sec.material.user_name}")
        except Exception as e:
            print(f"\n4. Plate Fiber Section: Skipped ({e})")
    else:
        print(f"\n4. Plate Fiber Section: Skipped (no NDMaterial available)")

    # Example 5: ElasticMembranePlateSection (no materials required)
    membrane_sec = ElasticMembranePlateSection("Membrane_Section",
                                             E=200000, nu=0.3, h=0.02, rho=7.85e-9)
    sections.append(membrane_sec)
    print(f"\n5. Elastic Membrane Plate Section: {membrane_sec}")
    print(f"   Has material: {membrane_sec.has_material()}")

    # Example 6: RC section with multiple materials
    rc_sec = RCSection("RC_Column",
                       core_material=concrete,
                       cover_material=cover_concrete,
                       steel_material="Rebar_Grade60",  # Using name
                       d=0.4, b=0.4, cover_to_center_of_bar=0.05)
    sections.append(rc_sec)
    print(f"\n6. RC Section: {rc_sec}")
    print(f"   Core material: {rc_sec.core_material.user_name}")
    print(f"   Cover material: {rc_sec.cover_material.user_name}")
    print(f"   Steel material: {rc_sec.steel_material.user_name}")

    # Example 7: Bidirectional section (no materials required)
    bidirectional_sec = BidirectionalSection("Biaxial_Section",
                                            E=200000, Fy=350, Hiso=1000, Hkin=500)
    sections.append(bidirectional_sec)
    print(f"\n7. Bidirectional Section: {bidirectional_sec}")
    print(f"   Has material: {bidirectional_sec.has_material()}")

    # Example 8: Isolator2Spring section (no materials required)
    isolator_sec = Isolator2SpringSection("Base_Isolator",
                                        tol=1e-6, k1=2000, Fy=100, k2=200,
                                        kv=20000, hb=0.15, Pe=1000, Po=50)
    sections.append(isolator_sec)
    print(f"\n8. Isolator 2Spring Section: {isolator_sec}")
    print(f"   Has material: {isolator_sec.has_material()}")

    # Example 9: Fiber section with mixed material inputs
    fiber_sec = FiberSection("RC_Beam_Section", GJ=1.5e6)

    # Add concrete patch using material name
    fiber_sec.add_rectangular_patch("Concrete_4000psi", 12, 8, -0.15, -0.25, 0.15, 0.25)

    # Add steel layers using material objects and tags
    fiber_sec.add_straight_layer(rebar, 4, 0.0005, -0.12, -0.22, 0.12, -0.22)  # Bottom
    fiber_sec.add_straight_layer(rebar.tag, 4, 0.0005, -0.12, 0.22, 0.12, 0.22)  # Top

    sections.append(fiber_sec)
    print(f"\n9. Fiber Section: {fiber_sec}")
    print(f"   Materials used: {[mat.user_name for mat in fiber_sec.get_materials()]}")
    print(f"   Primary material: {fiber_sec.material.user_name if fiber_sec.material else 'None'}")
    print("************************************************")
    fiber_sec.plot()
    plt.show()


    fiber_sec2 = FiberSection("Fiber_Section_2", GJ=1.5e6)
    # Add fibers using material objects
    fiber_sec2.add_fiber(0.0, 0.0, 0.001, steel)  # Center fiber
    fiber_sec2.add_circular_patch(material=concrete,
                                  num_subdiv_circ=16, num_subdiv_rad=4,
                                  y_center=0.0, z_center=0.0, int_rad=0.0, ext_rad=0.5)
    fiber_sec2.add_circular_layer(material=rebar,
                                  num_fibers=8, area_per_fiber=0.0001,
                                  y_center=0.0, z_center=0.0, radius=0.4)
    fiber_sec2.plot()
    plt.show()
    # Example 10: Parallel section combining existing sections
    try:
        parallel_sec = ParallelSection("Combined_Section",
                                     sections=[elastic_sec, uniaxial_sec])
        sections.append(parallel_sec)
        print(f"\n10. Parallel Section: {parallel_sec}")
        print(f"    Combined sections: {[sec.user_name for sec in parallel_sec.sections]}")
        print(f"    Total materials: {len(parallel_sec.get_materials())}")
    except Exception as e:
        print(f"\n10. Parallel Section: Skipped ({e})")

    # Example 11: Aggregator section with multiple materials
    try:
        materials_dict = {
            'P': steel,           # Material object
            'Mz': concrete.tag,   # Material tag
            'Vy': "Rebar_Grade60" # Material name
        }

        aggregator_sec = AggregatorSection("Multi_Response_Section", materials=materials_dict)
        sections.append(aggregator_sec)
        print(f"\n11. Aggregator Section: {aggregator_sec}")
        print(f"    Response materials: {[(code, mat.user_name) for code, mat in aggregator_sec.materials.items()]}")
    except Exception as e:
        print(f"\n11. Aggregator Section: Skipped ({e})")

    return sections


def demonstrate_all_section_types():
    """Provides a comprehensive demonstration of all implemented OpenSees section types.

    This function calls `create_example_sections` to instantiate various sections,
    then prints a summary of all created sections, displays their TCL output,
    and lists all available section types registered in the system.

    Returns:
        List[Section]: A list of instantiated Section objects used in the demonstration.

    Example:
        >>> import femora as fm
        >>> sections = fm.sections.demonstrate_all_section_types() # doctest: +SKIP
        ================================================================================
        COMPREHENSIVE SECTION TYPES DEMONSTRATION
        ================================================================================
        Created materials:
          Steel: tag=1, name='Steel_A992'
        ...
        ================================================================================
        SECTION SUMMARY
        ================================================================================
         1. W12x40_Beam             (Elastic             ) - No materials
         2. Steel_Axial             (Uniaxial            ) - 1 material(s)
        ...
        ================================================================================
        TCL OUTPUT SAMPLES
        ================================================================================
        # W12x40_Beam
        section Elastic 1 200000.0 7613.0 55500000.0; # W12x40_Beam
        ...
        ================================================================================
        AVAILABLE SECTION TYPES
        ================================================================================
         1. Elastic
         2. Fiber
        ...
        Total section types implemented: 11
    """
    print("="*80)
    print("COMPREHENSIVE SECTION TYPES DEMONSTRATION")
    print("="*80)

    sections = create_example_sections()

    print(f"\n{'='*80}")
    print("SECTION SUMMARY")
    print("="*80)

    for i, section in enumerate(sections, 1):
        materials_count = len(section.get_materials())
        materials_info = f"{materials_count} material(s)" if materials_count > 0 else "No materials"
        print(f"{i:2d}. {section.user_name:25s} ({section.section_name:20s}) - {materials_info}")

    print(f"\n{'='*80}")
    print("TCL OUTPUT SAMPLES")
    print("="*80)

    for section in sections[:5]:  # Show first 5 sections
        print(f"\n# {section.user_name}")
        print(section.to_tcl())

    print(f"\n{'='*80}")
    print("AVAILABLE SECTION TYPES")
    print("="*80)

    section_types = SectionRegistry.get_section_types()
    for i, section_type in enumerate(section_types, 1):
        print(f"{i:2d}. {section_type}")

    print(f"\nTotal section types implemented: {len(section_types)}")

    return sections


if __name__ == "__main__":
    from femora.components.section.section_patch import *
    from femora.components.section.section_layer import *
    # Example usage demonstrating enhanced material handling across all section types
    sections = demonstrate_all_section_types()