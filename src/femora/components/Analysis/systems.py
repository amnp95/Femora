from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import abstractmethod

class System(AnalysisComponent):
    """Base abstract class for a system of linear equations.

    This class provides a common interface and management for different
    system types used in numerical analysis, such as sparse or banded solvers.
    It includes mechanisms for registering, creating, and tracking
    system instances globally.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system (e.g., "FullGeneral", "Umfpack").

    Example:
        >>> import femora as fm
        >>> class MyCustomSystem(fm.System):
        ...     def __init__(self):
        ...         super().__init__("MyCustom")
        ...     def get_values(self):
        ...         return {"foo": "bar"}
        ...     def to_tcl(self):
        ...         return "system MyCustom"
        >>> fm.System.register_system("mycustom", MyCustomSystem)
        >>> my_sys = fm.System.create_system("mycustom")
        >>> print(my_sys.system_type)
        MyCustom
        >>> print(my_sys.tag)
        1
    """
    _systems = {}  # Class-level dictionary to store system types
    _created_systems = {}  # Class-level dictionary to track all created systems
    _next_tag = 1  # Class variable to track the next tag to assign
    
    def __init__(self, system_type: str):
        """Initializes a System instance.

        Args:
            system_type: The string identifier for the type of system
                to be created (e.g., "FullGeneral").

        Example:
            >>> import femora as fm
            >>> # This example would typically involve a concrete subclass
            >>> # Here, we assume 'fullgeneral' is already registered.
            >>> system = fm.System.create_system("fullgeneral")
            >>> print(system.system_type)
            FullGeneral
        """
        self.tag = System._next_tag
        System._next_tag += 1
        self.system_type = system_type
        
        # Register this system in the class-level tracking dictionary
        System._created_systems[self.tag] = self
    
    @staticmethod
    def register_system(name: str, system_class: Type['System']):
        """Registers a system type with a given name.

        This allows new system implementations to be dynamically added
        and created via `System.create_system`.

        Args:
            name: The string name to register the system under.
                This name is case-insensitive when creating systems.
            system_class: The class object of the system to register.

        Example:
            >>> import femora as fm
            >>> class DummySystem(fm.System):
            ...     def __init__(self):
            ...         super().__init__("Dummy")
            ...     def get_values(self): return {}
            ...     def to_tcl(self): return "system Dummy"
            >>> fm.System.register_system("dummy", DummySystem)
            >>> print("dummy" in fm.System.get_available_types())
            True
        """
        System._systems[name.lower()] = system_class
    
    @staticmethod
    def create_system(system_type: str, **kwargs) -> 'System':
        """Creates a new system instance of the specified type.

        Args:
            system_type: The string identifier for the type of system to create.
                This should correspond to a name registered via `register_system`.
            **kwargs: Additional keyword arguments passed directly to the
                constructor of the specific system class.

        Returns:
            System: An instance of the requested system type.

        Raises:
            ValueError: If an unknown system type is requested.

        Example:
            >>> import femora as fm
            >>> # Assuming 'fullgeneral' is registered by default
            >>> sys_fg = fm.System.create_system("fullgeneral")
            >>> print(sys_fg.system_type)
            FullGeneral
            >>> sys_mumps = fm.System.create_system("mumps", icntl14=1.2)
            >>> print(sys_mumps.icntl14)
            1.2
        """
        system_type = system_type.lower()
        if system_type not in System._systems:
            raise ValueError(f"Unknown system type: {system_type}")
        return System._systems[system_type](**kwargs)
    
    @staticmethod
    def get_available_types() -> List[str]:
        """Retrieves a list of all currently registered system types.

        Returns:
            List[str]: A list of string names for available system types.

        Example:
            >>> import femora as fm
            >>> types = fm.System.get_available_types()
            >>> print("fullgeneral" in types)
            True
            >>> print("nonexistent" in types)
            False
        """
        return list(System._systems.keys())
    
    @classmethod
    def get_system(cls, tag: int) -> 'System':
        """Retrieves a specific system instance by its unique tag.

        Args:
            tag: The unique integer ID of the system to retrieve.

        Returns:
            System: The system instance associated with the given tag.

        Raises:
            KeyError: If no system with the given tag exists.

        Example:
            >>> import femora as fm
            >>> fm.System.clear_all() # Ensure clean state for example
            >>> sys1 = fm.System.create_system("fullgeneral") # tag 1
            >>> sys2 = fm.System.create_system("bandgeneral") # tag 2
            >>> retrieved_sys = fm.System.get_system(sys1.tag)
            >>> print(retrieved_sys.system_type)
            FullGeneral
            >>> try:
            ...     fm.System.get_system(999)
            ... except KeyError as e:
            ...     print(e)
            No system found with tag 999
        """
        if tag not in cls._created_systems:
            raise KeyError(f"No system found with tag {tag}")
        return cls._created_systems[tag]

    @classmethod
    def get_all_systems(cls) -> Dict[int, 'System']:
        """Retrieves a dictionary of all created system instances.

        Returns:
            Dict[int, System]: A dictionary where keys are system tags
                and values are the corresponding System instances.

        Example:
            >>> import femora as fm
            >>> fm.System.clear_all() # Start with a clean slate for example
            >>> sys1 = fm.System.create_system("fullgeneral")
            >>> sys2 = fm.System.create_system("bandgeneral")
            >>> all_systems = fm.System.get_all_systems()
            >>> print(len(all_systems))
            2
            >>> print(all_systems[sys1.tag].system_type)
            FullGeneral
        """
        return cls._created_systems
    
    @classmethod
    def clear_all(cls) -> None:
        """Clears all created system instances and resets the tag counter.

        This effectively removes all systems from memory and resets the
        system management state, causing new systems to start tagging from 1.

        Example:
            >>> import femora as fm
            >>> sys1 = fm.System.create_system("fullgeneral")
            >>> print(len(fm.System.get_all_systems()))
            1
            >>> fm.System.clear_all()
            >>> print(len(fm.System.get_all_systems()))
            0
            >>> sys2 = fm.System.create_system("bandgeneral")
            >>> print(sys2.tag) # Tags restart from 1
            1
        """
        cls._created_systems.clear()
        cls._next_tag = 1
    
    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Abstract method to retrieve the parameters defining this system.

        Concrete subclasses must implement this method to expose their
        specific configuration values.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of
                parameter names and their current values.

        Example:
            >>> import femora as fm
            >>> sys_mumps = fm.System.create_system("mumps", icntl14=1.5, icntl7=0)
            >>> values = sys_mumps.get_values()
            >>> print(values["icntl14"])
            1.5
            >>> print(values["icntl7"])
            0
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all systems sequentially starting from 1.

        This private method is used internally after a system is removed
        to ensure that existing systems maintain consecutive tags.
        """
        new_systems = {}
        for idx, system in enumerate(sorted(cls._created_systems.values(), key=lambda s: s.tag), start=1):
            system.tag = idx
            new_systems[idx] = system
        cls._created_systems = new_systems
        cls._next_tag = len(cls._created_systems) + 1

    @classmethod
    def remove_system(cls, tag: int) -> None:
        """Deletes a system instance by its tag and re-tags remaining systems.

        When a system is removed, all remaining systems are re-assigned
        sequential tags starting from 1 to maintain a compact sequence
        of identifiers.

        Args:
            tag: The tag of the system instance to delete.

        Example:
            >>> import femora as fm
            >>> fm.System.clear_all()
            >>> sys1 = fm.System.create_system("fullgeneral") # tag 1
            >>> sys2 = fm.System.create_system("bandgeneral") # tag 2
            >>> sys3 = fm.System.create_system("bandspd")     # tag 3
            >>> fm.System.remove_system(sys2.tag)
            >>> print(len(fm.System.get_all_systems()))
            2
            >>> # Tags are reassigned: sys1 becomes tag 1, sys3 becomes tag 2
            >>> print(fm.System.get_system(1).system_type)
            FullGeneral
            >>> print(fm.System.get_system(2).system_type)
            BandSPD
        """
        if tag in cls._created_systems:
            del cls._created_systems[tag]
            cls._reassign_tags()


class FullGeneralSystem(System):
    """Represents a full general system solver.

    This system type does not employ any optimizations and uses a full
    matrix storage and solution scheme. It is generally not recommended
    for large problems due to its high memory and computational cost.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "FullGeneral".

    Example:
        >>> import femora as fm
        >>> system = fm.FullGeneralSystem()
        >>> print(system.system_type)
        FullGeneral
    """
    def __init__(self):
        """Initializes a FullGeneralSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.FullGeneralSystem()
            >>> print(system.system_type)
            FullGeneral
        """
        super().__init__("FullGeneral")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the FullGeneralSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.FullGeneralSystem()
            >>> print(system.to_tcl())
            system FullGeneral
        """
        return "system FullGeneral"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For FullGeneralSystem, there are no specific parameters to report.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> system = fm.FullGeneralSystem()
            >>> print(system.get_values())
            {}
        """
        return {}


class BandGeneralSystem(System):
    """Represents a band general system solver.

    This system uses a banded matrix storage scheme, which can be more
    memory-efficient than a full general system for matrices with a
    limited bandwidth.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "BandGeneral".

    Example:
        >>> import femora as fm
        >>> system = fm.BandGeneralSystem()
        >>> print(system.system_type)
        BandGeneral
    """
    def __init__(self):
        """Initializes a BandGeneralSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.BandGeneralSystem()
            >>> print(system.system_type)
            BandGeneral
        """
        super().__init__("BandGeneral")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the BandGeneralSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.BandGeneralSystem()
            >>> print(system.to_tcl())
            system BandGeneral
        """
        return "system BandGeneral"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For BandGeneralSystem, there are no specific parameters to report.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> system = fm.BandGeneralSystem()
            >>> print(system.get_values())
            {}
        """
        return {}


class BandSPDSystem(System):
    """Represents a band symmetric positive definite (SPD) system solver.

    This system is optimized for symmetric positive definite matrices with
    a banded structure, utilizing banded profile storage for efficiency.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "BandSPD".

    Example:
        >>> import femora as fm
        >>> system = fm.BandSPDSystem()
        >>> print(system.system_type)
        BandSPD
    """
    def __init__(self):
        """Initializes a BandSPDSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.BandSPDSystem()
            >>> print(system.system_type)
            BandSPD
        """
        super().__init__("BandSPD")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the BandSPDSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.BandSPDSystem()
            >>> print(system.to_tcl())
            system BandSPD
        """
        return "system BandSPD"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For BandSPDSystem, there are no specific parameters to report.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> system = fm.BandSPDSystem()
            >>> print(system.get_values())
            {}
        """
        return {}


class ProfileSPDSystem(System):
    """Represents a profile symmetric positive definite (SPD) system solver.

    This system is designed for symmetric positive definite matrices and
    uses skyline storage, which can be efficient for problems where the
    matrix profile is sparse but not necessarily banded.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "ProfileSPD".

    Example:
        >>> import femora as fm
        >>> system = fm.ProfileSPDSystem()
        >>> print(system.system_type)
        ProfileSPD
    """
    def __init__(self):
        """Initializes a ProfileSPDSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.ProfileSPDSystem()
            >>> print(system.system_type)
            ProfileSPD
        """
        super().__init__("ProfileSPD")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the ProfileSPDSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.ProfileSPDSystem()
            >>> print(system.to_tcl())
            system ProfileSPD
        """
        return "system ProfileSPD"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For ProfileSPDSystem, there are no specific parameters to report.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> system = fm.ProfileSPDSystem()
            >>> print(system.get_values())
            {}
        """
        return {}


class SuperLUSystem(System):
    """Represents a SuperLU sparse system solver.

    SuperLU is a general-purpose sparse direct solver for large,
    sparse, nonsymmetric systems of linear equations.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "SuperLU".

    Example:
        >>> import femora as fm
        >>> system = fm.SuperLUSystem()
        >>> print(system.system_type)
        SuperLU
    """
    def __init__(self):
        """Initializes a SuperLUSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.SuperLUSystem()
            >>> print(system.system_type)
            SuperLU
        """
        super().__init__("SuperLU")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the SuperLUSystem.

        Example:
            >>> import femora as fm
            >>> system = fm.SuperLUSystem()
            >>> print(system.to_tcl())
            system SuperLU
        """
        return "system SuperLU"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For SuperLUSystem, there are no specific parameters to report.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> system = fm.SuperLUSystem()
            >>> print(system.get_values())
            {}
        """
        return {}


class UmfpackSystem(System):
    """Represents an Umfpack sparse system solver.

    Umfpack is a sparse direct solver designed for unsymmetric matrices.
    It is part of the SuiteSparse collection.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "Umfpack".
        lvalue_fact (Optional[float]): Controls a factor related to
            the symbolic factorization phase.

    Example:
        >>> import femora as fm
        >>> system = fm.UmfpackSystem(lvalue_fact=1.5)
        >>> print(system.system_type)
        Umfpack
        >>> print(system.lvalue_fact)
        1.5
    """
    def __init__(self, lvalue_fact: Optional[float] = None):
        """Initializes an UmfpackSystem.

        Args:
            lvalue_fact: Optional. Controls the percentage increase in the
                estimated working space during symbolic factorization.

        Example:
            >>> import femora as fm
            >>> system = fm.UmfpackSystem(lvalue_fact=1.2)
            >>> print(system.lvalue_fact)
            1.2
            >>> default_system = fm.UmfpackSystem()
            >>> print(default_system.lvalue_fact)
            None
        """
        super().__init__("Umfpack")
        self.lvalue_fact = lvalue_fact
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing the UmfpackSystem.

        Example:
            >>> import femora as fm
            >>> system_default = fm.UmfpackSystem()
            >>> print(system_default.to_tcl())
            system Umfpack
            >>> system_custom = fm.UmfpackSystem(lvalue_fact=1.1)
            >>> print(system_custom.to_tcl())
            system Umfpack -lvalueFact 1.1
        """
        cmd = "system Umfpack"
        if self.lvalue_fact is not None:
            cmd += f" -lvalueFact {self.lvalue_fact}"
        return cmd
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary containing
                "lvalue_fact" and its current value.

        Example:
            >>> import femora as fm
            >>> system = fm.UmfpackSystem(lvalue_fact=1.3)
            >>> values = system.get_values()
            >>> print(values["lvalue_fact"])
            1.3
        """
        return {
            "lvalue_fact": self.lvalue_fact
        }


class MumpsSystem(System):
    """Represents a Mumps sparse direct solver.

    MUMPS (MUltifrontal Massively Parallel sparse direct Solver) is a
    high-performance parallel solver for sparse systems of linear equations.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type name of the system, always "Mumps".
        icntl14 (Optional[float]): Controls the percentage increase in the
            estimated working space.
        icntl7 (Optional[int]): Specifies the ordering strategy used for factorization.

    Example:
        >>> import femora as fm
        >>> system = fm.MumpsSystem(icntl14=1.2, icntl7=0)
        >>> print(system.system_type)
        Mumps
        >>> print(system.icntl14)
        1.2
    """
    def __init__(self, icntl14: Optional[float] = None, icntl7: Optional[int] = None):
        """Initializes a MumpsSystem.

        Args:
            icntl14: Optional. Controls the percentage increase in the estimated
                working space for factorization.
            icntl7: Optional. Computes a symmetric permutation (ordering) for factorization.
                Possible values:
                0: AMD
                1: set by user
                2: AMF
                3: SCOTCH
                4: PORD
                5: Metis
                6: AMD with QADM
                7: automatic

        Example:
            >>> import femora as fm
            >>> system_default = fm.MumpsSystem()
            >>> print(system_default.icntl14, system_default.icntl7)
            None None
            >>> system_custom = fm.MumpsSystem(icntl14=1.5, icntl7=3)
            >>> print(system_custom.icntl14, system_custom.icntl7)
            1.5 3
        """
        super().__init__("Mumps")
        self.icntl14 = icntl14
        self.icntl7 = icntl7
    
    def to_tcl(self) -> str:
        """Converts the system configuration to an OpenSees TCL command string.
        
        Returns:
            str: The TCL command string.

        Example:
            >>> import femora as fm
            >>> system_default = fm.MumpsSystem()
            >>> print(system_default.to_tcl())
            system Mumps
            >>> system_custom = fm.MumpsSystem(icntl14=1.1, icntl7=0)
            >>> print(system_custom.to_tcl())
            system Mumps -ICNTL14 1.1 -ICNTL7 0
        """
        cmd = "system Mumps"
        if self.icntl14 is not None:
            cmd += f" -ICNTL14 {self.icntl14}"
        if self.icntl7 is not None:
            cmd += f" -ICNTL7 {self.icntl7}"
        return cmd
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary containing
                "icntl14" and "icntl7" and their current values.

        Example:
            >>> import femora as fm
            >>> system = fm.MumpsSystem(icntl14=1.2, icntl7=0)
            >>> values = system.get_values()
            >>> print(values["icntl14"])
            1.2
            >>> print(values["icntl7"])
            0
        """
        return {
            "icntl14": self.icntl14,
            "icntl7": self.icntl7
        }


class SystemManager:
    """Manages system types and instances as a singleton.

    This class provides a centralized access point for creating, retrieving,
    and managing `System` objects throughout the application. It ensures
    that only one instance of `SystemManager` exists.

    Attributes:
        bandGeneral (Type[BandGeneralSystem]): The class for BandGeneralSystem.
        bandSPD (Type[BandSPDSystem]): The class for BandSPDSystem.
        profileSPD (Type[ProfileSPDSystem]): The class for ProfileSPDSystem.
        fullGeneral (Type[FullGeneralSystem]): The class for FullGeneralSystem.
        superLU (Type[SuperLUSystem]): The class for SuperLUSystem.
        umfpack (Type[UmfpackSystem]): The class for UmfpackSystem.
        mumps (Type[MumpsSystem]): The class for MumpsSystem.

    Example:
        >>> import femora as fm
        >>> manager1 = fm.SystemManager()
        >>> manager2 = fm.SystemManager()
        >>> print(manager1 is manager2)
        True
        >>> print(manager1.fullGeneral)
        <class 'femora.system.FullGeneralSystem'>
    """
    _instance = None

    def __new__(cls):
        """Ensures that only one instance of SystemManager is created."""
        if cls._instance is None:
            cls._instance = super(SystemManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initializes the SystemManager singleton.

        This constructor is called only once when the first instance
        of SystemManager is created. It populates references to the
        available concrete system classes.

        Attributes:
            bandGeneral (Type[BandGeneralSystem]): The class for BandGeneralSystem.
            bandSPD (Type[BandSPDSystem]): The class for BandSPDSystem.
            profileSPD (Type[ProfileSPDSystem]): The class for ProfileSPDSystem.
            fullGeneral (Type[FullGeneralSystem]): The class for FullGeneralSystem.
            superLU (Type[SuperLUSystem]): The class for SuperLUSystem.
            umfpack (Type[UmfpackSystem]): The class for UmfpackSystem.
            mumps (Type[MumpsSystem]): The class for MumpsSystem.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> print(manager.fullGeneral)
            <class 'femora.system.FullGeneralSystem'>
        """
        self.bandGeneral = BandGeneralSystem
        self.bandSPD = BandSPDSystem 
        self.profileSPD = ProfileSPDSystem
        self.fullGeneral = FullGeneralSystem
        self.superLU = SuperLUSystem
        self.umfpack = UmfpackSystem
        self.mumps = MumpsSystem
        
    def create_system(self, system_type: str, **kwargs) -> System:
        """Creates a new system instance through the global System registry.

        Args:
            system_type: The string identifier for the type of system to create.
            **kwargs: Additional keyword arguments passed to the system's constructor.

        Returns:
            System: An instance of the requested system type.

        Raises:
            ValueError: If an unknown system type is requested.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> sys_instance = manager.create_system("umfpack", lvalue_fact=1.1)
            >>> print(sys_instance.system_type)
            Umfpack
            >>> print(sys_instance.lvalue_fact)
            1.1
        """
        return System.create_system(system_type, **kwargs)

    def get_system(self, tag: int) -> System:
        """Retrieves a specific system instance by its unique tag.

        Args:
            tag: The unique integer ID of the system to retrieve.

        Returns:
            System: The system instance associated with the given tag.

        Raises:
            KeyError: If no system with the given tag exists.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> fm.System.clear_all() # Ensure clean state for example
            >>> sys1 = manager.create_system("bandgeneral")
            >>> retrieved_sys = manager.get_system(sys1.tag)
            >>> print(retrieved_sys.system_type)
            BandGeneral
        """
        return System.get_system(tag)

    def remove_system(self, tag: int) -> None:
        """Deletes a system instance by its tag and re-tags remaining systems.

        Args:
            tag: The tag of the system instance to delete.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> fm.System.clear_all()
            >>> sys1 = manager.create_system("fullgeneral")
            >>> sys2 = manager.create_system("bandgeneral")
            >>> manager.remove_system(sys1.tag)
            >>> print(len(manager.get_all_systems()))
            1
        """
        System.remove_system(tag)

    def get_all_systems(self) -> Dict[int, System]:
        """Retrieves a dictionary of all created system instances.

        Returns:
            Dict[int, System]: A dictionary where keys are system tags
                and values are the corresponding System instances.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> fm.System.clear_all()
            >>> manager.create_system("fullgeneral")
            >>> manager.create_system("bandgeneral")
            >>> all_systems = manager.get_all_systems()
            >>> print(len(all_systems))
            2
        """
        return System.get_all_systems()

    def get_available_types(self) -> List[str]:
        """Retrieves a list of all currently registered system types.

        Returns:
            List[str]: A list of string names for available system types.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> types = manager.get_available_types()
            >>> print("mumps" in types)
            True
        """
        return System.get_available_types()
    
    def clear_all(self):
        """Clears all created system instances and resets the tag counter.

        This affects all systems managed globally, effectively resetting
        the system management state.

        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.create_system("fullgeneral")
            >>> print(len(manager.get_all_systems()))
            1
            >>> manager.clear_all()
            >>> print(len(manager.get_all_systems()))
            0
        """  
        System.clear_all()


# Register all systems
System.register_system('fullgeneral', FullGeneralSystem)
System.register_system('bandgeneral', BandGeneralSystem)
System.register_system('bandspd', BandSPDSystem)
System.register_system('profilespd', ProfileSPDSystem)
System.register_system('superlu', SuperLUSystem)
System.register_system('umfpack', UmfpackSystem)
System.register_system('mumps', MumpsSystem)