from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from femora.components.pattern.h5drm_pattern import H5DRMPattern
from femora.components.pattern.multiple_support import MultipleSupportPattern
from femora.components.pattern.plain_pattern import PlainPattern
from femora.components.pattern.uniform_excitation import UniformExcitation
from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class PatternManager:
    """Local manager for ``Pattern`` lifecycle and tag assignment.

    The manager is intentionally not a singleton. Each instance owns an
    independent pattern tag space for one model context.
    """

    def __init__(self):
        """Create an empty manager with pattern tags starting at ``1``."""
        self._patterns: Dict[int, Pattern] = {}
        self._start_tag = 1

    def add(self, pattern: Pattern) -> Pattern:
        """Add an existing pattern and assign a tag if needed.

        Args:
            pattern: Unmanaged or already-managed ``Pattern`` instance.

        Returns:
            The same ``pattern`` instance after it is stored by this manager.

        Raises:
            TypeError: If ``pattern`` is not a ``Pattern`` instance.
            ValueError: If its preassigned tag conflicts with a different
                object already managed here.
        """
        if not isinstance(pattern, Pattern):
            raise TypeError("pattern must be a Pattern instance")
        if pattern.tag is None:
            pattern.tag = self._next_available_tag()
        elif pattern.tag in self._patterns and self._patterns[pattern.tag] is not pattern:
            raise ValueError(f"Pattern tag {pattern.tag} already exists")
        self._patterns[pattern.tag] = pattern
        self._sync_attached_load_tags(pattern)
        return pattern

    def get(self, tag: int) -> Optional[Pattern]:
        """Return the pattern with ``tag`` if it exists.

        Args:
            tag: Pattern tag to look up.

        Returns:
            The matching ``Pattern`` instance, or ``None``.
        """
        return self._patterns.get(tag)

    def get_all(self) -> Dict[int, Pattern]:
        """Return a shallow copy of all managed patterns keyed by tag."""
        return dict(self._patterns)

    def remove(self, tag: int) -> None:
        """Remove a managed pattern and compact the remaining tags.

        Args:
            tag: Tag of the pattern to remove. Missing tags are ignored.
        """
        pattern = self._patterns.pop(tag, None)
        if pattern is not None:
            pattern.tag = None
            self._reassign_tags()

    def clear(self) -> None:
        """Remove all patterns and clear their assigned tags."""
        for pattern in self._patterns.values():
            pattern.tag = None
        self._patterns.clear()

    def set_tag_start(self, start_tag: int) -> None:
        """Set the first tag used by this manager and retag existing patterns.

        Args:
            start_tag: Positive integer for the first assigned pattern tag.

        Raises:
            ValueError: If ``start_tag`` is less than ``1``.
        """
        start_tag = int(start_tag)
        if start_tag < 1:
            raise ValueError("start_tag must be a positive integer")
        self._start_tag = start_tag
        self._reassign_tags()

    def uniform_excitation(
        self,
        dof: int,
        time_series: TimeSeries,
        vel0: float = 0.0,
        factor: float = 1.0,
    ) -> UniformExcitation:
        """Create and manage a ``UniformExcitation`` pattern.

        Args:
            dof: 1-based DOF direction for the uniform excitation.
            time_series: Managed acceleration ``TimeSeries``.
            vel0: Initial velocity.
            factor: Scale factor applied to the time series.

        Returns:
            Managed ``UniformExcitation`` instance.
        """
        return self.add(UniformExcitation(dof, time_series, vel0, factor))  # type: ignore[return-value]

    def h5drm(
        self,
        filepath: str,
        factor: float,
        crd_scale: float,
        distance_tolerance: float,
        do_coordinate_transformation: int,
        transform_matrix: Optional[Sequence[float]] = None,
        origin: Optional[Sequence[float]] = None,
        **kwargs,
    ) -> H5DRMPattern:
        """Create and manage an ``H5DRMPattern``.

        Args:
            filepath: Path to the H5DRM dataset file.
            factor: Scale factor for DRM forces and displacements.
            crd_scale: Coordinate scale factor for the DRM dataset.
            distance_tolerance: Node matching tolerance.
            do_coordinate_transformation: ``0`` or ``1`` flag for coordinate
                transformation.
            transform_matrix: Optional 9-value transformation matrix. If not
                provided, ``T00`` through ``T22`` can be supplied in ``kwargs``.
            origin: Optional 3-value transformed origin. If not provided,
                ``x00`` through ``x02`` can be supplied in ``kwargs``.
            **kwargs: Compatibility support for individual matrix/origin values.

        Returns:
            Managed ``H5DRMPattern`` instance.
        """
        return self.add(
            H5DRMPattern(
                filepath=filepath,
                factor=factor,
                crd_scale=crd_scale,
                distance_tolerance=distance_tolerance,
                do_coordinate_transformation=do_coordinate_transformation,
                transform_matrix=transform_matrix,
                origin=origin,
                **kwargs,
            )
        )  # type: ignore[return-value]

    def plain(self, time_series: TimeSeries, factor: float = 1.0) -> PlainPattern:
        """Create and manage a ``PlainPattern``.

        Args:
            time_series: Managed ``TimeSeries`` referenced by the pattern.
            factor: Optional scale factor for all loads in the pattern.

        Returns:
            Managed ``PlainPattern`` instance.
        """
        return self.add(PlainPattern(time_series, factor))  # type: ignore[return-value]

    def multiple_support(self) -> MultipleSupportPattern:
        """Create and manage a ``MultipleSupportPattern``.

        Returns:
            Managed empty ``MultipleSupportPattern`` instance.
        """
        return self.add(MultipleSupportPattern())  # type: ignore[return-value]

    def create_pattern(self, pattern_type: str, **kwargs) -> Pattern:
        """Create and manage a pattern by type name.

        This compatibility factory delegates to the explicit factory methods
        such as :meth:`plain`, :meth:`uniform_excitation`, and
        :meth:`multiple_support`.

        Args:
            pattern_type: Case-insensitive pattern type name.
            **kwargs: Constructor arguments for the selected concrete class.

        Returns:
            Managed ``Pattern`` instance.

        Raises:
            KeyError: If ``pattern_type`` is not registered.
        """
        factories = {
            "uniformexcitation": self.uniform_excitation,
            "uniform_excitation": self.uniform_excitation,
            "h5drm": self.h5drm,
            "plain": self.plain,
            "multiplesupport": self.multiple_support,
            "multiple_support": self.multiple_support,
        }
        key = pattern_type.lower()
        if key not in factories:
            raise KeyError(f"Pattern type {pattern_type} not registered")
        return factories[key](**kwargs)

    get_pattern = get
    remove_pattern = remove
    get_all_patterns = get_all

    def _next_available_tag(self) -> int:
        """Return the next unused pattern tag in this manager's tag space."""
        tag = self._start_tag
        while tag in self._patterns:
            tag += 1
        return tag

    def _reassign_tags(self) -> None:
        """Retag all managed patterns from ``_start_tag`` in tag order."""
        items: List[Pattern] = sorted(
            self._patterns.values(),
            key=lambda item: item.tag if item.tag is not None else 0,
        )
        self._patterns.clear()
        for offset, pattern in enumerate(items):
            pattern.tag = self._start_tag + offset
            self._patterns[pattern.tag] = pattern
            self._sync_attached_load_tags(pattern)

    def _sync_attached_load_tags(self, pattern: Pattern) -> None:
        """Keep loads attached to a plain pattern aligned with its current tag."""
        get_loads = getattr(pattern, "get_loads", None)
        if get_loads is None:
            return
        for load in get_loads():
            load.pattern_tag = pattern.tag
