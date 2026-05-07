from __future__ import annotations

from typing import Optional, Sequence

from femora.core.pattern_base import Pattern


class H5DRMPattern(Pattern):
    """OpenSees ``H5DRM`` pattern.

    The pattern references an HDF5 DRM input file and emits the Femora/OpenSees
    H5DRM command including scale factors, node matching tolerance, optional
    coordinate transformation matrix, and origin.
    """

    def __init__(
        self,
        filepath: str,
        factor: float,
        crd_scale: float,
        distance_tolerance: float,
        do_coordinate_transformation: int,
        transform_matrix: Optional[Sequence[float]] = None,
        origin: Optional[Sequence[float]] = None,
        **kwargs,
    ):
        """Create an H5DRM load pattern.

        Args:
            filepath: Path to the H5DRM dataset.
            factor: Scale factor for DRM forces and displacements.
            crd_scale: Coordinate scale factor for the dataset.
            distance_tolerance: Tolerance used to match DRM points to mesh
                nodes.
            do_coordinate_transformation: ``0`` or ``1`` flag controlling
                coordinate transformation.
            transform_matrix: Optional 9-value transformation matrix. If not
                supplied, ``T00`` through ``T22`` must be present in ``kwargs``.
            origin: Optional 3-value transformed origin. If not supplied,
                ``x00`` through ``x02`` must be present in ``kwargs``.
            **kwargs: Compatibility support for individual matrix/origin
                entries.

        Raises:
            ValueError: If transformation flags or sequence lengths are invalid.
            KeyError: If required individual matrix/origin keys are missing.
        """
        super().__init__("H5DRM")
        self.filepath = str(filepath)
        self.factor = float(factor)
        self.crd_scale = float(crd_scale)
        self.distance_tolerance = float(distance_tolerance)
        self.do_coordinate_transformation = int(do_coordinate_transformation)
        if self.do_coordinate_transformation not in (0, 1):
            raise ValueError("do_coordinate_transformation must be 0 or 1")

        if transform_matrix is None:
            keys = ("T00", "T01", "T02", "T10", "T11", "T12", "T20", "T21", "T22")
            transform_matrix = [kwargs[key] for key in keys]
        self.transform_matrix = [float(value) for value in transform_matrix]
        if len(self.transform_matrix) != 9:
            raise ValueError("transform_matrix must contain 9 values")

        if origin is None:
            keys = ("x00", "x01", "x02")
            origin = [kwargs[key] for key in keys]
        self.origin = [float(value) for value in origin]
        if len(self.origin) != 3:
            raise ValueError("origin must contain 3 values")

    def to_tcl(self) -> str:
        """Render this pattern as an OpenSees TCL command."""
        matrix = " ".join(map(str, self.transform_matrix))
        origin = " ".join(map(str, self.origin))
        return (
            f'pattern H5DRM {self._require_tag()} "{self.filepath}" '
            f"{self.factor} {self.crd_scale} {self.distance_tolerance} "
            f"{self.do_coordinate_transformation} {matrix} {origin}"
        )
