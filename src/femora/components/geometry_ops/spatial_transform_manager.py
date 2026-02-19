"""
SpatialTransformManager
-----------------------

Singleton service for applying spatial geometry operations such as
translation, rotation, scaling, flipping, and reflection to FEMORA
objects that carry PyVista meshes.

This is purposefully separate from the OpenSees element transformation
classes that live under `components/transformation/`.

Targets supported:
- MeshPart: femora.components.Mesh.meshPartBase.MeshPart
- AssemblySection: femora.components.Assemble.Assembler.AssemblySection
- PyVista datasets: pv.DataSet and subclasses
- Collections of the above

Delegation for specialized behavior:
- If a target defines one of the following methods, delegation occurs
  prior to applying the generic operation:
  - _apply_transform(transform, *, cascade, inplace)
  - _translate(vector, *, inplace)
  - _rotate_x(angle, *, point=None, multiply_mode='pre', inplace=True)
  - _rotate_y(angle, *, point=None, multiply_mode='pre', inplace=True)
  - _rotate_z(angle, *, point=None, multiply_mode='pre', inplace=True)
  - _rotate_vector(vector, angle, *, point=None, multiply_mode='pre', inplace=True)
  - _rotate(rotation, *, point=None, multiply_mode='pre', inplace=True)
  - _scale(factor, *, point=None, multiply_mode='pre', inplace=True)
  - _flip_x/_flip_y/_flip_z, _reflect

PyVista reference for Transform operations:
https://docs.pyvista.org/api/utilities/_autosummary/pyvista.transform
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

import pyvista as pv
from pyvista import transform as pv_transform

# Avoid importing MeshPart/AssemblySection to prevent circular imports.
# We route behavior using duck-typing based on attributes.

DataTarget = Union[pv.DataSet, Sequence[Union["DataTarget", pv.DataSet]], Any]


class SpatialTransformManager:
    """Manages spatial transformations for FEMORA geometry objects.

    This singleton service provides a consistent API for applying affine
    transformations (translation, rotation, scaling, flipping, reflection)
    to various FEMORA objects that carry PyVista meshes, as well as raw
    PyVista datasets and collections thereof. It supports delegation to
    specialized per-target methods for custom transformation behavior.

    This manager is purposefully separate from OpenSees element transformation
    classes found elsewhere in the project.

    Delegation for specialized behavior:
        If a target object defines one of the following methods, delegation
        occurs prior to applying the generic operation:
        - `_apply_transform(transform, *, cascade, inplace)`
        - `_translate(vector, *, inplace)`
        - `_rotate_x(angle, *, point=None, multiply_mode='pre', inplace=True)`
        - `_rotate_y(angle, *, point=None, multiply_mode='pre', inplace=True)`
        - `_rotate_z(angle, *, point=None, multiply_mode='pre', inplace=True)`
        - `_rotate_vector(vector, angle, *, point=None, multiply_mode='pre', inplace=True)`
        - `_rotate(rotation, *, point=None, multiply_mode='pre', inplace=True)`
        - `_scale(factor, *, point=None, multiply_mode='pre', inplace=True)`
        - `_flip_x`, `_flip_y`, `_flip_z`, `_reflect`

    Attributes:
        _instance (Optional[SpatialTransformManager]): The singleton instance of
            the manager, or None if not yet created.

    Example:
        >>> import pyvista as pv
        >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
        >>> manager = SpatialTransformManager()
        >>>
        >>> # Create a sample PyVista dataset
        >>> sphere = pv.Sphere(radius=1.0)
        >>> print(sphere.bounds)
        (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        >>>
        >>> # Translate the sphere
        >>> translated_sphere = manager.translate(sphere, [1, 2, 3], inplace=False)
        >>> print(translated_sphere.bounds)
        (0.0, 2.0, 1.0, 3.0, 2.0, 4.0)
        >>>
        >>> # Scale the sphere in-place
        >>> manager.scale(sphere, 2.0, inplace=True)
        >>> print(sphere.bounds)
        (-2.0, 2.0, -2.0, 2.0, -2.0, 2.0)
    """

    _instance: Optional["SpatialTransformManager"] = None

    def __new__(cls) -> "SpatialTransformManager":
        """Creates or returns the singleton instance of SpatialTransformManager.

        Args:
            cls: The class itself.

        Returns:
            The single instance of the SpatialTransformManager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----- Public API: high-level operations -----
    def translate(
        self,
        target: DataTarget,
        vector: Sequence[float],
        *,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Translates the target object by a given vector.

        This method applies a translation transformation to the target.
        It supports delegation to a `_translate` method on the target if
        present.

        Args:
            target: The object(s) to be translated. Can be a PyVista dataset,
                a FEMORA MeshPart or AssemblySection, or a collection of these.
            vector: A sequence of 3 floats representing the translation
                vector [dx, dy, dz].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones. 'pre' (default) applies the
                translation before previous transformations, 'post' applies
                it after.
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s). If False, a new transformed
                object or collection is returned.

        Returns:
            The transformed object(s). If `inplace` is True, this is the
            original target object(s) (or their primary mesh for MeshPart/
            AssemblySection). If `inplace` is False, a new object(s) is returned.

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> mesh = pv.Sphere(center=(0,0,0))
            >>> translated_mesh = manager.translate(mesh, [10, 20, 30], inplace=False)
            >>> print(translated_mesh.center)
            [10. 20. 30.]
            >>>
            >>> manager.translate(mesh, [1, 1, 1], inplace=True) # Translate original mesh
            >>> print(mesh.center)
            [1. 1. 1.]
        """
        if self._delegate_op(target, "_translate", vector, inplace=inplace):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.translate(*vector)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def rotate(
        self,
        target: DataTarget,
        rotation: Union[Sequence[Sequence[float]], Sequence[float]],
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Rotates the target object using a rotation matrix or Euler angles.

        This method applies a rotation transformation to the target.
        It supports delegation to a `_rotate` method on the target if
        present.

        Args:
            target: The object(s) to be rotated.
            rotation: The rotation to apply. Can be a 3x3 rotation matrix
                (sequence of sequences) or Euler angles [rx, ry, rz] in degrees.
            point: Keyword only. Optional. The point about which to rotate.
                If None, rotation is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> cube = pv.Cube(center=(1, 0, 0))
            >>> rotated_cube_z = manager.rotate(cube, [0, 0, 90], inplace=False) # Rotate 90 degrees around Z
            >>> print(f"Original center: {cube.center}, Rotated center: {rotated_cube_z.center}")
            Original center: [1. 0. 0.], Rotated center: [0. 1. 0.]
            >>>
            >>> # Rotate around a specific point
            >>> manager.rotate(cube, [0, 90, 0], point=[1,0,0], inplace=True)
            >>> print(f"Center after in-place rotation around (1,0,0): {cube.center}")
            Center after in-place rotation around (1,0,0): [1. 0. 0.]
        """
        if self._delegate_op(
            target,
            "_rotate",
            rotation,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.rotate(rotation, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def rotate_vector(
        self,
        target: DataTarget,
        vector: Sequence[float],
        angle: float,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Rotates the target object around a specified vector.

        This method applies a rotation transformation to the target object
        by rotating it `angle` degrees about the given `vector`.
        It supports delegation to a `_rotate_vector` method on the target if
        present.

        Args:
            target: The object(s) to be rotated.
            vector: A sequence of 3 floats representing the axis of rotation.
            angle: The angle of rotation in degrees.
            point: Keyword only. Optional. The point about which to rotate.
                If None, rotation is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> sphere = pv.Sphere(center=(1, 0, 0))
            >>> # Rotate 90 degrees around the Y-axis
            >>> rotated_sphere = manager.rotate_vector(sphere, [0, 1, 0], 90, inplace=False)
            >>> print(f"Original center: {sphere.center}, Rotated center: {rotated_sphere.center}")
            Original center: [1. 0. 0.], Rotated center: [0. 0. -1.]
        """
        if self._delegate_op(
            target,
            "_rotate_vector",
            vector,
            angle,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.rotate_vector(vector, angle, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def rotate_x(
        self,
        target: DataTarget,
        angle: float,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Rotates the target object around the X-axis.

        This method applies a rotation transformation to the target object
        by rotating it `angle` degrees about the X-axis.
        It supports delegation to a `_rotate_x` method on the target if
        present.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Keyword only. Optional. The point about which to rotate.
                If None, rotation is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> cube = pv.Cube(center=(0, 1, 0))
            >>> # Rotate 90 degrees around the X-axis
            >>> rotated_cube = manager.rotate_x(cube, 90, inplace=False)
            >>> print(f"Original center: {cube.center}, Rotated center: {rotated_cube.center}")
            Original center: [0. 1. 0.], Rotated center: [0. 0. 1.]
        """
        if self._delegate_op(
            target,
            "_rotate_x",
            angle,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.rotate_x(angle, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def rotate_y(
        self,
        target: DataTarget,
        angle: float,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Rotates the target object around the Y-axis.

        This method applies a rotation transformation to the target object
        by rotating it `angle` degrees about the Y-axis.
        It supports delegation to a `_rotate_y` method on the target if
        present.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Keyword only. Optional. The point about which to rotate.
                If None, rotation is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> cube = pv.Cube(center=(1, 0, 0))
            >>> # Rotate 90 degrees around the Y-axis
            >>> rotated_cube = manager.rotate_y(cube, 90, inplace=False)
            >>> print(f"Original center: {cube.center}, Rotated center: {rotated_cube.center}")
            Original center: [1. 0. 0.], Rotated center: [0. 0. -1.]
        """
        if self._delegate_op(
            target,
            "_rotate_y",
            angle,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.rotate_y(angle, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def rotate_z(
        self,
        target: DataTarget,
        angle: float,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Rotates the target object around the Z-axis.

        This method applies a rotation transformation to the target object
        by rotating it `angle` degrees about the Z-axis.
        It supports delegation to a `_rotate_z` method on the target if
        present.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Keyword only. Optional. The point about which to rotate.
                If None, rotation is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> cube = pv.Cube(center=(1, 0, 0))
            >>> # Rotate 90 degrees around the Z-axis
            >>> rotated_cube = manager.rotate_z(cube, 90, inplace=False)
            >>> print(f"Original center: {cube.center}, Rotated center: {rotated_cube.center}")
            Original center: [1. 0. 0.], Rotated center: [0. 1. 0.]
        """
        if self._delegate_op(
            target,
            "_rotate_z",
            angle,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.rotate_z(angle, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def scale(
        self,
        target: DataTarget,
        factor: Union[float, Sequence[float]],
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Scales the target object(s) by a given factor.

        This method applies a scaling transformation to the target.
        It supports delegation to a `_scale` method on the target if
        present.

        Args:
            target: The object(s) to be scaled.
            factor: The scaling factor. Can be a single float for uniform scaling,
                or a sequence of 3 floats [sx, sy, sz] for non-uniform scaling.
            point: Keyword only. Optional. The point about which to scale.
                If None, scaling is about the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> cube = pv.Cube(bounds=(0,1,0,1,0,1))
            >>> # Uniform scaling
            >>> scaled_cube_uni = manager.scale(cube, 2.0, inplace=False)
            >>> print(scaled_cube_uni.bounds)
            (0.0, 2.0, 0.0, 2.0, 0.0, 2.0)
            >>>
            >>> # Non-uniform scaling
            >>> scaled_cube_nonuni = manager.scale(cube, [1.0, 2.0, 0.5], inplace=False)
            >>> print(scaled_cube_nonuni.bounds)
            (0.0, 1.0, 0.0, 2.0, 0.0, 0.5)
        """
        if self._delegate_op(
            target,
            "_scale",
            factor,
            point=point,
            multiply_mode=multiply_mode,
            inplace=inplace,
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        if isinstance(factor, (list, tuple)):
            transform.scale(*factor, point=point)
        else:
            transform.scale(factor, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def flip_x(
        self,
        target: DataTarget,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Flips the target object across the Y-Z plane (X-axis).

        This method applies a reflection transformation across the Y-Z plane.
        It supports delegation to a `_flip_x` method on the target if
        present.

        Args:
            target: The object(s) to be flipped.
            point: Keyword only. Optional. The point representing the origin of
                the Y-Z plane for reflection. If None, reflection is about
                the Y-Z plane passing through [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> sphere = pv.Sphere(center=(1, 0, 0))
            >>> flipped_sphere = manager.flip_x(sphere, inplace=False)
            >>> print(f"Original center: {sphere.center}, Flipped center: {flipped_sphere.center}")
            Original center: [1. 0. 0.], Flipped center: [-1. 0. 0.]
        """
        if self._delegate_op(target, "_flip_x", point=point, multiply_mode=multiply_mode, inplace=inplace):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.flip_x(point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def flip_y(
        self,
        target: DataTarget,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Flips the target object across the X-Z plane (Y-axis).

        This method applies a reflection transformation across the X-Z plane.
        It supports delegation to a `_flip_y` method on the target if
        present.

        Args:
            target: The object(s) to be flipped.
            point: Keyword only. Optional. The point representing the origin of
                the X-Z plane for reflection. If None, reflection is about
                the X-Z plane passing through [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> sphere = pv.Sphere(center=(0, 1, 0))
            >>> flipped_sphere = manager.flip_y(sphere, inplace=False)
            >>> print(f"Original center: {sphere.center}, Flipped center: {flipped_sphere.center}")
            Original center: [0. 1. 0.], Flipped center: [0. -1. 0.]
        """
        if self._delegate_op(target, "_flip_y", point=point, multiply_mode=multiply_mode, inplace=inplace):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.flip_y(point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def flip_z(
        self,
        target: DataTarget,
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Flips the target object across the X-Y plane (Z-axis).

        This method applies a reflection transformation across the X-Y plane.
        It supports delegation to a `_flip_z` method on the target if
        present.

        Args:
            target: The object(s) to be flipped.
            point: Keyword only. Optional. The point representing the origin of
                the X-Y plane for reflection. If None, reflection is about
                the X-Y plane passing through [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> sphere = pv.Sphere(center=(0, 0, 1))
            >>> flipped_sphere = manager.flip_z(sphere, inplace=False)
            >>> print(f"Original center: {sphere.center}, Flipped center: {flipped_sphere.center}")
            Original center: [0. 0. 1.], Flipped center: [0. 0. -1.]
        """
        if self._delegate_op(target, "_flip_z", point=point, multiply_mode=multiply_mode, inplace=inplace):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.flip_z(point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def reflect(
        self,
        target: DataTarget,
        normal: Sequence[float],
        *,
        point: Optional[Sequence[float]] = None,
        multiply_mode: str = "pre",
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Reflects the target object across a plane defined by a normal vector.

        This method applies a reflection transformation across a plane.
        It supports delegation to a `_reflect` method on the target if
        present.

        Args:
            target: The object(s) to be reflected.
            normal: A sequence of 3 floats representing the normal vector
                of the reflection plane.
            point: Keyword only. Optional. A point on the reflection plane.
                If None, the plane is assumed to pass through the origin [0,0,0].
            multiply_mode: Keyword only. Determines how the new transform is
                combined with existing ones ('pre' or 'post').
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s).

        Returns:
            The transformed object(s).

        Example:
            >>> import pyvista as pv
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> sphere = pv.Sphere(center=(1, 1, 1))
            >>> # Reflect across the X-Y plane (normal [0,0,1])
            >>> reflected_sphere = manager.reflect(sphere, [0, 0, 1], inplace=False)
            >>> print(f"Original center: {sphere.center}, Reflected center: {reflected_sphere.center}")
            Original center: [1. 1. 1.], Reflected center: [1. 1. -1.]
        """
        if self._delegate_op(
            target, "_reflect", normal, point=point, multiply_mode=multiply_mode, inplace=inplace
        ):
            return self._result_for_target(target)

        transform = self._build_transform(multiply_mode)
        transform.reflect(normal, point=point)
        return self.apply_transform(target, transform, cascade=cascade, inplace=inplace)

    def apply_transform(
        self,
        target: DataTarget,
        transform: pv_transform.Transform,
        *,
        cascade: bool = False,
        inplace: bool = True,
    ) -> Any:
        """Applies a pre-built PyVista transform object to the target.

        This is the core method for applying any PyVista `Transform` object
        to a target. It handles delegation to a `_apply_transform` method
        on the target if present, and cascades the transformation to sub-objects
        for AssemblySections if `cascade` is True.

        Args:
            target: The object(s) to which the transform will be applied.
                Can be a PyVista dataset, a FEMORA MeshPart or AssemblySection,
                or a collection of these.
            transform: A PyVista `Transform` object defining the transformation
                matrix.
            cascade: Keyword only. If True and the target is an AssemblySection,
                the transformation will also be applied to its underlying MeshParts.
            inplace: Keyword only. If True, the transformation is applied
                directly to the target object(s). If False, a new transformed
                object or collection is returned.

        Returns:
            The transformed object(s). If `inplace` is True, this is the
            original target object(s) (or their primary mesh for MeshPart/
            AssemblySection). If `inplace` is False, a new object(s) is returned.

        Raises:
            TypeError: If an unsupported target type is provided.

        Example:
            >>> import pyvista as pv
            >>> from pyvista import transform as pv_transform
            >>> from femora.components.transformation.spatial_transform_manager import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>>
            >>> mesh = pv.Box(bounds=(0,1,0,1,0,1))
            >>>
            >>> # Create a transform for translation and rotation
            >>> xfm = pv_transform.Transform()
            >>> xfm.translate([10, 0, 0])
            >>> xfm.rotate_z(45)
            >>>
            >>> transformed_mesh = manager.apply_transform(mesh, xfm, inplace=False)
            >>> print(transformed_mesh.center)
            [ 7.07106781  7.77817459  0.5       ]
        """
        # MeshPart (duck-typed): has mesh, element, region, and no meshparts_list
        if self._is_meshpart(target):
            if self._delegate_apply_transform(target, transform, cascade=cascade, inplace=inplace):
                return target.mesh
            return self._apply_to_dataset(target.mesh, transform, inplace=inplace)

        # AssemblySection (duck-typed): has mesh and meshparts_list
        if self._is_assembly_section(target):
            if self._delegate_apply_transform(target, transform, cascade=cascade, inplace=inplace):
                return target.mesh
            if cascade:
                # Apply to all underlying mesh parts first
                for mesh_part in getattr(target, "meshparts_list", []) or []:
                    self.apply_transform(mesh_part, transform, cascade=False, inplace=inplace)
            return self._apply_to_dataset(target.mesh, transform, inplace=inplace)

        # PyVista dataset
        if isinstance(target, pv.DataSet):
            return self._apply_to_dataset(target, transform, inplace=inplace)

        # Collections
        if isinstance(target, (list, tuple, set)):
            results: List[Any] = []
            for item in target:
                results.append(self.apply_transform(item, transform, cascade=cascade, inplace=inplace))
            return results

        raise TypeError(f"Unsupported target type: {type(target)}")

    # ----- Internal helpers -----
    def _build_transform(self, multiply_mode: str) -> pv_transform.Transform:
        """Constructs a new PyVista Transform object with the specified multiply mode.

        Args:
            multiply_mode: Specifies whether new transformations should 'pre_multiply'
                or 'post_multiply' existing ones. Must be 'pre' or 'post'.

        Returns:
            A new PyVista Transform instance configured for the given multiply mode.

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.
        """
        if multiply_mode not in {"pre", "post"}:
            raise ValueError("multiply_mode must be 'pre' or 'post'")
        t = pv_transform.Transform()
        if multiply_mode == "pre":
            t.pre_multiply()
        else:
            t.post_multiply()
        return t

    def _apply_to_dataset(
        self,
        dataset: Optional[pv.DataSet],
        transform: pv_transform.Transform,
        *,
        inplace: bool,
    ) -> pv.DataSet:
        """Applies a PyVista Transform to a single PyVista DataSet.

        Args:
            dataset: The PyVista DataSet to transform.
            transform: The PyVista Transform object to apply.
            inplace: Keyword only. If True, applies the transform in-place.
                Otherwise, a new dataset is returned.

        Returns:
            The transformed PyVista DataSet. This is `dataset` itself if
            `inplace` is True, or a new dataset if `inplace` is False.

        Raises:
            ValueError: If the target `dataset` is None.
        """
        if dataset is None:
            raise ValueError("Target dataset is None; cannot apply transform.")
        # Apply transformation matrix to the dataset
        dataset.transform(transform.matrix, inplace=inplace)
        return dataset

    def _delegate_op(self, target: Any, name: str, *args: Any, **kwargs: Any) -> bool:
        """Attempts to call an operation-specific override method on the target.

        If the `target` object has a callable method named `name`, that method
        is invoked with the provided `args` and `kwargs`. This allows targets
        to implement custom transformation logic.

        Args:
            target: The object on which to attempt delegation.
            name: The name of the method to look for on the target (e.g., '_translate').
            *args: Positional arguments to pass to the delegated method.
            **kwargs: Keyword arguments to pass to the delegated method.

        Returns:
            True if a callable method was found and invoked, False otherwise.
        """
        method = getattr(target, name, None)
        if callable(method):
            method(*args, **kwargs)
            return True
        return False

    def _delegate_apply_transform(
        self, target: Any, transform: pv_transform.Transform, *, cascade: bool, inplace: bool
    ) -> bool:
        """Attempts to call the general `_apply_transform` override method on the target.

        If the `target` object has a callable `_apply_transform` method, that method
        is invoked. This provides a general override for the `apply_transform` operation.

        Args:
            target: The object on which to attempt delegation.
            transform: The PyVista Transform object to pass to the delegated method.
            cascade: Keyword only. Passed to the delegated method.
            inplace: Keyword only. Passed to the delegated method.

        Returns:
            True if the `_apply_transform` method was found and invoked, False otherwise.
        """
        method = getattr(target, "_apply_transform", None)
        if callable(method):
            method(transform, cascade=cascade, inplace=inplace)
            return True
        return False

    def _result_for_target(self, target: Any) -> Any:
        """Provides a consistent return value after a transformation, especially after delegation.

        For MeshPart or AssemblySection objects, this returns their underlying
        primary PyVista mesh. For collections, it returns the collection itself.
        For raw PyVista datasets, it returns the dataset itself.

        Args:
            target: The object that was transformed or attempted to be transformed.

        Returns:
            The appropriate object representing the result of the transformation.
        """
        if self._is_meshpart(target) or self._is_assembly_section(target):
            return getattr(target, "mesh", target)
        return target

    # ----- Type guards (duck-typing) -----
    def _is_meshpart(self, obj: Any) -> bool:
        """Checks if an object duck-types as a FEMORA MeshPart.

        A MeshPart is identified by having `mesh`, `element`, and `region`
        attributes, but *not* a `meshparts_list` attribute.

        Args:
            obj: The object to check.

        Returns:
            True if the object appears to be a MeshPart, False otherwise.
        """
        return (
            hasattr(obj, "mesh")
            and hasattr(obj, "element")
            and hasattr(obj, "region")
            and not hasattr(obj, "meshparts_list")
        )

    def _is_assembly_section(self, obj: Any) -> bool:
        """Checks if an object duck-types as a FEMORA AssemblySection.

        An AssemblySection is identified by having both `mesh` and
        `meshparts_list` attributes.

        Args:
            obj: The object to check.

        Returns:
            True if the object appears to be an AssemblySection, False otherwise.
        """
        return hasattr(obj, "mesh") and hasattr(obj, "meshparts_list")


__all__ = ["SpatialTransformManager"]