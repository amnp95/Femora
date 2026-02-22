from typing import List, Dict, Type
from .base import AnalysisComponent

class Numberer(AnalysisComponent):
    """Base abstract class for a numberer.

    A numberer determines the mapping between equation numbers and Degrees of Freedom (DOFs)
    in a structural analysis model. This class provides a registration mechanism for
    different numberer implementations and manages their instances.

    Attributes:
        _numberers (dict[str, Type['Numberer']]): Class-level dictionary storing
            registered numberer types by name.
        _numberer_instances (dict[str, 'Numberer']): Class-level dictionary storing
            created numberer instances by type name.

    Example:
        >>> from femora.numberer import Numberer, PlainNumberer
        >>> Numberer.register_numberer('plain', PlainNumberer)
        >>> plain_num = Numberer.create_numberer('plain')
        >>> print(isinstance(plain_num, PlainNumberer))
        True
    """
    _numberers = {}  # Class-level dictionary to store numberer types
    _numberer_instances = {}  # Class-level dictionary to store created numberer instances

    @staticmethod
    def register_numberer(name: str, numberer_class: Type['Numberer']):
        """Registers a numberer type with a given name.

        Args:
            name: The string name to associate with the numberer class.
            numberer_class: The class object (inheriting from `Numberer`) to register.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer
            >>> Numberer.register_numberer('custom_plain', PlainNumberer)
            >>> custom_numberer = Numberer.create_numberer('custom_plain')
            >>> print(isinstance(custom_numberer, PlainNumberer))
            True
        """
        Numberer._numberers[name.lower()] = numberer_class

    @staticmethod
    def create_numberer(numberer_type: str, **kwargs) -> 'Numberer':
        """Creates a numberer instance of the specified type.

        If a numberer of this type has been previously registered using
        `register_numberer`, an instance will be created and stored for future retrieval.

        Args:
            numberer_type: The string name of the numberer type to create (e.g., 'plain', 'rcm').
            **kwargs: Additional keyword arguments to pass to the numberer's constructor.

        Returns:
            Numberer: An instance of the requested numberer type.

        Raises:
            ValueError: If an unknown `numberer_type` is provided.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer
            >>> Numberer.register_numberer('plain', PlainNumberer)
            >>> plain_num = Numberer.create_numberer('plain')
            >>> print(plain_num.to_tcl())
            numberer Plain
        """
        numberer_type = numberer_type.lower()
        if numberer_type not in Numberer._numberers:
            raise ValueError(f"Unknown numberer type: {numberer_type}")

        # Create the numberer instance
        numberer = Numberer._numberers[numberer_type](**kwargs)

        # Store in class-level instances dictionary
        Numberer._numberer_instances[numberer_type] = numberer

        return numberer

    @staticmethod
    def get_available_types() -> List[str]:
        """Returns a list of all registered numberer types.

        Returns:
            list[str]: A list of string names for available numberer types.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer, RCMNumberer
            >>> Numberer.register_numberer('plain', PlainNumberer)
            >>> Numberer.register_numberer('rcm', RCMNumberer)
            >>> types = Numberer.get_available_types()
            >>> print('plain' in types)
            True
            >>> print('rcm' in types)
            True
        """
        return list(Numberer._numberers.keys())

    @staticmethod
    def get_instances() -> Dict[str, 'Numberer']:
        """Returns a dictionary of all created numberer instances.

        The dictionary maps numberer type names to their respective instances.

        Returns:
            dict[str, Numberer]: A dictionary containing all instantiated numberers.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer
            >>> Numberer.register_numberer('plain', PlainNumberer)
            >>> _ = Numberer.create_numberer('plain')
            >>> instances = Numberer.get_instances()
            >>> print('plain' in instances)
            True
        """
        return Numberer._numberer_instances

    @staticmethod
    def get_instance(numberer_type: str) -> 'Numberer':
        """Retrieves a specific numberer instance if it has been created.

        Args:
            numberer_type: The string name of the numberer type to retrieve.

        Returns:
            Numberer or None: The instance of the requested numberer type, or None
                if no instance of that type has been created yet.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer
            >>> Numberer.register_numberer('plain', PlainNumberer)
            >>> _ = Numberer.create_numberer('plain')
            >>> plain_num = Numberer.get_instance('plain')
            >>> print(isinstance(plain_num, PlainNumberer))
            True
            >>> none_num = Numberer.get_instance('non_existent')
            >>> print(none_num is None)
            True
        """
        numberer_type = numberer_type.lower()
        if numberer_type not in Numberer._numberer_instances:
            return None
        return Numberer._numberer_instances[numberer_type]

    @staticmethod
    def reset_instances():
        """Clears all stored numberer instances.

        This method removes all numberer instances from the class-level cache,
        forcing new instances to be created if requested again.

        Example:
            >>> from femora.numberer import Numberer, PlainNumberer
            >>> Numberer.register_numberer('plain', PlainNumberer)
            >>> plain1 = Numberer.create_numberer('plain')
            >>> Numberer.reset_instances()
            >>> plain2 = Numberer.create_numberer('plain')
            >>> print(plain1 is plain2)
            False
        """
        Numberer._numberer_instances.clear()


class PlainNumberer(Numberer):
    """Implements a Plain numberer.

    This numberer assigns equation numbers to Degrees of Freedom (DOFs)
    based on the order in which nodes are created in the model.
    It is implemented as a singleton, ensuring only one instance exists.

    Attributes:
        _instance (PlainNumberer or None): The singleton instance of the class.

    Example:
        >>> from femora.numberer import PlainNumberer
        >>> num1 = PlainNumberer()
        >>> num2 = PlainNumberer()
        >>> print(num1 is num2)
        True
        >>> print(num1.to_tcl())
        numberer Plain
    """
    _instance = None

    def __new__(cls):
        """Creates or returns the singleton instance of PlainNumberer.

        Args:
            cls: The class itself.

        Returns:
            PlainNumberer: The singleton instance of PlainNumberer.
        """
        if cls._instance is None:
            cls._instance = super(PlainNumberer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the PlainNumberer.

        This constructor does not take any arguments as the PlainNumberer
        is stateless and implemented as a singleton.
        """
        pass

    def to_tcl(self) -> str:
        """Generates the Tcl command string for a Plain numberer.

        Returns:
            str: The Tcl command string, e.g., "numberer Plain".

        Example:
            >>> from femora.numberer import PlainNumberer
            >>> num = PlainNumberer()
            >>> print(num.to_tcl())
            numberer Plain
        """
        return "numberer Plain"


class RCMNumberer(Numberer):
    """Implements a Reverse Cuthill-McKee (RCM) numberer.

    This numberer is designed to reorder Degrees of Freedom (DOFs) to reduce
    the bandwidth of the system stiffness matrix, which can improve the
    efficiency of direct solvers. It is implemented as a singleton.

    Attributes:
        _instance (RCMNumberer or None): The singleton instance of the class.

    Example:
        >>> from femora.numberer import RCMNumberer
        >>> num1 = RCMNumberer()
        >>> num2 = RCMNumberer()
        >>> print(num1 is num2)
        True
        >>> print(num1.to_tcl())
        numberer RCM
    """
    _instance = None

    def __new__(cls):
        """Creates or returns the singleton instance of RCMNumberer.

        Args:
            cls: The class itself.

        Returns:
            RCMNumberer: The singleton instance of RCMNumberer.
        """
        if cls._instance is None:
            cls._instance = super(RCMNumberer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the RCMNumberer.

        This constructor does not take any arguments as the RCMNumberer
        is stateless and implemented as a singleton.
        """
        pass

    def to_tcl(self) -> str:
        """Generates the Tcl command string for an RCM numberer.

        Returns:
            str: The Tcl command string, e.g., "numberer RCM".

        Example:
            >>> from femora.numberer import RCMNumberer
            >>> num = RCMNumberer()
            >>> print(num.to_tcl())
            numberer RCM
        """
        return "numberer RCM"


class AMDNumberer(Numberer):
    """Implements an Alternate Minimum Degree (AMD) numberer.

    This numberer is designed to minimize fill-in (new non-zero elements)
    during the matrix factorization process, which can reduce memory usage
    and computation time for sparse matrix solvers. It is implemented as a singleton.

    Attributes:
        _instance (AMDNumberer or None): The singleton instance of the class.

    Example:
        >>> from femora.numberer import AMDNumberer
        >>> num1 = AMDNumberer()
        >>> num2 = AMDNumberer()
        >>> print(num1 is num2)
        True
        >>> print(num1.to_tcl())
        numberer AMD
    """
    _instance = None

    def __new__(cls):
        """Creates or returns the singleton instance of AMDNumberer.

        Args:
            cls: The class itself.

        Returns:
            AMDNumberer: The singleton instance of AMDNumberer.
        """
        if cls._instance is None:
            cls._instance = super(AMDNumberer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the AMDNumberer.

        This constructor does not take any arguments as the AMDNumberer
        is stateless and implemented as a singleton.
        """
        pass

    def to_tcl(self) -> str:
        """Generates the Tcl command string for an AMD numberer.

        Returns:
            str: The Tcl command string, e.g., "numberer AMD".

        Example:
            >>> from femora.numberer import AMDNumberer
            >>> num = AMDNumberer()
            >>> print(num.to_tcl())
            numberer AMD
        """
        return "numberer AMD"


class ParallelRCMNumberer(Numberer):
    """Implements a Parallel Reverse Cuthill-McKee (ParallelRCM) numberer.

    This numberer is a parallelized version of the RCM algorithm, designed
    to improve performance on large systems while still reducing the bandwidth
    of the system matrix. It is implemented as a singleton.

    Attributes:
        _instance (ParallelRCMNumberer or None): The singleton instance of the class.

    Example:
        >>> from femora.numberer import ParallelRCMNumberer
        >>> num1 = ParallelRCMNumberer()
        >>> num2 = ParallelRCMNumberer()
        >>> print(num1 is num2)
        True
        >>> print(num1.to_tcl())
        numberer ParallelRCM
    """
    _instance = None

    def __new__(cls):
        """Creates or returns the singleton instance of ParallelRCMNumberer.

        Args:
            cls: The class itself.

        Returns:
            ParallelRCMNumberer: The singleton instance of ParallelRCMNumberer.
        """
        if cls._instance is None:
            cls._instance = super(ParallelRCMNumberer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the ParallelRCMNumberer.

        This constructor does not take any arguments as the ParallelRCMNumberer
        is stateless and implemented as a singleton.
        """
        pass

    def to_tcl(self) -> str:
        """Generates the Tcl command string for a ParallelRCM numberer.

        Returns:
            str: The Tcl command string, e.g., "numberer ParallelRCM".

        Example:
            >>> from femora.numberer import ParallelRCMNumberer
            >>> num = ParallelRCMNumberer()
            >>> print(num.to_tcl())
            numberer ParallelRCM
        """
        return "numberer ParallelRCM"


class NumbererManager:
    """Manages instances and operations related to numberers.

    This class acts as a central point for obtaining, creating, and managing
    different types of numberers. It ensures that numberer instances are reused
    (singleton pattern for numberers themselves) and provides convenient
    access to common numberer types. The manager itself is a singleton.

    Attributes:
        _instance (NumbererManager or None): The singleton instance of the class.
        _numberer_instances (dict[str, Numberer]): A dictionary caching
            the specific numberer instances managed by this manager.
        rcm (Type[RCMNumberer]): Direct access to the RCMNumberer class.
        plain (Type[PlainNumberer]): Direct access to the PlainNumberer class.
        amd (Type[AMDNumberer]): Direct access to the AMDNumberer class.
        parallelrcm (Type[ParallelRCMNumberer]): Direct access to the ParallelRCMNumberer class.

    Example:
        >>> from femora.numberer import NumbererManager
        >>> manager1 = NumbererManager()
        >>> manager2 = NumbererManager()
        >>> print(manager1 is manager2)
        True
        >>> plain_num = manager1.get_numberer('plain')
        >>> print(plain_num.to_tcl())
        numberer Plain
    """
    _instance = None
    _numberer_instances = {}

    def __new__(cls):
        """Creates or returns the singleton instance of NumbererManager.

        Args:
            cls: The class itself.

        Returns:
            NumbererManager: The singleton instance of NumbererManager.
        """
        if cls._instance is None:
            cls._instance = super(NumbererManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the NumbererManager.

        Ensures that default numberer types are registered and their instances
        are available upon manager initialization.
        """
        # Initialize by creating all three numberer instances if they don't exist
        if not NumbererManager._numberer_instances:
            self._initialize_default_numberers()
        self.rcm = RCMNumberer
        self.plain = PlainNumberer
        self.amd = AMDNumberer
        self.parallelrcm = ParallelRCMNumberer


    def _initialize_default_numberers(self):
        """Automatically creates instances of the default numberer types.

        This method ensures that common numberers like 'plain', 'rcm', 'amd',
        and 'parallelrcm' are instantiated and cached when the manager is initialized.
        """
        self.get_numberer('plain')
        self.get_numberer('rcm')
        self.get_numberer('amd')
        self.get_numberer('parallelrcm')

    @classmethod
    def get_instance(cls) -> 'NumbererManager':
        """Retrieves the singleton instance of NumbererManager.

        Returns:
            NumbererManager: The single instance of the NumbererManager.

        Example:
            >>> from femora.numberer import NumbererManager
            >>> manager1 = NumbererManager.get_instance()
            >>> manager2 = NumbererManager.get_instance()
            >>> print(manager1 is manager2)
            True
        """
        if cls._instance is None:
            cls._instance = NumbererManager()
        return cls._instance

    def get_numberer(self, numberer_type: str) -> Numberer:
        """Retrieves a numberer instance of the specified type.

        This method first checks if an instance of the requested numberer type
        already exists (either in the global `Numberer` cache or the manager's
        own cache). If not found, it creates a new instance.

        Args:
            numberer_type: The string name of the numberer type to retrieve (e.g., 'plain', 'rcm').

        Returns:
            Numberer: An instance of the requested numberer type.

        Example:
            >>> from femora.numberer import NumbererManager, PlainNumberer
            >>> manager = NumbererManager.get_instance()
            >>> plain_num1 = manager.get_numberer('plain')
            >>> plain_num2 = manager.get_numberer('plain')
            >>> print(plain_num1 is plain_num2)
            True
            >>> print(isinstance(plain_num1, PlainNumberer))
            True
        """
        numberer_type = numberer_type.lower()

        # Check if the numberer already exists in Numberer class
        existing_numberer = Numberer.get_instance(numberer_type)
        if existing_numberer:
            # Update manager's instance dictionary if needed
            NumbererManager._numberer_instances[numberer_type] = existing_numberer
            return existing_numberer

        # Create new numberer if not found
        if numberer_type not in NumbererManager._numberer_instances:
            NumbererManager._numberer_instances[numberer_type] = Numberer.create_numberer(numberer_type)

        return NumbererManager._numberer_instances[numberer_type]


    def create_numberer(self, numberer_type: str) -> Numberer:
        """Creates a new numberer instance of the specified type.

        This method acts as an alias for `get_numberer`, ensuring that the
        numberer instance is created and cached if it doesn't already exist.

        Args:
            numberer_type: The string name of the numberer type to create.

        Returns:
            Numberer: A new or existing instance of the specified numberer type.

        Example:
            >>> from femora.numberer import NumbererManager, RCMNumberer
            >>> manager = NumbererManager.get_instance()
            >>> rcm_num = manager.create_numberer('rcm')
            >>> print(isinstance(rcm_num, RCMNumberer))
            True
        """
        return self.get_numberer(numberer_type)


    def get_all_numberers(self) -> Dict[str, Numberer]:
        """Returns a dictionary of all available numberer instances.

        This method ensures that all registered numberer types have
        corresponding instances created and cached, then returns them.

        Returns:
            dict[str, Numberer]: A dictionary where keys are numberer type names
                and values are their respective instances.

        Example:
            >>> from femora.numberer import NumbererManager, PlainNumberer, RCMNumberer
            >>> manager = NumbererManager.get_instance()
            >>> all_nums = manager.get_all_numberers()
            >>> print('plain' in all_nums)
            True
            >>> print(isinstance(all_nums['plain'], PlainNumberer))
            True
        """
        for numberer_type in Numberer.get_available_types():
            self.get_numberer(numberer_type)
        return NumbererManager._numberer_instances

    def reset(self):
        """Clears all cached numberer instances from both the manager and the global Numberer class.

        This effectively resets the state of all numberer singletons and caches.

        Example:
            >>> from femora.numberer import NumbererManager, PlainNumberer
            >>> manager = NumbererManager.get_instance()
            >>> plain1 = manager.get_numberer('plain')
            >>> manager.reset()
            >>> plain2 = manager.get_numberer('plain')
            >>> print(plain1 is plain2)
            False
        """
        NumbererManager._numberer_instances.clear()
        Numberer.reset_instances()


# Register all numberers
Numberer.register_numberer('plain', PlainNumberer)
Numberer.register_numberer('rcm', RCMNumberer)
Numberer.register_numberer('amd', AMDNumberer)
Numberer.register_numberer('parallelrcm', ParallelRCMNumberer)