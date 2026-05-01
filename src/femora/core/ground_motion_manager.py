from __future__ import annotations

from typing import Dict, Iterator

from femora.components.ground_motion.interpolated_ground_motion import InterpolatedGroundMotion
from femora.components.ground_motion.plain_ground_motion import PlainGroundMotion
from femora.core.ground_motion_base import GroundMotion
from femora.utils.signature import forward_signature


class GroundMotionManager:
    """Manager for ground motion instances.

    Each manager owns its own tags and storage. GroundMotion classes only
    validate and render themselves.
    """

    def __init__(self):
        self._ground_motions: Dict[int, GroundMotion] = {}
        self._start_tag = 1

    def __len__(self) -> int:
        return len(self._ground_motions)

    def __iter__(self) -> Iterator[GroundMotion]:
        return iter(self._ground_motions.values())

    def add(self, ground_motion: GroundMotion) -> GroundMotion:
        """Add a ground motion instance and assign its global tag."""
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

    @forward_signature(PlainGroundMotion)
    def plain(self, **kwargs) -> PlainGroundMotion:
        return self.add(PlainGroundMotion(**kwargs))  # type: ignore[return-value]

    @forward_signature(InterpolatedGroundMotion)
    def interpolated(self, **kwargs) -> InterpolatedGroundMotion:
        return self.add(InterpolatedGroundMotion(**kwargs))  # type: ignore[return-value]

    def get(self, tag: int) -> GroundMotion:
        tag = int(tag)
        if tag not in self._ground_motions:
            raise KeyError(f"No ground motion found with tag {tag}")
        return self._ground_motions[tag]

    def get_all(self) -> Dict[int, GroundMotion]:
        return self._ground_motions.copy()

    def remove(self, tag: int) -> None:
        tag = int(tag)
        if tag in self._ground_motions:
            removed = self._ground_motions.pop(tag)
            removed.tag = None
            self._reassign_tags()

    def clear(self) -> None:
        for ground_motion in self._ground_motions.values():
            ground_motion.tag = None
        self._ground_motions.clear()
        self._start_tag = 1

    def set_tag_start(self, start_tag: int) -> None:
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
