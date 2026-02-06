"""
This module defines various mesh part instances with the base class of MeshPart.
It includes the StructuredRectangular3D class, which represents a 3D 
structured rectangular mesh part.It provides functionality to 
initialize, generate, and validate a structured rectangular mesh grid using 
the PyVista library.

Classes:
    StructuredRectangular3D: A class representing a 3D structured rectangular mesh part.
    CustomRectangularGrid3D: A class representing a 3D custom rectangular grid mesh part.
    GeometricStructuredRectangular3D: A class representing a 3D geometric structured rectangular mesh part.
    CustomMesh: A class representing a custom mesh part that can load from a file or accept an existing PyVista mesh.

Functions:
    generate_mesh: Generates a structured rectangular mesh.
    get_parameters: Returns a list of parameters for the mesh part type.
    validate_parameters: Validates the input parameters for the mesh part.
    is_elemnt_compatible: Returns True if the element is compatible with the mesh part type.
    update_parameters: Updates the mesh part parameters.
    get_Notes: Returns notes for the mesh part type.


Usage:
    This module is intended to be used as part of the MeshMaker lib for 
    defining and manipulating 3D structured rectangular mesh parts.
"""
from typing import Dict, List, Tuple, Union, Optional
from abc import ABC, abstractmethod
import numpy as np
import pyvista as pv
import os
from femora.components.Mesh.meshPartBase import MeshPart, MeshPartRegistry
from femora.components.Element.elementBase import Element
from femora.components.Region.regionBase import RegionBase
from femora.constants import FEMORA_MAX_NDF



class StructuredRectangular3D(MeshPart):
    """
    Structured Rectangular 3D Mesh Part

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated element.
    region : RegionBase, optional
        Associated region.
    X Min or x_min : float
        Minimum X coordinate.
    X Max or x_max : float
        Maximum X coordinate.
    Y Min or y_min : float
        Minimum Y coordinate.
    Y Max or y_max : float
        Maximum Y coordinate.
    Z Min or z_min : float
        Minimum Z coordinate.
    Z Max or z_max : float
        Maximum Z coordinate.
    Nx Cells or nx : int
        Number of cells in X direction.
    Ny Cells or ny : int
        Number of cells in Y direction.
    Nz Cells or nz : int
        Number of cells in Z direction.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """
        Initialize a 3D Structured Rectangular Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated element.
        region : RegionBase, optional
            Associated region.
        X Min or x_min : float
            Minimum X coordinate.
        X Max or x_max : float
            Maximum X coordinate.
        Y Min or y_min : float
            Minimum Y coordinate.
        Y Max or y_max : float
            Maximum Y coordinate.
        Z Min or z_min : float
            Minimum Z coordinate.
        Z Max or z_max : float
            Maximum Z coordinate.
        Nx Cells or nx : int
            Number of cells in X direction.
        Ny Cells or ny : int
            Number of cells in Y direction.
        Nz Cells or nz : int
            Number of cells in Z direction.
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
        """
        Generate a structured rectangular mesh
        
        Returns:
            pv.UnstructuredGrid: Generated mesh
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
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[str]: List of parameter names
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
        """
        Check if the mesh part input parameters are valid.
        
        Returns:
            Dict[str, Union[int, float, str]]: Dictionary of parmaeters with valid values
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
        """
        Get the list of compatible element types
        Returns:
            List[str]: List of compatible element types
        """
        return element in cls._compatible_elements
    


    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params


    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Get notes for the mesh part type
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing notes about the mesh part
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
    """
    Custom Rectangular Grid 3D Mesh Part

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated element.
    region : RegionBase, optional
        Associated region.
    x_coords : list of float (comma separated string)
        List of X coordinates.
    y_coords : list of float (comma separated string)
        List of Y coordinates.
    z_coords : list of float (comma separated string)
        List of Z coordinates.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """
        Initialize a 3D Custom Rectangular Grid Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated element.
        region : RegionBase, optional
            Associated region.
        x_coords : list of float (comma separated string)
            List of X coordinates.
        y_coords : list of float (comma separated string)
            List of Y coordinates.
        z_coords : list of float (comma separated string)
            List of Z coordinates.
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Custom Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        self.params = kwargs
        self.generate_mesh()

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """
        Generate a custom rectangular grid mesh
        
        Returns:
            pv.UnstructuredGrid: Generated mesh
        """
        x_coords = self.params.get('x_coords', None).split(',')
        y_coords = self.params.get('y_coords', None).split(',')
        z_coords = self.params.get('z_coords', None).split(',')
        x = np.array(x_coords)
        y = np.array(y_coords)
        z = np.array(z_coords)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        self.mesh = pv.StructuredGrid(X, Y, Z).cast_to_unstructured_grid()
        del x, y, z, X, Y, Z
        return self.mesh
    
    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[str]: List of parameter names
        """
        return [
            ("x_coords", "List of X coordinates (List[float] , comma separated, required)"),
            ("y_coords", "List of Y coordinates (List[float] , comma separated, required)"),
            ("z_coords", "List of Z coordinates (List[float] , comma separated, required)")
        ]
    
    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, List[float]]]:
        """
        Check if the mesh part input parameters are valid.
        
        Returns:
            Dict[str, Union[int, float, str, List[float]]: Dictionary of parmaeters with valid values
        """
        valid_params = {}
        for param_name in ['x_coords', 'y_coords', 'z_coords']:
            if param_name in kwargs:
                try:
                    valid_params[param_name] = [float(x) for x in kwargs[param_name].split(',')]
                    # check if the values are in ascending order
                    if not all(valid_params[param_name][i] < valid_params[param_name][i+1] for i in range(len(valid_params[param_name])-1)):
                        raise ValueError(f"{param_name} must be in ascending order")
                    valid_params[param_name] = kwargs[param_name]
                except ValueError:
                    raise ValueError(f"{param_name} must be a list of float numbers")
            else:
                raise ValueError(f"{param_name} parameter is required")
        return valid_params

    @classmethod
    def is_elemnt_compatible(cls, element:str) -> bool:
        """
        Get the list of compatible element types
        Returns:
            List[str]: List of compatible element types
        """
        return element in ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]


    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params


    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Get notes for the mesh part type
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing notes about the mesh part
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
    """
    Geometric Structured Rectangular 3D Mesh Part

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated element.
    region : RegionBase, optional
        Associated region.
    x_min : float
        Minimum X coordinate.
    x_max : float
        Maximum X coordinate.
    y_min : float
        Minimum Y coordinate.
    y_max : float
        Maximum Y coordinate.
    z_min : float
        Minimum Z coordinate.
    z_max : float
        Maximum Z coordinate.
    nx : int
        Number of cells in X direction.
    ny : int
        Number of cells in Y direction.
    nz : int
        Number of cells in Z direction.
    x_ratio : float, optional
        Ratio of cell increment in X direction (default 1).
    y_ratio : float, optional
        Ratio of cell increment in Y direction (default 1).
    z_ratio : float, optional
        Ratio of cell increment in Z direction (default 1).
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    def __init__(self, user_name: str, element: Element, region: RegionBase=None,**kwargs):
        """
        Initialize a 3D Geometric Structured Rectangular Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated element.
        region : RegionBase, optional
            Associated region.
        x_min : float
            Minimum X coordinate.
        x_max : float
            Maximum X coordinate.
        y_min : float
            Minimum Y coordinate.
        y_max : float
            Maximum Y coordinate.
        z_min : float
            Minimum Z coordinate.
        z_max : float
            Maximum Z coordinate.
        nx : int
            Number of cells in X direction.
        ny : int
            Number of cells in Y direction.
        nz : int
            Number of cells in Z direction.
        x_ratio : float, optional
            Ratio of cell increment in X direction (default 1).
        y_ratio : float, optional
            Ratio of cell increment in Y direction (default 1).
        z_ratio : float, optional
            Ratio of cell increment in Z direction (default 1).
        """
        super().__init__(
            category='volume mesh',
            mesh_type='Geometric Rectangular Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        self.params = kwargs
        self.generate_mesh()

    @staticmethod
    def custom_linspace(start, end, num_elements, ratio=1):
        """
        Generate a sequence of numbers between start and end with specified spacing ratio.

        Parameters:
        - start (float): The starting value of the sequence.
        - end (float): The ending value of the sequence.
        - num_elements (int): The number of elements in the sequence.
        - ratio (float, optional): The ratio of increment between consecutive intervals. Defaults to 1 (linear spacing).

        Returns:
        - numpy.ndarray: The generated sequence.
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
        """
        Generate a geometric structured rectangular mesh
        
        Returns:
            pv.UnstructuredGrid: Generated mesh
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
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[str]: List of parameter names
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
        """
        Check if the mesh part input parameters are valid.
        
        Returns:
            Dict[str, Union[int, float, str]]: Dictionary of parmaeters with valid values
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
                valid_params[param_name] = 1
        
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
        """
        Get the list of compatible element types
        Returns:
            List[str]: List of compatible element types
        """
        return element in ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    
    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params = validated_params

    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Get notes for the mesh part type
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing notes about the mesh part
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
                "Requires manual specification of all grid points"
            ],
            "tips": [
                "Provide coordinates as comma-separated lists of float values",
                "Ensure coordinates are in ascending order",
                "Consider gradual transitions in spacing for better numerical results"
            ]
        }
    
# Register the 3D Geometric Structured Rectangular mesh part type
MeshPartRegistry.register_mesh_part_type('Volume mesh', 'Geometric Rectangular Grid', GeometricStructuredRectangular3D)


class ExternalMesh(MeshPart):
    """
    Custom Mesh Part that can load from a file or accept an existing PyVista mesh.

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated element.
    region : RegionBase, optional
        Associated region.
    mesh : pv.UnstructuredGrid, optional
        Existing PyVista mesh to use.
    filepath : str, optional
        Path to mesh file to load.
    scale : float, optional
        Scale factor for the mesh.
    rotate_x : float, optional
        Rotation angle around X-axis in degrees.
    rotate_y : float, optional
        Rotation angle around Y-axis in degrees.
    rotate_z : float, optional
        Rotation angle around Z-axis in degrees.
    translate_x : float, optional
        Translation along X-axis.
    translate_y : float, optional
        Translation along Y-axis.
    translate_z : float, optional
        Translation along Z-axis.
    transform_args : dict, optional
        Optional transformation arguments dictionary containing any of the above transformation parameters.
    """
    _compatible_elements = ["stdBrick", "bbarBrick", "SSPbrick", "PML3D"]
    
    def __init__(self, user_name: str, element: Element, region: RegionBase=None, **kwargs):
        """
        Initialize a Custom Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated element.
        region : RegionBase, optional
            Associated region.
        mesh : pv.UnstructuredGrid, optional
            Existing PyVista mesh to use.
        filepath : str, optional
            Path to mesh file to load.
        scale : float, optional
            Scale factor for the mesh.
        rotate_x : float, optional
            Rotation angle around X-axis in degrees.
        rotate_y : float, optional
            Rotation angle around Y-axis in degrees.
        rotate_z : float, optional
            Rotation angle around Z-axis in degrees.
        translate_x : float, optional
            Translation along X-axis.
        translate_y : float, optional
            Translation along Y-axis.
        translate_z : float, optional
            Translation along Z-axis.
        transform_args : dict, optional
            Optional transformation arguments dictionary containing any of the above transformation parameters.
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
        """
        Generate a mesh by loading from file or using the provided mesh and apply transformations
        
        Returns:
            pv.UnstructuredGrid: Generated mesh
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
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[Tuple[str, str]]: List of parameter names and descriptions
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
        """
        Check if the mesh part input parameters are valid.
        
        Returns:
            Dict[str, Union[int, float, str, pv.UnstructuredGrid, Dict]]: Dictionary of parameters with valid values
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
        """
        Check if an element type is compatible with this mesh part
        
        Args:
            element (str): Element type name to check
            
        Returns:
            bool: True if compatible, False otherwise
        """
        return element in cls._compatible_elements
    
    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        # Merge with existing parameters to maintain required params
        merged_params = {**self.params, **kwargs}
        validated_params = self.validate_parameters(**merged_params)
        self.params = validated_params
        self.generate_mesh()  # Regenerate the mesh with new parameters

    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Get notes for the mesh part type
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing notes about the mesh part
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
    """
    Structured Line Mesh Part for beam/column elements.
    Creates a grid of line elements with arbitrary normal direction.

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated beam element (must have section and transformation).
    region : RegionBase, optional
        Associated region.
    base_point_x : float, optional
        Base point X coordinate. Default: 0.0
    base_point_y : float, optional
        Base point Y coordinate. Default: 0.0
    base_point_z : float, optional
        Base point Z coordinate. Default: 0.0
    base_vector_1_x : float, optional
        First base vector X component. Default: 1.0
    base_vector_1_y : float, optional
        First base vector Y component. Default: 0.0
    base_vector_1_z : float, optional
        First base vector Z component. Default: 0.0
    base_vector_2_x : float, optional
        Second base vector X component. Default: 0.0
    base_vector_2_y : float, optional
        Second base vector Y component. Default: 1.0
    base_vector_2_z : float, optional
        Second base vector Z component. Default: 0.0
    normal_x : float, optional
        Normal direction X component. Default: 0.0
    normal_y : float, optional
        Normal direction Y component. Default: 0.0
    normal_z : float, optional
        Normal direction Z component. Default: 1.0
    grid_size_1 : int, optional
        Number of elements in direction 1. Default: 10
    grid_size_2 : int, optional
        Number of elements in direction 2. Default: 10
    spacing_1 : float, optional
        Spacing in direction 1. Default: 1.0
    spacing_2 : float, optional
        Spacing in direction 2. Default: 1.0
    length : float, optional
        Length of each line element along normal. Default: 1.0
    offset_1 : float, optional
        Optional offset in direction 1. Default: 0.0
    offset_2 : float, optional
        Optional offset in direction 2. Default: 0.0
    number_of_lines : int, optional
        Number of line elements along normal direction per grid point. Default: 1
    merge_points : bool, optional
        Whether to merge duplicate points. Default: True
    """
    _compatible_elements = ["DispBeamColumn", "ForceBeamColumn", "ElasticBeamColumn", "NonlinearBeamColumn"]
    
    def __init__(self, user_name: str, element: Element, region: Optional[RegionBase]=None, **kwargs):
        """
        Initialize a Structured Line Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated beam element (must have section and transformation).
        region : RegionBase, optional
            Associated region.
        base_point_x : float, optional
            Base point X coordinate. Default: 0.0
        base_point_y : float, optional
            Base point Y coordinate. Default: 0.0
        base_point_z : float, optional
            Base point Z coordinate. Default: 0.0
        base_vector_1_x : float, optional
            First base vector X component. Default: 1.0
        base_vector_1_y : float, optional
            First base vector Y component. Default: 0.0
        base_vector_1_z : float, optional
            First base vector Z component. Default: 0.0
        base_vector_2_x : float, optional
            Second base vector X component. Default: 0.0
        base_vector_2_y : float, optional
            Second base vector Y component. Default: 1.0
        base_vector_2_z : float, optional
            Second base vector Z component. Default: 0.0
        normal_x : float, optional
            Normal direction X component. Default: 0.0
        normal_y : float, optional
            Normal direction Y component. Default: 0.0
        normal_z : float, optional
            Normal direction Z component. Default: 1.0
        grid_size_1 : int, optional
            Number of elements in direction 1. Default: 10
        grid_size_2 : int, optional
            Number of elements in direction 2. Default: 10
        spacing_1 : float, optional
            Spacing in direction 1. Default: 1.0
        spacing_2 : float, optional
            Spacing in direction 2. Default: 1.0
        length : float, optional
            Length of each line element along normal. Default: 1.0
        offset_1 : float, optional
            Optional offset in direction 1. Default: 0.0
        offset_2 : float, optional
            Optional offset in direction 2. Default: 0.0
        number_of_lines : int, optional
            Number of line elements along normal direction per grid point. Default: 1
        merge_points : bool, optional
            Whether to merge duplicate points. Default: True
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
        """
        Check if element is compatible with line mesh
        
        Args:
            element (Element): Element to check
            
        Returns:
            bool: True if compatible, False otherwise
        """
        # Check element type compatibility using base class method
        if not self.is_elemnt_compatible(element.element_type):
            return False
        
        # Must have section and transformation
        if not element.get_section() or not element.get_transformation():
            return False
        
        return True

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """
        Generate a structured line mesh
        
        Returns:
            pv.UnstructuredGrid: Generated line mesh
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
        base_vector_1 = base_vector_1 / np.linalg.norm(base_vector_1)
        base_vector_2 = base_vector_2 / np.linalg.norm(base_vector_2)
        normal = normal / np.linalg.norm(normal)
        
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
        
        return self.mesh

    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[Tuple[str, str]]: List of (parameter_name, description) tuples
        """
        return [
            ('base_point_x', 'Base point X coordinate'),
            ('base_point_y', 'Base point Y coordinate'),
            ('base_point_z', 'Base point Z coordinate'),
            ('base_vector_1_x', 'First base vector X component'),
            ('base_vector_1_y', 'First base vector Y component'),
            ('base_vector_1_z', 'First base vector Z component'),
            ('base_vector_2_x', 'Second base vector X component'),
            ('base_vector_2_y', 'Second base vector Y component'),
            ('base_vector_2_z', 'Second base vector Z component'),
            ('normal_x', 'Normal direction X component'),
            ('normal_y', 'Normal direction Y component'),
            ('normal_z', 'Normal direction Z component'),
            ('grid_size_1', 'Number of elements in direction 1'),
            ('grid_size_2', 'Number of elements in direction 2'),
            ('spacing_1', 'Spacing in direction 1'),
            ('spacing_2', 'Spacing in direction 2'),
            ('length', 'Length of each line element along normal'),
            ('offset_1', 'Optional offset in direction 1'),
            ('offset_2', 'Optional offset in direction 2'),
            ('number_of_lines', 'Number of line elements along normal direction per grid point'),
            ('merge_points', 'Whether to merge duplicate points (True/False)')
        ]

    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """
        Validate the input parameters for the line mesh part.
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Dict[str, Union[int, float, str]]: Validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        validated_params = {}
        
        # Validate base point coordinates
        for coord in ['base_point_x', 'base_point_y', 'base_point_z']:
            if coord in kwargs:
                try:
                    validated_params[coord] = float(kwargs[coord])
                except (ValueError, TypeError):
                    raise ValueError(f"{coord} must be a valid number")
            else:
                validated_params[coord] = 0.0
        
        # Validate base vectors
        for vec_num in [1, 2]:
            for coord in ['x', 'y', 'z']:
                param_name = f'base_vector_{vec_num}_{coord}'
                if param_name in kwargs:
                    try:
                        validated_params[param_name] = float(kwargs[param_name])
                    except (ValueError, TypeError):
                        raise ValueError(f"{param_name} must be a valid number")
                else:
                    # Default values: base_vector_1 = [1,0,0], base_vector_2 = [0,1,0]
                    if vec_num == 1:
                        validated_params[param_name] = 1.0 if coord == 'x' else 0.0
                    else:
                        validated_params[param_name] = 1.0 if coord == 'y' else 0.0
        
        # Validate normal vector
        for coord in ['normal_x', 'normal_y', 'normal_z']:
            if coord in kwargs:
                try:
                    validated_params[coord] = float(kwargs[coord])
                except (ValueError, TypeError):
                    raise ValueError(f"{coord} must be a valid number")
            else:
                validated_params[coord] = 1.0 if coord == 'normal_z' else 0.0
        
        # Validate grid sizes
        for size_param in ['grid_size_1', 'grid_size_2']:
            if size_param in kwargs:
                try:
                    size = int(kwargs[size_param])
                    if size < 0:
                        raise ValueError(f"{size_param} must be non-negative")
                    validated_params[size_param] = size
                except (ValueError, TypeError):
                    raise ValueError(f"{size_param} must be a non-negative integer")
            else:
                validated_params[size_param] = 10
        
        # Validate spacings
        for spacing_param in ['spacing_1', 'spacing_2']:
            if spacing_param in kwargs:
                try:
                    spacing = float(kwargs[spacing_param])
                    if spacing <= 0:
                        raise ValueError(f"{spacing_param} must be positive")
                    validated_params[spacing_param] = spacing
                except (ValueError, TypeError):
                    raise ValueError(f"{spacing_param} must be a positive number")
            else:
                validated_params[spacing_param] = 1.0
        
        # Validate length
        if 'length' in kwargs:
            try:
                length = float(kwargs['length'])
                if length <= 0:
                    raise ValueError("length must be positive")
                validated_params['length'] = length
            except (ValueError, TypeError):
                raise ValueError("length must be a positive number")
        else:
            validated_params['length'] = 1.0
        
        # Validate offsets
        for offset_param in ['offset_1', 'offset_2']:
            if offset_param in kwargs:
                try:
                    offset = float(kwargs[offset_param])
                    validated_params[offset_param] = offset
                except (ValueError, TypeError):
                    raise ValueError(f"{offset_param} must be a valid number")
            else:
                validated_params[offset_param] = 0.0
        
        # Validate number of lines
        if 'number_of_lines' in kwargs:
            try:
                num_lines = int(kwargs['number_of_lines'])
                if num_lines < 1:
                    raise ValueError("number_of_lines must be at least 1")
                validated_params['number_of_lines'] = num_lines
            except (ValueError, TypeError):
                raise ValueError("number_of_lines must be a positive integer")
        else:
            validated_params['number_of_lines'] = 1
        
        # Validate merge_points
        if 'merge_points' in kwargs:
            merge_val = kwargs['merge_points']
            if isinstance(merge_val, str):
                merge_val = merge_val.lower()
                if merge_val in ['true', '1', 'yes', 'on']:
                    validated_params['merge_points'] = True
                elif merge_val in ['false', '0', 'no', 'off']:
                    validated_params['merge_points'] = False
                else:
                    raise ValueError("merge_points must be True/False or a valid boolean string")
            elif isinstance(merge_val, bool):
                validated_params['merge_points'] = merge_val
            else:
                raise ValueError("merge_points must be a boolean value")
        else:
            validated_params['merge_points'] = True
        
        return validated_params

    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params.update(validated_params)
        self.generate_mesh()

    @classmethod
    def get_Notes(cls) -> Dict[str, Union[str, List[str]]]:
        """
        Get notes for the line mesh part type.
        
        Returns:
            Dict[str, Union[str, List[str]]]: Notes with description, usage, limitations, and tips
        """
        return {
            "description": "Structured Line Grid creates a regular grid of line elements (beams/columns) with arbitrary normal direction. Each line element extends from a grid point along the specified normal direction.",
            "usage": [
                "Use for creating column grids in buildings",
                "Use for creating beam grids in floor systems", 
                "Use for creating inclined structural elements",
                "Ensure the associated element is a beam type with section and transformation",
                "Specify base vectors to define the grid orientation",
                "Specify normal vector to define the direction of line elements"
            ],
            "limitations": [
                "Only compatible with beam element types",
                "Requires element to have both section and geometric transformation",
                "Grid is limited to rectangular patterns",
                "All lines have the same length"
            ],
            "tips": [
                "Use base_vector_1 and base_vector_2 to define the grid plane orientation",
                "Use normal vector to define the direction of the line elements",
                "Set grid_size_1 and grid_size_2 to control the density of the grid",
                "Use spacing_1 and spacing_2 to control the distance between lines",
                "Use offset_1 and offset_2 to shift the entire grid",
                "Ensure base vectors are perpendicular for best results"
            ]
        }

# Register the Structured Line mesh part type
MeshPartRegistry.register_mesh_part_type('Line mesh', 'Structured Line Grid', StructuredLineMesh)


class SingleLineMesh(MeshPart):
    """
    Single Line Mesh Part for beam/column elements.
    Creates a single line element between two points.

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated beam element (must have section and transformation).
    region : RegionBase, optional
        Associated region.
    x0 : float, optional
        Start point X coordinate. Default: 0.0
    y0 : float, optional
        Start point Y coordinate. Default: 0.0
    z0 : float, optional
        Start point Z coordinate. Default: 0.0
    x1 : float, optional
        End point X coordinate. Default: 1.0
    y1 : float, optional
        End point Y coordinate. Default: 0.0
    z1 : float, optional
        End point Z coordinate. Default: 0.0
    number_of_lines : int, optional
        Number of line elements to create along the path. Default: 1
    merge_points : bool, optional
        Whether to merge duplicate points. Default: True
    """
    _compatible_elements = ["DispBeamColumn", "ForceBeamColumn", "ElasticBeamColumn", "NonlinearBeamColumn"]
    
    def __init__(self, user_name: str, element: Element, region: Optional[RegionBase]=None, **kwargs):
        """
        Initialize a Single Line Mesh Part.

        Parameters
        ----------
        user_name : str
            Unique user name for the mesh part.
        element : Element
            Associated beam element (must have section and transformation).
        region : RegionBase, optional
            Associated region.
        x0 : float, optional
            Start point X coordinate. Default: 0.0
        y0 : float, optional
            Start point Y coordinate. Default: 0.0
        z0 : float, optional
            Start point Z coordinate. Default: 0.0
        x1 : float, optional
            End point X coordinate. Default: 1.0
        y1 : float, optional
            End point Y coordinate. Default: 0.0
        z1 : float, optional
            End point Z coordinate. Default: 0.0
        number_of_lines : int, optional
            Number of line elements to create along the path. Default: 1
        merge_points : bool, optional
            Whether to merge duplicate points. Default: True
        """
        super().__init__(
            category='line mesh',
            mesh_type='Single Line',
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
        """
        Check if element is compatible with line mesh
        
        Args:
            element (Element): Element to check
            
        Returns:
            bool: True if compatible, False otherwise
        """
        # Check element type compatibility using base class method
        if not self.is_elemnt_compatible(element.element_type):
            return False
        
        # Must have section and transformation
        if not element.get_section() or not element.get_transformation():
            return False
        
        return True

    def generate_mesh(self) -> pv.PolyData:
        """
        Generate a single line mesh
        
        Returns:
            pv.PolyData: Generated line mesh
        """
        import numpy as np
        
        # Extract parameters
        x0 = self.params.get('x0', 0.0)
        y0 = self.params.get('y0', 0.0)
        z0 = self.params.get('z0', 0.0)
        x1 = self.params.get('x1', 1.0)
        y1 = self.params.get('y1', 0.0)
        z1 = self.params.get('z1', 0.0)
        number_of_lines = self.params.get('number_of_lines', 1)
        merge_points = self.params.get('merge_points', True)
        
        # Create start and end points
        start_point = np.array([x0, y0, z0])
        end_point = np.array([x1, y1, z1])
        
        # Calculate the direction vector
        direction = end_point - start_point
        
        # Create points array for multiple lines
        points = []
        lines = []
        point_id = 0
        
        for i in range(number_of_lines):
            # Calculate the start and end points for this line segment
            # Each line covers 1/number_of_lines of the total distance
            t_start = i / number_of_lines
            t_end = (i + 1) / number_of_lines
            
            line_start = start_point + t_start * direction
            line_end = start_point + t_end * direction
            
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


        mass_per_length = self.element.get_mass_per_length()
        print(f"Mass per length: {mass_per_length}")
        L = np.linalg.norm(direction)/ number_of_lines
        m = mass_per_length * L /2
        Mass = np.zeros((self.mesh.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        Mass[:, :3] = m  # Assign mass in translational DOFs
        Mass[:, 3:6] = m*(L**2)/4.
        if merge_points:
            start_ind = pv.UnstructuredGrid(self.mesh).find_closest_point(start_point)
            end_ind = pv.UnstructuredGrid(self.mesh).find_closest_point(end_point)
            Mass = 2 * Mass
            Mass[start_ind] /=2.
            Mass[end_ind] /=2.
        self.mesh.point_data['Mass'] = Mass
        return self.mesh

    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        """
        Get the list of parameters for this mesh part type.
        
        Returns:
            List[Tuple[str, str]]: List of (parameter_name, description) tuples
        """
        return [
            ('x0', 'Start point X coordinate'),
            ('y0', 'Start point Y coordinate'),
            ('z0', 'Start point Z coordinate'),
            ('x1', 'End point X coordinate'),
            ('y1', 'End point Y coordinate'),
            ('z1', 'End point Z coordinate'),
            ('number_of_lines', 'Number of line elements to create along the path. default is 1'),
            ('merge_points', 'Whether to merge duplicate points (True/False). default is True')
        ]

    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """
        Validate the input parameters for the single line mesh part.
        
        Args:
            **kwargs: Input parameters
            
        Returns:
            Dict[str, Union[int, float, str]]: Validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        validated_params = {}
        
        # Validate start point coordinates
        for coord in ['x0', 'y0', 'z0']:
            if coord in kwargs:
                try:
                    validated_params[coord] = float(kwargs[coord])
                except (ValueError, TypeError):
                    raise ValueError(f"{coord} must be a valid number")
            else:
                validated_params[coord] = 0.0
        
        # Validate end point coordinates
        for coord in ['x1', 'y1', 'z1']:
            if coord in kwargs:
                try:
                    validated_params[coord] = float(kwargs[coord])
                except (ValueError, TypeError):
                    raise ValueError(f"{coord} must be a valid number")
            else:
                validated_params[coord] = 1.0 if coord == 'x1' else 0.0
        
        # Validate number of lines
        if 'number_of_lines' in kwargs:
            try:
                num_lines = int(kwargs['number_of_lines'])
                if num_lines < 1:
                    raise ValueError("Number of lines must be at least 1")
                validated_params['number_of_lines'] = num_lines
            except (ValueError, TypeError):
                raise ValueError("number_of_lines must be a positive integer")
        else:
            validated_params['number_of_lines'] = 1
        
        # Check that start and end points are different
        start_point = np.array([validated_params['x0'], validated_params['y0'], validated_params['z0']])
        end_point = np.array([validated_params['x1'], validated_params['y1'], validated_params['z1']])
        
        if np.allclose(start_point, end_point):
            raise ValueError("Start and end points cannot be the same")
        
        # Validate merge_points
        if 'merge_points' in kwargs:
            merge_val = kwargs['merge_points']
            if isinstance(merge_val, str):
                merge_val = merge_val.lower().strip()
                if merge_val in ['true', '1', 'yes', 'on']:
                    validated_params['merge_points'] = True
                elif merge_val in ['false', '0', 'no', 'off']:
                    validated_params['merge_points'] = False
                elif merge_val == '':  # Handle empty string as default True
                    validated_params['merge_points'] = True
                else:
                    raise ValueError("merge_points must be True/False or a valid boolean string")
            elif isinstance(merge_val, bool):
                validated_params['merge_points'] = merge_val
            else:
                raise ValueError("merge_points must be a boolean value")
        else:
            validated_params['merge_points'] = True
        
        return validated_params

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        """
        Check if element type is compatible with this mesh part
        
        Args:
            element (str): Element type name
            
        Returns:
            bool: True if compatible, False otherwise
        """
        return element.lower() in [elem.lower() for elem in cls._compatible_elements]

    def update_parameters(self, **kwargs) -> None:
        """
        Update mesh part parameters
        
        Args:
            **kwargs: Keyword arguments to update
        """
        validated_params = self.validate_parameters(**kwargs)
        self.params.update(validated_params)
        self.generate_mesh()

    @classmethod
    def get_Notes(cls) -> Dict[str, Union[str, List[str]]]:
        """
        Get notes for the mesh part type
        
        Returns:
            Dict[str, Union[str, List[str]]]: Dictionary containing notes about the mesh part
        """
        return {
            "description": "Creates a single line element between two specified points. Ideal for individual beam or column elements.",
            "usage": [
                "Use for creating individual beam or column elements",
                "Specify start and end points to define the line direction and length",
                "Compatible with beam elements that have section and transformation properties",
                "Suitable for structural analysis requiring individual line elements"
            ],
            "limitations": [
                "Creates only one line element per mesh part",
                "Requires beam element with section and transformation",
                "Cannot create multiple lines or complex geometries"
            ],
            "tips": [
                "Ensure start and end points are different",
                "Use appropriate beam element type for your analysis",
                "Consider the coordinate system when specifying points",
                "Check that the element has proper section and transformation properties"
            ]
        }

# Register the Single Line mesh part type
MeshPartRegistry.register_mesh_part_type('Line mesh', 'Single Line', SingleLineMesh)



# Manager classes for organizing mesh types
class LineMeshManager:
    """Manager class for line mesh types"""
    single_line = SingleLineMesh
    structured_lines = StructuredLineMesh


class VolumeMeshManager:
    """Manager class for volume mesh types"""
    uniform_rectangular_grid = StructuredRectangular3D
    geometric_rectangular_grid = GeometricStructuredRectangular3D
    external_mesh = ExternalMesh


class CircularOGrid2D(MeshPart):
    """Circular O-Grid 2D quad mesh.

    Generates a structured quad mesh of a circular domain using an O-grid
    topology (central square surrounded by 4 ring blocks). All cells are
    VTK quads (cell type 9) lying on the Z=0 plane.

    Parameters
    ----------
    user_name : str
        Unique user name for the mesh part.
    element : Element
        Associated 2D shell/quad element.
    region : RegionBase, optional
        Associated region.
    R : float
        Outer radius of the circle (must be > 0).
    r0_ratio : float, optional
        Ratio of inner square radius relative to R (default 0.4; typically 0.3–0.5).
    nt : int, optional
        Number of elements per side of inner square and per outer arc (default 24).
    nr : int, optional
        Number of radial elements in each outer ring block (default 12).
    merge_tolerance : float, optional
        Tolerance used when merging duplicate nodes along shared edges (default 1e-12).
    """
    _compatible_elements = [
        "sspquad", "stdquad"
    ]

    def __init__(self, user_name: str, element: Element, region: Optional[RegionBase] = None, **kwargs):
        super().__init__(
            category='surface mesh',
            mesh_type='Circular O-Grid',
            user_name=user_name,
            element=element,
            region=region
        )
        kwargs = self.validate_parameters(**kwargs)
        self.params = kwargs if kwargs else {}
        # Basic element compatibility check
        if not self.is_elemnt_compatible(element.element_type):
            raise ValueError(f"Element type '{element.element_type}' is not compatible with Circular O-Grid 2D mesh")
        self.generate_mesh()

    @staticmethod
    def _merge_nodes(nodes: np.ndarray, quads: np.ndarray, tol: float) -> Tuple[np.ndarray, np.ndarray]:
        """Merge duplicate 2D nodes (same coordinates within tolerance).

        Parameters
        ----------
        nodes : np.ndarray
            Array of shape (N, 2) containing x,y coordinates.
        quads : np.ndarray
            Quad connectivity (E,4) referencing indices into nodes.
        tol : float
            Tolerance for merging.

        Returns
        -------
        (merged_nodes, remapped_quads)
        """
        node_map = {}
        new_nodes = []
        index_map = {}
        for i, (x, y) in enumerate(nodes):
            key = (round(x / tol) * tol, round(y / tol) * tol)
            if key not in node_map:
                node_map[key] = len(new_nodes)
                new_nodes.append([x, y, 0.0])  # elevate to 3D
            index_map[i] = node_map[key]
        merged_nodes = np.array(new_nodes, dtype=float)
        remapped_quads = np.zeros_like(quads)
        for e, q in enumerate(quads):
            remapped_quads[e] = [index_map[idx] for idx in q]
        return merged_nodes, remapped_quads

    def generate_mesh(self) -> pv.UnstructuredGrid:
        """Generate the circular O-grid quad mesh and store as unstructured grid."""
        R = self.params['R']
        r0_ratio = self.params['r0_ratio']
        nt = self.params['nt']
        nr = self.params['nr']
        tol = self.params.get('merge_tolerance', 1e-12)

        r0 = r0_ratio * R
        a = r0 / np.sqrt(2.0)  # half side of inner square

        # Central block (square -a..a)
        xs = np.linspace(-a, a, nt + 1)
        ys = np.linspace(-a, a, nt + 1)
        nodes_c = np.array([[xs[i], ys[j]] for j in range(nt + 1) for i in range(nt + 1)])
        quads_c = []
        for j in range(nt):
            for i in range(nt):
                n0 = j * (nt + 1) + i
                n1 = n0 + 1
                n2 = n0 + (nt + 1) + 1
                n3 = n0 + (nt + 1)
                quads_c.append([n0, n1, n2, n3])
        quads_c = np.array(quads_c)

        def ring_block(x_in, y_in, x_out, y_out):
            nodes = []
            for i in range(nt + 1):
                xin = x_in[i]; yin = y_in[i]
                xout = x_out[i]; yout = y_out[i]
                for j in range(nr + 1):
                    u = j / nr
                    x = (1 - u) * xin + u * xout
                    y = (1 - u) * yin + u * yout
                    nodes.append([x, y])
            nodes = np.array(nodes)
            quads = []
            for i in range(nt):
                for j in range(nr):
                    n0 = i * (nr + 1) + j
                    n1 = (i + 1) * (nr + 1) + j
                    n2 = (i + 1) * (nr + 1) + (j + 1)
                    n3 = i * (nr + 1) + (j + 1)
                    quads.append([n0, n1, n2, n3])
            return nodes, np.array(quads)

        # Build 4 ring blocks around central square
        theta_top = np.linspace(3 * np.pi / 4, np.pi / 4, nt + 1)
        x_in = np.linspace(-a, a, nt + 1); y_in = np.full(nt + 1, a)
        x_out = R * np.cos(theta_top); y_out = R * np.sin(theta_top)
        nodes_t, quads_t = ring_block(x_in, y_in, x_out, y_out)

        theta_r = np.linspace(np.pi / 4, -np.pi / 4, nt + 1)
        x_in = np.full(nt + 1, a); y_in = np.linspace(a, -a, nt + 1)
        x_out = R * np.cos(theta_r); y_out = R * np.sin(theta_r)
        nodes_r, quads_r = ring_block(x_in, y_in, x_out, y_out)

        theta_b = np.linspace(-3 * np.pi / 4, -np.pi / 4, nt + 1)
        x_in = np.linspace(-a, a, nt + 1); y_in = np.full(nt + 1, -a)
        x_out = R * np.cos(theta_b); y_out = R * np.sin(theta_b)
        nodes_b, quads_b = ring_block(x_in, y_in, x_out, y_out)

        theta_l = np.linspace(5 * np.pi / 4, 3 * np.pi / 4, nt + 1)
        x_in = np.full(nt + 1, -a); y_in = np.linspace(-a, a, nt + 1)
        x_out = R * np.cos(theta_l); y_out = R * np.sin(theta_l)
        nodes_l, quads_l = ring_block(x_in, y_in, x_out, y_out)

        # Combine all blocks
        nodes_all = np.vstack([nodes_c, nodes_t, nodes_r, nodes_b, nodes_l])
        quads_all = []
        offset = 0
        for nodes_block, quads_block in [
            (nodes_c, quads_c), (nodes_t, quads_t), (nodes_r, quads_r), (nodes_b, quads_b), (nodes_l, quads_l)
        ]:
            quads_all.append(quads_block + offset)
            offset += len(nodes_block)
        quads_all = np.vstack(quads_all)

        # Merge shared edge nodes
        merged_nodes, merged_quads = self._merge_nodes(nodes_all, quads_all, tol=tol)

        # Build VTK unstructured grid (quad cell type = 9)
        ncells = merged_quads.shape[0]
        cells = np.hstack([np.column_stack([np.full(ncells, 4), merged_quads])]).flatten()
        celltypes = np.full(ncells, 9, dtype=np.uint8)
        self.mesh = pv.UnstructuredGrid(cells, celltypes, merged_nodes)
        return self.mesh

    @classmethod
    def get_parameters(cls) -> List[Tuple[str, str]]:
        return [
            ("R", "Outer radius of the circle (float > 0)"),
            ("r0_ratio", "Ratio of inner square radius (0.2–0.8 typical, float)"),
            ("nt", "Elements per side / arc (int >= 1)"),
            ("nr", "Radial elements in each ring block (int >= 1)"),
            ("merge_tolerance", "Tolerance for node merging (float, optional)"),
        ]

    @classmethod
    def validate_parameters(cls, **kwargs) -> Dict[str, Union[int, float]]:
        required = ['R', 'r0_ratio', 'nt', 'nr']
        params: Dict[str, Union[int, float]] = {}
        for name in required:
            if name not in kwargs:
                raise ValueError(f"Parameter '{name}' is required for CircularOGrid2D")
        try:
            params['R'] = float(kwargs['R'])
            if params['R'] <= 0:
                raise ValueError("R must be > 0")
            params['r0_ratio'] = float(kwargs.get('r0_ratio', 0.4))
            if not (0.1 < params['r0_ratio'] < 0.9):
                raise ValueError("r0_ratio must be between 0.1 and 0.9")
            params['nt'] = int(kwargs.get('nt', 24))
            params['nr'] = int(kwargs.get('nr', 12))
            if params['nt'] < 1 or params['nr'] < 1:
                raise ValueError("nt and nr must be >= 1")
            params['merge_tolerance'] = float(kwargs.get('merge_tolerance', 1e-12))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid CircularOGrid2D parameter: {e}")
        return params

    @classmethod
    def is_elemnt_compatible(cls, element: str) -> bool:
        return element in cls._compatible_elements

    def update_parameters(self, **kwargs) -> None:
        updated = {**self.params, **kwargs}
        self.params = self.validate_parameters(**updated)
        self.generate_mesh()

    @staticmethod
    def get_Notes() -> Dict[str, Union[str, List[str]]]:
        return {
            "description": "Generates a 2D circular O-grid quad mesh (central square + ring blocks) for shell/quad elements.",
            "usage": [
                "Ideal for circular domains requiring structured quads",
                "Use 'R' for domain size and 'r0_ratio' to adjust central square size",
                "Increase 'nt' for finer tangential resolution and 'nr' for radial refinement",
                "Merge tolerance controls edge node unification"
            ],
            "limitations": [
                "Mesh lies on Z=0 plane (pure 2D)",
                "Produces quads only (no triangles)",
                "Not suitable for highly eccentric shapes"
            ],
            "tips": [
                "Choose r0_ratio ~0.3–0.5 for good element quality",
                "Keep nt ≈ 2*nr for balanced aspect ratios",
                "Refine gradually to avoid very small inner elements",
                "Verify element type supports quad topology"
            ]
        }

# Register the Circular O-Grid surface mesh part type
MeshPartRegistry.register_mesh_part_type('Surface mesh', 'Circular O-Grid', CircularOGrid2D)


class SurfaceMeshManager:
    """Manager class for surface mesh types"""
    circular_o_grid = CircularOGrid2D