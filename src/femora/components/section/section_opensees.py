"""
Enhanced OpenSees Section Implementations for FEMORA with Material Resolution
Based on OpenSees section types with validation and parameter management
"""

from typing import List, Dict, Union, Optional, Tuple
from abc import ABC, abstractmethod
import math
from femora.components.section.section_base import Section, SectionRegistry
from femora.components.Material.materialBase import Material
from femora.components.section.section_patch import PatchBase
from femora.components.section.section_layer import LayerBase
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import numpy as np



class ElasticSection(Section):
    """
    Elastic Section implementation for OpenSees.
    
    Parameters
    ----------
    user_name : str
        Name of the section instance.
    E : float
        Young's modulus.
    A : float
        Cross-sectional area.
    Iz : float
        Moment of inertia about z-axis.
    Iy : float, optional
        Moment of inertia about y-axis (3D).
    G : float, optional
        Shear modulus.
    J : float, optional
        Torsional constant.
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Elastic', user_name)
        self.params = kwargs if kwargs else {}
        # Elastic sections don't require external materials
        self.material = None


    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Elastic section"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Elastic {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Elastic section"""
        return ["E", "A", "Iz", "Iy", "G", "J"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Elastic section"""
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
        """Get the formatted help text for Elastic section"""
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
        """Validate parameters for Elastic section"""
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
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Elastic sections don't use external materials"""
        return []
    
    def get_area(self):
        return self.params.get("A", 0.0)
    
    def get_Iz(self):
        return self.params.get("Iz", 0.0)

    def get_Iy(self):
        return self.params.get("Iy",0.0)

    def get_J(self):
        return self.params.get("J", 0.0)


class AggregatorSection(Section):
    """
    Aggregator Section for OpenSees.
    Allows combining multiple uniaxial materials for different response codes.
    
    Parameters
    ----------
    user_name : str
        Name of the section instance.
    materials : dict
        Dictionary mapping response codes to materials (int, str, or Material).
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 materials: Optional[Dict[str, Union[int, str, Material]]] = None,
                 base_section: Optional[Union[int, str, 'Section']] = None, **kwargs):
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
        """
        Resolve section from different input types
        
        Args:
            section_input: Section tag, name, or object
            
        Returns:
            Section object
        """
        if isinstance(section_input, Section):
            return section_input
        
        if isinstance(section_input, (int, str)):
            from femora.components.section.section_base import SectionManager
            return SectionManager.get_section(section_input)
        
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def add_material(self, material_input: Union[int, str, Material], response_code: str):
        """Add a material with its response code"""
        valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
        if response_code not in valid_codes:
            raise ValueError(f"Invalid response code. Must be one of: {valid_codes}")
        
        material = self.resolve_material(material_input)
        self.materials[response_code] = material
        
        # Set as primary material if none exists
        if self.material is None:
            self.material = material

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Aggregator section"""
        mat_pairs = []
        for code, material in self.materials.items():
            mat_pairs.extend([str(material.tag), code])
        
        tcl_cmd = f"section Aggregator {self.tag} " + " ".join(mat_pairs)
        
        if self.base_section:
            tcl_cmd += f" -section {self.base_section.tag}"
        
        tcl_cmd += f"; # {self.user_name}"
        return tcl_cmd

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        materials = list(self.materials.values())
        if self.base_section:
            materials.extend(self.base_section.get_materials())
        return materials

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Aggregator section"""
        return ["materials", "base_section"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Aggregator section"""
        return [
            "Dictionary of materials mapped to response codes (P, Mz, My, Vy, Vz, T)",
            "Optional base section to aggregate with"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Aggregator section"""
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
        """Validate parameters for Aggregator section"""
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
        """Retrieve values for specific parameters"""
        values = {}
        if 'materials' in keys:
            values['materials'] = str(list(self.materials.keys()))
        if 'base_section' in keys:
            values['base_section'] = self.base_section.user_name if self.base_section else "None"
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'materials' in values:
            # This would need custom parsing logic for materials
            pass
        if 'base_section' in values and values['base_section'] != "None":
            self.base_section = self.resolve_section(values['base_section'])


class UniaxialSection(Section):
    """
    Uniaxial Section implementation for OpenSees.
    Uses a single uniaxial material for a specific response.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    material : int, str, or Material
        Uniaxial material (tag, name, or object).
    response_code : str
        Response code (e.g., 'P', 'Mz').
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 material: Union[int, str, Material] = None,
                 response_code: str = "P", **kwargs):
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
        """Generate the OpenSees TCL command for Uniaxial section"""
        return f"section Uniaxial {self.tag} {self.material.tag} {self.response_code}; # {self.user_name}"

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        return [self.material]

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Uniaxial section"""
        return ["material", "response_code"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Uniaxial section"""
        return [
            "Uniaxial material to use (tag, name, or object)",
            "Response code (P, Mz, My, Vy, Vz, T)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Uniaxial section"""
        return """
        <b>Uniaxial Section</b><br>
        Uses a single uniaxial material for one response quantity.<br><br>
        Specify the material and the response code it represents.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Uniaxial section"""
        validated_params = {}
        
        if 'response_code' in kwargs:
            response_code = kwargs['response_code']
            valid_codes = ['P', 'Mz', 'My', 'Vy', 'Vz', 'T']
            if response_code not in valid_codes:
                raise ValueError(f"Response code must be one of: {valid_codes}")
            validated_params['response_code'] = response_code
        
        return validated_params

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'material' in keys:
            values['material'] = self.material.user_name if self.material else "None"
        if 'response_code' in keys:
            values['response_code'] = self.response_code
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'material' in values:
            self.material = self.resolve_material(values['material'])
            self.params['material'] = self.material
        if 'response_code' in values:
            self.response_code = values['response_code']
            self.params['response_code'] = self.response_code


class FiberElement:
    """
    Represents a single fiber in a fiber section with enhanced material handling.

    Parameters
    ----------
    y_loc : float
        Y-coordinate of the fiber.
    z_loc : float
        Z-coordinate of the fiber.
    area : float
        Area of the fiber.
    material : int, str, or Material
        Material for the fiber (tag, name, or object).
    """
    
    def __init__(self, y_loc: float, z_loc: float, area: float, 
                 material: Union[int, str, Material]):
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
        """Plot the fiber on the given matplotlib axes"""
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
        """Generate OpenSees TCL command for this fiber"""
        return f"    fiber {self.y_loc} {self.z_loc} {self.area} {self.material.tag}"
    
    def __str__(self) -> str:
        return f"Fiber at ({self.y_loc}, {self.z_loc}) with area {self.area}, material '{self.material.user_name}'"


class WFSection2d(Section):
    """
    Wide-flange section for 2D problems using fiber discretization.
    Uses a single uniaxial material for the entire section.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    material : int, str, or Material
        Uniaxial material (tag, name, or object).
    d : float
        Section depth.
    tw : float
        Web thickness.
    bf : float
        Flange width.
    tf : float
        Flange thickness.
    Nflweb : int
        Number of fibers in web.
    Nflflange : int
        Number of fibers in flange.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 material: Union[int, str, Material] = None, **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'WFSection2d', user_name)
        
        # Resolve and store material
        if material is None:
            raise ValueError("WFSection2d requires a material")
        self.material = self.resolve_material(material)
        
        self.params = kwargs if kwargs else {}

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for WFSection2d"""
        param_order = self.get_parameters()[:-1]  # Exclude 'material' from params
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section WFSection2d {self.tag} {params_str} {self.material.tag}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for WFSection2d"""
        return ["d", "tw", "bf", "tf", "Nflweb", "Nflflange", "material"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for WFSection2d"""
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
        """Get the formatted help text for WFSection2d"""
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
        """Validate parameters for WFSection2d"""
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
        """Retrieve values for specific parameters"""
        values = {}
        for key in keys:
            if key == 'material':
                values[key] = self.material.user_name if self.material else "None"
            else:
                values[key] = self.params.get(key)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'material' in values:
            self.material = self.resolve_material(values['material'])
            del values['material']
        
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        return [self.material] if self.material else []


class PlateFiberSection(Section):
    """
    Plate fiber section for shell elements with plane-stress material models.
    Uses NDMaterial for fiber-discretized behavior through plate thickness.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    material : int, str, or Material
        NDMaterial for plane stress (tag, name, or object).
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", 
                 material: Union[int, str, Material] = None, **kwargs):
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
        """Generate the OpenSees TCL command for PlateFiber section"""
        return f"section PlateFiber {self.tag} {self.material.tag}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for PlateFiber section"""
        return ["material"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for PlateFiber section"""
        return ["NDMaterial for plane stress behavior (tag, name, or object)"]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for PlateFiber section"""
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
        """Validate parameters for PlateFiber section"""
        # No additional parameters to validate beyond material
        return {}

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'material' in keys:
            values['material'] = self.material.user_name if self.material else "None"
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'material' in values:
            self.material = self.resolve_material(values['material'])

    def get_materials(self) -> List[Material]:
        """Get all materials used by this section"""
        return [self.material] if self.material else []


class ElasticMembranePlateSection(Section):
    """
    Elastic section for membrane-plate behavior in shell elements.
    Uses built-in linear elastic properties - no external materials required.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    E : float
        Young's modulus.
    nu : float
        Poisson's ratio.
    h : float
        Plate thickness.
    rho : float
        Mass density.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'ElasticMembranePlateSection', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for ElasticMembranePlateSection"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section ElasticMembranePlateSection {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for ElasticMembranePlateSection"""
        return ["E", "nu", "h", "rho"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for ElasticMembranePlateSection"""
        return [
            "Young's modulus",
            "Poisson's ratio",
            "Plate thickness", 
            "Mass density"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for ElasticMembranePlateSection"""
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
        """Validate parameters for ElasticMembranePlateSection"""
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
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Elastic membrane plate sections don't use external materials"""
        return []


class RCSection(Section):
    """
    Specialized reinforced concrete section with individual material definitions
    for core concrete, cover concrete, and steel reinforcement.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    core_material : int, str, or Material
        Core concrete material (tag, name, or object).
    cover_material : int, str, or Material
        Cover concrete material (tag, name, or object).
    steel_material : int, str, or Material
        Steel reinforcement material (tag, name, or object).
    d : float
        Section depth.
    b : float
        Section width.
    cover_to_center_of_bar : float
        Cover distance to reinforcement centroid.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed",
                 core_material: Union[int, str, Material] = None,
                 cover_material: Union[int, str, Material] = None,
                 steel_material: Union[int, str, Material] = None,
                 **kwargs):
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
        """Generate the OpenSees TCL command for RC section"""
        param_order = self.get_parameters()[3:]  # Skip material parameters
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return (f"section RC {self.tag} {self.core_material.tag} {self.cover_material.tag} "
                f"{self.steel_material.tag} {params_str}; # {self.user_name}")

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for RC section"""
        return ["core_material", "cover_material", "steel_material", "d", "b", "cover_to_center_of_bar"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for RC section"""
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
        """Get the formatted help text for RC section"""
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
        """Validate parameters for RC section"""
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
        """Retrieve values for specific parameters"""
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
        """Update section parameters"""
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
        """Get all materials used by this section"""
        materials = []
        if self.core_material:
            materials.append(self.core_material)
        if self.cover_material and self.cover_material not in materials:
            materials.append(self.cover_material)
        if self.steel_material and self.steel_material not in materials:
            materials.append(self.steel_material)
        return materials


        


class ParallelSection(Section):
    """
    Combines several existing sections in parallel to sum their force-deformation behaviors.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    sections : list of int, str, or Section
        List of existing sections to combine in parallel (tags, names, or objects).
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed",
                 sections: Optional[List[Union[int, str, 'Section']]] = None, **kwargs):
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
        """Resolve section from different input types"""
        if isinstance(section_input, Section):
            return section_input
        
        if isinstance(section_input, (int, str)):
            from femora.components.section.section_base import SectionManager
            return SectionManager.get_section(section_input)
        
        raise ValueError(f"Invalid section input type: {type(section_input)}")

    def add_section(self, section_input: Union[int, str, 'Section']) -> None:
        """Add a section to the parallel combination"""
        resolved_section = self.resolve_section(section_input)
        self.sections.append(resolved_section)
        
        # Update primary material if none exists
        if self.material is None:
            section_materials = resolved_section.get_materials()
            if section_materials:
                self.material = section_materials[0]

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Parallel section"""
        section_tags = " ".join(str(sec.tag) for sec in self.sections)
        return f"section Parallel {self.tag} {section_tags}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Parallel section"""
        return ["sections"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Parallel section"""
        return ["List of existing sections to combine in parallel (tags, names, or objects)"]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Parallel section"""
        return """
        <b>Parallel Section</b><br>
        Combines several existing sections in parallel to sum their behaviors.<br><br>
        <b>Required Parameters:</b><br>
        • sections: List of existing sections to combine<br><br>
        <b>Note:</b> Sections can be specified as objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Parallel section"""
        # No additional parameters to validate
        return {}

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve values for specific parameters"""
        values = {}
        if 'sections' in keys:
            values['sections'] = ", ".join(sec.user_name for sec in self.sections)
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        if 'sections' in values:
            # This would need custom parsing logic for section names/tags
            pass

    def get_materials(self) -> List[Material]:
        """Get all materials used by the combined sections"""
        materials = []
        for section in self.sections:
            for material in section.get_materials():
                if material not in materials:
                    materials.append(material)
        return materials


class BidirectionalSection(Section):
    """
    Combines biaxial moment interaction with axial force using built-in yield surface.
    No external materials required - uses built-in bidirectional plasticity.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    E : float
        Elastic modulus.
    Fy : float
        Yield strength.
    Hiso : float
        Isotropic hardening parameter.
    Hkin : float
        Kinematic hardening parameter.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Bidirectional', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Bidirectional section"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Bidirectional {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Bidirectional section"""
        return ["E", "Fy", "Hiso", "Hkin"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Bidirectional section"""
        return [
            "Elastic modulus",
            "Yield strength",
            "Isotropic hardening parameter",
            "Kinematic hardening parameter"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Bidirectional section"""
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
        """Validate parameters for Bidirectional section"""
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
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Bidirectional sections don't use external materials"""
        return []


class Isolator2SpringSection(Section):
    """
    Used for modeling base isolation systems with bidirectional behavior and vertical coupling.
    No external materials required - uses built-in isolator behavior.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    tol : float
        Tolerance for convergence.
    k1 : float
        Initial stiffness.
    Fy : float
        Yield force.
    k2 : float
        Post-yield stiffness.
    kv : float
        Vertical stiffness.
    hb : float
        Isolation height.
    Pe : float
        Buckling load.
    Po : float
        Vertical load.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", **kwargs):
        kwargs = self.validate_section_parameters(**kwargs)
        super().__init__('section', 'Isolator2spring', user_name)
        self.params = kwargs if kwargs else {}
        # No external materials required
        self.material = None

    def to_tcl(self) -> str:
        """Generate the OpenSees TCL command for Isolator2spring section"""
        param_order = self.get_parameters()
        params_str = " ".join(str(self.params[param]) for param in param_order if param in self.params)
        return f"section Isolator2spring {self.tag} {params_str}; # {self.user_name}"

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Isolator2spring section"""
        return ["tol", "k1", "Fy", "k2", "kv", "hb", "Pe", "Po"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Isolator2spring section"""
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
        """Get the formatted help text for Isolator2spring section"""
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
        """Validate parameters for Isolator2spring section"""
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
        """Retrieve values for specific parameters"""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update section parameters"""
        self.params.clear()
        validated_params = self.validate_section_parameters(**values)
        self.params.update(validated_params)

    def get_materials(self) -> List[Material]:
        """Isolator2spring sections don't use external materials"""
        return []


class FiberSection(Section):
    """
    Complete Fiber Section implementation with enhanced material handling.

    Parameters
    ----------
    user_name : str
        Name of the section instance.
    GJ : float, optional
        Linear-elastic torsional stiffness.
    components : list, optional
        List of FiberElement, PatchBase, or LayerBase objects.
    kwargs : dict
        Additional parameters.
    """
    
    def __init__(self, user_name: str = "Unnamed", GJ: Optional[float] = None, 
                 components: Optional[List[Union[FiberElement, PatchBase, LayerBase]]] = None, **kwargs):
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
        """Add an individual fiber to the section"""
        fiber = FiberElement(y_loc, z_loc, area, material)
        self.fibers.append(fiber)
        
        # Update primary material if none exists
        if self.material is None:
            self.material = fiber.material

    def add_rectangular_patch(self, material: Union[int, str, Material], 
                            num_subdiv_y: int, num_subdiv_z: int,
                            y1: float, z1: float, y2: float, z2: float) -> None:
        """Add a rectangular patch to the section"""
        patch = RectangularPatch(material, num_subdiv_y, num_subdiv_z, y1, z1, y2, z2)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_quadrilateral_patch(self, material: Union[int, str, Material], 
                             num_subdiv_ij: int, num_subdiv_jk: int,
                             vertices: list) -> None:
        """Add a quadrilateral patch to the section"""
        from femora.components.section.section_patch import QuadrilateralPatch
        patch = QuadrilateralPatch(material, num_subdiv_ij, num_subdiv_jk, vertices)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_circular_patch(self, material: Union[int, str, Material], 
                         num_subdiv_circ: int, num_subdiv_rad: int,
                         y_center: float, z_center: float, int_rad: float, ext_rad: float,
                         start_ang: float = 0.0, end_ang: float = 360.0) -> None:
        """Add a circular patch to the section"""
        from femora.components.section.section_patch import CircularPatch
        patch = CircularPatch(material, num_subdiv_circ, num_subdiv_rad, y_center, z_center, int_rad, ext_rad, start_ang, end_ang)
        self.patches.append(patch)
        if self.material is None:
            self.material = patch.material

    def add_straight_layer(self, material: Union[int, str, Material], 
                         num_fibers: int, area_per_fiber: float,
                         y1: float, z1: float, y2: float, z2: float) -> None:
        """Add a straight layer of fibers to the section"""
        from femora.components.section.section_layer import StraightLayer
        layer = StraightLayer(material, num_fibers, area_per_fiber, y1, z1, y2, z2)
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def add_circular_layer(self, material: Union[int, str, Material], 
                         num_fibers: int, area_per_fiber: float,
                         y_center: float, z_center: float, radius: float,
                         start_ang: float = 0.0, end_ang: float = None) -> None:
        """Add a circular layer of fibers to the section"""
        from femora.components.section.section_layer import CircularLayer
        layer = CircularLayer(material, num_fibers, area_per_fiber, y_center, z_center, radius, start_ang, end_ang)
        self.layers.append(layer)
        if self.material is None:
            self.material = layer.material

    def to_tcl(self) -> str:
        """Generate complete OpenSees TCL command for fiber section"""
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
        """Get all materials used by this section"""
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

    def _discretize_to_fibers(self) -> List[tuple]:
        """Return list of (area, y, z) representing all contributions.

        This discretizes patches and layers into small fiber-like cells to
        compute area and second moments consistently.
        """
        fibers = []

        # Existing explicit fibers
        for f in self.fibers:
            fibers.append((f.area, f.y_loc, f.z_loc))

        # Layers -> treated as discrete fibers along the line
        for layer in self.layers:
            from femora.components.section.section_layer import StraightLayer, CircularLayer
            if isinstance(layer, StraightLayer):
                if layer.num_fibers <= 0:
                    continue
                ys = [layer.y1 + (i + 0.5) * (layer.y2 - layer.y1) / layer.num_fibers for i in range(layer.num_fibers)]
                zs = [layer.z1 + (i + 0.5) * (layer.z2 - layer.z1) / layer.num_fibers for i in range(layer.num_fibers)]
                for y, z in zip(ys, zs):
                    fibers.append((layer.area_per_fiber, y, z))
            elif isinstance(layer, CircularLayer):
                if layer.num_fibers <= 0:
                    continue
                if layer.num_fibers == 1:
                    angles = [math.radians(layer.start_ang)]
                else:
                    angles = list(np.linspace(math.radians(layer.start_ang), math.radians(layer.end_ang), layer.num_fibers))
                for ang in angles:
                    y = layer.y_center + layer.radius * math.cos(ang)
                    z = layer.z_center + layer.radius * math.sin(ang)
                    fibers.append((layer.area_per_fiber, y, z))

        # Patches -> discretize into subcells matching subdivision counts
        for patch in self.patches:
            # Local imports
            from femora.components.section.section_patch import RectangularPatch, QuadrilateralPatch, CircularPatch

            if isinstance(patch, RectangularPatch):
                ny = patch.num_subdiv_y
                nz = patch.num_subdiv_z
                dy = (patch.y2 - patch.y1) / ny
                dz = (patch.z2 - patch.z1) / nz
                for i in range(ny):
                    y = patch.y1 + (i + 0.5) * dy
                    for j in range(nz):
                        z = patch.z1 + (j + 0.5) * dz
                        fibers.append((dy * dz, y, z))

            elif isinstance(patch, QuadrilateralPatch):
                ni = patch.num_subdiv_ij
                nj = patch.num_subdiv_jk
                # vertices: v0,v1,v2,v3
                v = patch.vertices
                for i in range(ni):
                    s0 = i / ni
                    s1 = (i + 1) / ni
                    for j in range(nj):
                        t0 = j / nj
                        t1 = (j + 1) / nj
                        # compute four corners via bilinear mapping
                        def bilinear(s, t):
                            x = (1 - s) * (1 - t) * v[0][0] + s * (1 - t) * v[1][0] + s * t * v[2][0] + (1 - s) * t * v[3][0]
                            y = (1 - s) * (1 - t) * v[0][1] + s * (1 - t) * v[1][1] + s * t * v[2][1] + (1 - s) * t * v[3][1]
                            return x, y
                        c00 = bilinear(s0, t0)
                        c10 = bilinear(s1, t0)
                        c11 = bilinear(s1, t1)
                        c01 = bilinear(s0, t1)
                        # cell area via polygon area of 4 corners
                        xs = [c00[0], c10[0], c11[0], c01[0]]
                        ys = [c00[1], c10[1], c11[1], c01[1]]
                        area = 0.0
                        for k in range(4):
                            k1 = (k + 1) % 4
                            area += xs[k] * ys[k1] - xs[k1] * ys[k]
                        area = 0.5 * abs(area)
                        # centroid approx as average of corners
                        yc = sum(xs) / 4.0
                        zc = sum(ys) / 4.0
                        fibers.append((area, yc, zc))

            elif isinstance(patch, CircularPatch):
                nr = patch.num_subdiv_rad
                nc = patch.num_subdiv_circ
                theta0 = math.radians(patch.start_ang)
                theta1 = math.radians(patch.end_ang)
                # normalize wrap
                if theta1 <= theta0:
                    theta1 += 2 * math.pi
                dtheta = (theta1 - theta0) / nc
                for ir in range(nr):
                    r_in = patch.int_rad + (ir) * (patch.ext_rad - patch.int_rad) / nr
                    r_out = patch.int_rad + (ir + 1) * (patch.ext_rad - patch.int_rad) / nr
                    for ic in range(nc):
                        th0 = theta0 + ic * dtheta
                        th1 = theta0 + (ic + 1) * dtheta
                        # area of sector segment
                        area = 0.5 * (th1 - th0) * (r_out * r_out - r_in * r_in)
                        # radial centroid for ring segment
                        if abs(r_out - r_in) < 1e-12:
                            r_cent = 0.5 * (r_in + r_out)
                        else:
                            r_cent = (2.0 / 3.0) * (r_out**3 - r_in**3) / (r_out**2 - r_in**2)
                        th_cent = 0.5 * (th0 + th1)
                        y = patch.y_center + r_cent * math.cos(th_cent)
                        z = patch.z_center + r_cent * math.sin(th_cent)
                        fibers.append((area, y, z))

        return fibers

    def get_area(self) -> float:
        """Compute total area of the fiber section by summing discretized contributions."""
        comps = self._discretize_to_fibers()
        total_area = sum(a for a, _, _ in comps)
        return float(total_area)

    def get_Iy(self) -> float:
        """Second moment about the local y-axis (Iy = integral z^2 dA) about centroid."""
        comps = self._discretize_to_fibers()
        if not comps:
            return 0.0
        A = sum(a for a, _, _ in comps)
        if A <= 0:
            return 0.0
        y_bar = sum(a * y for a, y, z in comps) / A
        z_bar = sum(a * z for a, y, z in comps) / A
        # Iy = sum(a * (z - z_bar)^2)
        Iy = 0.0
        for a, y, z in comps:
            Iy += a * (z - z_bar) ** 2
        return float(Iy)

    def get_Iz(self) -> float:
        """Second moment about the local z-axis (Iz = integral y^2 dA) about centroid."""
        comps = self._discretize_to_fibers()
        if not comps:
            return 0.0
        A = sum(a for a, _, _ in comps)
        if A <= 0:
            return 0.0
        y_bar = sum(a * y for a, y, z in comps) / A
        z_bar = sum(a * z for a, y, z in comps) / A
        Iz = 0.0
        for a, y, z in comps:
            Iz += a * (y - y_bar) ** 2
        return float(Iz)

    def get_J(self) -> float:
        """Polar moment (approx) J = Iy + Iz about section centroid."""
        return float(self.get_Iy() + self.get_Iz())

    @classmethod
    def get_parameters(cls) -> List[str]:
        """Parameters for Fiber section"""
        return ["GJ", "fibers", "patches", "layers"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Parameter descriptions for Fiber section"""
        return [
            "Linear-elastic torsional stiffness (optional)",
            "Individual fiber definitions",
            "Patch definitions (rectangular, quadrilateral, circular)",
            "Layer definitions (straight lines, arcs)"
        ]

    @classmethod
    def get_help_text(cls) -> str:
        """Get the formatted help text for Fiber section"""
        return """
        <b>Fiber Section</b><br>
        Creates a section using fiber discretization for nonlinear analysis.<br><br>
        Fibers are added programmatically using the add_fiber() method.<br>
        Each fiber has coordinates, area, and a material.<br><br>
        <b>Materials:</b> Accepts UniaxialMaterial objects, tags, or names
        """

    @classmethod
    def validate_section_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate parameters for Fiber section"""
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
        """Retrieve values for specific parameters"""
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
        """Update section parameters"""
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
        """Remove all individual fibers"""
        self.fibers.clear()
    
    def clear_patches(self) -> None:
        """Remove all patches"""
        self.patches.clear()

    def clear_layers(self) -> None:
        """Remove all layers"""
        self.layers.clear()
    
    def clear_all(self) -> None:
        """Remove all fibers, patches, and layers"""
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
        """
        Plot the complete fiber section

        Args:
            ax: Matplotlib axes to plot on (if None, creates new figure)
            figsize: Figure size if creating new figure
            show_fibers: Whether to show individual fibers
            show_patches: Whether to show patches
            show_layers: Whether to show layers
            show_patch_outline: Whether to show patch outlines
            show_fiber_grid: Whether to show fiber grid in patches
            show_layer_line: Whether to show layer lines
            title: Custom title for the plot
            material_colors: Custom color mapping for materials
            save_path: Path to save the figure (optional)
            dpi: DPI for saved figure

        Returns:
            matplotlib Figure object
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
        """
        Static method to plot fiber section components.
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
        """Generate color mapping for materials."""
        return self.generate_material_colors(self.fibers, self.patches, self.layers)

    @staticmethod
    def generate_material_colors(
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase]
    ) -> Dict[str, str]:
        """Static method to generate color mapping for materials."""
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
        """Calculate appropriate scale factor for fiber visualization."""
        return self.calculate_scale_factor(self.fibers)

    @staticmethod
    def calculate_scale_factor(fibers: List[FiberElement]) -> float:
        """Static method to calculate appropriate scale factor for fiber visualization."""
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
        """Add legend showing materials."""
        self._add_legend_to_axes(ax, material_colors)

    @staticmethod
    def _add_legend_to_axes(ax: plt.Axes, material_colors: Dict[str, str]) -> None:
        """Static helper method to add legend showing materials."""
        if not material_colors:
            return
        legend_elements = [
            mpatches.Patch(color=color, label=material_name)
            for material_name, color in material_colors.items()
        ]
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0.)

    def _add_section_info(self, ax: plt.Axes) -> None:
        """Add section information text."""
        self._add_section_info_to_axes(ax, self.fibers, self.patches, self.layers)

    @staticmethod
    def _add_section_info_to_axes(
        ax: plt.Axes,
        fibers: List[FiberElement],
        patches: List[PatchBase],
        layers: List[LayerBase]
    ) -> None:
        """Static helper method to add section information text."""
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
    """
    Create example sections demonstrating enhanced material handling across all section types
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
    """
    Comprehensive demonstration of all implemented section types
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