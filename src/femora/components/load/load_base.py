from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Union, Any, Tuple, TYPE_CHECKING


class Load(ABC):
    """
    Base abstract class for all load types (node, element, sp).

    A `Load` represents a single OpenSees command that is intended to be
    placed inside a `pattern Plain { ... }` block. Loads do not carry a
    `TimeSeries`; the enclosing `Plain` pattern provides it.
    """

    _loads: Dict[int, "Load"] = {}
    _next_tag: int = 1

    def __init__(self, load_type: str):
        self.tag: int = Load._next_tag
        Load._next_tag += 1

        self.load_type: str = load_type
        self.pattern_tag: Optional[int] = None

        Load._loads[self.tag] = self

    # -------------------------------
    # Registry helpers
    # -------------------------------
    @classmethod
    def get_load(cls, tag: int) -> "Load":
        if tag not in cls._loads:
            raise KeyError(f"No load found with tag {tag}")
        return cls._loads[tag]

    @classmethod
    def remove_load(cls, tag: int) -> None:
        if tag in cls._loads:
            del cls._loads[tag]

    @classmethod
    def get_all_loads(cls) -> Dict[int, "Load"]:
        return cls._loads

    @classmethod
    def clear_all(cls) -> None:
        cls._loads.clear()
        cls._next_tag = 1

    # -------------------------------
    # Required interface
    # -------------------------------
    @staticmethod
    @abstractmethod
    def get_parameters() -> List[tuple]:
        """Return a list of (name, description) for UI/metadata."""
        raise NotImplementedError

    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list, tuple]]:
        """Return a serializable dictionary of current properties."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def validate(**kwargs) -> Dict[str, Any]:
        """Validate constructor/update args and return normalized values."""
        raise NotImplementedError

    @abstractmethod
    def update_values(self, **kwargs) -> None:
        """Update this load's properties after validation."""
        raise NotImplementedError

    @abstractmethod
    def to_tcl(self) -> str:
        """Render the OpenSees TCL command for this load."""
        raise NotImplementedError


class LoadRegistry:
    """
    Registry to manage available load types for creation by name.
    """

    _types: Dict[str, Type[Load]] = {}

    @classmethod
    def register_load_type(cls, name: str, load_class: Type[Load]) -> None:
        cls._types[name.lower()] = load_class

    @classmethod
    def get_load_types(cls) -> List[str]:
        return list(cls._types.keys())

    @classmethod
    def create_load(cls, load_type: str, **kwargs) -> Load:
        key = load_type.lower()
        if key not in cls._types:
            raise KeyError(f"Load type {load_type} not registered")
        return cls._types[key](**kwargs)  # type: ignore[misc]


class LoadManager:
    """
    Singleton facade around `Load` and `LoadRegistry`.
    """

    _instance: Optional["LoadManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoadManager, cls).__new__(cls)
        return cls._instance

    def create_load(self, load_type: str, **kwargs) -> Load:
        return LoadRegistry.create_load(load_type, **kwargs)

    def get_load(self, tag: int) -> Load:
        return Load.get_load(tag)

    def remove_load(self, tag: int) -> None:
        Load.remove_load(tag)

    def get_all_loads(self) -> Dict[int, Load]:
        return Load.get_all_loads()

    def clear_all(self) -> None:
        Load.clear_all()

    def get_available_types(self) -> List[str]:
        return LoadRegistry.get_load_types()

    # -------------------------------
    # Convenience class accessors (return class objects, not instances)
    # -------------------------------
    if TYPE_CHECKING:
        from .node_load import NodeLoad
        from .element_load import ElementLoad
        from .sp_load import SpLoad

    @property
    def node(self) -> 'Type[NodeLoad]':
        """
        Access the NodeLoad class.

        Example:
            lm.node(node_tag=3, values=[0.0, -50.0])
        """
        from .node_load import NodeLoad  # local import to avoid cycles
        return NodeLoad

    @property
    def element(self) -> 'Type[ElementLoad]':
        """
        Access the ElementLoad class.

        Example:
            lm.element(kind="beamUniform", ele_tags=[3], params={"Wy": -200.0})
        """
        from .element_load import ElementLoad  # local import to avoid cycles
        return ElementLoad

    # Alias
    @property
    def ele(self) -> 'Type[ElementLoad]':
        return self.element

    @property
    def sp(self) -> 'Type[SpLoad]':
        """
        Access the SpLoad class.

        Example:
            lm.sp(node_tag=4, dof=2, value=-100.0)
        """
        from .sp_load import SpLoad  # local import to avoid cycles
        return SpLoad


