from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Union

from femora.components.ground_motion.interpolated_ground_motion import InterpolatedGroundMotion
from femora.components.ground_motion.plain_ground_motion import PlainGroundMotion
from femora.components.TimeSeries.timeSeriesBase import TimeSeries
from femora.core.ground_motion_base import GroundMotion


class GroundMotionManager:
    """Manager for a local collection of ground motions.

    The manager is responsible for ground-motion lifecycle and numbering:
    adding instances, assigning tags, looking up objects, deleting objects, and
    retagging after removals or tag-start changes. It is intentionally not a
    singleton. Each ``GroundMotionManager`` instance owns an independent tag
    space, which allows future model or ``MeshMaker`` instances to keep local
    ground-motion collections.

    Concrete ground-motion classes validate and render themselves, while this
    manager controls ownership. Prefer factory methods such as ``plain(...)``
    and ``interpolated(...)`` for normal use; use ``add(...)`` when an instance
    has already been constructed manually.

    Example:
        ```python
        accel = model.timeSeries.path(dt=0.01, filePath="support.acc")
        disp = model.timeSeries.path(dt=0.01, filePath="support.disp")

        gm = model.groundMotion.plain(accel=accel, disp=disp)
        print(gm.tag)      # 1
        print(gm.to_tcl()) # groundMotion 1 Plain -accel ... -disp ...
        ```
    """

    def __init__(self):
        """Create an empty ground-motion manager with tags starting at 1."""
        self._ground_motions: Dict[int, GroundMotion] = {}
        self._start_tag = 1

    def __len__(self) -> int:
        """Return the number of managed ground motions."""
        return len(self._ground_motions)

    def __iter__(self) -> Iterator[GroundMotion]:
        """Iterate over managed ground motions in tag order."""
        return iter(self._ground_motions.values())

    def add(self, ground_motion: GroundMotion) -> GroundMotion:
        """Add a ground motion instance and assign its local tag.

        Args:
            ground_motion: Unmanaged ``GroundMotion`` instance to store.

        Returns:
            The same ground-motion instance, now tagged and managed.

        Raises:
            ValueError: If ``ground_motion`` is not a ``GroundMotion`` or if it
                already has a tag from another manager.
        """
        if not isinstance(ground_motion, GroundMotion):
            raise ValueError("ground_motion must be a GroundMotion instance")
        if ground_motion.tag is not None:
            existing = self._ground_motions.get(ground_motion.tag)
            if existing is ground_motion:
                return ground_motion
            raise ValueError("ground_motion already has a tag managed elsewhere")

        tag = self._next_tag()
        ground_motion.tag = tag
        self._ground_motions[tag] = ground_motion
        return ground_motion

    def plain(
        self,
        accel: Optional[TimeSeries] = None,
        vel: Optional[TimeSeries] = None,
        disp: Optional[TimeSeries] = None,
        integrator: Optional[str] = None,
        integrator_args: Optional[List[Union[int, float, str]]] = None,
        factor: float = 1.0,
    ) -> PlainGroundMotion:
        """Create, tag, and store a ``PlainGroundMotion``.

        Args:
            accel: Acceleration time series. Optional if ``vel`` or ``disp`` is
                provided.
            vel: Velocity time series. Optional if ``accel`` or ``disp`` is
                provided.
            disp: Displacement time series. Optional if ``accel`` or ``vel`` is
                provided.
            integrator: Optional OpenSees integration method, such as
                ``"Trapezoidal"`` or ``"Simpson"``.
            integrator_args: Optional arguments appended after ``integrator`` in
                the ``-int`` option.
            factor: Constant scale factor for the ground motion.

        Returns:
            The managed ``PlainGroundMotion`` instance.
        """
        ground_motion = PlainGroundMotion(
            accel=accel,
            vel=vel,
            disp=disp,
            integrator=integrator,
            integrator_args=integrator_args,
            factor=factor,
        )
        self.add(ground_motion)
        return ground_motion

    def interpolated(
        self,
        ground_motions: List[GroundMotion],
        factors: List[float],
    ) -> InterpolatedGroundMotion:
        """Create, tag, and store an ``InterpolatedGroundMotion``.

        Args:
            ground_motions: Ground motions to combine. Each item must be a
                ``GroundMotion`` instance.
            factors: Interpolation factors. Must have the same length as
                ``ground_motions``.

        Returns:
            The managed ``InterpolatedGroundMotion`` instance.
        """
        ground_motion = InterpolatedGroundMotion(
            ground_motions=ground_motions,
            factors=factors,
        )
        self.add(ground_motion)
        return ground_motion

    def get(self, tag: int) -> GroundMotion:
        """Return a managed ground motion by tag.

        Args:
            tag: Ground-motion tag in this manager's local tag space.

        Raises:
            KeyError: If no ground motion exists with ``tag``.
        """
        tag = int(tag)
        if tag not in self._ground_motions:
            raise KeyError(f"No ground motion found with tag {tag}")
        return self._ground_motions[tag]

    def get_all(self) -> Dict[int, GroundMotion]:
        """Return a copy of all managed ground motions keyed by tag."""
        return self._ground_motions.copy()

    def remove(self, tag: int) -> None:
        """Remove a ground motion and retag remaining instances.

        Args:
            tag: Ground-motion tag to remove. Missing tags are ignored.
        """
        tag = int(tag)
        if tag in self._ground_motions:
            removed = self._ground_motions.pop(tag)
            removed.tag = None
            self._reassign_tags()

    def clear(self) -> None:
        """Remove all ground motions and reset the next tag start to 1."""
        for ground_motion in self._ground_motions.values():
            ground_motion.tag = None
        self._ground_motions.clear()
        self._start_tag = 1

    def set_tag_start(self, start_tag: int) -> None:
        """Set the first tag and retag existing ground motions.

        Args:
            start_tag: First tag to use for this manager. Must be positive.

        Raises:
            ValueError: If ``start_tag`` is less than 1.
        """
        start_tag = int(start_tag)
        if start_tag < 1:
            raise ValueError("start_tag must be a positive integer")
        self._start_tag = start_tag
        self._reassign_tags()

    def _next_tag(self) -> int:
        if not self._ground_motions:
            return self._start_tag
        return max(self._ground_motions) + 1

    def _reassign_tags(self) -> None:
        ground_motions = sorted(
            self._ground_motions.values(),
            key=lambda ground_motion: ground_motion.tag or 0,
        )
        self._ground_motions.clear()
        for tag, ground_motion in enumerate(ground_motions, start=self._start_tag):
            ground_motion.tag = tag
            self._ground_motions[tag] = ground_motion


__all__ = [
    "GroundMotion",
    "GroundMotionManager",
    "PlainGroundMotion",
    "InterpolatedGroundMotion",
]
