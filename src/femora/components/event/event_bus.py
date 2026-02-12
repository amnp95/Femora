from enum import Enum, auto
from collections import defaultdict
from typing import Callable, Dict, List


class FemoraEvent(Enum):
    """Standard signals that core Femora components emit.

    Components may add their own events later, but these cover the interface
    life-cycle we need right now.
    """

    PRE_ASSEMBLE = auto()           # Before any mesh merge (reserved, not used yet)
    POST_ASSEMBLE = auto()          # The assembled mesh exists – may still be unpartitioned
    PRE_EXPORT = auto()             # Just before MeshMaker starts writing nodes/elements
    POST_EXPORT = auto()            # After all nodes/elements are written (reserved, not used yet)
    RESOLVE_CORE_CONFLICTS = auto()         # Core arrays are final
    EMBEDDED_BEAM_SOLID_TCL = auto()       # Embedded beam solid interface (TCL export)
    INTERFACE_ELEMENTS_TCL = auto()       # Interface elements (TCL export)


class EventBus:
    """Very small pub/sub helper – no third-party dependencies."""

    _subscribers: Dict[FemoraEvent, List[Callable]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event: FemoraEvent, callback: Callable) -> None:
        """Register *callback* for *event* if not already present."""
        if callback not in cls._subscribers[event]:
            cls._subscribers[event].append(callback)

    @classmethod
    def emit(cls, event: FemoraEvent, **payload):
        """Call all subscribers for *event* with the given *payload* dict."""
        for cb in list(cls._subscribers[event]):  # copy to prevent mutation issues
            cb(**payload)
            # try:
            #     cb(**payload)
            # except Exception as exc:
            #     # Interfaces shouldn’t crash the export; report and continue.
            #     print(f"[EventBus] subscriber {cb} raised: {exc}") 