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
    """
    Singleton manager for spatial transforms on FEMORA geometry objects.

    Provides a consistent API for applying affine transforms using
    PyVista's Transform utilities and supports delegation to specialized
    per-target methods when available.
    """

    _instance: Optional["SpatialTransformManager"] = None

    def __new__(cls) -> "SpatialTransformManager":
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
        """
        Apply a prebuilt PyVista transform to the target.

        Returns the mutated dataset(s) for convenience.
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
        if dataset is None:
            raise ValueError("Target dataset is None; cannot apply transform.")
        # Apply transformation matrix to the dataset
        dataset.transform(transform.matrix, inplace=inplace)
        return dataset

    def _delegate_op(self, target: Any, name: str, *args: Any, **kwargs: Any) -> bool:
        """Attempt to call an op-specific override on the target if present."""
        method = getattr(target, name, None)
        if callable(method):
            method(*args, **kwargs)
            return True
        return False

    def _delegate_apply_transform(
        self, target: Any, transform: pv_transform.Transform, *, cascade: bool, inplace: bool
    ) -> bool:
        method = getattr(target, "_apply_transform", None)
        if callable(method):
            method(transform, cascade=cascade, inplace=inplace)
            return True
        return False

    def _result_for_target(self, target: Any) -> Any:
        """
        Convenience method for returning a consistent result after delegation.
        MeshPart/AssemblySection return their primary dataset, collections return
        the collection itself, datasets return themselves.
        """
        if self._is_meshpart(target) or self._is_assembly_section(target):
            return getattr(target, "mesh", target)
        return target

    # ----- Type guards (duck-typing) -----
    def _is_meshpart(self, obj: Any) -> bool:
        return (
            hasattr(obj, "mesh")
            and hasattr(obj, "element")
            and hasattr(obj, "region")
            and not hasattr(obj, "meshparts_list")
        )

    def _is_assembly_section(self, obj: Any) -> bool:
        return hasattr(obj, "mesh") and hasattr(obj, "meshparts_list")
    


    def clear(self):
        """Clears all spatial transformations from the manager.

        This method is an alias for clear_all_transformations to provide a more intuitive
        interface for clearing transformations.
        """
        # since transformations are applied in-place to datasets, there is no internal state to clear.
        # This method is provided for API consistency and future extensibility.
        pass


__all__ = ["SpatialTransformManager"]


