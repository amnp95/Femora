from __future__ import annotations

from typing import Optional, Sequence, Union, Any

import pyvista as pv

from .spatial_transform_manager import SpatialTransformManager


class MeshPartTransform:
    """Provides a proxy for applying spatial transformations to a MeshPart instance.

    This class encapsulates a `SpatialTransformManager` and binds its
    transformation methods directly to a `MeshPart` object, allowing
    convenient chained or individual transformations. All transformations
    can be applied in-place or return a new transformed `MeshPart` or `pv.PolyData`.

    Attributes:
        _meshpart (Any): The MeshPart instance to which transformations are applied.
            Typed as Any to avoid circular typing imports.
        _ops (SpatialTransformManager): The underlying manager responsible for
            executing the spatial transformations.

    Example:
        >>> import pyvista as pv
        >>> # Assume MeshPart and SpatialTransformManager are imported or defined
        >>> # For demonstration, we use a mock MeshPart
        >>> class MockMeshPart:
        ...     def __init__(self, mesh_data):
        ...         self.mesh = mesh_data
        ...         self.transform = MeshPartTransform(self)
        ...     def __repr__(self):
        ...         return f"MockMeshPart(center={self.mesh.center.tolist()})"
        >>>
        >>> part = MockMeshPart(pv.Sphere())
        >>> print(part.mesh.center)
        [0.0, 0.0, 0.0]
        >>>
        >>> # Use the transform proxy to translate the MeshPart in-place
        >>> part.transform.translate([10.0, 20.0, 30.0], inplace=True)
        >>> print(part.mesh.center)
        [10.0, 20.0, 30.0]
        >>>
        >>> # Rotate and return a new mesh without modifying the original part
        >>> new_mesh = part.transform.rotate_z(90.0, inplace=False)
        >>> # The new_mesh is a pyvista.PolyData object
        >>> import numpy as np
        >>> print(np.round(new_mesh.center, 5).tolist())
        [-20.0, 10.0, 30.0]
    """

    def __init__(self, meshpart: Any) -> None:
        """Initializes the MeshPartTransform proxy.

        Args:
            meshpart: The `MeshPart` instance to which this transform proxy is bound.
                It is typed as `Any` to resolve potential circular import issues
                and avoid direct dependency.
        """
        self._meshpart = meshpart
        self._ops = SpatialTransformManager()

    def translate(self, vector: Sequence[float], *, multiply_mode: str = "pre", inplace: bool = True):
        """Translates the MeshPart by a given vector.

        Args:
            vector: A sequence of three floats [x, y, z] representing the
                translation vector.
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, center={self.mesh.center.tolist()})"
            ...
            >>> part = MockMeshPart(pv.Sphere())
            >>> print(part)
            MockMeshPart(tag=1, center=[0.0, 0.0, 0.0])
            >>>
            >>> # Translate in-place
            >>> part.transform.translate([10.0, 0.0, 0.0], inplace=True)
            >>> print(part)
            MockMeshPart(tag=1, center=[10.0, 0.0, 0.0])
            >>>
            >>> # Translate and return a new object
            >>> new_part_mesh = part.transform.translate([0.0, 5.0, 0.0], inplace=False)
            >>> print(part) # Original part is unchanged
            MockMeshPart(tag=1, center=[10.0, 0.0, 0.0])
            >>> print(new_part_mesh.center.tolist()) # New mesh is translated
            [10.0, 5.0, 0.0]
        """
        return self._ops.translate(self._meshpart, vector, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate(self, rotation: Union[Sequence[Sequence[float]], Sequence[float]], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Rotates the MeshPart using a rotation matrix or axis-angle representation.

        Args:
            rotation: The rotation to apply. Can be a 3x3 rotation matrix (sequence of
                sequences) or an axis-angle representation (sequence of four floats:
                [ax, ay, az, angle_degrees]).
            point: The optional point around which to rotate. If None, rotation occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, center={self.mesh.center.tolist()})"
            ...
            >>> part = MockMeshPart(pv.Box(x_length=1, y_length=2, z_length=3))
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -1.0, 1.0, -1.5, 1.5]
            >>>
            >>> # Rotate 90 degrees around the Z-axis (axis-angle)
            >>> rotated_part_mesh = part.transform.rotate([0, 0, 1, 90.0], inplace=False)
            >>> # Bounds will change due to rotation; new bounds will swap X and Y extents
            >>> import numpy as np
            >>> print(np.round(rotated_part_mesh.bounds, 5).tolist())
            [-1.0, 1.0, -0.5, 0.5, -1.5, 1.5]
        """
        return self._ops.rotate(self._meshpart, rotation, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_vector(self, vector: Sequence[float], angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Rotates the MeshPart by a given angle around a specified vector.

        Args:
            vector: A sequence of three floats [x, y, z] representing the
                axis of rotation. This vector will be normalized internally.
            angle: The rotation angle in degrees.
            point: The optional point around which to rotate. If None, rotation occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, center={self.mesh.center.tolist()})"
            ...
            >>> part = MockMeshPart(pv.Sphere())
            >>> initial_center = part.mesh.center.tolist()
            >>> print(initial_center)
            [0.0, 0.0, 0.0]
            >>>
            >>> # Rotate 45 degrees around the Z-axis (equivalent to rotate_z)
            >>> rotated_part_mesh = part.transform.rotate_vector([0, 0, 1], 45.0, inplace=False)
            >>> # For rotation around origin, a sphere's center remains unchanged
            >>> print(rotated_part_mesh.center.tolist())
            [0.0, 0.0, 0.0]
            >>>
            >>> # Rotate around a point other than origin
            >>> part_shifted = MockMeshPart(pv.Sphere().translate([1,0,0]))
            >>> print(part_shifted.mesh.center.tolist())
            [1.0, 0.0, 0.0]
            >>> rotated_shifted_part_mesh = part_shifted.transform.rotate_vector(
            ...     [0, 0, 1], 90.0, point=[0, 0, 0], inplace=False
            ... )
            >>> # Center of [1,0,0] rotated 90 degrees about Z-axis at [0,0,0] becomes [0,1,0]
            >>> print(np.round(rotated_shifted_part_mesh.center, 5).tolist())
            [0.0, 1.0, 0.0]
        """
        return self._ops.rotate_vector(self._meshpart, vector, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_x(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Rotates the MeshPart by a given angle around the X-axis.

        Args:
            angle: The rotation angle in degrees.
            point: The optional point around which to rotate. If None, rotation occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> part = MockMeshPart(pv.Box(x_length=1, y_length=2, z_length=3))
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -1.0, 1.0, -1.5, 1.5]
            >>>
            >>> # Rotate 90 degrees around the X-axis
            >>> rotated_part_mesh = part.transform.rotate_x(90.0, inplace=False)
            >>> # Expected bounds change (Y and Z extents swap)
            >>> print(np.round(rotated_part_mesh.bounds, 5).tolist())
            [-0.5, 0.5, -1.5, 1.5, -1.0, 1.0]
        """
        return self._ops.rotate_x(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_y(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Rotates the MeshPart by a given angle around the Y-axis.

        Args:
            angle: The rotation angle in degrees.
            point: The optional point around which to rotate. If None, rotation occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> part = MockMeshPart(pv.Box(x_length=1, y_length=2, z_length=3))
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -1.0, 1.0, -1.5, 1.5]
            >>>
            >>> # Rotate 90 degrees around the Y-axis
            >>> rotated_part_mesh = part.transform.rotate_y(90.0, inplace=False)
            >>> # Expected bounds change (X and Z extents swap)
            >>> print(np.round(rotated_part_mesh.bounds, 5).tolist())
            [-1.5, 1.5, -1.0, 1.0, -0.5, 0.5]
        """
        return self._ops.rotate_y(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def rotate_z(self, angle: float, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Rotates the MeshPart by a given angle around the Z-axis.

        Args:
            angle: The rotation angle in degrees.
            point: The optional point around which to rotate. If None, rotation occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> part = MockMeshPart(pv.Box(x_length=1, y_length=2, z_length=3))
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -1.0, 1.0, -1.5, 1.5]
            >>>
            >>> # Rotate 90 degrees around the Z-axis
            >>> rotated_part_mesh = part.transform.rotate_z(90.0, inplace=False)
            >>> # Expected bounds change (X and Y extents swap)
            >>> print(np.round(rotated_part_mesh.bounds, 5).tolist())
            [-1.0, 1.0, -0.5, 0.5, -1.5, 1.5]
        """
        return self._ops.rotate_z(self._meshpart, angle, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def scale(self, factor: Union[float, Sequence[float]], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Scales the MeshPart by a given factor.

        Args:
            factor: The scaling factor. Can be a single float (uniform scaling)
                or a sequence of three floats [sx, sy, sz] for non-uniform scaling.
            point: The optional point around which to scale. If None, scaling occurs
                around the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> part = MockMeshPart(pv.Box(x_length=1, y_length=1, z_length=1))
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -0.5, 0.5, -0.5, 0.5]
            >>>
            >>> # Uniform scale by 2.0
            >>> scaled_part_mesh = part.transform.scale(2.0, inplace=False)
            >>> print(np.round(scaled_part_mesh.bounds, 5).tolist())
            [-1.0, 1.0, -1.0, 1.0, -1.0, 1.0]
            >>>
            >>> # Non-uniform scale
            >>> non_uniform_scaled_mesh = part.transform.scale([1.0, 2.0, 3.0], inplace=False)
            >>> print(np.round(non_uniform_scaled_mesh.bounds, 5).tolist())
            [-0.5, 0.5, -1.0, 1.0, -1.5, 1.5]
        """
        return self._ops.scale(self._meshpart, factor, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_x(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Flips (mirrors) the MeshPart along the X-axis.

        Args:
            point: The optional point acting as the plane origin for reflection.
                If None, the reflection plane passes through the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> # Create a non-symmetrical mesh
            >>> mesh = pv.Box(x_length=1, y_length=2, z_length=3).translate([0.5, 0, 0])
            >>> part = MockMeshPart(mesh)
            >>> print(part.mesh.bounds)
            [0.0, 1.0, -1.0, 1.0, -1.5, 1.5]
            >>>
            >>> # Flip along X-axis (reflection across YZ plane at X=0)
            >>> flipped_part_mesh = part.transform.flip_x(inplace=False)
            >>> # The bounds should become [-1.0, 0.0, ...]
            >>> print(np.round(flipped_part_mesh.bounds, 5).tolist())
            [-1.0, 0.0, -1.0, 1.0, -1.5, 1.5]
        """
        return self._ops.flip_x(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_y(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Flips (mirrors) the MeshPart along the Y-axis.

        Args:
            point: The optional point acting as the plane origin for reflection.
                If None, the reflection plane passes through the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> # Create a non-symmetrical mesh
            >>> mesh = pv.Box(x_length=1, y_length=2, z_length=3).translate([0, 1.0, 0])
            >>> part = MockMeshPart(mesh)
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, 0.0, 2.0, -1.5, 1.5]
            >>>
            >>> # Flip along Y-axis (reflection across XZ plane at Y=0)
            >>> flipped_part_mesh = part.transform.flip_y(inplace=False)
            >>> # The bounds should become [..., -2.0, 0.0, ...]
            >>> print(np.round(flipped_part_mesh.bounds, 5).tolist())
            [-0.5, 0.5, -2.0, 0.0, -1.5, 1.5]
        """
        return self._ops.flip_y(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def flip_z(self, *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Flips (mirrors) the MeshPart along the Z-axis.

        Args:
            point: The optional point acting as the plane origin for reflection.
                If None, the reflection plane passes through the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, bounds={np.round(self.mesh.bounds, 5).tolist()})"
            ...
            >>> # Create a non-symmetrical mesh
            >>> mesh = pv.Box(x_length=1, y_length=2, z_length=3).translate([0, 0, 1.5])
            >>> part = MockMeshPart(mesh)
            >>> print(part.mesh.bounds)
            [-0.5, 0.5, -1.0, 1.0, 0.0, 3.0]
            >>>
            >>> # Flip along Z-axis (reflection across XY plane at Z=0)
            >>> flipped_part_mesh = part.transform.flip_z(inplace=False)
            >>> # The bounds should become [..., -3.0, 0.0]
            >>> print(np.round(flipped_part_mesh.bounds, 5).tolist())
            [-0.5, 0.5, -1.0, 1.0, -3.0, 0.0]
        """
        return self._ops.flip_z(self._meshpart, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def reflect(self, normal: Sequence[float], *, point: Optional[Sequence[float]] = None, multiply_mode: str = "pre", inplace: bool = True):
        """Reflects the MeshPart across a plane defined by a normal vector and a point.

        Args:
            normal: A sequence of three floats [nx, ny, nz] representing the
                normal vector of the reflection plane. This vector will be
                normalized internally.
            point: The optional point through which the reflection plane passes.
                If None, the reflection plane passes through the origin [0, 0, 0].
            multiply_mode: The order in which the new transform is applied.
                Can be "pre" (new transform * existing) or "post" (existing *
                new transform). Defaults to "pre".
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, center={np.round(self.mesh.center, 5).tolist()})"
            ...
            >>> # Create a mesh not centered at origin for better demonstration
            >>> mesh = pv.Sphere().translate([1.0, 1.0, 1.0])
            >>> part = MockMeshPart(mesh)
            >>> print(part.mesh.center)
            [1.0, 1.0, 1.0]
            >>>
            >>> # Reflect across the YZ plane (normal [1,0,0]) passing through origin
            >>> reflected_part_mesh = part.transform.reflect([1, 0, 0], inplace=False)
            >>> print(np.round(reflected_part_mesh.center, 5).tolist())
            [-1.0, 1.0, 1.0]
            >>>
            >>> # Reflect across a plane defined by normal [0,0,1] and point [0,0,1]
            >>> # The plane is z=1. Reflecting [1,1,1] across z=1 should yield [1,1,1].
            >>> reflected_shifted_mesh = part.transform.reflect([0, 0, 1], point=[0, 0, 1], inplace=False)
            >>> print(np.round(reflected_shifted_mesh.center, 5).tolist())
            [1.0, 1.0, 1.0]
        """
        return self._ops.reflect(self._meshpart, normal, point=point, multiply_mode=multiply_mode, cascade=False, inplace=inplace)

    def apply_transform(self, transform: pv.transform.Transform, *, inplace: bool = True):
        """Applies a pre-defined `pyvista.Transform` object to the MeshPart.

        Args:
            transform: A `pyvista.Transform` object specifying the transformation matrix.
            inplace: If True, the transformation is applied directly to the
                `_meshpart`'s mesh. If False, a new `pv.PolyData` object
                with the transformed mesh is returned.

        Returns:
            The `MeshPart` instance (if `inplace=True`) or a new `pv.PolyData`
            object (if `inplace=False`) representing the transformed mesh.

        Example:
            >>> import pyvista as pv
            >>> import numpy as np
            >>> class MockMeshPart: # Mock for demonstration
            ...     def __init__(self, mesh_data):
            ...         self.mesh = mesh_data
            ...         self.transform = MeshPartTransform(self)
            ...         self.tag = 1
            ...     def __repr__(self):
            ...         return f"MockMeshPart(tag={self.tag}, center={np.round(self.mesh.center, 5).tolist()})"
            ...
            >>> part = MockMeshPart(pv.Sphere())
            >>> print(part.mesh.center)
            [0.0, 0.0, 0.0]
            >>>
            >>> # Create a PyVista transform object
            >>> pv_transform = pv.Transform()
            >>> pv_transform.translate([5.0, 0.0, 0.0])
            >>> pv_transform.rotate_z(90.0)
            >>>
            >>> # Apply the transform to the MeshPart
            >>> transformed_part_mesh = part.transform.apply_transform(pv_transform, inplace=False)
            >>> # Initial center (0,0,0) -> translated (5,0,0) -> rotated 90 deg about Z origin
            >>> # Point (5,0,0) rotated 90 deg about Z (origin) becomes (0,5,0)
            >>> print(np.round(transformed_part_mesh.center, 5).tolist())
            [0.0, 5.0, 0.0]
        """
        return self._ops.apply_transform(self._meshpart, transform, cascade=False, inplace=inplace)


__all__ = ["MeshPartTransform"]