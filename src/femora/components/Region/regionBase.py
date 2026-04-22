from femora.components.Damping.dampingBase import DampingBase
import weakref 
from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union

class RegionBase(ABC):
    """
    Abstract base class for defining regions in a structural model.
    
    RegionBase provides a foundation for defining and managing regions in a structural model,
    which can be used to associate specific properties or behaviors (such as damping) 
    with parts of the model. Regions are automatically tracked with unique tags.
    
    The class maintains a registry of all region instances, including a special "global region"
    with tag 0 that represents the entire model. Regions can be retrieved by their tags,
    and the class ensures that tags remain unique.
    
    Attributes:
        _regions (dict): Class-level dictionary mapping tags to region instances
        _global_region (RegionBase): Reference to the global region instance (tag 0)
        
    Note:
        This is an abstract class. Concrete region implementations should be created
        through subclasses like ElementRegion, NodeRegion, or GlobalRegion.
    """
    _regions = {}  # Dictionary to hold regions
    _global_region = None  # Global region instance

    def __new__(cls, tag=None, damping: Type[DampingBase] = None):
        """
        Control the creation of new region instances to maintain unique tags.
        
        This method ensures that:
        1. If a region with the requested tag already exists, return that instance
        2. If tag=0 is requested, create or return the global region
        3. Otherwise create a new region instance
        
        Args:
            tag (int, optional): Unique identifier for the region
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            
        Returns:
            RegionBase: Either an existing or new region instance
        """
        if tag in cls._regions:
            return cls._regions[tag]
        
        if tag == 0:
            cls._global_region = super().__new__(cls)
            cls._regions[0] = cls._global_region
            return cls._global_region

        # Create a new instance for a unique tag
        instance = super().__new__(cls)
        return instance

    def __init__(self, tag=None, damping: Type[DampingBase] = None):
        """
        Initialize a region with a tag and optional damping.
        
        Args:
            tag (int, optional): Unique identifier for the region. If None, a new tag is assigned.
                                If 0, this creates or references the global region.
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            
        Raises:
            ValueError: If tag=0 is used with a class that is not GlobalRegion
        """
        if tag == 0:
            # check the region is type of global region for tag 0
            if not isinstance(self, GlobalRegion):
                raise ValueError("Region with tag 0 should be of type GlobalRegion \
                                 please use GlobalRegion class to create a global region")
            self._tag = tag
            self._name = "GlobalRegion"
            self._regions[0] = self
            self.damping = damping
        elif tag is None:
            tag = self._get_next_tag()
            self._tag = tag
            self._name = f"region {tag}"
            self._regions[tag] = self
            self.damping = damping

        # Default values
        if not hasattr(self, "active"):
            self.active = True

    @property
    def tag(self):
        """
        Get the unique identifier for this region.
        
        Returns:
            int: The region's tag
        """
        return self._tag
    
    @property
    def name(self):
        """
        Get the name of this region.
        
        Returns:
            str: The region's name
        """
        return self._name
    
    @property
    def damping(self):
        """
        Get the damping behavior assigned to this region.
        
        Returns:
            DampingBase or None: The damping instance, or None if not assigned
        """
        return self._damping() if self._damping else None

    @damping.setter
    def damping(self, value: Optional[Type[DampingBase]]):
        """
        Assign a damping behavior to this region.
        
        Args:
            value (Type[DampingBase], optional): The damping instance to assign
            
        Raises:
            TypeError: If value is not a subclass of DampingBase
        """
        if value is not None and not issubclass(value.__class__, DampingBase):
            raise TypeError("damping must be a subclass of DampingBase")
        self._damping = weakref.ref(value) if value else None 

    @damping.deleter
    def damping(self):
        """Remove the damping behavior from this region."""
        self._damping_ref = None 
        
    def set_damping(self, damping_instance: Type[DampingBase]):
        """
        Set the damping behavior of this region.
        
        This method provides an alternative way to assign damping to a region,
        with the same functionality as the damping property setter.
        
        Args:
            damping_instance (Type[DampingBase], required): The damping instance to assign
            
        Raises:
            TypeError: If damping_instance is not a subclass of DampingBase
        """
        self.damping = damping_instance

    def __str__(self) -> str:
        """
        Get a string representation of this region.
        
        Returns:
            str: A multi-line string describing the region's properties
        """
        type_name = self.get_type()
        res = f"Region class"
        res += f"\n\tTag: {self.tag}"
        res += f"\n\tName: {self.name}"
        res += f"\n\tType: {type_name}"
        res += f"\n\tActive: {self.active}"
        res += f"\n\tDamping: " + ("\n\t" + str(self.damping)).replace("\n", "\n\t") if self.damping else "\n\tDamping: None"
        return res

    @classmethod
    def _get_next_tag(cls):
        """
        Get the next available tag for a new region.
        
        Returns:
            int: Next available tag number
        """
        return len(cls._regions)

    @classmethod
    def _update_tags(cls):
        """
        Update tags and names of all regions except the global region.
        
        This method ensures that region tags remain sequential after
        regions are removed.
        """
        tags = sorted(cls._regions.keys())
        if 0 in tags:
            tags.remove(0)  # Preserve the global region tag
        new_regions = {0: cls._regions[0]} if 0 in cls._regions else {}
        for i, old_tag in enumerate(tags, start=1):
            region = cls._regions[old_tag]
            region._tag = i
            region._name = f"region{i}"
            new_regions[i] = region
        cls._regions = new_regions

    @classmethod
    def remove_region(cls, tag):
        """
        Remove a region by its tag.
        
        Args:
            tag (int): The tag of the region to remove
            
        Raises:
            ValueError: If attempting to remove the global region (tag 0)
        """
        if tag == 0:
            raise ValueError("Cannot remove the global region (tag 0)")
        if tag in cls._regions:
            del cls._regions[tag]
            cls._update_tags()

    @classmethod
    def get_region(cls, tag) -> Optional["RegionBase"]:
        """
        Get a region by its tag.
        
        Args:
            tag (int): The tag of the region to retrieve
            
        Returns:
            RegionBase or None: The region with the specified tag, or None if not found
        """
        return cls._regions.get(tag)

    @classmethod
    def get_all_regions(cls) -> Dict[int, "RegionBase"]:
        """
        Get all registered regions.
        
        Returns:
            Dict[int, RegionBase]: Dictionary mapping tags to region instances
        """
        return cls._regions

    @classmethod
    def clear(cls) -> None:
        """
        Clear all regions, including the global region.
        
        This resets the region registry to an empty state.
        """
        cls._regions = {}
        cls._global_region = None

    @staticmethod
    def print_regions() -> None:
        """
        Print information about all registered regions.
        
        Displays detailed information about each region instance currently registered.
        """
        for tag, region in RegionBase.get_all_regions().items():
            print(region)

    @abstractmethod
    def to_tcl(self) -> str:
        """
        Convert the region to a TCL representation.
        
        Returns:
            str: TCL command string that defines this region
        """
        pass

    @abstractmethod
    def validate(self):
        """
        Validate region parameters.
        
        Raises:
            ValueError: If region parameters are invalid
        """
        pass

    @staticmethod
    @abstractmethod
    def get_Parameters() -> Dict[str, str]:
        """
        Get parameters for the region.
        
        Returns:
            Dict[str, str]: Dictionary mapping parameter names to their types
        """
        pass

    @staticmethod
    @abstractmethod
    def getNotes() -> Dict[str, list[str]]:
        """
        Get notes for the region.
        
        Returns:
            Dict[str, list[str]]: Dictionary containing notes and references for the region
        """
        pass

    @staticmethod
    @abstractmethod
    def get_type(self) -> str:
        """
        Get the type name of this region.
        
        Returns:
            str: The region type name
        """
        pass

    @abstractmethod
    def setComponent(self, component:str, value:list[int]):
        """
        Set components for this region.
        
        Args:
            component (str): The type of component to set
            value (list[int]): List of component values
            
        Raises:
            ValueError: If the component type is invalid for this region
        """
        pass


class GlobalRegion(RegionBase):
    """
    A special region representing the entire structural model.
    
    GlobalRegion is a singleton class that represents the entire model as a region.
    It is automatically created with tag 0 and is used as the default region when
    no specific region is specified.
    
    This class ensures that only one global region exists at any time.
    
    Args:
        damping (Type[DampingBase], optional): Damping behavior to assign to this region
    """
    def __new__(cls, damping: Type[DampingBase] = None):
        """
        Create or return the singleton global region instance.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            
        Returns:
            GlobalRegion: The global region instance (tag 0)
        """
        return super().__new__(cls, tag=0)

    def __init__(self, damping: Type[DampingBase] = None):
        """
        Initialize the global region.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
        """
        super().__init__(tag=0, damping=damping)
        self.elements = None
        self.element_range = None
        self.nodes = None
        self.node_range = None

    def to_tcl(self) -> str:
        """
        TCL representation for global region.
        
        Returns:
            str: TCL command string for the global region
        """
        #return "#region 0"
        return ""

    def validate(self):
        """No validation required for global region."""
        pass

    @staticmethod
    def get_Parameters() -> Dict[str, str]:
        """
        No parameters for global region.
        
        Returns:
            Dict[str, str]: Empty dictionary as global region has no parameters
        """
        return {}

    @staticmethod
    def getNotes() -> Dict[str, list[str]]:
        """
        Notes about global region.
        
        Returns:
            Dict[str, list[str]]: Dictionary containing notes and references for the global region
        """
        return {
            "Notes": [
                "Global region representing entire model"
            ],
            "References": []    
        }
        
    @staticmethod
    def get_type() -> str:
        """
        Get the type name of the global region.
        
        Returns:
            str: Always returns "GlobalRegion"
        """
        return "GlobalRegion"
    
    def setComponent(self, component:str, values:list[int]):
        """
        Set component values for the global region.
        
        The global region can have elements, element ranges, nodes, or node ranges
        assigned to it.
        
        Args:
            component (str): One of "element", "elementRange", "node", "nodeRange"
            values (list[int]): List of element/node IDs or [start, end] range
            
        Raises:
            ValueError: If the component type is invalid or range doesn't have exactly 2 elements
        """
        if component == "element":
            self.elements = values
            self.element_range = None
            self.nodes = None
            self.node_range = None
        elif component == "elementRange":
            if len(values) != 2:
                raise ValueError("element_range should have 2 elements")
            self.element_range = values
            self.elements = None
            self.nodes = None
            self.node_range = None
        elif component == "node":
            self.nodes = values
            self.node_range = None
            self.elements = None
            self.element_range = None
        elif component == "nodeRange":
            if len(values) != 2:
                raise ValueError("node_range should have 2 elements")
            self.node_range = values
            self.nodes = None
            self.elements = None
            self.element_range = None
        else:
            raise ValueError(f"""Invalid component {component} for GlobalRegion
                             valid components are element, elementRange, node, nodeRange""")
        

def initialize_region_base():
    """
    Initialize the RegionBase with the global region.
    
    This function creates the global region (tag 0) if it doesn't exist.
    It's typically called when setting up a new model or resetting the region system.
    """
    GlobalRegion()


class ElementRegion(RegionBase):
    """
    A region defined by a set of elements or an element range.
    
    ElementRegion represents a collection of elements in a structural model
    that can have specific properties or behaviors assigned to them, such as
    damping characteristics. Elements can be specified either as a list of
    individual element IDs or as a continuous range.
    
    Parameters:
        damping (Type[DampingBase], optional): Damping behavior to assign to this region
        **kwargs: Additional parameters including:
            tag (int, optional): Unique identifier for the region
            elements (list[int], optional): List of element IDs to include in the region
            element_range (list[int], optional): Two-element list specifying start and end
                of an element range [start, end]
            element_only (bool, optional): If True, includes only the specified elements
                
    Note:
        Cannot specify both elements and element_range simultaneously
    """
    def __new__(cls, damping: Type[DampingBase] = None, **kwargs):
        """
        Create a new ElementRegion instance.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            **kwargs: Additional parameters including tag, elements, element_range, element_only
            
        Returns:
            ElementRegion: A new ElementRegion instance
        """
        return super().__new__(cls, tag=kwargs.pop("tag", None))
    
    def __init__(self, damping: Type[DampingBase] = None ,**kwargs):
        """
        Initialize an ElementRegion instance.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            **kwargs: Additional parameters including tag, elements, element_range, element_only
            
        Raises:
            ValueError: If both elements and element_range are provided simultaneously
        """
        super().__init__(tag=kwargs.pop("tag", None), damping=damping)
        self.elements = []
        self.element_range = []
        self.element_only = False

        if kwargs:
            validated = self.validate(**kwargs)
            self.elements = validated["elements"]
            self.element_range = validated["element_range"]
            self.element_only = validated["element_only"]

    def to_tcl(self):
        """
        Generate TCL representation for the ElementRegion.
        
        Returns:
            str: TCL command string for the ElementRegion
        """
        cmd = f"eval \"region {self.tag}"
        if len(self.element_range) > 0:
            cmd += " -eleRange {} {}".format(*self.element_range)
            if self.element_only:
                cmd += "Only"
        elif len(self.elements) > 0:
            cmd += " -ele" + ("Only" if self.element_only else "")
            cmd += " " + " ".join(str(e) for e in self.elements)

        if self.damping:
            if self.damping.get_Type() in ["RayleighDamping", "Frequency Rayleigh"]:
                cmd += f" -rayleigh {self.damping.alphaM} {self.damping.betaK} {self.damping.betaKInit} {self.damping.betaKComm}"
            else:
                cmd += f" -damp {self.damping.tag}"
        cmd += "\""
        return cmd
    
    def __str__(self):
        """
        Get a string representation of the ElementRegion.
        
        Returns:
            str: A multi-line string describing the ElementRegion's properties
        """
        res = super().__str__()
        res += f"\n\tNum of Elements: {len(self.elements)}"
        res += f"\n\tElement Range: {self.element_range}"
        res += f"\n\tElement Only: {self.element_only}"
        return res

    @staticmethod
    def get_Parameters():
        """
        Get parameters for the ElementRegion.
        
        Returns:
            Dict[str, str]: Dictionary mapping parameter names to their types
        """
        return {
            "elements": "lineEdit",
            "element_range": "lineEdit",
            "element_only": "checkbox"
        }
    
    @staticmethod
    def getNotes()->Dict[str, list[str]]:
        """
        Get notes for the ElementRegion.
        
        Returns:
            Dict[str, list[str]]: Dictionary containing notes and references for the ElementRegion
        """
        return {
            "Notes": [
                "Use elements list for specific elements: [1, 2, 3, ...]"
                "If you use GUI, use comma separated values 1, 2, 3, ...",
                "Use element_range for a range: [start, end]",
                "If you use GUI, use comma separated values start, end for range",
                "Cannot use both elements and element_range simultaneously",
                "Set element_only=True to include only elements (default is False)",
                "If you use GUI, check the checkbox to include only elements"
            ],
            "References": []
        }

    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, bool, list]]:
        """
        Validate parameters for the ElementRegion.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            Dict[str, Union[str, bool, list]]: Validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        if "elements" in kwargs and "element_range" in kwargs:
            raise ValueError("Both elements and element_range cannot be provided at the same time")
        
        elements = []
        element_range = []
        element_only = False

        if "elements" in kwargs:
            elements = kwargs["elements"]
            if not isinstance(elements, list):
                raise ValueError("elements should be a list of integers")
            for e in elements:
                if not isinstance(e, int):
                    raise ValueError("elements should be a list of integers")
                

        if "element_range" in kwargs:
            element_range = kwargs["element_range"]
            if not isinstance(element_range, list):
                raise ValueError("element_range should be a list of integers")
            if len(element_range) != 2:
                raise ValueError("element_range should have 2 elements")
            for e in element_range:
                if not isinstance(e, int):
                    raise ValueError("element_range should be a list of integers")

        if "element_only" in kwargs:
            element_only = kwargs["element_only"]
            if not isinstance(element_only, bool):
                raise ValueError("element_only should be a boolean")
            
        return {
            "elements": elements,
            "element_range": element_range,
            "element_only": element_only
        }
    
    @staticmethod
    def get_type() -> str:
        """
        Get the type name of the ElementRegion.
        
        Returns:
            str: Always returns "ElementRegion"
        """
        return "ElementRegion"
    
    def setComponent(self, component:str, value:list[int]):
        """
        Set component values for the ElementRegion.
        
        Args:
            component (str): One of "element", "elementRange"
            value (list[int]): List of element IDs or [start, end] range
            
        Raises:
            ValueError: If the component type is invalid or range doesn't have exactly 2 elements
        """
        if component == "element":
            self.elements = value
            self.element_range = []
        elif component == "elementRange":
            if len(value) != 2:
                raise ValueError("element_range should have 2 elements")
            self.element_range = value
            self.elements = []
        else:
            raise ValueError(f"""Invalid component {component} for ElementRegion 
                             valid components are element and elementRange""")


class NodeRegion(RegionBase):
    """
    A region defined by a set of nodes or a node range.
    
    NodeRegion represents a collection of nodes in a structural model
    that can have specific properties or behaviors assigned to them, such as
    damping characteristics. Nodes can be specified either as a list of
    individual node IDs or as a continuous range.
    
    Parameters:
        damping (Type[DampingBase], optional): Damping behavior to assign to this region
        **kwargs: Additional parameters including:
            tag (int, optional): Unique identifier for the region
            nodes (list[int], optional): List of node IDs to include in the region
            node_range (list[int], optional): Two-element list specifying start and end
                of a node range [start, end]
            node_only (bool, optional): If True, includes only the specified nodes
                
    Note:
        Cannot specify both nodes and node_range simultaneously
    """
    def __new__(cls, damping: Type[DampingBase] = None, **kwargs):
        """
        Create a new NodeRegion instance.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            **kwargs: Additional parameters including tag, nodes, node_range, node_only
            
        Returns:
            NodeRegion: A new NodeRegion instance
        """
        return super().__new__(cls, tag=kwargs.pop("tag", None))
    
    def __init__(self, damping: Type[DampingBase] = None, **kwargs):
        """
        Initialize a NodeRegion instance.
        
        Args:
            damping (Type[DampingBase], optional): Damping behavior to assign to this region
            **kwargs: Additional parameters including tag, nodes, node_range, node_only
            
        Raises:
            ValueError: If both nodes and node_range are provided simultaneously
        """
        super().__init__(tag=kwargs.pop("tag", None), damping=damping)
        self.nodes = []
        self.node_range = []
        self.node_only = False
        
        if kwargs:
            validated = self.validate(**kwargs)
            self.nodes = validated["nodes"]
            self.node_range = validated["node_range"]
            self.node_only = validated["node_only"]

    def to_tcl(self):
        """
        Generate TCL representation for the NodeRegion.
        
        Returns:
            str: TCL command string for the NodeRegion
        """
        cmd = f"region {self.tag}"
        if len(self.node_range) > 0:
            cmd += " -node" + ("Only" if self.node_only else "") + "Range"
            cmd += " {} {}".format(*self.node_range)
        elif len(self.nodes) > 0:
            cmd += " -node" + ("Only" if self.node_only else "")
            cmd += " " + " ".join(str(n) for n in self.nodes)

        if self.damping:
            if self.damping.get_Type() in ["RayleighDamping", "Frequency Rayleigh"]:
                cmd += F"-rayleigh {self.damping.alphaM} {self.damping.betaK} {self.damping.betaKInit} {self.damping.betaKComm}"
            else:
                cmd += f"-damp {self.damping.tag}"
        return cmd
    
    def __str__(self):
        """
        Get a string representation of the NodeRegion.
        
        Returns:
            str: A multi-line string describing the NodeRegion's properties
        """
        res = super().__str__()
        res += f"\n\tNum of Nodes: {len(self.nodes)}"
        res += f"\n\tNode Range: {self.node_range}"
        return res

    @staticmethod
    def get_Parameters():
        """
        Get parameters for the NodeRegion.
        
        Returns:
            Dict[str, str]: Dictionary mapping parameter names to their types
        """
        return {
            "nodes": "lineEdit",
            "node_range": "lineEdit"
        }

    @staticmethod
    def getNotes()->Dict[str, list[str]]:
        """
        Get notes for the NodeRegion.
        
        Returns:
            Dict[str, list[str]]: Dictionary containing notes and references for the NodeRegion
        """
        return {
            "Notes": [
                "Use nodes list for specific nodes: [1, 2, 3, ...]",
                "If you use GUI, use comma separated values 1, 2, 3, ...",
                "Use node_range for a range: [start, end]",
                "If you use GUI, use comma separated values start, end for range",
                "Cannot use both nodes and node_range simultaneously",
                "Set node_only=True to include only nodes (default is False)",
                "If you use GUI, check the checkbox to include only nodes",
            ],
            "References": []
        }

    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list]]:
        """
        Validate parameters for the NodeRegion.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            Dict[str, Union[str, list]]: Validated parameters
            
        Raises:
            ValueError: If parameters are invalid
        """
        if "nodes" in kwargs and "node_range" in kwargs:
            raise ValueError("Both nodes and node_range cannot be provided at the same time")
        
        nodes = []
        node_range = []
        node_only = False

        if "nodes" in kwargs:
            nodes = kwargs["nodes"]
            if not isinstance(nodes, list):
                raise ValueError("nodes should be a list of integers")
            for n in nodes:
                if not isinstance(n, int):
                    raise ValueError("nodes should be a list of integers")

        if "node_range" in kwargs:
            node_range = kwargs["node_range"]
            if not isinstance(node_range, list):
                raise ValueError("node_range should be a list of integers")
            if len(node_range) != 2:
                raise ValueError("node_range should have 2 elements")
            for n in node_range:
                if not isinstance(n, int):
                    raise ValueError("node_range should be a list of integers")
                
        if "node_only" in kwargs:
            node_only = kwargs["node_only"]
            if not isinstance(node_only, bool):
                raise ValueError("node_only should be a boolean")
            
        return {
            "nodes": nodes,
            "node_range": node_range,
            "node_only": node_only
        }

    @staticmethod
    def get_type() -> str:
        """
        Get the type name of the NodeRegion.
        
        Returns:
            str: Always returns "NodeRegion"
        """
        return "NodeRegion"
    
    def setComponent(self, component:str, value:list[int]):
        """
        Set component values for the NodeRegion.
        
        Args:
            component (str): One of "node", "nodeRange"
            value (list[int]): List of node IDs or [start, end] range
            
        Raises:
            ValueError: If the component type is invalid or range doesn't have exactly 2 elements
        """
        if component == "node":
            self.nodes = value
            self.node_range = []
        elif component == "nodeRange":
            if len(value) != 2:
                raise ValueError("node_range should have 2 elements")
            self.node_range = value
            self.nodes = []
        else:
            raise ValueError(f"""Invalid component {component} for NodeRegion
                             valid components are node and nodeRange""")


class RegionManager:
    """
    A centralized manager for all region instances in MeshMaker.
    
    The RegionManager implements the Singleton pattern to ensure a single, consistent
    point of region management across the entire application. It provides methods for
    creating, retrieving, and managing region objects used to define specific parts
    of structural models for analysis and damping assignments.
    
    All region objects created through this manager are automatically tracked and tagged,
    simplifying the process of defining and managing model regions. A special GlobalRegion
    with tag 0 is automatically created when the RegionManager is initialized.
    """
    _instance = None
    def __new__(cls):
        """
        Create a new RegionManager instance or return the existing one if already created.
        
        Returns:
            RegionManager: The singleton instance of the RegionManager
        """
        if cls._instance is None:
            cls._instance = super(RegionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the RegionManager and create the GlobalRegion.
        
        This method ensures that the global region (tag 0) is automatically created
        when the RegionManager is initialized. The initialization only happens once
        due to the singleton pattern.
        """
        if not self._initialized:
            self._initialized = True
            initialize_region_base()

        self.elementRegion = ElementRegion
        self.nodeRegion = NodeRegion
        self.globalRegion = GlobalRegion()

    @property
    def regions(self):
        """
        Get all regions as a dictionary mapping tags to region instances.
        
        Returns:
            Dict[int, RegionBase]: A dictionary mapping tags to region instances
        """
        return RegionBase.get_all_regions()

    def get_region(self, tag):
        """
        Get a region by its tag.
        
        Args:
            tag (int): The unique identifier of the region instance
            
        Returns:
            RegionBase: The region instance with the specified tag, or None if not found
        """
        return RegionBase.get_region(tag)
    
    def create_region(self, regionType: str, damping=None, **kwargs):
        """
        Create a new region instance of the specified type.
        
        This method creates and returns a new region object based on the provided type
        and parameters. The region is automatically registered and tracked.
        
        Args:
            regionType (str): The type of region to create. Available types include:
                'ElementRegion': A region defined by a set of elements or element range
                'NodeRegion': A region defined by a set of nodes or node range
                'GlobalRegion': The global region representing the entire model
            damping: Optional damping instance to associate with the region
            **kwargs: Specific parameters for the region type being created
                (e.g., elements, element_range for ElementRegion,
                nodes, node_range for NodeRegion)
        
        Returns:
            RegionBase: A new instance of the requested region type
            
        Raises:
            ValueError: If the region type is unknown or if required parameters are missing or invalid
        """
        if regionType.lower() == "elementregion":
            return ElementRegion(damping=damping, **kwargs)
        elif regionType.lower() == "noderegion":
            return NodeRegion(damping=damping, **kwargs)
        elif regionType.lower() == "globalregion":
            return GlobalRegion(damping=damping)
        else:
            raise ValueError(f"""Invalid region type {regionType}
                             valid region types are ElementRegion, NodeRegion, GlobalRegion""")

    def remove_region(self, tag):
        """
        Remove a region by its tag.
        
        This method removes the specified region instance and automatically
        updates the tags of the remaining region instances to maintain sequential numbering.
        The GlobalRegion (tag 0) cannot be removed.
        
        Args:
            tag (int): The unique identifier of the region instance to remove
            
        Raises:
            ValueError: If attempting to remove the GlobalRegion (tag 0)
        """
        RegionBase.remove_region(tag)

    def clear_regions(self):
        """
        Remove all regions and reinitialize the GlobalRegion.
        
        This method clears all region instances, including the GlobalRegion,
        and then recreates the GlobalRegion with tag 0.
        """
        RegionBase.clear()
        initialize_region_base()

    def print_regions(self):
        """
        Print information about all regions.
        
        This method prints detailed information about all region instances
        including their tags, types, elements/nodes, and damping assignments.
        """
        RegionBase.print_regions()

    def GlobalRegion(self):
        """
        Get the GlobalRegion instance.
        
        Returns:
            GlobalRegion: The global region instance
        """
        return RegionBase.get_region(0)
    
    def clear(self):
        """
        Clear all regions and reinitialize the GlobalRegion.
        
        This method is an alias for clear_regions() to provide a more intuitive
        interface for clearing all regions.
        """
        self.clear_regions()
    
    
if __name__ == "__main__":
    from femora.components.Damping.dampingBase import RayleighDamping, ModalDamping
    # ---- Test Global Region ----
    # test the DampingBase class
    damping1 = DampingBase()
    damping2 = DampingBase()
    damping3 = DampingBase()

    RayleighDamping1 = RayleighDamping(alphaM=0.1, betaK=0.2, betaKInit=0.3, betaKComm=0.4)
    RayleighDamping2 = RayleighDamping(alphaM=0.5, betaK=0.6, betaKInit=0.7, betaKComm=0.8)
    ModalDamping1 = ModalDamping(numberofModes=2, dampingFactors="0.1,0.2")
    ModalDamping2 = ModalDamping(numberofModes=3, dampingFactors="0.3,0.4,0.5")

    initialize_region_base()
    global_region = RegionBase.get_region(0)
    global_region2 = GlobalRegion()
    global_region3 = GlobalRegion()



    assert global_region == global_region2, "Global regions should be equal"
    assert global_region is global_region3, "Global regions should be the same instance"
    assert global_region is not None, "Global region should exist"
    assert global_region.tag == 0, "Global region tag should be 0"
    assert global_region.name == "GlobalRegion", "Global region name incorrect"
    global_region.damping = DampingBase.get_damping(4)


    eleregion1 = ElementRegion(elements=[1, 2, 3])
    print("Global Region tests passed")



    eleregion1 = ElementRegion(elements=[1, 2, 3])
    eleregion2 = ElementRegion(element_range=[4, 10])
    eleregion4 = ElementRegion()
    eleregion5 = ElementRegion(tag=0)

    # Test Element Regions
    assert eleregion1.tag == 2, "Element region 1 tag should be 1"
    assert eleregion2.tag == 3, "Element region 2 tag should be 2"
    assert len(eleregion1.elements) == 3, "Element region 1 should have 3 elements"
    assert eleregion2.element_range == [4, 10], "Element region 2 range incorrect"
    eleregion3 = ElementRegion(tag=2)
    assert eleregion3.tag == 2, "Element region 3 tag should be 2"
    assert len(eleregion3.elements) == 0, "Element region 3 should have 0 elements"
    print("Element Region tests passed")

    # Test Node Regions
    noderegion1 = NodeRegion(nodes=[1, 2, 3])
    noderegion2 = NodeRegion(node_range=[4, 10])

    assert noderegion1.tag == 5, "Node region 1 tag should be 3"
    assert noderegion2.tag == 6, "Node region 2 tag should be 4"
    assert len(noderegion1.nodes) == 3, "Node region 1 should have 3 nodes"
    assert noderegion2.node_range == [4, 10], "Node region 2 range incorrect"
    noderegion3 = NodeRegion(tag=5)
    assert noderegion3.tag == 5, "Node region 3 tag should be 3"
    print("Node Region tests passed")

    # Test region removal and tag updates
    # Test removing global region (should raise ValueError)
    try:
        RegionBase.remove_region(0)
        assert False, "Should have raised ValueError"
    except ValueError:
        assert True

    # assign with damping 
    eleDamping = ElementRegion(elements=[1, 2, 4], damping=RayleighDamping1)
    nodeDamping = NodeRegion(nodes=[1, 2, 4], damping=ModalDamping1)
    baseDamping = GlobalRegion(damping=RayleighDamping1)
    # print(eleDamping)
    # print(nodeDamping)
    # print(baseDamping)

    print("Region assignment with damping passed")
    
    # Test damping assignment
    noderegion1.damping = RayleighDamping2
    assert noderegion1.damping is not None, "Damping should be assigned"
    print("Damping assignment test passed")

    print("\nAll tests passed successfully!")

