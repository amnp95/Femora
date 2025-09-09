"""
Geometric Transformation Classes for OpenSees

This module implements geometric transformation classes for OpenSees finite element analysis.
It provides 2D and 3D geometric transformations with support for Linear, PDelta, and 
Corotational transformation types.

Classes:
    GeometricTransformation: Abstract base class for all geometric transformations
    GeometricTransformation2D: 2D geometric transformation implementation
    GeometricTransformation3D: 3D geometric transformation implementation
    GeometricTransformationManager: Singleton manager for geometric transformations

Usage:
    # 2D Linear transformation
    transform_2d = GeometricTransformation2D(1, "Linear")
    
    # 3D PDelta transformation with joint offsets
    transform_3d = GeometricTransformation3D(2, "PDelta", 0, 0, -1, dXi=0.1, dZj=0.5)
"""

import math
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any




class GeometricTransformation(ABC):
    """
    Abstract base class for geometric transformations in OpenSees.

    This class manages tagging, instance tracking, and provides a common interface for 2D and 3D geometric transformations.

    Attributes:
        _instances (list): Class-level list of all transformation instances.
        _start_tag (int): Starting tag for auto-tagging transformations.
        eps (float): Tolerance for floating-point comparisons.

    Args:
        transf_type (str): The type of transformation (e.g., 'Linear', 'PDelta', 'Corotational').
        dimension (int): The spatial dimension (2 or 3).

    Methods:
        set_start_tag: Set the starting tag for all transformations.
        get_all_instances: Return a copy of all transformation instances.
        clear_all_instances: Remove all transformation instances.
        remove: Remove this instance and retag remaining instances.
        has_joint_offsets: Abstract method to check for joint offsets.
        to_tcl: Abstract method to generate TCL command.
    """
    _instances = []
    _start_tag = 1

    @classmethod
    def set_start_tag(cls, start_tag):
        if not isinstance(start_tag, int) or start_tag < 0:
            raise ValueError("start_tag must be a non-negative integer")
        cls._start_tag = start_tag
        cls._retag_all_instances()

    def __init__(self, transf_type, dimension, description=""):
        self._transformation_type = transf_type
        self._dimension = dimension
        self._transf_tag = self._assign_tag()
        self.__class__._instances.append(self)
        self.eps = 1e-12 
        self.description = description

    @classmethod
    def _assign_tag(cls):
        return cls._start_tag + len(cls._instances)

    @classmethod
    def get_all_instances(cls):
        return cls._instances.copy()

    @classmethod
    def clear_all_instances(cls):
        cls._instances.clear()

    @classmethod
    def reset(cls):
        cls._instances.clear()
        cls._start_tag = 1

    @property
    def transf_tag(self):
        return self._transf_tag


    @property
    def tag(self):
        return self._transf_tag

    @property
    def transformation_type(self):
        return self._transformation_type

    @property
    def dimension(self):
        return self._dimension

    def remove(self):
        try:
            self.__class__._instances.remove(self)
        except ValueError:
            raise ValueError("Transformation not found in instances")
        self.__class__._retag_all_instances()

    @classmethod
    def _retag_all_instances(cls):
        for i, instance in enumerate(cls._instances, start=cls._start_tag):
            instance._transf_tag = i 

    @abstractmethod
    def has_joint_offsets(self):
        pass

    @abstractmethod
    def to_tcl(self):
        pass


    def __repr__(self):
        return f"{self.__class__.__name__}(tag={self.transf_tag}, type={self.transformation_type})"

    def __str__(self):
        return f"{self.transformation_type} {self.dimension}D Transformation (Tag: {self.transf_tag})"

class GeometricTransformation2D(GeometricTransformation):

    """
    2D geometric transformation for OpenSees elements.

    Supports Linear, PDelta, and Corotational types, with optional joint offsets.

    Args:
        transf_type (str): The type of transformation (e.g., 'Linear', 'PDelta', 'Corotational').
        d_xi, d_yi, d_xj, d_yj (float, optional): Joint offsets at i and j nodes (default 0.0).

    Methods:
        has_joint_offsets: Returns True if any joint offset is nonzero.
        to_tcl: Returns the TCL command string for this transformation.
    """
    def __init__(self, transf_type, d_xi=0.0, d_yi=0.0, d_xj=0.0, d_yj=0.0, description=""):
        super().__init__(transf_type, 2, description=description)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)

    def has_joint_offsets(self):
        """Check if any joint offset is nonzero."""
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_xj, self.d_yj])

    def to_tcl(self):
        """Generate the TCL command for this 2D transformation."""
        cmd = f"geomTransf {self.transformation_type} {self.transf_tag}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_xj} {self.d_yj}"
        return cmd
        if self.description != "":
            cmd += f"; # {self.description}"



class GeometricTransformation3D(GeometricTransformation):

    """
    3D geometric transformation for OpenSees elements.

    Supports Linear, PDelta, and Corotational types, with orientation vector and optional joint offsets.

    Args:
        transf_type (str): The type of transformation (e.g., 'Linear', 'PDelta', 'Corotational').
        vecxz_x, vecxz_y, vecxz_z (float): Components of the local xz-plane vector for orientation.
        d_xi, d_yi, d_zi, d_xj, d_yj, d_zj (float, optional): Joint offsets at i and j nodes (default 0.0).

    Methods:
        has_joint_offsets: Returns True if any joint offset is nonzero.
        to_tcl: Returns the TCL command string for this transformation.
    """
    def __init__(self, transf_type, vecxz_x:'float|str', vecxz_y:'float|str', vecxz_z:'float|str', d_xi='0.0', d_yi='0.0', d_zi='0.0', d_xj='0.0', d_yj='0.0', d_zj='0.0', description=""):
        super().__init__(transf_type, 3, description=description)
        self.vecxz_x = float(vecxz_x)
        self.vecxz_y = float(vecxz_y)
        self.vecxz_z = float(vecxz_z)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_zi = float(d_zi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)
        self.d_zj = float(d_zj)
        self._validate_vecxz()

    def _validate_vecxz(self):
        """Validate that the orientation vector is not zero."""
        mag = math.sqrt(self.vecxz_x**2 + self.vecxz_y**2 + self.vecxz_z**2)
        if mag < self.eps:
            raise ValueError("vecxz vector cannot be zero")

    def has_joint_offsets(self):
        """Check if any joint offset is nonzero."""
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_zi, self.d_xj, self.d_yj, self.d_zj])

    def to_tcl(self):
        """Generate the TCL command for this 3D transformation."""
        cmd = f"geomTransf {self.transformation_type} {self.transf_tag} {self.vecxz_x} {self.vecxz_y} {self.vecxz_z}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_zi} {self.d_xj} {self.d_yj} {self.d_zj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd




class GeometricTransformationManager:
    """
    Singleton manager for geometric transformations.
    Provides methods to add, remove, retrieve, and filter transformations.
    """
    _instance = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.transformation2d = GeometricTransformation2D
        self.transformation3d = GeometricTransformation3D   

    @classmethod
    def set_start_tag(cls, start_tag):
        GeometricTransformation.set_start_tag(start_tag)

    @classmethod
    def get_all_transformations(cls):
        """
        Returns a list of all geometric transformations.
        """
        return GeometricTransformation.get_all_instances()
    
    @classmethod
    def clear_all_transformations(cls):
        """
        Clears all geometric transformations.
        """
        GeometricTransformation.clear_all_instances()
    
    @classmethod
    def remove_transformation(cls, transf_tag):
        """
        Removes a geometric transformation by its tag.
        """
        instances = GeometricTransformation.get_all_instances()
        for instance in instances:
            if instance.transf_tag == transf_tag:
                instance.remove()
                return
        raise ValueError(f"Transformation with tag {transf_tag} not found.")

    @classmethod
    def get_transformation_by_tag(cls, transf_tag):
        """
        Retrieves a geometric transformation by its tag.
        """
        instances = GeometricTransformation.get_all_instances()
        for instance in instances:
            if instance.transf_tag == transf_tag:
                return instance
        raise ValueError(f"Transformation with tag {transf_tag} not found.")
    
    @classmethod
    def get_transformation(cls, identifier:Union[str, int]) -> GeometricTransformation:
        """
        Retrieves a geometric transformation by its tag or type.
        Tag or name of the transformation can be provided.
        """
        if isinstance(identifier, int):
            return cls.get_transformation_by_tag(identifier)
        elif isinstance(identifier, str):
            raise NotImplementedError("Retrieving by name is not implemented yet.")
        else:
            raise TypeError("Identifier must be an integer (tag) or string (name).")
        
    
    @classmethod
    def filter_transformations(cls, transf_type=None, dimension=None):
        """
        Filters transformations by type and/or dimension.
        :param transf_type: Type of transformation (e.g., 'Linear', 'PDelta', 'Corotational').
        :param dimension: Dimension of transformation (2 or 3).
        :return: List of filtered transformations.
        """
        instances = GeometricTransformation.get_all_instances()
        filtered = []
        for instance in instances:
            if (transf_type is None or instance.transformation_type == transf_type) and \
               (dimension is None or instance.dimension == dimension):
                filtered.append(instance)
        return filtered
    
# Example usage of the GeometricTransformation classes

if __name__ == "__main__":
    # Example usage
    print("=== Geometric Transformation Examples with Class-Managed Auto-Tagging ===")
    
    # 2D Examples
    print("\n2D Transformations:")
    linear_2d = GeometricTransformation2D("Linear")
    print(f"Linear 2D (Tag {linear_2d.transf_tag}): {linear_2d.to_tcl()}")
    
    pdelta_2d_offset = GeometricTransformation2D("PDelta", d_xi=0.1, d_yi=0.2)
    print(f"PDelta 2D with offsets (Tag {pdelta_2d_offset.transf_tag}): {pdelta_2d_offset.to_tcl()}")
    
    corot_2d = GeometricTransformation2D("Corotational")
    print(f"Corotational 2D (Tag {corot_2d.transf_tag}): {corot_2d.to_tcl()}")
    
    # 3D Examples
    print("\n3D Transformations:")
    linear_3d = GeometricTransformation3D("Linear", 0, 0, -1)
    print(f"Linear 3D (Tag {linear_3d.transf_tag}): {linear_3d.to_tcl()}")
    
    pdelta_3d_offset = GeometricTransformation3D("PDelta", 0, 1, 0, d_xi=0.1, d_zj=0.5)
    print(f"PDelta 3D with offsets (Tag {pdelta_3d_offset.transf_tag}): {pdelta_3d_offset.to_tcl()}")
    
    corot_3d = GeometricTransformation3D("Corotational", 1, 0, 0)
    print(f"Corotational 3D (Tag {corot_3d.transf_tag}): {corot_3d.to_tcl()}")
    
    # Class-level instance management
    print("\n=== Class-Level Instance Management ===")
    all_instances = GeometricTransformation.get_all_instances()
    print(f"Total transformations created: {len(all_instances)}")
    for transform in all_instances:
        print(f"  Tag {transform.transf_tag}: {transform.transformation_type} {transform.dimension}D")
    
    # Demonstration of retagging when removing
    print("\n=== Class-Managed Retagging Demonstration ===")
    print("Before removal:")
    for transform in GeometricTransformation.get_all_instances():
        print(f"  Tag {transform.transf_tag}: {transform.transformation_type} {transform.dimension}D")
    
    # Remove the second transformation (PDelta 2D)
    print(f"\nRemoving transformation with tag {pdelta_2d_offset.transf_tag}...")
    pdelta_2d_offset.remove()
    
    print("After removal and retagging (managed by GeometricTransformation class):")
    for transform in GeometricTransformation.get_all_instances():
        print(f"  Tag {transform.transf_tag}: {transform.transformation_type} {transform.dimension}D")
    
    print(f"Total transformation count: {len(GeometricTransformation.get_all_instances())}")
    print(f"Next tag will be: {GeometricTransformation._start_tag + len(GeometricTransformation._instances) + 1}")