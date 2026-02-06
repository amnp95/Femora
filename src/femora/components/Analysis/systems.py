from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import abstractmethod

class System(AnalysisComponent):
    """Base abstract class for handling systems of linear equations.

    This class provides a framework for managing different types of solvers
    used in structural analysis, such as direct or sparse solvers. It
    includes mechanisms for registering, creating, retrieving, and managing
    system instances throughout the application.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): A string indicating the specific type of system
            (e.g., "FullGeneral", "Umfpack").
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all() # Ensure a clean state for predictable tags
        >>> fm.System.register_system('my_fullgeneral', fm.FullGeneralSystem)
        >>> system = fm.System.create_system('my_fullgeneral')
        >>> print(system.tag)
        1
        >>> print(system.system_type)
        FullGeneral
    """
    _systems = {}  # Class-level dictionary to store system types
    _created_systems = {}  # Class-level dictionary to track all created systems
    _next_tag = 1  # Class variable to track the next tag to assign
    
    def __init__(self, system_type: str):
        """Initializes a System instance.

        Args:
            system_type: The string identifier for the type of system.
        """
        self.tag = System._next_tag
        System._next_tag += 1
        self.system_type = system_type
        
        # Register this system in the class-level tracking dictionary
        System._created_systems[self.tag] = self
    
    @staticmethod
    def register_system(name: str, system_class: Type['System']):
        """Registers a new system type with the System factory.

        Args:
            name: The string name to register the system under (case-insensitive).
            system_class: The class object of the system to be registered.
        
        Example:
            >>> import femora as fm
            >>> class MyCustomSystem(fm.System):
            ...     def __init__(self):
            ...         super().__init__("MyCustom")
            ...     def get_values(self): return {}
            ...     def to_tcl(self): return "system MyCustom"
            >>> fm.System.register_system('mycustom', MyCustomSystem)
            >>> system = fm.System.create_system('mycustom')
            >>> print(system.system_type)
            MyCustom
        """
        System._systems[name.lower()] = system_class
    
    @staticmethod
    def create_system(system_type: str, **kwargs) -> 'System':
        """Creates a new system instance of the specified type.

        Args:
            system_type: The string identifier of the system type to create
                (e.g., "FullGeneral", "Umfpack").
            **kwargs: Additional keyword arguments to pass to the system's
                constructor.

        Returns:
            A new instance of the requested System subclass.

        Raises:
            ValueError: If an unknown system type is requested.
        
        Example:
            >>> import femora as fm
            >>> fm.System.register_system('fullgeneral_eg', fm.FullGeneralSystem)
            >>> system = fm.System.create_system('fullgeneral_eg')
            >>> print(system.system_type)
            FullGeneral
            >>> try:
            ...     fm.System.create_system('nonexistent')
            ... except ValueError as e:
            ...     print(e)
            Unknown system type: nonexistent
        """
        system_type = system_type.lower()
        if system_type not in System._systems:
            raise ValueError(f"Unknown system type: {system_type}")
        return System._systems[system_type](**kwargs)
    
    @staticmethod
    def get_available_types() -> List[str]:
        """Retrieves a list of all currently registered system types.

        Returns:
            A list of strings, where each string is the name of an
            available system type.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all() # Clear previous registrations for predictable output
            >>> fm.System.register_system('fullgeneral_type', fm.FullGeneralSystem)
            >>> fm.System.register_system('umfpack_type', fm.UmfpackSystem)
            >>> types = fm.System.get_available_types()
            >>> print(sorted(types))
            ['fullgeneral_type', 'umfpack_type']
        """
        return list(System._systems.keys())
    
    @classmethod
    def get_system(cls, tag: int) -> 'System':
        """Retrieves a specific system instance by its unique tag.

        Args:
            tag: The unique integer tag of the system to retrieve.

        Returns:
            The System instance associated with the given tag.

        Raises:
            KeyError: If no system with the given tag exists.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all()
            >>> fm.System.register_system('temp_system', fm.FullGeneralSystem)
            >>> system1 = fm.System.create_system('temp_system')
            >>> system2 = fm.System.create_system('temp_system')
            >>> retrieved_system = fm.System.get_system(system1.tag)
            >>> print(retrieved_system.tag)
            1
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
        """Retrieves all currently created system instances.

        Returns:
            A dictionary where keys are system tags (int) and values are
            the corresponding System instances.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all()
            >>> fm.System.register_system('temp_sys_all', fm.FullGeneralSystem)
            >>> sys1 = fm.System.create_system('temp_sys_all')
            >>> sys2 = fm.System.create_system('temp_sys_all')
            >>> all_systems = fm.System.get_all_systems()
            >>> print(len(all_systems))
            2
            >>> print(sys1.tag in all_systems)
            True
        """
        return cls._created_systems
    
    @classmethod
    def clear_all(cls) -> None:
        """Clears all created system instances and resets the tag counter.

        After this call, all previously created system instances are removed,
        and the next created system will have a tag of 1.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all()
            >>> fm.System.register_system('temp_clear', fm.FullGeneralSystem)
            >>> system1 = fm.System.create_system('temp_clear')
            >>> print(len(fm.System.get_all_systems()))
            1
            >>> fm.System.clear_all()
            >>> print(len(fm.System.get_all_systems()))
            0
            >>> system2 = fm.System.create_system('temp_clear')
            >>> print(system2.tag)
            1
        """
        cls._created_systems.clear()
        cls._next_tag = 1
    
    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Abstract method to get the parameters defining this system.

        Each concrete System subclass must implement this method to
        return a dictionary of its defining properties.

        Returns:
            A dictionary of parameter values, where keys are parameter names
            (str) and values can be strings, integers, floats, or booleans.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all()
            >>> fm.System.register_system('mumps', fm.MumpsSystem)
            >>> mumps_sys = fm.System.create_system('mumps', icntl14=1.2, icntl7=5)
            >>> values = mumps_sys.get_values()
            >>> print(values['icntl14'])
            1.2
            >>> print(values['icntl7'])
            5
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all existing systems sequentially starting from 1.

        This private method is typically called after a system is removed
        to maintain contiguous numbering of system tags.
        """
        new_systems = {}
        for idx, system in enumerate(sorted(cls._created_systems.values(), key=lambda s: s.tag), start=1):
            system.tag = idx
            new_systems[idx] = system
        cls._created_systems = new_systems
        cls._next_tag = len(cls._created_systems) + 1

    @classmethod
    def remove_system(cls, tag: int) -> None:
        """Deletes a system by its tag and re-tags all remaining systems.

        The tags of all remaining systems are reassigned sequentially
        starting from 1 to ensure contiguous numbering.

        Args:
            tag: The unique integer tag of the system to delete.
        
        Example:
            >>> import femora as fm
            >>> fm.System.clear_all() # Ensure clean state
            >>> fm.System.register_system('temp_remove', fm.FullGeneralSystem)
            >>> sys1 = fm.System.create_system('temp_remove') # original tag 1
            >>> sys2 = fm.System.create_system('temp_remove') # original tag 2
            >>> sys3 = fm.System.create_system('temp_remove') # original tag 3
            >>> fm.System.remove_system(sys2.tag) # Remove original tag 2
            >>> print(fm.System.get_system(1).tag) # Original sys1 is still tag 1
            1
            >>> print(fm.System.get_system(2).tag) # Original sys3 is now tag 2
            2
            >>> try:
            ...     fm.System.get_system(3) # Original tag 3 no longer exists
            ... except KeyError as e:
            ...     print(str(e))
            No system found with tag 3
        """
        if tag in cls._created_systems:
            del cls._created_systems[tag]
            cls._reassign_tags()


class FullGeneralSystem(System):
    """Represents a full general system solver.

    This solver does not optimize matrix storage and uses a full matrix.
    It is generally not recommended for large-scale problems due to its
    memory and computational overhead.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "FullGeneral".
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.FullGeneralSystem()
        >>> print(system.system_type)
        FullGeneral
        >>> print(system.to_tcl())
        system FullGeneral
    """
    def __init__(self):
        """Initializes a FullGeneralSystem."""
        super().__init__("FullGeneral")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'FullGeneral' system
            in OpenSees.
        """
        return "system FullGeneral"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For FullGeneralSystem, there are no specific parameters.

        Returns:
            An empty dictionary.
        """
        return {}


class BandGeneralSystem(System):
    """Represents a band general system solver.

    This solver uses banded matrix storage, which can be more efficient
    than a full general system for matrices with a limited bandwidth.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "BandGeneral".
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.BandGeneralSystem()
        >>> print(system.system_type)
        BandGeneral
        >>> print(system.to_tcl())
        system BandGeneral
    """
    def __init__(self):
        """Initializes a BandGeneralSystem."""
        super().__init__("BandGeneral")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'BandGeneral' system
            in OpenSees.
        """
        return "system BandGeneral"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For BandGeneralSystem, there are no specific parameters.

        Returns:
            An empty dictionary.
        """
        return {}


class BandSPDSystem(System):
    """Represents a band Symmetric Positive Definite (SPD) system solver.

    This solver is optimized for symmetric positive definite matrices
    and uses banded profile storage, which is efficient for structural
    problems with well-ordered nodes.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "BandSPD".
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.BandSPDSystem()
        >>> print(system.system_type)
        BandSPD
        >>> print(system.to_tcl())
        system BandSPD
    """
    def __init__(self):
        """Initializes a BandSPDSystem."""
        super().__init__("BandSPD")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'BandSPD' system
            in OpenSees.
        """
        return "system BandSPD"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For BandSPDSystem, there are no specific parameters.

        Returns:
            An empty dictionary.
        """
        return {}


class ProfileSPDSystem(System):
    """Represents a profile Symmetric Positive Definite (SPD) system solver.

    This solver is designed for symmetric positive definite matrices and
    uses skyline storage, which can be more memory efficient than banded
    storage for certain matrix profiles.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "ProfileSPD".
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.ProfileSPDSystem()
        >>> print(system.system_type)
        ProfileSPD
        >>> print(system.to_tcl())
        system ProfileSPD
    """
    def __init__(self):
        """Initializes a ProfileSPDSystem."""
        super().__init__("ProfileSPD")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'ProfileSPD' system
            in OpenSees.
        """
        return "system ProfileSPD"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For ProfileSPDSystem, there are no specific parameters.

        Returns:
            An empty dictionary.
        """
        return {}


class SuperLUSystem(System):
    """Represents a SuperLU sparse system solver.

    SuperLU is a robust direct solver optimized for large, sparse systems
    of linear equations. It is generally recommended for problems where
    the system matrix is sparse.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "SuperLU".
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.SuperLUSystem()
        >>> print(system.system_type)
        SuperLU
        >>> print(system.to_tcl())
        system SuperLU
    """
    def __init__(self):
        """Initializes a SuperLUSystem."""
        super().__init__("SuperLU")
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'SuperLU' system
            in OpenSees.
        """
        return "system SuperLU"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        For SuperLUSystem, there are no specific parameters.

        Returns:
            An empty dictionary.
        """
        return {}


class UmfpackSystem(System):
    """Represents an Umfpack sparse system solver.

    Umfpack is a direct solver designed for sparse, unsymmetric
    matrices. It offers high performance for many sparse matrix problems.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "Umfpack".
        lvalue_fact (Optional[float]): Controls the percentage increase in
            the estimated working space for the factorization.
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.UmfpackSystem(lvalue_fact=1.5)
        >>> print(system.system_type)
        Umfpack
        >>> print(system.lvalue_fact)
        1.5
        >>> print(system.to_tcl())
        system Umfpack -lvalueFact 1.5
    """
    def __init__(self, lvalue_fact: Optional[float] = None):
        """Initializes an UmfpackSystem.

        Args:
            lvalue_fact: Optional. Controls the percentage increase in the
                estimated working space for the factorization.
        """
        super().__init__("Umfpack")
        self.lvalue_fact = lvalue_fact
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating an 'Umfpack' system
            in OpenSees, including optional parameters.
        """
        cmd = "system Umfpack"
        if self.lvalue_fact is not None:
            cmd += f" -lvalueFact {self.lvalue_fact}"
        return cmd
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Retrieves the parameters defining this system.

        Returns:
            A dictionary containing the 'lvalue_fact' parameter.
        """
        return {
            "lvalue_fact": self.lvalue_fact
        }


class MumpsSystem(System):
    """Represents a Mumps sparse direct solver.

    MUMPS (MUltifrontal Massively Parallel sparse direct Solver) is a
    high-performance parallel direct solver for large sparse linear systems.
    It provides various options for ordering and memory management.

    Attributes:
        tag (int): The unique identifier for this system instance.
        system_type (str): The specific type of the system, "Mumps".
        icntl14 (Optional[float]): Controls the percentage increase in the
            estimated working space for the factorization.
        icntl7 (Optional[int]): Specifies the symmetric permutation (ordering)
            strategy for factorization:
            *   0: AMD (Approximate Minimum Degree)
            *   1: User-defined permutation
            *   2: AMF (Approximate Minimum Fill)
            *   3: SCOTCH
            *   4: PORD
            *   5: Metis
            *   6: AMD with QADM
            *   7: Automatic selection
    
    Example:
        >>> import femora as fm
        >>> fm.System.clear_all()
        >>> system = fm.MumpsSystem(icntl14=1.2, icntl7=5)
        >>> print(system.system_type)
        Mumps
        >>> print(system.icntl14)
        1.2
        >>> print(system.icntl7)
        5
        >>> print(system.to_tcl())
        system Mumps -ICNTL14 1.2 -ICNTL7 5
    """
    def __init__(self, icntl14: Optional[float] = None, icntl7: Optional[int] = None):
        """Initializes a MumpsSystem.

        Args:
            icntl14: Optional. Controls the percentage increase in the estimated
                working space for the factorization.
            icntl7: Optional. Computes a symmetric permutation (ordering) for
                factorization:
                *   0: AMD (Approximate Minimum Degree)
                *   1: User-defined permutation
                *   2: AMF (Approximate Minimum Fill)
                *   3: SCOTCH
                *   4: PORD
                *   5: Metis
                *   6: AMD with QADM
                *   7: Automatic selection
        """
        super().__init__("Mumps")
        self.icntl14 = icntl14
        self.icntl7 = icntl7
    
    def to_tcl(self) -> str:
        """Converts the system configuration to a TCL command string.

        Returns:
            The TCL command string for creating a 'Mumps' system
            in OpenSees, including optional parameters.
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
            A dictionary containing the 'icntl14' and 'icntl7' parameters.
        """
        return {
            "icntl14": self.icntl14,
            "icntl7": self.icntl7
        }


class SystemManager:
    """Manages all system instances in a singleton pattern.

    This class provides a centralized point of access for creating,
    retrieving, and clearing system solver configurations. It ensures
    that only one instance of SystemManager exists throughout the
    application.

    Attributes:
        bandGeneral (Type[BandGeneralSystem]): The class representing the
            BandGeneral system type.
        bandSPD (Type[BandSPDSystem]): The class representing the BandSPD
            system type.
        profileSPD (Type[ProfileSPDSystem]): The class representing the
            ProfileSPD system type.
        fullGeneral (Type[FullGeneralSystem]): The class representing the
            FullGeneral system type.
        superLU (Type[SuperLUSystem]): The class representing the SuperLU
            system type.
        umfpack (Type[UmfpackSystem]): The class representing the Umfpack
            system type.
        mumps (Type[MumpsSystem]): The class representing the Mumps
            system type.
    
    Example:
        >>> import femora as fm
        >>> manager = fm.SystemManager()
        >>> system = manager.create_system('bandgeneral')
        >>> print(system.system_type)
        BandGeneral
        >>> manager.clear_all()
        >>> print(len(manager.get_all_systems()))
        0
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initializes the SystemManager instance.

        This constructor sets up direct references to the concrete
        system classes, making them accessible as attributes.
        """
        self.bandGeneral = BandGeneralSystem
        self.bandSPD = BandSPDSystem 
        self.profileSPD = ProfileSPDSystem
        self.fullGeneral = FullGeneralSystem
        self.superLU = SuperLUSystem
        self.umfpack = UmfpackSystem
        self.mumps = MumpsSystem
        
    def create_system(self, system_type: str, **kwargs) -> System:
        """Creates a new system instance of the specified type.

        This method delegates to `System.create_system` to instantiate
        the requested solver.

        Args:
            system_type: The string identifier of the system type to create.
            **kwargs: Additional keyword arguments to pass to the system's
                constructor.

        Returns:
            A new instance of the requested System subclass.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> fm.System.clear_all()
            >>> fm.System.register_system('umfpack_mgr', fm.UmfpackSystem)
            >>> system = manager.create_system('umfpack_mgr', lvalue_fact=1.5)
            >>> print(system.system_type)
            Umfpack
            >>> print(system.lvalue_fact)
            1.5
        """
        return System.create_system(system_type, **kwargs)

    def get_system(self, tag: int) -> System:
        """Retrieves a specific system instance by its unique tag.

        This method delegates to `System.get_system`.

        Args:
            tag: The unique integer tag of the system to retrieve.

        Returns:
            The System instance associated with the given tag.

        Raises:
            KeyError: If no system with the given tag exists.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.clear_all()
            >>> fm.System.register_system('fullgeneral_mgr', fm.FullGeneralSystem)
            >>> system = manager.create_system('fullgeneral_mgr')
            >>> retrieved = manager.get_system(system.tag)
            >>> print(retrieved.tag)
            1
        """
        return System.get_system(tag)

    def remove_system(self, tag: int) -> None:
        """Deletes a system by its tag and re-tags remaining systems.

        This method delegates to `System.remove_system`.

        Args:
            tag: The unique integer tag of the system to delete.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.clear_all()
            >>> fm.System.register_system('removable_mgr', fm.FullGeneralSystem)
            >>> sys1 = manager.create_system('removable_mgr') # tag 1
            >>> sys2 = manager.create_system('removable_mgr') # tag 2
            >>> sys3 = manager.create_system('removable_mgr') # tag 3
            >>> manager.remove_system(sys2.tag) # Remove original tag 2
            >>> all_systems = manager.get_all_systems()
            >>> print(len(all_systems))
            2
            >>> print(manager.get_system(1).system_type) # Original tag 1
            FullGeneral
            >>> print(manager.get_system(2).system_type) # Original tag 3, now tag 2
            FullGeneral
            >>> try:
            ...     manager.get_system(3)
            ... except KeyError as e:
            ...     print(str(e))
            No system found with tag 3
        """
        System.remove_system(tag)

    def get_all_systems(self) -> Dict[int, System]:
        """Retrieves all currently created system instances.

        This method delegates to `System.get_all_systems`.

        Returns:
            A dictionary where keys are system tags (int) and values are
            the corresponding System instances.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.clear_all()
            >>> fm.System.register_system('all_mgr', fm.FullGeneralSystem)
            >>> sys1 = manager.create_system('all_mgr')
            >>> all_systems = manager.get_all_systems()
            >>> print(len(all_systems))
            1
        """
        return System.get_all_systems()

    def get_available_types(self) -> List[str]:
        """Retrieves a list of all currently registered system types.

        This method delegates to `System.get_available_types`.

        Returns:
            A list of strings, where each string is the name of an
            available system type.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.clear_all() # Ensure fresh registration state for example
            >>> fm.System.register_system('test_type_mgr', fm.FullGeneralSystem)
            >>> types = manager.get_available_types()
            >>> print('test_type_mgr' in types)
            True
        """
        return System.get_available_types()
    
    def clear_all(self):
        """Clears all created system instances and resets the tag counter.

        This method delegates to `System.clear_all`.
        
        Example:
            >>> import femora as fm
            >>> manager = fm.SystemManager()
            >>> manager.clear_all()
            >>> fm.System.register_system('clear_mgr', fm.FullGeneralSystem)
            >>> system = manager.create_system('clear_mgr')
            >>> print(len(manager.get_all_systems()))
            1
            >>> manager.clear_all()
            >>> print(len(manager.get_all_systems()))
            0
        """
        System.clear_all()


# Register all systems initially. This ensures that the System factory
# is populated with common solver types upon import.
System.register_system('fullgeneral', FullGeneralSystem)
System.register_system('bandgeneral', BandGeneralSystem)
System.register_system('bandspd', BandSPDSystem)
System.register_system('profilespd', ProfileSPDSystem)
System.register_system('superlu', SuperLUSystem)
System.register_system('umfpack', UmfpackSystem)
System.register_system('mumps', MumpsSystem)