"""
This module defines various mesh part instances, all inheriting from `MeshPart`.

It includes classes for creating structured 3D rectangular meshes, custom rectangular
grids, geometrically graded rectangular grids, external meshes loaded from files,
and structured and single line meshes for beam elements.

Attributes:
    StructuredRectangular3D: Represents a 3D structured rectangular mesh part with uniform spacing.
    CustomRectangularGrid3D: Represents a 3D custom rectangular grid mesh part with user-defined coordinates.
    GeometricStructuredRectangular3D: Represents a 3D rectangular mesh with geometric spacing.
    ExternalMesh: Represents a mesh loaded from a file or provided as a PyVista mesh.
    StructuredLineMesh: Represents a 2D structured grid of 3D line elements.
    SingleLineMesh: Represents a single 3D line element.
    CircularOGrid2D: Represents a 2D circular quad mesh with O-grid topology.
    CompositeMesh: Represents a mesh part containing multiple element types defined by cell data.
    LineMeshManager: A manager class for line mesh types.
    VolumeMeshManager: A manager class for volume mesh types.
    SurfaceMeshManager: A manager class for surface mesh types.
"""
from typing import Dict, List, Tuple, Union, Optional
from abc import ABC, abstractmethod
import numpy as np
import pyvista as pv
import os
from femora.components.Mesh.meshPartBase import MeshPart, MeshPartRegistry
from femora.core.element_base import Element
from femora.components.Region.regionBase import RegionBase
from femora.components.Material.materialBase import Material
from femora.constants import FEMORA_MAX_NDF



class StructuredRectangular3D(MeshPart):
    """Represents a 3D structured rectangular mesh part with uniform cell spacing.

    This class provides functionality to initialize, generate, and validate
    a structured rectangular mesh grid using the PyVista library.

    Attributes:
        _compatible_elements (list[str]): List of compatible element types for this mesh part.
        params (dict): Dictionary storing the validated parameters for mesh generation.
        mesh (pv.UnstructuredGrid): The generated PyVista unstructured grid.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """Initializes a 3D Structured Rectangular Mesh Part.

        Args:
            user_name: The unique user-defined name for this mesh part.
            element: The associated Femora Element object.
            region: Optional. The associated Femora RegionBase object.
            **kwargs: Additional parameters for mesh generation. These can include:
                X Min (float): Minimum X coordinate.
                X Max (float): Maximum X coordinate.
                Y Min (float): Minimum Y coordinate.
                Y Max (float): Maximum Y coordinate.
                Z Min (float): Minimum Z coordinate.
                Z Max (float): Maximum Z coordinate.
                Nx Cells (int): Number of cells in X direction.
                Ny Cells (int): Number of cells in Y direction.
                Nz Cells (int): Number of cells in Z direction.
                (Also accepts 'x_min', 'x_max', etc. for backward compatibility).

        Raises:
            ValueError: If any required parameter is missing or invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element # Assuming Element base exists
            >>> from femora.components.Material.materialBase import Material
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.StructuredRectangular3D(
            ...     user_name="my_volume_mesh",
            ...     element=dummy_element,
            ...     x_min=0, x_max=10, y_min=0, y_max=5, z_min=0, z_max=2,
            ...     nx=10, ny=5, nz=2
            ... )
            >>> print(mesh_part.mesh.n_cells)
            100
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        kwargs = self.validate_parameters(**kwargs)
        self.params = kwargs if kwargs else {}
        self.generate_mesh()


    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generates a structured rectangular mesh based on current parameters.

        Returns:
            pv.UnstructuredGrid: The generated PyVista unstructured grid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.StructuredRectangular3D(
            ...     user_name="my_mesh", element=dummy_element, nx=2, ny=2, nz=2,
            ...     x_min=0, x_max=2, y_min=0, y_max=2, z_min=0, z_max=2
            ... )
            >>> mesh = mesh_part.generate_mesh()
            >>> print(mesh.n_cells)
            8
        """
        
        # Extract parameters - support both old and new naming conventions
        x_min = self.params.get('X Min', self.params.get('x_min', 0))
        x_max = self.params.get('X Max', self.params.get('x_max', 1))
        y_min = self.params.get('Y Min', self.params.get('y_min', 0))
        y_max = self.params.get('Y Max', self.params.get('y_max', 1))
        z_min = self.params.get('Z Min', self.params.get('z_min', 0))
        z_max = self.params.get('Z Max', self.params.get('z_max', 1))
        nx = self.params.get('Nx Cells', self.params.get('nx', 10))
        ny = self.params.get('Ny Cells', self.params.get('ny', 10))
        nz = self.params.get('Nz Cells', self.params.get('nz', 10))
        X = np.linspace(x_min, x_max, nx + 1)
        Y = np.linspace(y_min, y_max, ny + 1)
        Z = np.linspace(z_min, z_max, nz + 1)
        X, Y, Z = np.meshgrid(X, Y, Z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        return self.mesh


    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """Gets a list of parameters required for this mesh part type.

        Returns:
            List[Tuple[str, str]]: A list of tuples, where each tuple contains
                (parameter_name, parameter_description).

        Example:
            >>> import femora as fm
            >>> params = fm.components.Mesh.meshParts.StructuredRectangular3D.get_parameters()
            >>> print(len(params))
            9
            >>> print(params[0])
            ('X Min', 'Minimum X coordinate (float)')
        """
        return [
            ("X Min", "Minimum X coordinate (float)"),
            ("X Max", "Maximum X coordinate (float)"),
            ("Y Min", "Minimum Y coordinate (float)"),
            ("Y Max", "Maximum Y coordinate (float)"),
            ("Z Min", "Minimum Z coordinate (float)"),
            ("Z Max", "Maximum Z coordinate (float)"),
            ("Nx Cells", "Number of cells in X direction (integer)"),
            ("Ny Cells", "Number of cells in Y direction (integer)"),
            ("Nz Cells", "Number of cells in Z direction (integer)")
        ]
    

    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the input parameters for creating this mesh part.

        Args:
            **kwargs: Arbitrary keyword arguments representing the mesh parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters
                with their correct types.

        Raises:
            ValueError: If any parameter is missing, has an invalid type, or an invalid value.

        Example:
            >>> import femora as fm
            >>> valid_params = fm.components.Mesh.meshParts.StructuredRectangular3D.validate_parameters(
            ...     x_min=0, x_max=10, y_min=0, y_max=5, z_min=0, z_max=2,
            ...     nx=10, ny=5, nz=2
            ... )
            >>> print(valid_params['X Min'])
            0.0
            >>> try:
            ...     fm.components.Mesh.meshParts.StructuredRectangular3D.validate_parameters(nx=-1)
            ... except ValueError as e:
            ...     print(e)
            Nx Cells must be greater than 0
        """
        valid_params = {}
        
        # Parameter mapping for backward compatibility
        param_mapping = {
            'x_min': 'X Min',
            'x_max': 'X Max', 
            'y_min': 'Y Min',
            'y_max': 'Y Max',
            'z_min': 'Z Min',
            'z_max': 'Z Max',
            'nx': 'Nx Cells',
            'ny': 'Ny Cells',
            'nz': 'Nz Cells'
        }
        
        # Normalize parameter names - convert new format to old format for consistency
        normalized_kwargs = {}
        for key, value in kwargs.items():
            if key in param_mapping:
                normalized_kwargs[param_mapping[key]] = value
            else:
                normalized_kwargs[key] = value
        
        for param_name in ['X Min', 'X Max', 'Y Min', 'Y Max', 'Z Min', 'Z Max']:
            if param_name in normalized_kwargs:
                try:
                    valid_params[param_name] = float(normalized_kwargs[param_name])
                except ValueError:
                    raise ValueError(f"{param_name} must be a float number")
            else:
                raise ValueError(f"{param_name} parameter is required")
        
        for param_name in ['Nx Cells', 'Ny Cells', 'Nz Cells']:
            if param_name in normalized_kwargs:
                try:
                    valid_params[param_name] = int(normalized_kwargs[param_name])
                except ValueError:
                    raise ValueError(f"{param_name} must be an integer number")
            else:
                raise ValueError(f"{param_name} parameter is required")
            
        if valid_params['X Min'] >= valid_params['X Max']:
            raise ValueError("X Min must be less than X Max")
        if valid_params['Y Min'] >= valid_params['Y Max']:
            raise ValueError("Y Min must be less than Y Max")
        if valid_params['Z Min'] >= valid_params['Z Max']:
            raise ValueError("Z Min must be less than Z Max")
        
        if valid_params['Nx Cells'] <= 0:
            raise ValueError("Nx Cells must be greater than 0")
        if valid_params['Ny Cells'] <= 0:
            raise ValueError("Ny Cells must be greater than 0")
        if valid_params['Nz Cells'] <= 0:
            raise ValueError("Nz Cells must be greater than 0")
        
        return valid_params
    
    @classmethod
    def is_elemnt_compatible(cls, element:str) -> bool:
        """Checks if the given element type is compatible with this mesh part.

        Args:
            element: The string name of the element type to check.

        Returns:
            bool: True if the element type is compatible, False otherwise.

        Example:
            >>> import femora as fm
            >>> is_compatible = fm.components.Mesh.meshParts.StructuredRectangular3D.is_elemnt_compatible("stdBrick")
            >>> print(is_compatible)
            True
            >>> is_compatible = fm.components.Mesh.meshParts.StructuredRectangular3D.is_elemnt_compatible("beamElement")
            >>> print(is_compatible)
            False
        """
        return element in cls._compatible_elements
    


    def update_parameters(self, **kwargs) -> None:
        """Updates the mesh part's parameters and regenerates the mesh.

        Args:
            **kwargs: Keyword arguments for the parameters to update.
                These will be validated before updating.

        Raises:
            ValueError: If any provided parameter is invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.StructuredRectangular3D(
            ...     user_name="my_mesh", element=dummy_element, nx=2, ny=2, nz=2,
            ...     x_min=0, x_max=2, y_min=0, y_max=2, z_min=0, z_max=2
            ... )
            >>> print(mesh_part.mesh.n_cells)
            8
            >>> mesh_part.update_parameters(nx=4, ny=4, nz=4)
            >>> print(mesh_part.mesh.n_cells)
            64
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params
        self.generate_mesh()


    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Provides notes, usage, limitations, and tips for this mesh part type.

        Returns:
            Dict[str, Union[str, list]]: A dictionary containing various notes
                about the mesh part, including:
                - 'description': A brief description.
                - 'usage': A list of use cases.
                - 'limitations': A list of limitations.
                - 'tips': A list of helpful tips.

        Example:
            >>> import femora as fm
            >>> notes = fm.components.Mesh.meshParts.StructuredRectangular3D.get_Notes()
            >>> print(notes["description"])
            Generates a structured 3D rectangular grid mesh with uniform spacing
        """
        return {
            "description": "Generates a structured 3D rectangular grid mesh with uniform spacing",
            "usage": [
                "Used for creating regular 3D meshes with equal spacing in each direction",
                "Suitable for simple geometries where uniform mesh density is desired",
                "Efficient for problems requiring regular grid structures"
            ],
            "limitations": [
                "Only creates rectangular/cuboid domains",
                "Cannot handle irregular geometries",
                "Uniform spacing in each direction"
            ],
            "tips": [
                "Ensure the number of cells (Nx, Ny, Nz) is appropriate for your analysis",
                "Consider mesh density requirements for accuracy",
                "Check that the domain bounds (Min/Max) cover your area of interest"
            ]
        }

# Register the 3D Structured Rectangular mesh part type
MeshPartRegistry.register_mesh_part_type('Volume mesh', 'Uniform Rectangular Grid', StructuredRectangular3D)


class CustomRectangularGrid3D(MeshPart):
    """Represents a 3D custom rectangular grid mesh part with user-defined coordinate arrays.

    This class allows for the creation of 3D rectangular meshes with non-uniform
    spacing by specifying explicit coordinate lists for each axis.

    Attributes:
        _compatible_elements (list[str]): List of compatible element types for this mesh part.
        params (dict): Dictionary storing the validated parameters for mesh generation.
        mesh (pv.UnstructuredGrid): The generated PyVista unstructured grid.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """Initializes a 3D Custom Rectangular Grid Mesh Part.

        Args:
            user_name: The unique user-defined name for this mesh part.
            element: The associated Femora Element object.
            region: Optional. The associated Femora RegionBase object.
            **kwargs: Additional parameters for mesh generation. These must include:
                x_coords (str): Comma-separated string of float values for X coordinates.
                y_coords (str): Comma-separated string of float values for Y coordinates.
                z_coords (str): Comma-separated string of float values for Z coordinates.

        Raises:
            ValueError: If any required parameter is missing or invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.CustomRectangularGrid3D(
            ...     user_name="my_custom_mesh",
            ...     element=dummy_element,
            ...     x_coords="0.0, 1.0, 3.0",
            ...     y_coords="0.0, 0.5, 1.0",
            ...     z_coords="0.0, 2.0"
            ... )
            >>> print(mesh_part.mesh.n_cells)
            4
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Custom Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        self.params = self.validate_parameters(**kwargs)
        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generates a custom rectangular grid mesh based on provided coordinates.

        Returns:
            pv.UnstructuredGrid: The generated PyVista unstructured grid.

        Raises:
            ValueError: If 'x_coords', 'y_coords', or 'z_coords' are missing from parameters.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.CustomRectangularGrid3D(
            ...     user_name="my_custom_mesh", element=dummy_element,
            ...     x_coords="0.0,1.0,2.0", y_coords="0.0,1.0", z_coords="0.0,1.0"
            ... )
            >>> mesh = mesh_part.generate_mesh()
            >>> print(mesh.n_cells)
            2
        """
        x_coords_str = self.params.get('x_coords')
        y_coords_str = self.params.get('y_coords')
        z_coords_str = self.params.get('z_coords')

        if not all([x_coords_str, y_coords_str, z_coords_str]):
            raise ValueError("All 'x_coords', 'y_coords', and 'z_coords' must be provided.")

        x = np.array([float(val) for val in x_coords_str.split(',')])
        y = np.array([float(val) for val in y_coords_str.split(',')])
        z = np.array([float(val) for val in z_coords_str.split(',')])

        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        del x, y, z, X, Y, Z
        return self.mesh
    
    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """Gets a list of parameters required for this mesh part type.

        Returns:
            List[Tuple[str, str]]: A list of tuples, where each tuple contains
                (parameter_name, parameter_description).

        Example:
            >>> import femora as fm
            >>> params = fm.components.Mesh.meshParts.CustomRectangularGrid3D.get_parameters()
            >>> print(len(params))
            3
            >>> print(params[0])
            ('x_coords', 'List of X coordinates (List[float] , comma separated, required)')
        """
        return [
            ("x_coords", "List of X coordinates (List[float] , comma separated, required)"),
            ("y_coords", "List of Y coordinates (List[float] , comma separated, required)"),
            ("z_coords", "List of Z coordinates (List[float] , comma separated, required)")
        ]
    
    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, List[float]]]:
        """Validates the input parameters for creating this mesh part.

        Args:
            **kwargs: Arbitrary keyword arguments representing the mesh parameters.

        Returns:
            Dict[str, Union[int, float, str, List[float]]]: A dictionary of validated
                parameters with their correct types.

        Raises:
            ValueError: If any parameter is missing, has an invalid type, or if
                coordinates are not in ascending order.

        Example:
            >>> import femora as fm
            >>> valid_params = fm.components.Mesh.meshParts.CustomRectangularGrid3D.validate_parameters(
            ...     x_coords="0.0, 1.0, 2.0", y_coords="0.0, 0.5, 1.0", z_coords="0.0, 2.0"
            ... )
            >>> print(valid_params['x_coords'])
            0.0, 1.0, 2.0
            >>> try:
            ...     fm.components.Mesh.meshParts.CustomRectangularGrid3D.validate_parameters(x_coords="1.0, 0.0")
            ... except ValueError as e:
            ...     print(e)
            x_coords must be in ascending order
        """
        valid_params = {}
        for param_name in ['x_coords', 'y_coords', 'z_coords']:
            if param_name in kwargs:
                try:
                    # Temporarily convert to list of floats for validation
                    coords_list = [float(x) for x in kwargs[param_name].split(',')]
                    # check if the values are in ascending order
                    if not all(coords_list[i] < coords_list[i+1] for i in range(len(coords_list)-1)):
                        raise ValueError(f"{param_name} must be in ascending order")
                    # Store the original string back
                    valid_params[param_name] = kwargs[param_name]
                except ValueError:
                    raise ValueError(f"{param_name} must be a comma-separated list of float numbers "
                                     "and in ascending order.")
            else:
                raise ValueError(f"{param_name} parameter is required")
        return valid_params

    @classmethod
    def is_elemnt_compatible(cls, element:str) -> bool:
        """Checks if the given element type is compatible with this mesh part.

        Args:
            element: The string name of the element type to check.

        Returns:
            bool: True if the element type is compatible, False otherwise.

        Example:
            >>> import femora as fm
            >>> is_compatible = fm.components.Mesh.meshParts.CustomRectangularGrid3D.is_elemnt_compatible("bbarBrick")
            >>> print(is_compatible)
            True
            >>> is_compatible = fm.components.Mesh.meshParts.CustomRectangularGrid3D.is_elemnt_compatible("shellElement")
            >>> print(is_compatible)
            False
        """
        return element in ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]


    def update_parameters(self, **kwargs) -> None:
        """Updates the mesh part's parameters and regenerates the mesh.

        Args:
            **kwargs: Keyword arguments for the parameters to update.
                These will be validated before updating.

        Raises:
            ValueError: If any provided parameter is invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.CustomRectangularGrid3D(
            ...     user_name="my_custom_mesh", element=dummy_element,
            ...     x_coords="0.0,1.0", y_coords="0.0,1.0", z_coords="0.0,1.0"
            ... )
            >>> print(mesh_part.mesh.n_cells)
            1
            >>> mesh_part.update_parameters(x_coords="0.0,1.0,2.0", y_coords="0.0,0.5,1.0")
            >>> print(mesh_part.mesh.n_cells)
            4
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params
        self.generate_mesh()


    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Provides notes, usage, limitations, and tips for this mesh part type.

        Returns:
            Dict[str, Union[str, list]]: A dictionary containing various notes
                about the mesh part.

        Example:
            >>> import femora as fm
            >>> notes = fm.components.Mesh.meshParts.CustomRectangularGrid3D.get_Notes()
            >>> print(notes["description"])
            Generates a 3D rectangular grid mesh with custom spacing
        """
        return {
            "description": "Generates a 3D rectangular grid mesh with custom spacing",
            "usage": [
                "Used for creating 3D meshes with variable spacing in each direction",
                "Suitable for problems requiring non-uniform mesh density",
                "Useful when specific grid point locations are needed"
            ],
            "limitations": [
                "Only creates rectangular/cuboid domains",
                "Cannot handle irregular geometries",
                "Requires manual specification of all grid points"
            ],
            "tips": [
                "Provide coordinates as comma-separated lists of float values",
                "Ensure coordinates are in ascending order",
                "Consider gradual transitions in spacing for better numerical results"
            ]
        }


# Register the 3D Structured Rectangular mesh part type
MeshPartRegistry.register_mesh_part_type('Volume mesh', 'Custom Rectangular Grid', CustomRectangularGrid3D)




class GeometricStructuredRectangular3D(MeshPart):
    """Represents a 3D structured rectangular mesh with geometrically graded spacing.

    This class provides functionality to create 3D rectangular meshes where the
    element sizes can be graded along each axis using a specified ratio.

    Attributes:
        _compatible_elements (list[str]): List of compatible element types for this mesh part.
        params (dict): Dictionary storing the validated parameters for mesh generation.
        mesh (pv.UnstructuredGrid): The generated PyVista unstructured grid.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """Initializes a 3D Geometric Structured Rectangular Mesh Part.

        Args:
            user_name: The unique user-defined name for this mesh part.
            element: The associated Femora Element object.
            region: Optional. The associated Femora RegionBase object.
            **kwargs: Additional parameters for mesh generation. These can include:
                x_min (float): Minimum X coordinate.
                x_max (float): Maximum X coordinate.
                y_min (float): Minimum Y coordinate.
                y_max (float): Maximum Y coordinate.
                z_min (float): Minimum Z coordinate.
                z_max (float): Maximum Z coordinate.
                nx (int): Number of cells in X direction.
                ny (int): Number of cells in Y direction.
                nz (int): Number of cells in Z direction.
                x_ratio (float, optional): Ratio of cell increment in X direction. Defaults to 1 (uniform).
                y_ratio (float, optional): Ratio of cell increment in Y direction. Defaults to 1 (uniform).
                z_ratio (float, optional): Ratio of cell increment in Z direction. Defaults to 1 (uniform).

        Raises:
            ValueError: If any required parameter is missing or invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D(
            ...     user_name="my_graded_mesh",
            ...     element=dummy_element,
            ...     x_min=0, x_max=10, nx=5, x_ratio=1.5,
            ...     y_min=0, y_max=5, ny=3, y_ratio=1.2,
            ...     z_min=0, z_max=2, nz=2
            ... )
            >>> print(mesh_part.mesh.n_cells)
            30
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Geometric Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        self.params = self.validate_parameters(**kwargs)
        self.generate_mesh()

    @staticmethod
    def custom_linspace(start: float, end: float, num_elements: int, ratio: float = 1) -> np.ndarray:
        """Generates a sequence of numbers between start and end with specified spacing ratio.

        Args:
            start: The starting value of the sequence.
            end: The ending value of the sequence.
            num_elements: The number of intervals/cells in the sequence (not points).
            ratio: Optional. The ratio of increment between consecutive intervals.
                Defaults to 1 (linear spacing). If ratio > 1, increments increase.
                If ratio < 1, increments decrease.

        Returns:
            np.ndarray: The generated sequence of coordinates (num_elements + 1 points).

        Raises:
            ValueError: If `num_elements` is not greater than 0.

        Example:
            >>> import numpy as np
            >>> from femora.components.Mesh.meshParts import GeometricStructuredRectangular3D
            >>> # Uniform spacing
            >>> coords_uniform = GeometricStructuredRectangular3D.custom_linspace(0, 10, 2, ratio=1)
            >>> print(np.round(coords_uniform, 2))
            [ 0.  5. 10.]
            >>> # Increasing spacing
            >>> coords_increasing = GeometricStructuredRectangular3D.custom_linspace(0, 10, 2, ratio=2)
            >>> print(np.round(coords_increasing, 2))
            [ 0.   3.33 10.  ]
            >>> # Decreasing spacing
            >>> coords_decreasing = GeometricStructuredRectangular3D.custom_linspace(0, 10, 2, ratio=0.5)
            >>> print(np.round(coords_decreasing, 2))
            [ 0.   6.67 10.  ]
        """
        if num_elements <= 0:
            raise ValueError("Number of elements must be greater than 0")

        if num_elements == 1:
            return np.array([start, end])
        
        num_intervals = num_elements
        total = end - start
        
        if ratio == 1:
            return np.linspace(start, end, num_elements+1)
        else:            
            # Determine the base increment
            x = total * (1 - ratio) / (1 - ratio**num_intervals)
            # Generate the increments using the ratio
            increments = x * (ratio ** np.arange(num_intervals))
            # Compute the cumulative sum and add the start value
            elements = start + np.cumsum(np.hstack([0, increments]))
            return elements

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generates a geometric structured rectangular mesh based on current parameters.

        Returns:
            pv.UnstructuredGrid: The generated PyVista unstructured grid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D(
            ...     user_name="my_mesh", element=dummy_element,
            ...     x_min=0, x_max=1, nx=2, x_ratio=2,
            ...     y_min=0, y_max=1, ny=1,
            ...     z_min=0, z_max=1, nz=1
            ... )
            >>> mesh = mesh_part.generate_mesh()
            >>> print(mesh.n_cells)
            2
            >>> print(np.round(mesh.points[:, 0], 2)) # X coordinates will be graded
            [0.   0.33 1.   0.   0.33 1.   0.   0.33 1.   0.   0.33 1.  ]
        """
        x_min = self.params.get('x_min', 0)
        x_max = self.params.get('x_max', 1)
        y_min = self.params.get('y_min', 0)
        y_max = self.params.get('y_max', 1)
        z_min = self.params.get('z_min', 0)
        z_max = self.params.get('z_max', 1)
        nx = self.params.get('nx', 10)
        ny = self.params.get('ny', 10)
        nz = self.params.get('nz', 10)
        x_ratio = self.params.get('x_ratio', 1)
        y_ratio = self.params.get('y_ratio', 1)
        z_ratio = self.params.get('z_ratio', 1)
        x = self.custom_linspace(x_min, x_max, nx, x_ratio)
        y = self.custom_linspace(y_min, y_max, ny, y_ratio)
        z = self.custom_linspace(z_min, z_max, nz, z_ratio)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()

        return self.mesh

    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """Gets a list of parameters required for this mesh part type.

        Returns:
            List[Tuple[str, str]]: A list of tuples, where each tuple contains
                (parameter_name, parameter_description).

        Example:
            >>> import femora as fm
            >>> params = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.get_parameters()
            >>> print(len(params))
            12
            >>> print(params[0])
            ('x_min', 'Minimum X coordinate (float)')
        """
        return [
            ("x_min", "Minimum X coordinate (float)"),
            ("x_max", "Maximum X coordinate (float)"),
            ("y_min", "Minimum Y coordinate (float)"),
            ("y_max", "Maximum Y coordinate (float)"),
            ("z_min", "Minimum Z coordinate (float)"),
            ("z_max", "Maximum Z coordinate (float)"),
            ("nx", "Number of cells in X direction (integer)"),
            ("ny", "Number of cells in Y direction (integer)"),
            ("nz", "Number of cells in Z direction (integer)"),
            ("x_ratio", "Ratio of cell increment in X direction (float)"),
            ("y_ratio", "Ratio of cell increment in Y direction (float)"),
            ("z_ratio", "Ratio of cell increment in Z direction (float)")
        ]
    
    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validates the input parameters for creating this mesh part.

        Args:
            **kwargs: Arbitrary keyword arguments representing the mesh parameters.

        Returns:
            Dict[str, Union[int, float, str]]: A dictionary of validated parameters
                with their correct types.

        Raises:
            ValueError: If any parameter is missing, has an invalid type,
                an invalid value (e.g., min > max, cells <= 0, ratio <= 0).

        Example:
            >>> import femora as fm
            >>> valid_params = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.validate_parameters(
            ...     x_min=0, x_max=10, y_min=0, y_max=5, z_min=0, z_max=2,
            ...     nx=10, ny=5, nz=2, x_ratio=1.1
            ... )
            >>> print(valid_params['x_max'])
            10.0
            >>> try:
            ...     fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.validate_parameters(nx=-1)
            ... except ValueError as e:
            ...     print(e)
            nx must be greater than 0
        """
        valid_params = {}
        for param_name in ['x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max']:
            if param_name in kwargs:
                try:
                    valid_params[param_name] = float(kwargs[param_name])
                except ValueError:
                    raise ValueError(f"{param_name} must be a float number")
            else:
                raise ValueError(f"{param_name} parameter is required")
        
        for param_name in ['nx', 'ny', 'nz']:
            if param_name in kwargs:
                try:
                    valid_params[param_name] = int(kwargs[param_name])
                except ValueError:
                    raise ValueError(f"{param_name} must be an integer number")
            else:
                raise ValueError(f"{param_name} parameter is required")
            
        for param_name in ['x_ratio', 'y_ratio', 'z_ratio']:
            if param_name in kwargs:
                try:
                    valid_params[param_name] = float(kwargs[param_name])
                    # check if the value is greater than 0
                    if valid_params[param_name] <= 0:
                        raise ValueError(f"{param_name} must be greater than 0")
                except ValueError:
                    raise ValueError(f"{param_name} must be a float number")
            else:
                valid_params[param_name] = 1.0 # Default value
        
        if valid_params['x_min'] >= valid_params['x_max']:
            raise ValueError("x_min must be less than x_max")
        if valid_params['y_min'] >= valid_params['y_max']:
            raise ValueError("y_min must be less than y_max")
        if valid_params['z_min'] >= valid_params['z_max']:
            raise ValueError("z_min must be less than z_max")
        
        if valid_params['nx'] <= 0:
            raise ValueError("nx must be greater than 0")
        if valid_params['ny'] <= 0:
            raise ValueError("ny must be greater than 0")
        if valid_params['nz'] <= 0:
            raise ValueError("nz must be greater than 0")
        
        return valid_params
    
    @classmethod
    def is_elemnt_compatible(cls, element:str) -> bool:
        """Checks if the given element type is compatible with this mesh part.

        Args:
            element: The string name of the element type to check.

        Returns:
            bool: True if the element type is compatible, False otherwise.

        Example:
            >>> import femora as fm
            >>> is_compatible = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.is_elemnt_compatible("SSPbrick")
            >>> print(is_compatible)
            True
            >>> is_compatible = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.is_elemnt_compatible("quad")
            >>> print(is_compatible)
            False
        """
        return element in ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    
    def update_parameters(self, **kwargs) -> None:
        """Updates the mesh part's parameters and regenerates the mesh.

        Args:
            **kwargs: Keyword arguments for the parameters to update.
                These will be validated before updating.

        Raises:
            ValueError: If any provided parameter is invalid.

        Example:
            >>> import femora as fm
            >>> from femora.components.Element.elementBase import Element
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D(
            ...     user_name="my_mesh", element=dummy_element,
            ...     x_min=0, x_max=1, nx=2, x_ratio=1.0,
            ...     y_min=0, y_max=1, ny=1, z_min=0, z_max=1, nz=1
            ... )
            >>> print(mesh_part.mesh.n_cells)
            2
            >>> mesh_part.update_parameters(x_ratio=1.5, nx=3)
            >>> print(mesh_part.mesh.n_cells)
            3
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params
        self.generate_mesh()

    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Provides notes, usage, limitations, and tips for this mesh part type.

        Returns:
            Dict[str, Union[str, list]]: A dictionary containing various notes
                about the mesh part.

        Example:
            >>> import femora as fm
            >>> notes = fm.components.Mesh.meshParts.GeometricStructuredRectangular3D.get_Notes()
            >>> print(notes["description"])
            Generates a structured 3D rectangular grid mesh with geometric spacing
        """
        return {
            "description": "Generates a structured 3D rectangular grid mesh with geometric spacing",
            "usage": [
                "Used for creating 3D meshes with variable spacing in each direction",
                "Suitable for problems requiring non-uniform mesh density",
                "Useful when specific grid point locations are needed"
            ],
            "limitations": [
                "Only creates rectangular/cuboid domains",
                "Cannot handle irregular geometries",
                "Uniform spacing is an option, but not truly custom spacing"
            ],
            "tips": [
                "A ratio > 1 increases element size away from the start_point (min coordinate)",
                "A ratio < 1 decreases element size away from the start_point (min coordinate)",
                "Ensure ratios are positive (ratio = 1 means uniform spacing)",
                "Ensure min coordinates are less than max coordinates"
            ]
        }
    
# Register the 3D Geometric Structured Rectangular mesh part type
MeshPartRegistry.register_mesh_part_type('Volume mesh', 'Geometric Rectangular Grid', GeometricStructuredRectangular3D)


class ExternalMesh(MeshPart):
    """Represents a custom mesh part that can load from a file or accept an existing PyVista mesh.

    This class provides functionality to import meshes from various file formats
    or directly from PyVista objects, and allows for optional scaling, rotation,
    and translation transformations.

    Attributes:
        _compatible_elements (list[str]): List of compatible element types.
        params (dict): Dictionary storing the validated parameters, including mesh
            source and transformations.
        mesh (pv.UnstructuredGrid): The generated or loaded PyVista unstructured grid.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    
    def __init__(self, user_name: str, element: Element, region: RegionBase=None, **kwargs):
        """Initializes an External Mesh Part.

        Args:
            user_name: The unique user-defined name for this mesh part.
            element: The associated Femora Element object.
            region: Optional. The associated Femora RegionBase object.
            **kwargs: Additional parameters for mesh loading and transformation.
                These can include:
                mesh (pv.UnstructuredGrid): An existing PyVista mesh object to use.
                filepath (str): Path to a mesh file to load (e.g., .vtk, .vtu, .stl, .obj, .ply).
                scale (float, optional): Scale factor for the mesh.
                rotate_x (float, optional): Rotation angle around X-axis in degrees.
                rotate_y (float, optional): Rotation angle around Y-axis in degrees.
                rotate_z (float, optional): Rotation angle around Z-axis in degrees.
                translate_x (float, optional): Translation distance along X-axis.
                translate_y (float, optional): Translation distance along Y-axis.
                translate_z (float, optional): Translation distance along Z-axis.
                transform_args (dict, optional): A dictionary of transformation
                    parameters, which will be merged with direct `**kwargs`.
                    Direct `**kwargs` take precedence.

        Raises:
            ValueError: If neither 'mesh' nor 'filepath' is provided, or if
                any parameter is invalid.
            FileNotFoundError: If `filepath` is provided but the file does not exist.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> from femora.components.Element.elementBase import Element
            >>> # Create a dummy PyVista mesh for the example
            >>> dummy_pv_mesh = pv.Cube().extract_surface().cast_to_unstructured_grid()
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>>
            >>> # Example 1: Load from existing PyVista mesh and scale
            >>> mesh_part_1 = fm.components.Mesh.meshParts.ExternalMesh(
            ...     user_name="my_external_mesh_1", element=dummy_element,
            ...     mesh=dummy_pv_mesh, scale=2.0
            ... )
            >>> print(f"Mesh 1 points: {mesh_part_1.mesh.n_points}")
            Mesh 1 points: 8
            >>>
            >>> # Example 2: Demonstrate file loading (requires a dummy file)
            >>> # To run this, you'd need a simple VTK file like 'test_cube.vtk'
            >>> # (e.g., pv.Cube().save('test_cube.vtk'))
            >>> # dummy_element_2 = DummyElement(tag=2, nodes=[])
            >>> # mesh_part_2 = fm.components.Mesh.meshParts.ExternalMesh(
            >>> #     user_name="my_external_mesh_2", element=dummy_element_2,
            >>> #     filepath="test_cube.vtk", rotate_z=90, translate_x=5
            >>> # )
            >>> # print(f"Mesh 2 points: {mesh_part_2.mesh.n_points}")
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Custom Mesh',
            user_name=user_name,
            element=element,
            region=region
        )
        self.params = self.validate_parameters(**kwargs)
        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generates a mesh by loading from a file or using a provided PyVista mesh,
        and then applies specified transformations.

        Returns:
            pv.UnstructuredGrid: The generated and transformed PyVista unstructured grid.

        Raises:
            ValueError: If neither 'mesh' nor 'filepath' is found in parameters,
                or if the loaded mesh cannot be converted to an unstructured grid.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> from femora.components.Element.elementBase import Element
            >>> # Create a dummy PyVista mesh
            >>> dummy_pv_mesh = pv.Sphere(radius=1.0).extract_surface().cast_to_unstructured_grid()
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.ExternalMesh(
            ...     user_name="gen_mesh_example", element=dummy_element,
            ...     mesh=dummy_pv_mesh, scale=0.5, translate_x=1.0
            ... )
            >>> mesh = mesh_part.generate_mesh()
            >>> print(mesh.n_points) # Still same number of points
            80
            >>> print(f"Mesh bounds after transform: {np.round(mesh.bounds, 2)}")
            Mesh bounds after transform: [0.5  1.5 -0.5  0.5 -0.5  0.5]
        """
        if 'mesh' in self.params:
            # Use the provided mesh
            self.mesh = self.params['mesh']
        elif 'filepath' in self.params:
            # Load mesh from file
            self.mesh = pv.read(self.params['filepath'])
        else:
            raise ValueError("Either 'mesh' or 'filepath' parameter is required")
            
        # Apply scale if specified
        if 'scale' in self.params:
            self.mesh.scale(self.params['scale'], inplace=True)
            
        # Apply rotations if specified (in X, Y, Z order)
        if 'rotate_x' in self.params:
            self.mesh.rotate_x(self.params['rotate_x'], inplace=True)
        if 'rotate_y' in self.params:
            self.mesh.rotate_y(self.params['rotate_y'], inplace=True)
        if 'rotate_z' in self.params:
            self.mesh.rotate_z(self.params['rotate_z'], inplace=True)
            
        # Apply translation if specified
        translate_x = self.params.get('translate_x', 0)
        translate_y = self.params.get('translate_y', 0)
        translate_z = self.params.get('translate_z', 0)
        
        # Only translate if at least one component is non-zero
        if translate_x != 0 or translate_y != 0 or translate_z != 0:
            self.mesh.translate([translate_x, translate_y, translate_z], inplace=True)
            
        # Ensure we have an unstructured grid
        if not isinstance(self.mesh, pv.UnstructuredGrid):
            try:
                self.mesh = self.mesh.cast_to_unstructured_grid()
            except Exception as e:
                raise ValueError(f"Failed to convert mesh to unstructured grid: {str(e)}")
            
        return self.mesh

    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """Gets a list of parameters required for this mesh part type.

        Returns:
            List[Tuple[str, str]]: A list of tuples, where each tuple contains
                (parameter_name, parameter_description).

        Example:
            >>> import femora as fm
            >>> params = fm.components.Mesh.meshParts.ExternalMesh.get_parameters()
            >>> print(len(params))
            9
            >>> print(params[0])
            ('mesh', 'Existing PyVista mesh object (pv.UnstructuredGrid or convertible)')
        """
        return [
            ("mesh", "Existing PyVista mesh object (pv.UnstructuredGrid or convertible)"),
            ("filepath", "Path to mesh file to load (str)"),
            ("scale", "Scale factor for the mesh (float)"),
            ("rotate_x", "Rotation angle around X-axis in degrees (float)"),
            ("rotate_y", "Rotation angle around Y-axis in degrees (float)"),
            ("rotate_z", "Rotation angle around Z-axis in degrees (float)"),
            ("translate_x", "Translation along X-axis (float)"),
            ("translate_y", "Translation along Y-axis (float)"),
            ("translate_z", "Translation along Z-axis (float)"),
        ]
    
    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, pv.UnstructuredGrid, Dict]]:
        """Validates the input parameters for creating this mesh part.

        Args:
            **kwargs: Arbitrary keyword arguments representing the mesh parameters.

        Returns:
            Dict[str, Union[int, float, str, pv.UnstructuredGrid, Dict]]: A dictionary
                of validated parameters with their correct types.

        Raises:
            ValueError: If neither 'mesh' nor 'filepath' is provided, or if
                any parameter has an invalid type or value.
            FileNotFoundError: If `filepath` is provided but the file does not exist.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> dummy_pv_mesh = pv.Sphere()
            >>> valid_params = fm.components.Mesh.meshParts.ExternalMesh.validate_parameters(
            ...     mesh=dummy_pv_mesh, scale=2.0, rotate_x=45
            ... )
            >>> print(valid_params['scale'])
            2.0
            >>> try:
            ...     fm.components.Mesh.meshParts.ExternalMesh.validate_parameters(scale=-1)
            ... except ValueError as e:
            ...     print(e)
            Scale factor must be greater than 0
        """
        valid_params = {}
        
        # Check if either mesh or filepath is provided
        if 'mesh' in kwargs:
            try:
                # Verify it's a PyVista mesh
                mesh = kwargs['mesh']
                if not isinstance(mesh, (pv.UnstructuredGrid, pv.PolyData, pv.StructuredGrid)):
                    raise ValueError("'mesh' parameter must be a PyVista mesh")
                valid_params['mesh'] = mesh
            except Exception as e:
                raise ValueError(f"Invalid mesh object: {str(e)}")
        elif 'filepath' in kwargs:
            filepath = kwargs['filepath']
            if not isinstance(filepath, str):
                raise ValueError("'filepath' parameter must be a string")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Mesh file not found: {filepath}")
            valid_params['filepath'] = filepath
        else:
            raise ValueError("Either 'mesh' or 'filepath' parameter is required")
        
        # Process transformation parameters
        transform_params = ['scale', 'rotate_x', 'rotate_y', 'rotate_z', 
                           'translate_x', 'translate_y', 'translate_z']
        
        # Handle transform_args dict if provided
        if 'transform_args' in kwargs and isinstance(kwargs['transform_args'], dict):
            # Extract parameters from transform_args
            for param in transform_params:
                if param in kwargs['transform_args']:
                    try:
                        valid_params[param] = float(kwargs['transform_args'][param])
                    except ValueError:
                        raise ValueError(f"Transform parameter '{param}' must be a number")
        
        # Direct parameters override those in transform_args
        for param in transform_params:
            if param in kwargs:
                try:
                    valid_params[param] = float(kwargs[param])
                except ValueError:
                    raise ValueError(f"Parameter '{param}' must be a number")
                    
        # Scale must be positive if provided
        if 'scale' in valid_params and valid_params['scale'] <= 0:
            raise ValueError("Scale factor must be greater than 0")
            
        return valid_params
    
    @classmethod
    def is_elemnt_compatible(cls, element:str) -> bool:
        """Checks if an element type is compatible with this mesh part.

        Args:
            element: Element type name to check.

        Returns:
            bool: True if compatible, False otherwise.

        Example:
            >>> import femora as fm
            >>> is_compatible = fm.components.Mesh.meshParts.ExternalMesh.is_elemnt_compatible("PML3D")
            >>> print(is_compatible)
            True
            >>> is_compatible = fm.components.Mesh.meshParts.ExternalMesh.is_elemnt_compatible("LineElement")
            >>> print(is_compatible)
            False
        """
        return element in cls._compatible_elements
    
    def update_parameters(self, **kwargs) -> None:
        """Updates the mesh part parameters and regenerates the mesh.

        Args:
            **kwargs: Keyword arguments to update. These will be validated.

        Raises:
            ValueError: If any provided parameter is invalid.
            FileNotFoundError: If a new `filepath` is provided but the file does not exist.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> from femora.components.Element.elementBase import Element
            >>> dummy_pv_mesh = pv.Sphere(radius=1.0).extract_surface().cast_to_unstructured_grid()
            >>> class DummyElement(Element):
            ...     def __init__(self, tag, nodes, section=None, transformation=None, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 3)
            ...         self.element_type = "stdBrick"
            ...     def get_section(self): return None
            ...     def get_transformation(self): return None
            ...     def get_mass_per_length(self): return 1.0
            >>> dummy_element = DummyElement(tag=1, nodes=[])
            >>> mesh_part = fm.components.Mesh.meshParts.ExternalMesh(
            ...     user_name="update_example", element=dummy_element,
            ...     mesh=dummy_pv_mesh, scale=1.0
            ... )
            >>> old_bounds = mesh_part.mesh.bounds
            >>> mesh_part.update_parameters(scale=2.0, translate_x=5.0)
            >>> new_bounds = mesh_part.mesh.bounds
            >>> print(f"Old bounds: {np.round(old_bounds, 2)}, New bounds: {np.round(new_bounds, 2)}")
            Old bounds: [-1.  1. -1.  1. -1.  1.], New bounds: [3.  7. -2.  2. -2.  2.]
        """
        # Merge with existing parameters to maintain required params
        merged_params = {**self.params, **kwargs}
        validated_params = self.validate_parameters(**merged_params)
        self.params = validated_params
        self.generate_mesh()  # Regenerate the mesh with new parameters

    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Provides notes, usage, limitations, and tips for this mesh part type.

        Returns:
            Dict[str, Union[str, list]]: A dictionary containing various notes
                about the mesh part.

        Example:
            >>> import femora as fm
            >>> notes = fm.components.Mesh.meshParts.ExternalMesh.get_Notes()
            >>> print(notes["description"])
            Handles custom meshes imported from files or existing PyVista meshes
        """
        return {
            "description": "Handles custom meshes imported from files or existing PyVista meshes",
            "usage": [
                "Used for importing pre-generated meshes from external sources",
                "Suitable for complex geometries created in other software",
                "Useful when working with irregular or complex domain shapes",
                "Can transform meshes with scaling, rotation, and translation operations",
                "Right now it only supports one kind of element type, but it can be extended to support more",
                "The compatibility of the element type is not checked, so it is the user's responsibility to check that the element type is compatible with the mesh part type"
            ],
            "limitations": [
                "Quality and compatibility of imported meshes depends on the source",
                "Some mesh types may require conversion to unstructured grid",
                "Not all mesh formats preserve all required metadata"
            ],
            "tips": [
                "Ensure imported meshes have appropriate element types for analysis",
                "Check mesh quality after import (aspect ratio, skewness, etc.)",
                "Parameters can be provided directly or in the transform_args dict",
                "Transformations are applied in this order: scale → rotate → translate",
                "Common file formats include .vtk, .vtu, .stl, .obj, and .ply"
            ]
        }

# Register the Custom Mesh part type under the General mesh category
MeshPartRegistry.register_mesh_part_type('General mesh', 'External mesh', ExternalMesh)


class StructuredLineMesh(MeshPart):
    """Represents a structured line mesh part for beam/column elements.

    This class creates a 2D grid of 3D line elements (beams or columns)
    with an arbitrary normal direction. Each grid point generates a stack
    of line elements along the normal.

    Attributes:
        _compatible_elements (list[str]): List of compatible element types.
        params (dict): Dictionary storing the validated parameters for mesh generation.
        mesh (pv.UnstructuredGrid): The generated PyVista unstructured grid containing line elements.
    """
    _compatible_elements = ["DispBeamColumn", "ForceBeamColumn", "ElasticBeamColumn", "NonlinearBeamColumn"]
    
    def __init__(self, user_name: str, element: Element, region: Optional[RegionBase]=None, **kwargs):
        """Initializes a Structured Line Mesh Part.

        Args:
            user_name: The unique user-defined name for this mesh part.
            element: The associated beam Element object. Must have a section and transformation.
            region: Optional. The associated Femora RegionBase object.
            **kwargs: Additional parameters for mesh generation. These can include:
                base_point_x (float, optional): X coordinate of the grid's origin. Defaults to 0.0.
                base_point_y (float, optional): Y coordinate of the grid's origin. Defaults to 0.0.
                base_point_z (float, optional): Z coordinate of the grid's origin. Defaults to 0.0.
                base_vector_1_x (float, optional): X component of the first grid direction vector. Defaults to 1.0.
                base_vector_1_y (float, optional): Y component of the first grid direction vector. Defaults to 0.0.
                base_vector_1_z (float, optional): Z component of the first grid direction vector. Defaults to 0.0.
                base_vector_2_x (float, optional): X component of the second grid direction vector. Defaults to 0.0.
                base_vector_2_y (float, optional): Y component of the second grid direction vector. Defaults to 1.0.
                base_vector_2_z (float, optional): Z component of the second grid direction vector. Defaults to 0.0.
                normal_x (float, optional): X component of the normal direction for line elements. Defaults to 0.0.
                normal_y (float, optional): Y component of the normal direction for line elements. Defaults to 0.0.
                normal_z (float, optional): Z component of the normal direction for line elements. Defaults to 1.0.
                grid_size_1 (int, optional): Number of elements (intervals) in direction 1. Defaults to 10.
                grid_size_2 (int, optional): Number of elements (intervals) in direction 2. Defaults to 10.
                spacing_1 (float, optional): Spacing between grid points in direction 1. Defaults to 1.0.
                spacing_2 (float, optional): Spacing between grid points in direction 2. Defaults to 1.0.
                length (float, optional): Total length of the stack of line elements at each grid point. Defaults to 1.0.
                offset_1 (float, optional): Optional offset for the grid in direction 1. Defaults to 0.0.
                offset_2 (float, optional): Optional offset for the grid in direction 2. Defaults to 0.0.
                number_of_lines (int, optional): Number of line elements to create along
                    the normal direction at each grid point. Defaults to 1.
                merge_points (bool, optional): Whether to merge duplicate points generated
                    at shared grid locations. Defaults to True.

        Raises:
            ValueError: If the `element` is not compatible (e.g., not a beam element
                or missing section/transformation) or if any parameter is invalid.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> from femora.core.element_base import Element
            >>> from femora.components.Section.SectionBase import Section # Assuming Section exists
            >>> from femora.components.Transformation.TransformationBase import Transformation # Assuming Transformation exists
            >>> class DummySection(Section):
            ...     def __init__(self, tag, A=1.0, Iy=1.0, Iz=1.0, G=1.0, J=1.0): self.tag, self.A, self.Iy, self.Iz, self.J = tag, A, Iy, Iz, J
            ...     def get_area(self): return self.A
            ...     def get_Iy(self): return self.Iy
            ...     def get_Iz(self): return self.Iz
            ...     def get_J(self): return self.J
            >>> class DummyTransformation(Transformation):
            ...     def __init__(self, tag, vecxz=[0,0,1]): self.tag, self.vecxz_x, self.vecxz_y, self.vecxz_z = tag, vecxz[0], vecxz[1], vecxz[2]
            >>> class DummyBeamElement(Element):
            ...     def __init__(self, tag, nodes, section, transformation, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 6)
            ...         self.element_type = "DispBeamColumn"
            ...     def get_section(self): return self._section
            ...     def get_transformation(self): return self._transformation
            ...     def get_mass_per_length(self): return 10.0
            >>> dummy_section = DummySection(tag=1)
            >>> dummy_transf = DummyTransformation(tag=1)
            >>> beam_element = DummyBeamElement(tag=1, nodes=[], section=dummy_section, transformation=dummy_transf)
            >>>
            >>> # Example: Create a 2x2 grid of columns
            >>> mesh_part = fm.components.Mesh.meshParts.StructuredLineMesh(
            ...     user_name="my_column_grid",
            ...     element=beam_element,
            ...     base_point_x=0, base_point_y=0, base_point_z=0,
            ...     base_vector_1_x=1, base_vector_1_y=0, base_vector_1_z=0,
            ...     base_vector_2_x=0, base_vector_2_y=1, base_vector_2_z=0,
            ...     normal_x=0, normal_y=0, normal_z=1,
            ...     grid_size_1=1, grid_size_2=1, spacing_1=5, spacing_2=5,
            ...     length=3, number_of_lines=2 # Two segments per column
            ... )
            >>> print(f"Number of nodes: {mesh_part.mesh.n_points}") # (1+1)*(1+1) * (2+1) merged points
            Number of nodes: 12
            >>> print(f"Number of cells: {mesh_part.mesh.n_cells}") # (1+1)*(1+1) * 2 cells
            Number of cells: 8
        """
        super().__init__(
            category='line mesh',
            mesh_type='Structured Line Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        
        # Validate element compatibility
        if not self.is_element_compatible(element):
            raise ValueError(f"Element type '{element.element_type}' is not compatible with line mesh. "
                           f"Must be a beam element with section and transformation.")
        
        kwargs = self.validate_parameters(**kwargs)
        self.params = kwargs if kwargs else {}
        self.generate_mesh()

    def is_element_compatible(self, element: Element) -> bool:
        """Checks if the given element is compatible with line mesh generation.

        This involves checking if the element's type is in the compatible list
        and if it possesses both a section and a transformation object.

        Args:
            element: The Element object to check for compatibility.

        Returns:
            bool: True if the element is compatible, False otherwise.

        Example:
            >>> import femora as fm
            >>> from femora.core.element_base import Element
            >>> from femora.components.Section.SectionBase import Section
            >>> from femora.components.Transformation.TransformationBase import Transformation
            >>> class ValidBeamElement(Element):
            ...     def __init__(self, tag, nodes, section, transformation):
            ...         super().__init__(tag, nodes, section, transformation, None, 6)
            ...         self.element_type = "DispBeamColumn"
            ...     def get_section(self): return Section(1)
            ...     def get_transformation(self): return Transformation(1)
            ...     def get_mass_per_length(self): return 1.0
            >>> class InvalidBeamElement(Element):
            ...     def __init__(self, tag, nodes, section, transformation):
            ...         super().__init__(tag, nodes, section, transformation, None, 6)
            ...         self.element_type = "DispBeamColumn"
            ...     def get_section(self): return None # Missing section
            ...     def get_transformation(self): return Transformation(1)
            ...     def get_mass_per_length(self): return 1.0
            >>> valid_element = ValidBeamElement(1, [], None, None)
            >>> invalid_element = InvalidBeamElement(2, [], None, None)
            >>> print(fm.components.Mesh.meshParts.StructuredLineMesh.is_element_compatible(valid_element))
            True
            >>> print(fm.components.Mesh.meshParts.StructuredLineMesh.is_element_compatible(invalid_element))
            False
        """
        # Check element type compatibility using base class method
        if not self.is_elemnt_compatible(element.element_type):
            return False
        
        # Must have section and transformation
        if not element.get_section() or not element.get_transformation():
            return False
        
        return True

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generates a structured line mesh based on the current parameters.

        Constructs a grid of points and connects them to form line elements.
        If `merge_points` is True, duplicate points at grid intersections are merged.
        Mass properties are also assigned to the mesh points based on the element's
        mass per length and section properties.

        Returns:
            pv.UnstructuredGrid: The generated PyVista unstructured grid representing the line mesh.

        Example:
            >>> import femora as fm
            >>> import pyvista as pv
            >>> from femora.core.element_base import Element
            >>> from femora.components.Section.SectionBase import Section
            >>> from femora.components.Transformation.TransformationBase import Transformation
            >>> class DummySection(Section):
            ...     def __init__(self, tag, A=1.0, Iy=1.0, Iz=1.0, J=1.0): self.tag, self.A, self.Iy, self.Iz, self.J = tag, A, Iy, Iz, J
            ...     def get_area(self): return self.A
            ...     def get_Iy(self): return self.Iy
            ...     def get_Iz(self): return self.Iz
            ...     def get_J(self): return self.J if self.J is not None else (self.Iy + self.Iz) # Ensure J exists
            >>> class DummyTransformation(Transformation):
            ...     def __init__(self, tag, vecxz=[0,0,1]): self.tag, self.vecxz_x, self.vecxz_y, self.vecxz_z = tag, vecxz[0], vecxz[1], vecxz[2]
            >>> class DummyBeamElement(Element):
            ...     def __init__(self, tag, nodes, section, transformation, material=None):
            ...         super().__init__(tag, nodes, section, transformation, material, 6)
            ...         self.element_type = "DispBeamColumn"
            ...         self._section = section # Store section for get_section()
            ...         self._transformation = transformation # Store transformation
            ...     def get_section(self): return self._section
            ...     def get_transformation(self): return self._transformation
            ...     def get_mass_per_length(self): return 1.0 # Unit mass per length
            >>> dummy_section = DummySection(tag=1, A=0.1, Iy=0.001, Iz=0.002, J=0.003)
            >>> dummy_transf = DummyTransformation(tag=1)
            >>> beam_element = DummyBeamElement(tag=1, nodes=[], section=dummy_section, transformation=dummy_transf)
            >>>
            >>> mesh_part = fm.components.Mesh.meshParts.StructuredLineMesh(
            ...     user_name="gen_mesh_ex", element=beam_element,
            ...     grid_size_1=1, grid_size_2=0, spacing_1=1.0, length=1.0, number_of_lines=1
            ... )
            >>> mesh = mesh_part.generate_mesh()
            >>> print(mesh.n_cells)
            1
            >>> print(mesh.point_data['Mass'].shape)
            (2, 6)
        """
        import numpy as np
        
        # Extract parameters
        base_point = np.array([
            self.params.get('base_point_x', 0),
            self.params.get('base_point_y', 0),
            self.params.get('base_point_z', 0)
        ])
        
        base_vector_1 = np.array([
            self.params.get('base_vector_1_x', 1),
            self.params.get('base_vector_1_y', 0),
            self.params.get('base_vector_1_z', 0)
        ])
        
        base_vector_2 = np.array([
            self.params.get('base_vector_2_x', 0),
            self.params.get('base_vector_2_y', 1),
            self.params.get('base_vector_2_z', 0)
        ])
        
        normal = np.array([
            self.params.get('normal_x', 0),
            self.params.get('normal_y', 0),
            self.params.get('normal_z', 1)
        ])
        
        grid_size_1 = self.params.get('grid_size_1', 10)
        grid_size_2 = self.params.get('grid_size_2', 10)
        spacing_1 = self.params.get('spacing_1', 1.0)
        spacing_2 = self.params.get('spacing_2', 1.0)
        length = self.params.get('length', 1.0)
        offset_1 = self.params.get('offset_1', 0.0)
        offset_2 = self.params.get('offset_2', 0.0)
        number_of_lines = self.params.get('number_of_lines', 1)
        merge_points = self.params.get('merge_points', True)
        
        # Normalize vectors
        base_vector_1_norm = np.linalg.norm(base_vector_1)
        if base_vector_1_norm > 1e-12:
            base_vector_1 = base_vector_1 / base_vector_1_norm
        else:
            base_vector_1 = np.array([1.0, 0.0, 0.0])

        base_vector_2_norm = np.linalg.norm(base_vector_2)
        if base_vector_2_norm > 1e-12:
            base_vector_2 = base_vector_2 / base_vector_2_norm
        else:
            base_vector_2 = np.array([0.0, 1.0, 0.0])

        normal_norm = np.linalg.norm(normal)
        if normal_norm > 1e-12:
            normal = normal / normal_norm
        else:
            normal = np.array([0.0, 0.0, 1.0])
        
        # Generate grid points
        points = []
        lines = []
        point_id = 0
        
        for i in range(grid_size_1 + 1):
            for j in range(grid_size_2 + 1):
                # Calculate grid point
                grid_point = (base_point + 
                            (i * spacing_1 + offset_1) * base_vector_1 +
                            (j * spacing_2 + offset_2) * base_vector_2)
                
                # Create multiple line elements along the normal direction
                for k in range(number_of_lines):
                    # Calculate the start and end points for this line segment
                    # Each line covers 1/number_of_lines of the total length
                    t_start = k / number_of_lines
                    t_end = (k + 1) / number_of_lines
                    
                    line_start = grid_point + t_start * length * normal
                    line_end = grid_point + t_end * length * normal
                    
                    # Add points for this line
                    points.append(line_start)
                    points.append(line_end)
                    
                    # Add line (connect two points)
                    lines.extend([2, point_id, point_id + 1])
                    point_id += 2
        
        # Create PyVista PolyData
        if points:
            points_array = np.array(points)
            poly_mesh = pv.PolyData(points_array, lines=lines)
            
            # Merge points if requested
            if merge_points:
                poly_mesh = poly_mesh.merge_points(tolerance=1e-4,
                                                 inplace=False,
                                                 progress_bar=False)
            
            # Cast to UnstructuredGrid
            self.mesh = poly_mesh.cast_to_unstructured_grid()
        else:
            # Create empty mesh if no points
            self.mesh = pv.PolyData().cast_to_unstructured_grid()

        # Assign mass properties
        if self.mesh.n_points > 0:
            mass_per_length = self.element.get_mass_per_length()
            if mass_per_length is None:
                mass_per_length = 0.0 # Default if not defined in element
            
            total_length_per_line_segment = length / number_of_lines
            m_translational_lumped_per_node = mass_per_length * total_length_per_line_segment / 2.0
            
            Mass = np.zeros((self.mesh.n_points, FEMORA_MAX_NDF), dtype=np.float32)
            Mass[:, :3] = m_translational_lumped_per_node  # Assign mass in translational DOFs
            
            # Rotational mass calculation, if section and transformation exist
            section = self.element.get_section()
            transf = self.element.get_transformation()
            
            m_rx, m_ry, m_rz = 0.0, 0.0, 0.0 # Initialize rotational masses

            if