from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union

import pyvista as pv
from pyvista import transform as pv_transform

# Avoid importing MeshPart/AssemblySection to prevent circular imports.
# We route behavior using duck-typing based on attributes.

DataTarget = Union[pv.DataSet, Sequence[Union["DataTarget", pv.DataSet]], Any]


class SpatialTransformManager:
    """Manages spatial transformations for FEMORA objects and PyVista meshes.

    This singleton service provides a consistent API for applying affine
    geometric operations such as translation, rotation, scaling, flipping,
    and reflection to FEMORA objects and PyVista datasets. It leverages
    PyVista's Transform utilities and supports delegation to specialized
    per-target methods when available, allowing objects to define custom
    transformation logic.

    Targets supported:
        - `femora.components.Mesh.meshPartBase.MeshPart`
        - `femora.components.Assemble.Assembler.AssemblySection`
        - PyVista datasets (`pv.DataSet` and its subclasses)
        - Collections (lists, tuples, sets) of the above

    Delegation:
        If a target object defines a method matching `_apply_transform` or
        specific operation methods (e.g., `_translate`, `_rotate_x`), this
        manager will delegate the operation to that method before applying
        the generic transformation. This allows for specialized handling
        by target objects.

    Attributes:
        _instance (Optional[SpatialTransformManager]): The singleton instance
            of the manager.

    Example:
        >>> import pyvista as pv
        >>> from femora.spatial_transform import SpatialTransformManager
        >>> manager = SpatialTransformManager()
        >>> mesh = pv.Sphere()
        >>> original_center = mesh.center
        >>> translated_mesh = manager.translate(mesh, [1.0, 2.0, 3.0], inplace=False)
        >>> # The mesh's center will be shifted by [1.0, 2.0, 3.0]
    """

    _instance: Optional["SpatialTransformManager"] = None

    def __new__(cls) -> "SpatialTransformManager":
        """Creates or returns the singleton instance of SpatialTransformManager.

        Returns:
            SpatialTransformManager: The singleton instance of the manager.
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
        """Translates the target object(s) by a given vector.

        This method applies a translation transformation to the target.
        It first checks for a custom `_translate` method on the target for
        delegation. If not found, it builds a PyVista transform and applies it.

        Args:
            target: The object(s) to be translated. Can be a PyVista dataset,
                a FEMORA MeshPart or AssemblySection, or a collection of these.
            vector: A sequence of three floats `[dx, dy, dz]` representing
                the translation vector.
            multiply_mode: Optional. Specifies how the new transform is
                combined with existing ones. 'pre' (default) applies
                this transform before existing transforms; 'post' applies
                it after.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), the transformation is applied
                to the target object(s) in-place. If False, a new transformed
                object or collection of objects is returned.

        Returns:
            Any: The transformed target object(s). If `inplace` is True, returns
                the modified input `target`. If `inplace` is False, returns a
                newly transformed object or collection.

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Sphere()
            >>> translated_mesh = manager.translate(mesh, [1.0, 2.0, 0.0], inplace=False)
            >>> # The mesh's center will be shifted by [1.0, 2.0, 0.0]
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
        """Rotates the target object(s) using a rotation matrix or angles.

        This method applies a rotation transformation to the target.
        It first checks for a custom `_rotate` method on the target for
        delegation. If not found, it builds a PyVista transform and applies it.

        Args:
            target: The object(s) to be rotated.
            rotation: The rotation to apply. Can be:
                - A 3x3 rotation matrix (sequence of sequences of floats).
                - A sequence of three Euler angles `[rx, ry, rz]` in degrees.
            point: Optional. The 3D point `[x, y, z]` about which to rotate.
                If None, rotation is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Sphere()
            >>> rotated_mesh = manager.rotate(mesh, [90, 0, 0], point=[0, 0, 0], inplace=False)
            >>> # The mesh will be rotated 90 degrees around the X-axis.
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
        """Rotates the target object(s) about an arbitrary vector.

        This method applies a rotation transformation to the target around
        a specified vector axis. It first checks for a custom `_rotate_vector`
        method on the target for delegation.

        Args:
            target: The object(s) to be rotated.
            vector: A sequence of three floats `[vx, vy, vz]` defining
                the axis of rotation.
            angle: The angle of rotation in degrees.
            point: Optional. The 3D point `[x, y, z]` about which to rotate.
                If None, rotation is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cylinder()
            >>> # Rotate 45 degrees around the Z-axis, centered at [0,0,0]
            >>> rotated_mesh = manager.rotate_vector(mesh, [0, 0, 1], 45, point=[0,0,0], inplace=False)
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
        """Rotates the target object(s) about the X-axis.

        This method applies a rotation transformation around the X-axis.
        It first checks for a custom `_rotate_x` method on the target for
        delegation.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Optional. The 3D point `[x, y, z]` about which to rotate.
                If None, rotation is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Plane()
            >>> rotated_mesh = manager.rotate_x(mesh, 90, inplace=False)
            >>> # The plane will now be vertical instead of horizontal.
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
        """Rotates the target object(s) about the Y-axis.

        This method applies a rotation transformation around the Y-axis.
        It first checks for a custom `_rotate_y` method on the target for
        delegation.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Optional. The 3D point `[x, y, z]` about which to rotate.
                If None, rotation is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cube()
            >>> rotated_mesh = manager.rotate_y(mesh, 45, point=mesh.center, inplace=False)
            >>> # The cube will be rotated 45 degrees around its own Y-axis.
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
        """Rotates the target object(s) about the Z-axis.

        This method applies a rotation transformation around the Z-axis.
        It first checks for a custom `_rotate_z` method on the target for
        delegation.

        Args:
            target: The object(s) to be rotated.
            angle: The angle of rotation in degrees.
            point: Optional. The 3D point `[x, y, z]` about which to rotate.
                If None, rotation is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.ParametricSuperellipsoid()
            >>> rotated_mesh = manager.rotate_z(mesh, 180, point=[1,1,1], inplace=False)
            >>> # Rotates 180 degrees around Z axis passing through [1,1,1].
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
        It first checks for a custom `_scale` method on the target for
        delegation.

        Args:
            target: The object(s) to be scaled.
            factor: The scaling factor(s). Can be a single float (uniform
                scaling) or a sequence of three floats `[sx, sy, sz]` for
                non-uniform scaling.
            point: Optional. The 3D point `[x, y, z]` about which to scale.
                If None, scaling is about the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Box()
            >>> scaled_mesh = manager.scale(mesh, 2.0, inplace=False)
            >>> # The box will be twice as large uniformly.
            >>> non_uniform_scaled_mesh = manager.scale(mesh, [0.5, 1.0, 2.0], inplace=False)
            >>> # The box will be scaled non-uniformly.
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
        """Flips the target object(s) about the X-axis.

        This method applies a reflection transformation across the YZ plane.
        It first checks for a custom `_flip_x` method on the target for
        delegation.

        Args:
            target: The object(s) to be flipped.
            point: Optional. The 3D point `[x, y, z]` defining the origin
                of the reflection plane (YZ plane passing through `x`).
                If None, reflects about the origin's YZ plane.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cylinder(center=[1,0,0])
            >>> flipped_mesh = manager.flip_x(mesh, point=[0,0,0], inplace=False)
            >>> # The cylinder at [1,0,0] will be mirrored to [-1,0,0].
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
        """Flips the target object(s) about the Y-axis.

        This method applies a reflection transformation across the XZ plane.
        It first checks for a custom `_flip_y` method on the target for
        delegation.

        Args:
            target: The object(s) to be flipped.
            point: Optional. The 3D point `[x, y, z]` defining the origin
                of the reflection plane (XZ plane passing through `y`).
                If None, reflects about the origin's XZ plane.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Plane(i_size=1, j_size=1, i_resolution=1, j_resolution=1, normal=[0,1,0])
            >>> # A plane aligned with the XZ plane, originally facing +Y.
            >>> flipped_mesh = manager.flip_y(mesh, point=mesh.center, inplace=False)
            >>> # The plane will now be facing -Y.
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
        """Flips the target object(s) about the Z-axis.

        This method applies a reflection transformation across the XY plane.
        It first checks for a custom `_flip_z` method on the target for
        delegation.

        Args:
            target: The object(s) to be flipped.
            point: Optional. The 3D point `[x, y, z]` defining the origin
                of the reflection plane (XY plane passing through `z`).
                If None, reflects about the origin's XY plane.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cone(direction=[0,0,1], center=[0,0,1])
            >>> # A cone pointing up, with its base at Z=0.
            >>> flipped_mesh = manager.flip_z(mesh, point=[0,0,0], inplace=False)
            >>> # The cone will now point down, with its base still at Z=0.
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
        """Reflects the target object(s) across a plane defined by a normal vector.

        This method applies a reflection transformation across an arbitrary plane.
        It first checks for a custom `_reflect` method on the target for
        delegation.

        Args:
            target: The object(s) to be reflected.
            normal: A sequence of three floats `[nx, ny, nz]` representing
                the normal vector of the reflection plane.
            point: Optional. The 3D point `[x, y, z]` through which the
                reflection plane passes. If None, the plane passes through
                the origin `[0, 0, 0]`.
            multiply_mode: Optional. 'pre' (default) or 'post'.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), applies in-place.

        Returns:
            Any: The transformed target object(s).

        Raises:
            ValueError: If `multiply_mode` is not 'pre' or 'post'.

        Example:
            >>> import pyvista as pv
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cube(center=[1,1,1])
            >>> # Reflect across the plane X=0 (normal [1,0,0] through origin).
            >>> reflected_mesh = manager.reflect(mesh, [1, 0, 0], point=[0,0,0], inplace=False)
            >>> # The cube will be mirrored to center at [-1,1,1].
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
        """Applies a pre-built PyVista Transform object to the target(s).

        This is the core method for applying any general affine transformation
        to various target types, including PyVista datasets, FEMORA MeshParts,
        AssemblySections, or collections thereof. It handles delegation to
        custom `_apply_transform` methods on target objects and supports
        cascading transformations for AssemblySections.

        Args:
            target: The object(s) to which the transform will be applied.
                Can be a PyVista dataset, a FEMORA MeshPart or AssemblySection,
                or a collection of these.
            transform: A `pyvista.transform.Transform` object defining the
                affine transformation to apply.
            cascade: Optional. If True, and the target is an AssemblySection,
                the transform will also be applied to its constituent MeshParts.
                Defaults to False.
            inplace: Optional. If True (default), the transformation is applied
                to the target object(s) in-place. If False, a new transformed
                object or collection of objects is returned.

        Returns:
            Any: The transformed target object(s). If `inplace` is True, returns
                the modified input `target` (or its primary mesh for Femora objects).
                If `inplace` is False, returns a newly transformed object or
                collection.

        Raises:
            TypeError: If the `target` type is not supported.
            ValueError: If an internal dataset for a target object is None.

        Example:
            >>> import pyvista as pv
            >>> from pyvista import transform as pv_transform
            >>> from femora.spatial_transform import SpatialTransformManager
            >>> manager = SpatialTransformManager()
            >>> mesh = pv.Cube()
            >>>
            >>> # Create a custom transform (e.g., scale by 2 and then translate)
            >>> custom_transform = pv_transform.Transform()
            >>> custom_transform.scale(2.0).translate([1, 0, 0])
            >>>
            >>> transformed_mesh = manager.apply_transform(mesh, custom_transform, inplace=False)
            >>> # The mesh will be scaled by 2 and then translated by [1,0,0].
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
            multiply_mode: 'pre' or 'post', indicating how transformations are
                multiplied.

        Returns:
            pv_transform.Transform: A new PyVista Transform instance.

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
        """Applies a PyVista Transform matrix to a PyVista DataSet.

        Args:
            dataset: The PyVista DataSet to transform.
            transform: The PyVista Transform object containing the matrix.
            inplace: If True, modifies the dataset in-place.

        Returns:
            pv.DataSet: The transformed dataset.

        Raises:
            ValueError: If the input `dataset` is None.
        """
        if dataset is None:
            raise ValueError("Target dataset is None; cannot apply transform.")
        # Apply transformation matrix to the dataset
        dataset.transform(transform.matrix, inplace=inplace)
        return dataset

    def _delegate_op(self, target: Any, name: str, *args: Any, **kwargs: Any) -> bool:
        """Attempts to delegate an operation to a target's custom method.

        Args:
            target: The object on which to check for a custom method.
            name: The name of the custom method (e.g., '_translate').
            *args: Positional arguments to pass to the custom method.
            **kwargs: Keyword arguments to pass to the custom method.

        Returns:
            bool: True if the custom method exists and was called, False otherwise.
        """
        method = getattr(target, name, None)
        if callable(method):
            method(*args, **kwargs)
            return True
        return False

    def _delegate_apply_transform(
        self, target: Any, transform: pv_transform.Transform, *, cascade: bool, inplace: bool
    ) -> bool:
        """Attempts to delegate the `_apply_transform` operation to a target.

        Args:
            target: The object on which to check for a custom `_apply_transform` method.
            transform: The PyVista Transform object.
            cascade: Whether to cascade the transform.
            inplace: Whether to apply the transform in-place.

        Returns:
            bool: True if the custom method exists and was called, False otherwise.
        """
        method = getattr(target, "_apply_transform", None)
        if callable(method):
            method(transform, cascade=cascade, inplace=inplace)
            return True
        return False

    def _result_for_target(self, target: Any) -> Any:
        """Retrieves the appropriate result object after a transformation.

        For MeshPart or AssemblySection, returns their internal mesh.
        For other types, returns the target itself.

        Args:
            target: The original target object.

        Returns:
            Any: The object representing the transformed result (e.g., mesh for
                Femora components, or the target itself for others).
        """
        if self._is_meshpart(target) or self._is_assembly_section(target):
            return getattr(target, "mesh", target)
        return target

    # ----- Type guards (duck-typing) -----
    def _is_meshpart(self, obj: Any) -> bool:
        """Checks if an object duck-types as a MeshPart.

        Args:
            obj: The object to check.

        Returns:
            bool: True if the object has 'mesh', 'element', 'region' attributes
                and lacks 'meshparts_list'.
        """
        return (
            hasattr(obj, "mesh")
            and hasattr(obj, "element")
            and hasattr(obj, "region")
            and not hasattr(obj, "meshparts_list")
        )

    def _is_assembly_section(self, obj: Any) -> bool:
        """Checks if an object duck-types as an AssemblySection.

        Args:
            obj: The object to check.

        Returns:
            bool: True if the object has 'mesh' and 'meshparts_list' attributes.
        """
        return hasattr(obj, "mesh") and hasattr(obj, "meshparts_list")


__all__ = ["SpatialTransformManager"]