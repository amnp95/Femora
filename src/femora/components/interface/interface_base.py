from abc import ABC
from typing import List, Dict, Optional
from femora.components.event.event_bus import FemoraEvent, EventBus

class InterfaceBase(ABC):
    """Common logic for all interface objects."""

    _registry: dict[str, "InterfaceBase"] = {}

    def __init__(self, name: str, owners: List[str]):
        if name in InterfaceBase._registry:
            raise ValueError(f"Interface with name '{name}' already exists")
        self.name = name
        self.owners = owners  # could be meshpart names or other ids
        InterfaceBase._registry[name] = self
        self._subscribe_events()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _subscribe_events(self):
        EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        EventBus.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        EventBus.subscribe(FemoraEvent.RESOLVE_CORE_CONFLICTS, self._on_resolve_core_conflicts)
        EventBus.subscribe(FemoraEvent.PRE_EXPORT, self._on_pre_export)
        EventBus.subscribe(FemoraEvent.POST_EXPORT, self._on_post_export)
        EventBus.subscribe(FemoraEvent.INTERFACE_ELEMENTS_TCL, self._on_interface_tcl_export)

    # The following are intentionally no-ops; subclasses/mix-ins may override
    def _on_pre_assemble(self, **payload):
        pass

    def _on_post_assemble(self, **payload):
        pass

    def _on_pre_export(self, **payload):
        pass

    def _on_post_export(self, **payload):
        pass

    def _on_resolve_core_conflicts(self, **payload):
        pass
    
    def _on_interface_tcl_export(self, **payload):
        pass
    # ------------------------------------------------------------------
    # Helper class-methods
    # ------------------------------------------------------------------
    @classmethod
    def get(cls, name: str):
        return cls._registry.get(name)

    @classmethod
    def all(cls):
        return cls._registry.copy() 
    


class InterfaceManager:
    """Singleton that keeps track of all InterfaceBase objects."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
        from femora.components.interface.embedded_node_interface import EmbeddedNodeInterface
        self.beam_solid_interface = EmbeddedBeamSolidInterface
        self.node_interface = EmbeddedNodeInterface


    # Public helpers ----------------------------------------------------
    def create_interface(self, interface_cls, *args, **kwargs) -> InterfaceBase:
        """Helper that instantiates *interface_cls* and returns it."""
        if not issubclass(interface_cls, InterfaceBase):
            raise TypeError("interface_cls must be a subclass of InterfaceBase")
        return interface_cls(*args, **kwargs)

    def get(self, name: str) -> Optional[InterfaceBase]:
        return InterfaceBase.get(name)

    def all(self) -> Dict[str, InterfaceBase]:
        return InterfaceBase.all()