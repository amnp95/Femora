"""Geometric Transformation Classes for OpenSees.

This module provides a robust set of classes for defining 2D and 3D geometric
transformations within OpenSees finite element analysis. It supports common
transformation types such as 'Linear', 'PDelta', and 'Corotational', along
with optional joint offsets and orientation vectors.

The classes are designed to manage instances and assign unique tags automatically,
simplifying the process of defining and referencing transformations in OpenSees
input scripts.

Example:
    >>> from femora.opensees.geom_transformations import GeometricTransformation2D, GeometricTransformation3D
    >>> # Create a 2D Linear transformation
    >>> transf2d = GeometricTransformation2D("Linear")
    >>> print(transf2d.to_tcl())
    geomTransf Linear 1
    >>> # Create a 3D PDelta transformation with local xz-plane orientation and joint offsets
    >>> transf3d = GeometricTransformation3D("PDelta", vecxz_x=0, vecxz_y=1, vecxz_z=0, d_xi=0.1, d_zj=0.5)
    >>> print(transf3d.to_tcl())
    geomTransf PDelta 2 0.0 1.0 0.0 -jntOffset 0.1 0.0 0.0 0.0 0.0 0.5
    >>> # Clear all created transformations (important for testing/re-running examples)
    >>> GeometricTransformation2D.clear_all_instances()
"""

import math
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any




class GeometricTransformation(ABC):
    """Abstract base class for geometric transformations in OpenSees.

    This class provides a common interface and manages tagging and instance
    tracking for 2D and 3D geometric transformations within OpenSees models.

    Attributes:
        eps (float): Tolerance for floating-point comparisons (default 1e-12).
        description (str): An optional description for the transformation.
        transf_tag (int): The unique integer tag assigned to this transformation.
        transformation_type (str): The type of transformation (e.g., 'Linear', 'PDelta').
        dimension (int): The spatial dimension of the transformation (2 or 3).

    Example:
        >>> # This is an abstract class, so direct instantiation is not possible.
        >>> # See GeometricTransformation2D or GeometricTransformation3D for examples.
    """
    _instances: List['GeometricTransformation'] = []
    _start_tag: int = 1

    @classmethod
    def set_start_tag(cls, start_tag: int):
        """Sets the starting tag for all geometric transformations.

        All existing and future transformations will be re-tagged starting
        from the provided `start_tag`.

        Args:
            start_tag: The non-negative integer from which to start tagging
                transformations.

        Raises:
            ValueError: If `start_tag` is not a non-negative integer.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformation, GeometricTransformation2D
            >>> transf_a = GeometricTransformation2D("Linear")
            >>> print(f"Tag before reset: {transf_a.transf_tag}")
            Tag before reset: 1
            >>> GeometricTransformation.set_start_tag(100)
            >>> print(f"Tag after reset: {transf_a.transf_tag}")
            Tag after reset: 100
            >>> transf_b = GeometricTransformation2D("PDelta")
            >>> print(f"New transformation tag: {transf_b.transf_tag}")
            New transformation tag: 101
            >>> GeometricTransformation.clear_all_instances()
        """
        if not isinstance(start_tag, int) or start_tag < 0:
            raise ValueError("start_tag must be a non-negative integer")
        cls._start_tag = start_tag
        cls._retag_all_instances()

    def __init__(self, transf_type: str, dimension: int, description: str = ""):
        """Initializes a GeometricTransformation object.

        Args:
            transf_type: The type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            dimension: The spatial dimension of the transformation (2 or 3).
            description: Optional. A descriptive string for this transformation.
        """
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
    def get_all_instances(cls) -> List['GeometricTransformation']:
        """Returns a copy of all active geometric transformation instances.

        Returns:
            A list containing all `GeometricTransformation` objects that have
            been created and not yet removed.
        """
        return cls._instances.copy()

    @classmethod
    def clear_all_instances(cls):
        """Clears all active geometric transformation instances.

        This effectively removes all created transformations from memory and
        resets the internal instance tracking.
        """
        cls._instances.clear()

    @classmethod
    def reset(cls):
        """Resets the state of the GeometricTransformation class.

        Clears all instances and resets the starting tag to its default value (1).
        """
        cls._instances.clear()
        cls._start_tag = 1

    @property
    def transf_tag(self) -> int:
        """The unique integer tag assigned to this transformation."""
        return self._transf_tag


    @property
    def tag(self) -> int:
        """The unique integer tag assigned to this transformation (alias for `transf_tag`)."""
        return self._transf_tag

    @property
    def transformation_type(self) -> str:
        """The type of geometric transformation (e.g., 'Linear', 'PDelta')."""
        return self._transformation_type

    @property
    def dimension(self) -> int:
        """The spatial dimension of the transformation (2 for 2D, 3 for 3D)."""
        return self._dimension

    def remove(self):
        """Removes this transformation instance from the global list and retags others.

        The transformation is removed from the list of active instances, and
        all remaining instances are re-tagged sequentially starting from
        the current `_start_tag`.

        Raises:
            ValueError: If the transformation instance is not found in the
                list of active instances (e.g., already removed).

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformation, GeometricTransformation2D
            >>> transf1 = GeometricTransformation2D("Linear")
            >>> transf2 = GeometricTransformation2D("PDelta")
            >>> transf3 = GeometricTransformation2D("Corotational")
            >>> transf_list = GeometricTransformation.get_all_instances()
            >>> [t.transf_tag for t in transf_list]
            [1, 2, 3]
            >>> transf2.remove()
            >>> [t.transf_tag for t in GeometricTransformation.get_all_instances()]
            [1, 2]
            >>> # Note: The tag for transf3 (now index 1) became 2 after removal.
            >>> transf3.transf_tag
            2
            >>> GeometricTransformation.clear_all_instances()
        """
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
    def has_joint_offsets(self) -> bool:
        """Abstract method to check if the transformation has any defined joint offsets.

        Returns:
            True if any joint offset is non-zero, False otherwise.
        """
        pass

    @abstractmethod
    def to_tcl(self) -> str:
        """Abstract method to generate the OpenSees TCL command string for this transformation.

        Returns:
            A string representing the OpenSees TCL command for the geometric transformation.
        """
        pass


    def __repr__(self):
        return f"{self.__class__.__name__}(tag={self.transf_tag}, type={self.transformation_type})"

    def __str__(self):
        return f"{self.transformation_type} {self.dimension}D Transformation (Tag: {self.transf_tag})"

class GeometricTransformation2D(GeometricTransformation):
    """Represents a 2D geometric transformation for OpenSees elements.

    This class supports 'Linear', 'PDelta', and 'Corotational' transformation
    types, and allows for optional joint offsets at the start (i) and end (j)
    nodes of an element.

    Attributes:
        d_xi (float): Joint offset in the local x-direction at node i.
        d_yi (float): Joint offset in the local y-direction at node i.
        d_xj (float): Joint offset in the local x-direction at node j.
        d_yj (float): Joint offset in the local y-direction at node j.

    Example:
        >>> from femora.opensees.geom_transformations import GeometricTransformation2D
        >>> # Linear 2D transformation without offsets
        >>> linear_2d = GeometricTransformation2D("Linear")
        >>> print(linear_2d.to_tcl())
        geomTransf Linear 1
        >>> # PDelta 2D transformation with offsets
        >>> pdelta_2d_offset = GeometricTransformation2D("PDelta", d_xi=0.1, d_yi=0.2)
        >>> print(pdelta_2d_offset.to_tcl())
        geomTransf PDelta 2 -jntOffset 0.1 0.2 0.0 0.0
        >>> GeometricTransformation2D.clear_all_instances()
    """
    def __init__(self, transf_type: str, d_xi: float = 0.0, d_yi: float = 0.0,
                 d_xj: float = 0.0, d_yj: float = 0.0, description: str = ""):
        """Initializes a GeometricTransformation2D object.

        Args:
            transf_type: The type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            d_xi: Optional. Joint offset in the local x-direction at node i.
            d_yi: Optional. Joint offset in the local y-direction at node i.
            d_xj: Optional. Joint offset in the local x-direction at node j.
            d_yj: Optional. Joint offset in the local y-direction at node j.
            description: Optional. A descriptive string for this transformation.
        """
        super().__init__(transf_type, 2, description=description)
        self.d_xi = float(d_xi)
        self.d_yi = float(d_yi)
        self.d_xj = float(d_xj)
        self.d_yj = float(d_yj)

    def has_joint_offsets(self) -> bool:
        """Checks if any joint offset defined for this 2D transformation is non-zero.

        Returns:
            True if any of `d_xi`, `d_yi`, `d_xj`, or `d_yj` is numerically
            different from zero (within `self.eps` tolerance), False otherwise.
        """
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_xj, self.d_yj])

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command string for this 2D transformation.

        Returns:
            A string representing the OpenSees TCL command. For example:
            `geomTransf Linear 1` or `geomTransf PDelta 2 -jntOffset 0.1 0.2 0.0 0.0`.
        """
        cmd = f"geomTransf {self.transformation_type} {self.transf_tag}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_xj} {self.d_yj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd



class GeometricTransformation3D(GeometricTransformation):
    """Represents a 3D geometric transformation for OpenSees elements.

    This class supports 'Linear', 'PDelta', and 'Corotational' transformation
    types, incorporating an orientation vector for the local xz-plane and
    optional joint offsets at the start (i) and end (j) nodes.

    Attributes:
        vecxz_x (float): X-component of the vector defining the local xz-plane.
        vecxz_y (float): Y-component of the vector defining the local xz-plane.
        vecxz_z (float): Z-component of the vector defining the local xz-plane.
        d_xi (float): Joint offset in the local x-direction at node i.
        d_yi (float): Joint offset in the local y-direction at node i.
        d_zi (float): Joint offset in the local z-direction at node i.
        d_xj (float): Joint offset in the local x-direction at node j.
        d_yj (float): Joint offset in the local y-direction at node j.
        d_zj (float): Joint offset in the local z-direction at node j.

    Example:
        >>> from femora.opensees.geom_transformations import GeometricTransformation3D
        >>> # Linear 3D transformation with local xz-plane defined by [0, 0, -1]
        >>> linear_3d = GeometricTransformation3D("Linear", 0, 0, -1)
        >>> print(linear_3d.to_tcl())
        geomTransf Linear 1 0.0 0.0 -1.0
        >>> # PDelta 3D transformation with offsets and local xz-plane [0, 1, 0]
        >>> pdelta_3d_offset = GeometricTransformation3D("PDelta", 0, 1, 0, d_xi=0.1, d_zj=0.5)
        >>> print(pdelta_3d_offset.to_tcl())
        geomTransf PDelta 2 0.0 1.0 0.0 -jntOffset 0.1 0.0 0.0 0.0 0.0 0.5
        >>> GeometricTransformation3D.clear_all_instances()
    """
    def __init__(self, transf_type: str, vecxz_x: float, vecxz_y: float, vecxz_z: float,
                 d_xi: float = 0.0, d_yi: float = 0.0, d_zi: float = 0.0,
                 d_xj: float = 0.0, d_yj: float = 0.0, d_zj: float = 0.0, description: str = ""):
        """Initializes a GeometricTransformation3D object.

        Args:
            transf_type: The type of geometric transformation (e.g., 'Linear',
                'PDelta', 'Corotational').
            vecxz_x: The X-component of the vector defining the local xz-plane.
                This vector, along with the element's local x-axis, defines the
                local y-axis. Cannot be a zero vector.
            vecxz_y: The Y-component of the vector defining the local xz-plane.
            vecxz_z: The Z-component of the vector defining the local xz-plane.
            d_xi: Optional. Joint offset in the local x-direction at node i.
            d_yi: Optional. Joint offset in the local y-direction at node i.
            d_zi: Optional. Joint offset in the local z-direction at node i.
            d_xj: Optional. Joint offset in the local x-direction at node j.
            d_yj: Optional. Joint offset in the local y-direction at node j.
            d_zj: Optional. Joint offset in the local z-direction at node j.
            description: Optional. A descriptive string for this transformation.

        Raises:
            ValueError: If the `vecxz` vector components result in a zero vector.
        """
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

    def has_joint_offsets(self) -> bool:
        """Checks if any joint offset defined for this 3D transformation is non-zero.

        Returns:
            True if any of `d_xi` through `d_zj` is numerically different
            from zero (within `self.eps` tolerance), False otherwise.
        """
        return any(abs(val) > self.eps for val in [self.d_xi, self.d_yi, self.d_zi, self.d_xj, self.d_yj, self.d_zj])

    def to_tcl(self) -> str:
        """Generates the OpenSees TCL command string for this 3D transformation.

        Returns:
            A string representing the OpenSees TCL command. For example:
            `geomTransf Linear 1 0.0 0.0 -1.0` or
            `geomTransf PDelta 2 0.0 1.0 0.0 -jntOffset 0.1 0.0 0.0 0.0 0.0 0.5`.
        """
        cmd = f"geomTransf {self.transformation_type} {self.transf_tag} {self.vecxz_x} {self.vecxz_y} {self.vecxz_z}"
        if self.has_joint_offsets():
            cmd += f" -jntOffset {self.d_xi} {self.d_yi} {self.d_zi} {self.d_xj} {self.d_yj} {self.d_zj}"
        if self.description != "":
            cmd += f"; # {self.description}"
        return cmd




class GeometricTransformationManager:
    """Singleton manager for geometric transformations.

    This class provides a centralized point of access and management for all
    2D and 3D geometric transformations within an OpenSees model. It ensures
    that only one instance of the manager exists throughout the application.

    Attributes:
        _instance (GeometricTransformationManager): The singleton instance of the manager.
        transformation2d (type): A reference to the GeometricTransformation2D class.
        transformation3d (type): A reference to the GeometricTransformation3D class.

    Example:
        >>> from femora.opensees.geom_transformations import GeometricTransformationManager
        >>> manager = GeometricTransformationManager()
        >>> # Add a 2D transformation
        >>> transf2d = manager.transformation2d("Linear")
        >>> print(f"Created 2D transformation with tag: {transf2d.transf_tag}")
        Created 2D transformation with tag: 1
        >>> # Add a 3D transformation
        >>> transf3d = manager.transformation3d("PDelta", 1, 0, 0)
        >>> print(f"Created 3D transformation with tag: {transf3d.transf_tag}")
        Created 3D transformation with tag: 2
        >>> # Retrieve a transformation
        >>> retrieved_transf = manager.get_transformation_by_tag(1)
        >>> print(f"Retrieved transformation: {retrieved_transf.transformation_type}")
        Retrieved transformation: Linear
        >>> # Clear all transformations
        >>> manager.clear_all_transformations()
    """
    _instance: 'GeometricTransformationManager' = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the GeometricTransformationManager.

        Sets up references to the 2D and 3D transformation classes for
        convenient creation. Note that for a singleton, this `__init__`
        method will be called on subsequent instantiations even if `__new__`
        returns an existing instance.
        """
        self.transformation2d = GeometricTransformation2D
        self.transformation3d = GeometricTransformation3D

    @classmethod
    def set_start_tag(cls, start_tag: int):
        """Sets the starting tag for all geometric transformations managed globally.

        This delegates to the `GeometricTransformation` base class method,
        affecting all transformations created or currently managed.

        Args:
            start_tag: The non-negative integer from which to start tagging
                transformations.

        Raises:
            ValueError: If `start_tag` is not a non-negative integer.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> transf1 = manager.transformation2d("Linear")
            >>> print(f"Initial tag: {transf1.transf_tag}")
            Initial tag: 1
            >>> manager.set_start_tag(100)
            >>> print(f"Tag after reset: {transf1.transf_tag}")
            Tag after reset: 100
            >>> transf2 = manager.transformation2d("PDelta")
            >>> print(f"New transformation tag: {transf2.transf_tag}")
            New transformation tag: 101
            >>> manager.clear_all_transformations()
        """
        GeometricTransformation.set_start_tag(start_tag)

    @classmethod
    def get_all_transformations(cls) -> List[GeometricTransformation]:
        """Returns a list of all active geometric transformation instances.

        Returns:
            A list containing all `GeometricTransformation` objects that have
            been created and not yet removed.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> _ = manager.transformation2d("Linear")
            >>> _ = manager.transformation3d("PDelta", 1, 0, 0)
            >>> all_transfs = manager.get_all_transformations()
            >>> print(f"Number of transformations: {len(all_transfs)}")
            Number of transformations: 2
            >>> manager.clear_all_transformations()
        """
        return GeometricTransformation.get_all_instances()

    @classmethod
    def clear_all_transformations(cls):
        """Clears all active geometric transformation instances.

        This removes all created transformations from memory and resets the
        internal instance tracking of the base `GeometricTransformation` class.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> _ = manager.transformation2d("Linear")
            >>> print(f"Count before clear: {len(manager.get_all_transformations())}")
            Count before clear: 1
            >>> manager.clear_all_transformations()
            >>> print(f"Count after clear: {len(manager.get_all_transformations())}")
            Count after clear: 0
        """
        GeometricTransformation.clear_all_instances()

    @classmethod
    def remove_transformation(cls, transf_tag: int):
        """Removes a geometric transformation by its unique tag.

        If found, the transformation is removed from the global list, and all
        remaining transformations are re-tagged.

        Args:
            transf_tag: The integer tag of the transformation to remove.

        Raises:
            ValueError: If no transformation with the given `transf_tag` is found.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> transf1 = manager.transformation2d("Linear")
            >>> transf2 = manager.transformation3d("PDelta", 1, 0, 0)
            >>> print(f"Tags before removal: {[t.transf_tag for t in manager.get_all_transformations()]}")
            Tags before removal: [1, 2]
            >>> manager.remove_transformation(1)
            >>> print(f"Tags after removal of tag 1: {[t.transf_tag for t in manager.get_all_transformations()]}")
            Tags after removal of tag 1: [1]
            >>> manager.clear_all_transformations()
        """
        instances = GeometricTransformation.get_all_instances()
        for instance in instances:
            if instance.transf_tag == transf_tag:
                instance.remove()
                return
        raise ValueError(f"Transformation with tag {transf_tag} not found.")

    @classmethod
    def get_transformation_by_tag(cls, transf_tag: int) -> GeometricTransformation:
        """Retrieves a geometric transformation by its unique tag.

        Args:
            transf_tag: The integer tag of the transformation to retrieve.

        Returns:
            The `GeometricTransformation` instance with the matching tag.

        Raises:
            ValueError: If no transformation with the given `transf_tag` is found.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> transf = manager.transformation2d("Linear")
            >>> retrieved = manager.get_transformation_by_tag(transf.transf_tag)
            >>> print(f"Retrieved type: {retrieved.transformation_type}")
            Retrieved type: Linear
            >>> manager.clear_all_transformations()
        """
        instances = GeometricTransformation.get_all_instances()
        for instance in instances:
            if instance.transf_tag == transf_tag:
                return instance
        raise ValueError(f"Transformation with tag {transf_tag} not found.")

    @classmethod
    def get_transformation(cls, identifier: Union[str, int]) -> GeometricTransformation:
        """Retrieves a geometric transformation by its tag or type.

        Currently, retrieval by name (type) is not implemented and will raise
        a `NotImplementedError`.

        Args:
            identifier: The unique integer tag of the transformation, or a string
                representing its type (e.g., 'Linear', 'PDelta').

        Returns:
            The `GeometricTransformation` instance with the matching identifier.

        Raises:
            NotImplementedError: If the `identifier` is a string (retrieval by
                name is not yet supported).
            ValueError: If an integer `identifier` is provided but no
                transformation with that tag is found.
            TypeError: If the `identifier` is neither an integer nor a string.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> transf = manager.transformation2d("Linear")
            >>> retrieved_by_tag = manager.get_transformation(transf.transf_tag)
            >>> print(f"Retrieved by tag: {retrieved_by_tag.transformation_type}")
            Retrieved by tag: Linear
            >>> try:
            ...     manager.get_transformation("Linear")
            ... except NotImplementedError as e:
            ...     print(e)
            Retrieving by name is not implemented yet.
            >>> manager.clear_all_transformations()
        """
        if isinstance(identifier, int):
            return cls.get_transformation_by_tag(identifier)
        elif isinstance(identifier, str):
            raise NotImplementedError("Retrieving by name is not implemented yet.")
        else:
            raise TypeError("Identifier must be an integer (tag) or string (name).")


    @classmethod
    def filter_transformations(cls, transf_type: str = None, dimension: int = None) -> List[GeometricTransformation]:
        """Filters transformations by type and/or dimension.

        Args:
            transf_type: Optional. The type of transformation to filter by
                (e.g., 'Linear', 'PDelta', 'Corotational').
            dimension: Optional. The spatial dimension of transformation to
                filter by (2 for 2D, 3 for 3D).

        Returns:
            A list of `GeometricTransformation` instances that match the
            specified criteria. If no criteria are provided, all instances
            are returned.

        Example:
            >>> from femora.opensees.geom_transformations import GeometricTransformationManager
            >>> manager = GeometricTransformationManager()
            >>> _ = manager.transformation2d("Linear")
            >>> _ = manager.transformation2d("PDelta")
            >>> _ = manager.transformation3d("Linear", 1, 0, 0)
            >>> linear_transfs = manager.filter_transformations(transf_type="Linear")
            >>> print(f"Linear transformations: {len(linear_transfs)}")
            Linear transformations: 2
            >>> dim2_transfs = manager.filter_transformations(dimension=2)
            >>> print(f"2D transformations: {len(dim2_transfs)}")
            2D transformations: 2
            >>> manager.clear_all_transformations()
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