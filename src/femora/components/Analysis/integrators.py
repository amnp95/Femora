from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import ABC, abstractmethod


class Integrator(AnalysisComponent):
    """Base abstract class for numerical integrators in structural analysis.

    Integrators determine how displacement, velocity, and acceleration (or load
    and displacement increments in static analysis) are updated in nonlinear
    solution algorithms. This class provides a common interface and management
    for various integrator types, abstracting away the specifics of each.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): A string indicating the specific type of
            integrator (e.g., "LoadControl", "Newmark").
        _integrators (dict[str, Type[Integrator]]): A class-level dictionary
            mapping string names to integrator classes for creation.
        _created_integrators (dict[int, Integrator]): A class-level dictionary
            tracking all active integrator instances by their unique tags.
        _next_tag (int): A class variable used to assign the next available
            unique tag to a new integrator instance.

    Example:
        >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
        >>> # Register LoadControlIntegrator if not already done via file-level calls
        >>> if 'loadcontrol' not in Integrator.get_available_types():
        ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
        >>> load_control_integrator = Integrator.create_integrator('loadcontrol', incr=0.1)
        >>> print(load_control_integrator.tag)
        1
        >>> print(load_control_integrator.integrator_type)
        LoadControl
    """
    _integrators: Dict[str, Type['Integrator']] = {}  # Class-level dictionary to store integrator types
    _created_integrators: Dict[int, 'Integrator'] = {}  # Class-level dictionary to track all created integrators
    _next_tag: int = 1  # Class variable to track the next tag to assign
    
    def __init__(self, integrator_type: str):
        """Initializes an Integrator instance.

        This constructor assigns a unique tag to the integrator and registers it
        within the class-level tracking system.

        Args:
            integrator_type: The string identifier for the type of integrator.

        Example:
            >>> # This __init__ is typically called by subclasses or factory methods.
            >>> # For example, a subclass might call:
            >>> # super().__init__("LoadControl")
            >>> from femora.analysis.integrators import LoadControlIntegrator
            >>> lc = LoadControlIntegrator(incr=0.1)
            >>> print(lc.integrator_type)
            LoadControl
        """
        self.tag = Integrator._next_tag
        Integrator._next_tag += 1
        self.integrator_type = integrator_type
        
        # Register this integrator in the class-level tracking dictionary
        Integrator._created_integrators[self.tag] = self
    
    @staticmethod
    def register_integrator(name: str, integrator_class: Type['Integrator']):
        """Registers an integrator class with a given name.

        This static method allows custom integrator types to be added to the
        system, making them available for creation via `create_integrator`.

        Args:
            name: The string name to associate with the integrator class.
            integrator_class: The class object of the integrator to register.

        Example:
            >>> from femora.analysis.integrators import Integrator
            >>> class CustomIntegrator(Integrator):
            ...     def __init__(self):
            ...         super().__init__("Custom")
            ...     def get_values(self): return {}
            ...     def to_tcl(self): return "integrator Custom"
            >>> Integrator.register_integrator('custom_test', CustomIntegrator)
            >>> print('custom_test' in Integrator.get_available_types())
            True
        """
        Integrator._integrators[name.lower()] = integrator_class
    
    @staticmethod
    def create_integrator(integrator_type: str, **kwargs) -> 'Integrator':
        """Creates an integrator instance of the specified type.

        This factory method simplifies the creation of integrators by looking up
        the appropriate class from the registered types and instantiating it
        with the given keyword arguments.

        Args:
            integrator_type: The string identifier for the desired integrator type.
            **kwargs: Arbitrary keyword arguments to pass to the constructor of
                the specific integrator class.

        Returns:
            Integrator: An instance of the requested integrator type.

        Raises:
            ValueError: If an unknown `integrator_type` is requested.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> # Register LoadControlIntegrator first if not already done
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> integrator = Integrator.create_integrator('loadcontrol', incr=0.05, num_iter=5)
            >>> print(integrator.integrator_type)
            LoadControl
            >>> # Attempting to create an unregistered type raises an error
            >>> try:
            ...     Integrator.create_integrator('unknown', param=1)
            ... except ValueError as e:
            ...     print(e)
            Unknown integrator type: unknown
        """
        integrator_type = integrator_type.lower()
        if integrator_type not in Integrator._integrators:
            raise ValueError(f"Unknown integrator type: {integrator_type}")
        return Integrator._integrators[integrator_type](**kwargs)
    
    @staticmethod
    def get_available_types() -> List[str]:
        """Returns a list of all registered integrator types.

        Returns:
            list[str]: A list of string names for available integrator types.

        Example:
            >>> from femora.analysis.integrators import Integrator, NewmarkIntegrator
            >>> if 'newmark' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('newmark', NewmarkIntegrator)
            >>> types = Integrator.get_available_types()
            >>> print('newmark' in types)
            True
            >>> print(isinstance(types, list))
            True
        """
        return list(Integrator._integrators.keys())
    
    @classmethod
    def get_integrator(cls, tag: int) -> 'Integrator':
        """Retrieves a specific integrator instance by its unique tag.

        Args:
            tag: The unique integer tag of the integrator to retrieve.

        Returns:
            Integrator: The integrator instance with the specified tag.

        Raises:
            KeyError: If no integrator with the given tag exists.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> Integrator.clear_all() # Start fresh for example consistency
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> integrator1 = Integrator.create_integrator('loadcontrol', incr=0.1)
            >>> integrator2 = Integrator.create_integrator('loadcontrol', incr=0.2)
            >>> retrieved_integrator = Integrator.get_integrator(integrator1.tag)
            >>> print(retrieved_integrator.tag)
            1
            >>> print(retrieved_integrator.incr)
            0.1
            >>> try:
            ...     Integrator.get_integrator(999)
            ... except KeyError as e:
            ...     print(e)
            No integrator found with tag 999
        """
        if tag not in cls._created_integrators:
            raise KeyError(f"No integrator found with tag {tag}")
        return cls._created_integrators[tag]

    @classmethod
    def get_all_integrators(cls) -> Dict[int, 'Integrator']:
        """Retrieves all created integrator instances.

        Returns:
            dict[int, Integrator]: A dictionary where keys are unique integrator
                tags and values are the corresponding integrator instances.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> Integrator.clear_all()
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> integrator1 = Integrator.create_integrator('loadcontrol', incr=0.1)
            >>> integrator2 = Integrator.create_integrator('loadcontrol', incr=0.2)
            >>> all_integrators = Integrator.get_all_integrators()
            >>> print(len(all_integrators))
            2
            >>> print(all_integrators[integrator1.tag].incr)
            0.1
        """
        return cls._created_integrators
    
    @classmethod
    def clear_all(cls) -> None:
        """Clears all created integrator instances and resets the tag counter.

        This method removes all registered integrator objects, effectively
        resetting the integrator system.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> Integrator.clear_all()
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> _ = Integrator.create_integrator('loadcontrol', incr=0.1)
            >>> print(len(Integrator.get_all_integrators()))
            1
            >>> Integrator.clear_all()
            >>> print(len(Integrator.get_all_integrators()))
            0
        """
        cls._created_integrators.clear()
        cls._next_tag = 1
    
    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        This abstract method must be implemented by concrete integrator
        subclasses to expose their internal configuration.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> # This is an abstract method and must be implemented by subclasses.
            >>> from femora.analysis.integrators import LoadControlIntegrator
            >>> load_control = LoadControlIntegrator(incr=0.1, num_iter=5)
            >>> values = load_control.get_values()
            >>> print(values['incr'])
            0.1
            >>> print(values['num_iter'])
            5
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all integrators sequentially starting from 1.

        This internal method is called after an integrator is removed to ensure
        that existing integrators maintain a contiguous and sequential tagging.
        """
        new_integrators = {}
        for idx, integrator in enumerate(sorted(cls._created_integrators.values(), key=lambda i: i.tag), start=1):
            integrator.tag = idx
            new_integrators[idx] = integrator
        cls._created_integrators = new_integrators
        cls._next_tag = len(cls._created_integrators) + 1

    @classmethod
    def remove_integrator(cls, tag: int) -> None:
        """Deletes an integrator by its tag and re-tags remaining integrators.

        If an integrator with the specified tag exists, it is removed, and all
        remaining integrators are re-tagged sequentially from 1 to maintain
        a clean numbering system.

        Args:
            tag: The unique integer tag of the integrator to delete.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> Integrator.clear_all()
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> integrator1 = Integrator.create_integrator('loadcontrol', incr=0.1)
            >>> integrator2 = Integrator.create_integrator('loadcontrol', incr=0.2)
            >>> integrator3 = Integrator.create_integrator('loadcontrol', incr=0.3)
            >>> print(list(Integrator.get_all_integrators().keys()))
            [1, 2, 3]
            >>> Integrator.remove_integrator(2)
            >>> print(list(Integrator.get_all_integrators().keys()))
            [1, 2]
            >>> print(Integrator.get_integrator(2).incr)
            0.3
        """
        if tag in cls._created_integrators:
            del cls._created_integrators[tag]
            cls._reassign_tags()


class StaticIntegrator(Integrator):
    """Base abstract class for integrators used in static analysis.

    This class serves as a marker for integrators suitable for static,
    time-independent structural problems.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): The specific type of static integrator.

    Example:
        >>> from femora.analysis.integrators import LoadControlIntegrator
        >>> static_integrator = LoadControlIntegrator(incr=0.01)
        >>> print(static_integrator.integrator_type)
        LoadControl
        >>> print(isinstance(static_integrator, StaticIntegrator))
        True
    """
    def __init__(self, integrator_type: str):
        """Initializes a StaticIntegrator instance.

        Args:
            integrator_type: The string identifier for the type of static integrator.
        """
        super().__init__(integrator_type)
        
    @staticmethod
    def get_static_types() -> List[str]:
        """Returns a list of all registered static integrator types.

        Returns:
            list[str]: A list of string names for available static integrator types.

        Example:
            >>> from femora.analysis.integrators import Integrator, LoadControlIntegrator
            >>> Integrator.clear_all()
            >>> if 'loadcontrol' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
            >>> static_types = StaticIntegrator.get_static_types()
            >>> print('loadcontrol' in static_types)
            True
            >>> print(isinstance(static_types, list))
            True
        """
        return [t for t, cls in Integrator._integrators.items() 
                if issubclass(cls, StaticIntegrator)]


class TransientIntegrator(Integrator):
    """Base abstract class for integrators used in dynamic (transient) analysis.

    This class serves as a marker for integrators suitable for dynamic,
    time-dependent structural problems.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): The specific type of transient integrator.

    Example:
        >>> from femora.analysis.integrators import NewmarkIntegrator
        >>> transient_integrator = NewmarkIntegrator(gamma=0.5, beta=0.25)
        >>> print(transient_integrator.integrator_type)
        Newmark
        >>> print(isinstance(transient_integrator, TransientIntegrator))
        True
    """
    def __init__(self, integrator_type: str):
        """Initializes a TransientIntegrator instance.

        Args:
            integrator_type: The string identifier for the type of transient integrator.
        """
        super().__init__(integrator_type)
        
    @staticmethod
    def get_transient_types() -> List[str]:
        """Returns a list of all registered transient integrator types.

        Returns:
            list[str]: A list of string names for available transient
                integrator types.

        Example:
            >>> from femora.analysis.integrators import Integrator, NewmarkIntegrator
            >>> Integrator.clear_all()
            >>> if 'newmark' not in Integrator.get_available_types():
            ...     Integrator.register_integrator('newmark', NewmarkIntegrator)
            >>> transient_types = TransientIntegrator.get_transient_types()
            >>> print('newmark' in transient_types)
            True
            >>> print(isinstance(transient_types, list))
            True
        """
        return [t for t, cls in Integrator._integrators.items() 
                if issubclass(cls, TransientIntegrator)]

#------------------------------------------------------
# Static Integrators
#------------------------------------------------------

class LoadControlIntegrator(StaticIntegrator):
    """Implements the Load Control integrator for static analysis.

    This integrator applies load increments in a controlled manner, typically
    used for monotonic loading paths where the load is the primary control variable.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "LoadControl".
        incr (float): The load factor increment.
        num_iter (int): The target number of iterations for the solution algorithm.
        min_incr (float): The minimum allowed load increment.
        max_incr (float): The maximum allowed load increment.

    Example:
        >>> from femora.analysis.integrators import LoadControlIntegrator
        >>> lc_integrator = LoadControlIntegrator(incr=0.1, num_iter=10, min_incr=0.01, max_incr=0.2)
        >>> print(lc_integrator.integrator_type)
        LoadControl
        >>> print(lc_integrator.incr)
        0.1
        >>> print(lc_integrator.to_tcl())
        integrator LoadControl 0.1 10 0.01 0.2
    """
    def __init__(self, incr: float, num_iter: int = 1, min_incr: Optional[float] = None, 
                 max_incr: Optional[float] = None):
        """Initializes a LoadControlIntegrator.

        Args:
            incr: The initial load factor increment to apply.
            num_iter: Optional. The target number of iterations the user would
                like to occur in the solution algorithm. Defaults to 1.
            min_incr: Optional. The minimum step size (load increment) the
                solver will allow. Defaults to `incr`.
            max_incr: Optional. The maximum step size (load increment) the
                solver will allow. Defaults to `incr`.

        Example:
            >>> from femora.analysis.integrators import LoadControlIntegrator
            >>> lc = LoadControlIntegrator(incr=0.05)
            >>> print(lc.incr)
            0.05
            >>> print(lc.min_incr)
            0.05
            >>> lc_detailed = LoadControlIntegrator(incr=0.1, num_iter=5, min_incr=0.02, max_incr=0.15)
            >>> print(lc_detailed.num_iter)
            5
        """
        super().__init__("LoadControl")
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import LoadControlIntegrator
            >>> lc = LoadControlIntegrator(incr=0.01, num_iter=2, min_incr=0.005, max_incr=0.02)
            >>> print(lc.to_tcl())
            integrator LoadControl 0.01 2 0.005 0.02
        """
        return f"integrator LoadControl {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import LoadControlIntegrator
            >>> lc = LoadControlIntegrator(incr=0.1)
            >>> values = lc.get_values()
            >>> print(values['incr'])
            0.1
            >>> print(values['num_iter'])
            1
        """
        return {
            "incr": self.incr,
            "num_iter": self.num_iter,
            "min_incr": self.min_incr,
            "max_incr": self.max_incr
        }


class DisplacementControlIntegrator(StaticIntegrator):
    """Implements the Displacement Control integrator for static analysis.

    This integrator controls the solution by incrementing the displacement at
    a specified node and degree of freedom, useful for capturing post-peak behavior.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "DisplacementControl".
        node_tag (int): The tag of the node whose displacement response controls
            the solution.
        dof (int): The degree of freedom (1 through ndf) at the control node.
        incr (float): The first displacement increment.
        num_iter (int): The target number of iterations for the solution algorithm.
        min_incr (float): The minimum allowed displacement increment.
        max_incr (float): The maximum allowed displacement increment.

    Example:
        >>> from femora.analysis.integrators import DisplacementControlIntegrator
        >>> dc_integrator = DisplacementControlIntegrator(node_tag=10, dof=2, incr=0.001)
        >>> print(dc_integrator.integrator_type)
        DisplacementControl
        >>> print(dc_integrator.node_tag)
        10
        >>> print(dc_integrator.to_tcl())
        integrator DisplacementControl 10 2 0.001 1 0.001 0.001
    """
    def __init__(self, node_tag: int, dof: int, incr: float, num_iter: int = 1, 
                 min_incr: Optional[float] = None, max_incr: Optional[float] = None):
        """Initializes a DisplacementControlIntegrator.

        Args:
            node_tag: The tag of the node whose response controls the solution.
            dof: The degree of freedom (1 through ndf) at the specified node.
            incr: The first displacement increment to apply.
            num_iter: Optional. The target number of iterations the user would
                like to occur. Defaults to 1.
            min_incr: Optional. The minimum step size (displacement increment)
                the solver will allow. Defaults to `incr`.
            max_incr: Optional. The maximum step size (displacement increment)
                the solver will allow. Defaults to `incr`.

        Example:
            >>> from femora.analysis.integrators import DisplacementControlIntegrator
            >>> dc = DisplacementControlIntegrator(node_tag=5, dof=1, incr=0.005)
            >>> print(dc.node_tag)
            5
            >>> print(dc.dof)
            1
            >>> print(dc.incr)
            0.005
        """
        super().__init__("DisplacementControl")
        self.node_tag = node_tag
        self.dof = dof
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import DisplacementControlIntegrator
            >>> dc = DisplacementControlIntegrator(node_tag=1, dof=3, incr=0.002)
            >>> print(dc.to_tcl())
            integrator DisplacementControl 1 3 0.002 1 0.002 0.002
        """
        return f"integrator DisplacementControl {self.node_tag} {self.dof} {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import DisplacementControlIntegrator
            >>> dc = DisplacementControlIntegrator(node_tag=2, dof=2, incr=0.01, num_iter=3)
            >>> values = dc.get_values()
            >>> print(values['node_tag'])
            2
            >>> print(values['incr'])
            0.01
        """
        return {
            "node_tag": self.node_tag,
            "dof": self.dof,
            "incr": self.incr,
            "num_iter": self.num_iter,
            "min_incr": self.min_incr,
            "max_incr": self.max_incr
        }


class ParallelDisplacementControlIntegrator(StaticIntegrator):
    """Implements the Parallel Displacement Control integrator for static analysis.

    This integrator is similar to `DisplacementControlIntegrator` but designed
    for parallel processing environments. It controls the solution by incrementing
    the displacement at a specified node and degree of freedom.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "ParallelDisplacementControl".
        node_tag (int): The tag of the node whose displacement response controls
            the solution.
        dof (int): The degree of freedom (1 through ndf) at the control node.
        incr (float): The first displacement increment.
        num_iter (int): The target number of iterations for the solution algorithm.
        min_incr (float): The minimum allowed displacement increment.
        max_incr (float): The maximum allowed displacement increment.

    Example:
        >>> from femora.analysis.integrators import ParallelDisplacementControlIntegrator
        >>> pdc_integrator = ParallelDisplacementControlIntegrator(node_tag=20, dof=3, incr=0.0005)
        >>> print(pdc_integrator.integrator_type)
        ParallelDisplacementControl
        >>> print(pdc_integrator.node_tag)
        20
        >>> print(pdc_integrator.to_tcl())
        integrator ParallelDisplacementControl 20 3 0.0005 1 0.0005 0.0005
    """
    def __init__(self, node_tag: int, dof: int, incr: float, num_iter: int = 1, 
                 min_incr: Optional[float] = None, max_incr: Optional[float] = None):
        """Initializes a ParallelDisplacementControlIntegrator.

        Args:
            node_tag: The tag of the node whose response controls the solution.
            dof: The degree of freedom (1 through ndf) at the specified node.
            incr: The first displacement increment to apply.
            num_iter: Optional. The target number of iterations the user would
                like to occur. Defaults to 1.
            min_incr: Optional. The minimum step size (displacement increment)
                the solver will allow. Defaults to `incr`.
            max_incr: Optional. The maximum step size (displacement increment)
                the solver will allow. Defaults to `incr`.

        Example:
            >>> from femora.analysis.integrators import ParallelDisplacementControlIntegrator
            >>> pdc = ParallelDisplacementControlIntegrator(node_tag=6, dof=2, incr=0.001)
            >>> print(pdc.node_tag)
            6
            >>> print(pdc.incr)
            0.001
        """
        super().__init__("ParallelDisplacementControl")
        self.node_tag = node_tag
        self.dof = dof
        self.incr = incr
        self.num_iter = num_iter
        self.min_incr = min_incr if min_incr is not None else incr
        self.max_incr = max_incr if max_incr is not None else incr
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import ParallelDisplacementControlIntegrator
            >>> pdc = ParallelDisplacementControlIntegrator(node_tag=1, dof=1, incr=0.0001)
            >>> print(pdc.to_tcl())
            integrator ParallelDisplacementControl 1 1 0.0001 1 0.0001 0.0001
        """
        return f"integrator ParallelDisplacementControl {self.node_tag} {self.dof} {self.incr} {self.num_iter} {self.min_incr} {self.max_incr}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import ParallelDisplacementControlIntegrator
            >>> pdc = ParallelDisplacementControlIntegrator(node_tag=3, dof=3, incr=0.0005)
            >>> values = pdc.get_values()
            >>> print(values['node_tag'])
            3
            >>> print(values['dof'])
            3
        """
        return {
            "node_tag": self.node_tag,
            "dof": self.dof,
            "incr": self.incr,
            "num_iter": self.num_iter,
            "min_incr": self.min_incr,
            "max_incr": self.max_incr
        }


class MinUnbalDispNormIntegrator(StaticIntegrator):
    """Implements the Minimum Unbalanced Displacement Norm integrator for static analysis.

    This integrator attempts to minimize the norm of the unbalanced displacement
    vector, often used in adaptive stepping algorithms for static analysis.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "MinUnbalDispNorm".
        dlambda1 (float): The first load increment (pseudo-time step).
        jd (int): A factor relating the first load increment at subsequent time steps.
        min_lambda (float): The minimum load increment.
        max_lambda (float): The maximum load increment.
        det (bool): A flag indicating whether to use the determinant of the
            tangent matrix in the algorithm.

    Example:
        >>> from femora.analysis.integrators import MinUnbalDispNormIntegrator
        >>> mudn_integrator = MinUnbalDispNormIntegrator(dlambda1=0.005, jd=2, min_lambda=0.001, max_lambda=0.01, det=True)
        >>> print(mudn_integrator.integrator_type)
        MinUnbalDispNorm
        >>> print(mudn_integrator.dlambda1)
        0.005
        >>> print(mudn_integrator.to_tcl())
        integrator MinUnbalDispNorm 0.005 2 0.001 0.01 -det
    """
    def __init__(self, dlambda1: float, jd: int = 1, min_lambda: Optional[float] = None, 
                 max_lambda: Optional[float] = None, det: bool = False):
        """Initializes a MinUnbalDispNormIntegrator.

        Args:
            dlambda1: The first load increment (pseudo-time step) to apply.
            jd: Optional. A factor relating the first load increment at subsequent
                time steps. Defaults to 1.
            min_lambda: Optional. The minimum load increment allowed.
                Defaults to `dlambda1`.
            max_lambda: Optional. The maximum load increment allowed.
                Defaults to `dlambda1`.
            det: Optional. A flag indicating whether to use the determinant
                of the tangent matrix. Defaults to False.

        Example:
            >>> from femora.analysis.integrators import MinUnbalDispNormIntegrator
            >>> mudn = MinUnbalDispNormIntegrator(dlambda1=0.001)
            >>> print(mudn.dlambda1)
            0.001
            >>> print(mudn.jd)
            1
            >>> mudn_det = MinUnbalDispNormIntegrator(dlambda1=0.01, det=True)
            >>> print(mudn_det.det)
            True
        """
        super().__init__("MinUnbalDispNorm")
        self.dlambda1 = dlambda1
        self.jd = jd
        self.min_lambda = min_lambda if min_lambda is not None else dlambda1
        self.max_lambda = max_lambda if max_lambda is not None else dlambda1
        self.det = det
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import MinUnbalDispNormIntegrator
            >>> mudn = MinUnbalDispNormIntegrator(dlambda1=0.001, jd=1, min_lambda=0.0005, max_lambda=0.002, det=False)
            >>> print(mudn.to_tcl())
            integrator MinUnbalDispNorm 0.001 1 0.0005 0.002
            >>> mudn_det = MinUnbalDispNormIntegrator(dlambda1=0.01, det=True)
            >>> print(mudn_det.to_tcl())
            integrator MinUnbalDispNorm 0.01 1 0.01 0.01 -det
        """
        det_str = " -det" if self.det else ""
        return f"integrator MinUnbalDispNorm {self.dlambda1} {self.jd} {self.min_lambda} {self.max_lambda}{det_str}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import MinUnbalDispNormIntegrator
            >>> mudn = MinUnbalDispNormIntegrator(dlambda1=0.001, det=True)
            >>> values = mudn.get_values()
            >>> print(values['dlambda1'])
            0.001
            >>> print(values['det'])
            True
        """
        return {
            "dlambda1": self.dlambda1,
            "jd": self.jd,
            "min_lambda": self.min_lambda,
            "max_lambda": self.max_lambda,
            "det": self.det
        }


class ArcLengthIntegrator(StaticIntegrator):
    """Implements the Arc-Length Control integrator for static analysis.

    This integrator uses a path-following technique where the solution progresses
    along a prescribed arc-length in the load-displacement space, enabling the
    capture of limit points and post-peak response.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "ArcLength".
        s (float): The arc length parameter for the incrementation.
        alpha (float): A scaling factor on the reference loads.

    Example:
        >>> from femora.analysis.integrators import ArcLengthIntegrator
        >>> al_integrator = ArcLengthIntegrator(s=0.1, alpha=0.5)
        >>> print(al_integrator.integrator_type)
        ArcLength
        >>> print(al_integrator.s)
        0.1
        >>> print(al_integrator.to_tcl())
        integrator ArcLength 0.1 0.5
    """
    def __init__(self, s: float, alpha: float):
        """Initializes an ArcLengthIntegrator.

        Args:
            s: The arc length parameter for the incrementation.
            alpha: A scaling factor applied to the reference loads, affecting
                how much the load contributes to the arc-length increment.

        Example:
            >>> from femora.analysis.integrators import ArcLengthIntegrator
            >>> al = ArcLengthIntegrator(s=0.01, alpha=0.7)
            >>> print(al.s)
            0.01
            >>> print(al.alpha)
            0.7
        """
        super().__init__("ArcLength")
        self.s = s
        self.alpha = alpha
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import ArcLengthIntegrator
            >>> al = ArcLengthIntegrator(s=0.05, alpha=0.6)
            >>> print(al.to_tcl())
            integrator ArcLength 0.05 0.6
        """
        return f"integrator ArcLength {self.s} {self.alpha}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import ArcLengthIntegrator
            >>> al = ArcLengthIntegrator(s=0.1, alpha=0.5)
            >>> values = al.get_values()
            >>> print(values['s'])
            0.1
            >>> print(values['alpha'])
            0.5
        """
        return {
            "s": self.s,
            "alpha": self.alpha
        }


#------------------------------------------------------
# Transient Integrators
#------------------------------------------------------

class CentralDifferenceIntegrator(TransientIntegrator):
    """Implements the Central Difference integrator for dynamic analysis.

    The Central Difference method is an explicit, conditionally stable integrator
    often used for wave propagation problems or when mass and stiffness matrices
    are diagonal (lumped).

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "CentralDifference".

    Example:
        >>> from femora.analysis.integrators import CentralDifferenceIntegrator
        >>> cd_integrator = CentralDifferenceIntegrator()
        >>> print(cd_integrator.integrator_type)
        CentralDifference
        >>> print(cd_integrator.to_tcl())
        integrator CentralDifference
    """
    def __init__(self):
        """Initializes a CentralDifferenceIntegrator.

        Example:
            >>> from femora.analysis.integrators import CentralDifferenceIntegrator
            >>> cd = CentralDifferenceIntegrator()
            >>> print(cd.integrator_type)
            CentralDifference
        """
        super().__init__("CentralDifference")
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import CentralDifferenceIntegrator
            >>> cd = CentralDifferenceIntegrator()
            >>> print(cd.to_tcl())
            integrator CentralDifference
        """
        return "integrator CentralDifference"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: An empty dictionary
                as Central Difference has no parameters.

        Example:
            >>> from femora.analysis.integrators import CentralDifferenceIntegrator
            >>> cd = CentralDifferenceIntegrator()
            >>> values = cd.get_values()
            >>> print(values)
            {}
        """
        return {}


class NewmarkIntegrator(TransientIntegrator):
    """Implements the Newmark Method integrator for dynamic analysis.

    The Newmark-beta method is a widely used family of implicit, unconditionally
    stable integrators for dynamic structural analysis, allowing for control
    over numerical damping and period elongation through `gamma` and `beta` parameters.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "Newmark".
        gamma (float): The gamma parameter of the Newmark method.
        beta (float): The beta parameter of the Newmark method.
        form (str): Flag indicating the primary variable for integration:
            'D' (displacement), 'V' (velocity), or 'A' (acceleration).

    Example:
        >>> from femora.analysis.integrators import NewmarkIntegrator
        >>> newmark_integrator = NewmarkIntegrator(gamma=0.5, beta=0.25)
        >>> print(newmark_integrator.integrator_type)
        Newmark
        >>> print(newmark_integrator.gamma)
        0.5
        >>> print(newmark_integrator.to_tcl())
        integrator Newmark 0.5 0.25
        >>> newmark_v = NewmarkIntegrator(gamma=0.6, beta=0.3, form='V')
        >>> print(newmark_v.to_tcl())
        integrator Newmark 0.6 0.3 -form V
    """
    def __init__(self, gamma: float, beta: float, form: str = "D"):
        """Initializes a NewmarkIntegrator.

        Args:
            gamma: The gamma factor, typically between 0.5 and 1.0.
            beta: The beta factor, typically between 0.0 and 0.5.
            form: Optional. A flag to indicate the primary variable for
                integration. Can be 'D' (displacement, default), 'V' (velocity),
                or 'A' (acceleration).

        Raises:
            ValueError: If `form` is not one of 'D', 'V', or 'A'.

        Example:
            >>> from femora.analysis.integrators import NewmarkIntegrator
            >>> nm = NewmarkIntegrator(gamma=0.6, beta=0.3025)
            >>> print(nm.gamma)
            0.6
            >>> print(nm.beta)
            0.3025
            >>> try:
            ...     NewmarkIntegrator(gamma=0.5, beta=0.25, form='X')
            ... except ValueError as e:
            ...     print(e)
            form must be one of 'D', 'V', or 'A'
        """
        super().__init__("Newmark")
        self.gamma = gamma
        self.beta = beta
        if form not in ["D", "V", "A"]:
            raise ValueError("form must be one of 'D', 'V', or 'A'")
        self.form = form
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import NewmarkIntegrator
            >>> nm = NewmarkIntegrator(gamma=0.5, beta=0.25)
            >>> print(nm.to_tcl())
            integrator Newmark 0.5 0.25
            >>> nm_vel = NewmarkIntegrator(gamma=0.6, beta=0.3, form='V')
            >>> print(nm_vel.to_tcl())
            integrator Newmark 0.6 0.3 -form V
        """
        if self.form == "D":
            return f"integrator Newmark {self.gamma} {self.beta}"
        else:
            return f"integrator Newmark {self.gamma} {self.beta} -form {self.form}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import NewmarkIntegrator
            >>> nm = NewmarkIntegrator(gamma=0.6, beta=0.3, form='A')
            >>> values = nm.get_values()
            >>> print(values['gamma'])
            0.6
            >>> print(values['form'])
            A
        """
        return {
            "gamma": self.gamma,
            "beta": self.beta,
            "form": self.form
        }


class HHTIntegrator(TransientIntegrator):
    """Implements the Hilber-Hughes-Taylor (HHT) Method integrator for dynamic analysis.

    The HHT-alpha method is an implicit, unconditionally stable integrator that
    introduces numerical dissipation while minimizing period elongation, making
    it suitable for a wide range of dynamic problems.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "HHT".
        alpha (float): The alpha parameter controlling numerical dissipation.
        gamma (float): The gamma parameter.
        beta (float): The beta parameter.

    Example:
        >>> from femora.analysis.integrators import HHTIntegrator
        >>> hht_integrator = HHTIntegrator(alpha=-0.1)
        >>> print(hht_integrator.integrator_type)
        HHT
        >>> print(hht_integrator.alpha)
        -0.1
        >>> # Python's float precision may vary, so format for exact match
        >>> print(f"{hht_integrator.gamma:.3f}")
        1.600
        >>> print(f"{hht_integrator.beta:.3f}")
        0.551
        >>> # Actual TCL string will have more precision
        >>> # print(hht_integrator.to_tcl())
    """
    def __init__(self, alpha: float, gamma: Optional[float] = None, beta: Optional[float] = None):
        """Initializes an HHTIntegrator.

        Args:
            alpha: The alpha factor, typically between -1/3 and 0 for
                unconditional stability and numerical dissipation.
            gamma: Optional. The gamma factor. If None, it defaults to
                `1.5 - alpha`.
            beta: Optional. The beta factor. If None, it defaults to
                `(2 - alpha)^2 / 4`.

        Example:
            >>> from femora.analysis.integrators import HHTIntegrator
            >>> hht1 = HHTIntegrator(alpha=-0.05)
            >>> print(hht1.alpha)
            -0.05
            >>> print(f"{hht1.gamma:.2f}")
            1.55
            >>> hht2 = HHTIntegrator(alpha=0.0, gamma=0.5, beta=0.25)
            >>> print(hht2.beta)
            0.25
        """
        super().__init__("HHT")
        self.alpha = alpha
        # Default values if not provided
        if gamma is None:
            self.gamma = 1.5 - alpha
        else:
            self.gamma = gamma
            
        if beta is None:
            self.beta = ((2.0 - alpha) ** 2) / 4.0
        else:
            self.beta = beta
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import HHTIntegrator
            >>> hht = HHTIntegrator(alpha=-0.05)
            >>> print(f"integrator HHT {hht.alpha} {hht.gamma} {hht.beta}") # Replicate float precision
            integrator HHT -0.05 1.55 0.530625
        """
        return f"integrator HHT {self.alpha} {self.gamma} {self.beta}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import HHTIntegrator
            >>> hht = HHTIntegrator(alpha=-0.1)
            >>> values = hht.get_values()
            >>> print(values['alpha'])
            -0.1
            >>> print(f"{values['gamma']:.3f}")
            1.600
        """
        return {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "beta": self.beta
        }


class GeneralizedAlphaIntegrator(TransientIntegrator):
    """Implements the Generalized Alpha Method integrator for dynamic analysis.

    The Generalized-alpha method is an implicit, unconditionally stable
    integrator that offers independent control over numerical dissipation in
    high and low frequencies, making it very versatile for dynamic problems.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "GeneralizedAlpha".
        alpha_m (float): The alpha_m parameter for controlling mass matrix contribution.
        alpha_f (float): The alpha_f parameter for controlling force contribution.
        gamma (float): The gamma parameter.
        beta (float): The beta parameter.

    Example:
        >>> from femora.analysis.integrators import GeneralizedAlphaIntegrator
        >>> ga_integrator = GeneralizedAlphaIntegrator(alpha_m=0.2, alpha_f=0.4)
        >>> print(ga_integrator.integrator_type)
        GeneralizedAlpha
        >>> print(ga_integrator.alpha_m)
        0.2
        >>> print(f"{ga_integrator.gamma:.3f}")
        0.300
        >>> print(f"{ga_integrator.beta:.3f}")
        0.290
        >>> # Actual TCL string will have more precision
        >>> # print(ga_integrator.to_tcl())
    """
    def __init__(self, alpha_m: float, alpha_f: float, gamma: Optional[float] = None, 
                 beta: Optional[float] = None):
        """Initializes a GeneralizedAlphaIntegrator.

        Args:
            alpha_m: The alpha_m factor, related to controlling numerical
                damping on the mass matrix.
            alpha_f: The alpha_f factor, related to controlling numerical
                damping on the force term.
            gamma: Optional. The gamma factor. If None, it defaults to
                `0.5 + alpha_m - alpha_f`.
            beta: Optional. The beta factor. If None, it defaults to
                `(1 + alpha_m - alpha_f)^2 / 4`.

        Example:
            >>> from femora.analysis.integrators import GeneralizedAlphaIntegrator
            >>> ga1 = GeneralizedAlphaIntegrator(alpha_m=0.2, alpha_f=0.3)
            >>> print(ga1.alpha_m)
            0.2
            >>> print(f"{ga1.gamma:.2f}")
            0.40
            >>> ga2 = GeneralizedAlphaIntegrator(alpha_m=0.0, alpha_f=0.0, gamma=0.5, beta=0.25)
            >>> print(ga2.beta)
            0.25
        """
        super().__init__("GeneralizedAlpha")
        self.alpha_m = alpha_m
        self.alpha_f = alpha_f
        
        # Default values if not provided
        if gamma is None:
            self.gamma = 0.5 + alpha_m - alpha_f
        else:
            self.gamma = gamma
            
        if beta is None:
            self.beta = ((1.0 + alpha_m - alpha_f) ** 2) / 4.0
        else:
            self.beta = beta
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import GeneralizedAlphaIntegrator
            >>> ga = GeneralizedAlphaIntegrator(alpha_m=0.1, alpha_f=0.2)
            >>> print(f"integrator GeneralizedAlpha {ga.alpha_m} {ga.alpha_f} {ga.gamma} {ga.beta}") # Replicate float precision
            integrator GeneralizedAlpha 0.1 0.2 0.4 0.2025
        """
        return f"integrator GeneralizedAlpha {self.alpha_m} {self.alpha_f} {self.gamma} {self.beta}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import GeneralizedAlphaIntegrator
            >>> ga = GeneralizedAlphaIntegrator(alpha_m=0.1, alpha_f=0.1)
            >>> values = ga.get_values()
            >>> print(values['alpha_m'])
            0.1
            >>> print(f"{values['beta']:.2f}")
            0.25
        """
        return {
            "alpha_m": self.alpha_m,
            "alpha_f": self.alpha_f,
            "gamma": self.gamma,
            "beta": self.beta
        }


class TRBDF2Integrator(TransientIntegrator):
    """Implements the TRBDF2 (Trapezoidal-Backward Difference Formula 2) integrator for dynamic analysis.

    The TRBDF2 method is a second-order, unconditionally stable implicit
    integrator that combines a trapezoidal rule step with a backward
    differentiation formula step, offering good accuracy and stability properties.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "TRBDF2".

    Example:
        >>> from femora.analysis.integrators import TRBDF2Integrator
        >>> trbdf2_integrator = TRBDF2Integrator()
        >>> print(trbdf2_integrator.integrator_type)
        TRBDF2
        >>> print(trbdf2_integrator.to_tcl())
        integrator TRBDF2
    """
    def __init__(self):
        """Initializes a TRBDF2Integrator.

        Example:
            >>> from femora.analysis.integrators import TRBDF2Integrator
            >>> trbdf2 = TRBDF2Integrator()
            >>> print(trbdf2.integrator_type)
            TRBDF2
        """
        super().__init__("TRBDF2")
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import TRBDF2Integrator
            >>> trbdf2 = TRBDF2Integrator()
            >>> print(trbdf2.to_tcl())
            integrator TRBDF2
        """
        return "integrator TRBDF2"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: An empty dictionary
                as TRBDF2 has no parameters.

        Example:
            >>> from femora.analysis.integrators import TRBDF2Integrator
            >>> trbdf2 = TRBDF2Integrator()
            >>> values = trbdf2.get_values()
            >>> print(values)
            {}
        """
        return {}


class ExplicitDifferenceIntegrator(TransientIntegrator):
    """Implements the Explicit Difference integrator for dynamic analysis.

    Similar to Central Difference, this is an explicit, conditionally stable
    integrator. It updates displacement, velocity, and acceleration explicitly
    without solving a system of equations, suitable for certain types of problems.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "ExplicitDifference".

    Example:
        >>> from femora.analysis.integrators import ExplicitDifferenceIntegrator
        >>> ed_integrator = ExplicitDifferenceIntegrator()
        >>> print(ed_integrator.integrator_type)
        ExplicitDifference
        >>> print(ed_integrator.to_tcl())
        integrator ExplicitDifference
    """
    def __init__(self):
        """Initializes an ExplicitDifferenceIntegrator.

        Example:
            >>> from femora.analysis.integrators import ExplicitDifferenceIntegrator
            >>> ed = ExplicitDifferenceIntegrator()
            >>> print(ed.integrator_type)
            ExplicitDifference
        """
        super().__init__("ExplicitDifference")
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import ExplicitDifferenceIntegrator
            >>> ed = ExplicitDifferenceIntegrator()
            >>> print(ed.to_tcl())
            integrator ExplicitDifference
        """
        return "integrator ExplicitDifference"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: An empty dictionary
                as Explicit Difference has no parameters.

        Example:
            >>> from femora.analysis.integrators import ExplicitDifferenceIntegrator
            >>> ed = ExplicitDifferenceIntegrator()
            >>> values = ed.get_values()
            >>> print(values)
            {}
        """
        return {}


class PFEMIntegrator(TransientIntegrator):
    """Implements the Particle Finite Element Method (PFEM) integrator for fluid-structure interaction.

    This integrator is specifically designed for analyses involving fluid-structure
    interaction using the Particle Finite Element Method, often involving free
    surface flows and large deformations.

    Attributes:
        tag (int): The unique identifier for this integrator instance.
        integrator_type (str): Always "PFEM".
        gamma (float): The gamma factor used in the PFEM integration scheme.
        beta (float): The beta factor used in the PFEM integration scheme.

    Example:
        >>> from femora.analysis.integrators import PFEMIntegrator
        >>> pfem_integrator = PFEMIntegrator(gamma=0.6, beta=0.3)
        >>> print(pfem_integrator.integrator_type)
        PFEM
        >>> print(pfem_integrator.gamma)
        0.6
        >>> print(pfem_integrator.to_tcl())
        integrator PFEM 0.6 0.3
    """
    def __init__(self, gamma: float = 0.5, beta: float = 0.25):
        """Initializes a PFEMIntegrator.

        Args:
            gamma: Optional. The gamma factor for the PFEM integration scheme.
                Defaults to 0.5.
            beta: Optional. The beta factor for the PFEM integration scheme.
                Defaults to 0.25.

        Example:
            >>> from femora.analysis.integrators import PFEMIntegrator
            >>> pfem = PFEMIntegrator()
            >>> print(pfem.gamma)
            0.5
            >>> pfem_custom = PFEMIntegrator(gamma=0.6, beta=0.3)
            >>> print(pfem_custom.gamma)
            0.6
        """
        super().__init__("PFEM")
        self.gamma = gamma
        self.beta = beta
    
    def to_tcl(self) -> str:
        """Converts the integrator's configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this integrator.

        Example:
            >>> from femora.analysis.integrators import PFEMIntegrator
            >>> pfem = PFEMIntegrator(gamma=0.55, beta=0.275)
            >>> print(pfem.to_tcl())
            integrator PFEM 0.55 0.275
        """
        return f"integrator PFEM {self.gamma} {self.beta}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool, list]]:
        """Returns a dictionary of the integrator's defining parameters.

        Returns:
            dict[str, Union[str, int, float, bool, list]]: A dictionary
                containing the name-value pairs of the integrator's
                parameters.

        Example:
            >>> from femora.analysis.integrators import PFEMIntegrator
            >>> pfem = PFEMIntegrator(gamma=0.5, beta=0.25)
            >>> values = pfem.get_values()
            >>> print(values['gamma'])
            0.5
            >>> print(values['beta'])
            0.25
        """
        return {
            "gamma": self.gamma,
            "beta": self.beta
        }


class IntegratorManager:
    """Manages all available and created integrator instances in a singleton pattern.

    This class provides a centralized point of access for creating, retrieving,
    and managing all integrator objects within the Femora framework. It ensures
    that integrator types are registered and instances are uniquely tracked.

    Attributes:
        newmark (Type[NewmarkIntegrator]): A reference to the NewmarkIntegrator class.
        hht (Type[HHTIntegrator]): A reference to the HHTIntegrator class.
        generalizedAlpha (Type[GeneralizedAlphaIntegrator]): A reference to the
            GeneralizedAlphaIntegrator class.
        trbdf2 (Type[TRBDF2Integrator]): A reference to the TRBDF2Integrator class.
        centralDifference (Type[CentralDifferenceIntegrator]): A reference to the
            CentralDifferenceIntegrator class.
        explicitDifference (Type[ExplicitDifferenceIntegrator]): A reference to the
            ExplicitDifferenceIntegrator class.
        pfem (Type[PFEMIntegrator]): A reference to the PFEMIntegrator class.
        loadControl (Type[LoadControlIntegrator]): A reference to the
            LoadControlIntegrator class.
        displacementControl (Type[DisplacementControlIntegrator]): A reference to the
            DisplacementControlIntegrator class.
        parallelDisplacementControl (Type[ParallelDisplacementControlIntegrator]): A
            reference to the ParallelDisplacementControlIntegrator class.
        minUnbalDispNorm (Type[MinUnbalDispNormIntegrator]): A reference to the
            MinUnbalDispNormIntegrator class.
        arcLength (Type[ArcLengthIntegrator]): A reference to the ArcLengthIntegrator class.

    Example:
        >>> from femora.analysis.integrators import IntegratorManager
        >>> manager = IntegratorManager()
        >>> nm = manager.create_integrator("Newmark", gamma=0.5, beta=0.25)
        >>> print(nm.integrator_type)
        Newmark
        >>> print(manager.get_available_types()) # Will show registered types
        ['loadcontrol', 'displacementcontrol', 'paralleldisplacementcontrol', 'minunbaldispnorm', 'arclength', 'centraldifference', 'newmark', 'hht', 'generalizedalpha', 'trbdf2', 'explicitdifference', 'pfem']
    """
    _instance: Optional['IntegratorManager'] = None
    

    def __new__(cls):
        """Ensures that only a single instance of IntegratorManager exists.

        Returns:
            IntegratorManager: The singleton instance of the manager.
        """
        if cls._instance is None:
            cls._instance = super(IntegratorManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initializes the IntegratorManager, populating references to integrator classes.

        This constructor sets up direct attributes for each concrete integrator
        type, allowing easy access via `manager.newmark` for instance,
        without needing to call `create_integrator` for class references.
        """
        self.newmark = NewmarkIntegrator
        self.hht = HHTIntegrator
        self.generalizedAlpha = GeneralizedAlphaIntegrator
        self.trbdf2 = TRBDF2Integrator
        self.centralDifference = CentralDifferenceIntegrator
        self.explicitDifference = ExplicitDifferenceIntegrator
        self.pfem = PFEMIntegrator
        self.loadControl = LoadControlIntegrator
        self.displacementControl = DisplacementControlIntegrator
        self.parallelDisplacementControl = ParallelDisplacementControlIntegrator
        self.minUnbalDispNorm = MinUnbalDispNormIntegrator
        self.arcLength = ArcLengthIntegrator

    def create_integrator(self, integrator_type: str, **kwargs) -> Integrator:
        """Creates a new integrator instance using the factory method.

        Args:
            integrator_type: The string identifier for the desired integrator type.
            **kwargs: Arbitrary keyword arguments to pass to the constructor of
                the specific integrator class.

        Returns:
            Integrator: An instance of the requested integrator type.

        Raises:
            ValueError: If an unknown `integrator_type` is requested.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> lc = manager.create_integrator("LoadControl", incr=0.1)
            >>> print(lc.integrator_type)
            LoadControl
            >>> newmark = manager.create_integrator("Newmark", gamma=0.5, beta=0.25)
            >>> print(newmark.tag) # Assigned unique tag
            2
        """
        return Integrator.create_integrator(integrator_type, **kwargs)

    def get_integrator(self, tag: int) -> Integrator:
        """Retrieves a specific integrator instance by its unique tag.

        Args:
            tag: The unique integer tag of the integrator to retrieve.

        Returns:
            Integrator: The integrator instance with the specified tag.

        Raises:
            KeyError: If no integrator with the given tag exists.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> manager.clear_all() # Ensure clean state for example
            >>> lc = manager.create_integrator("LoadControl", incr=0.1)
            >>> retrieved = manager.get_integrator(lc.tag)
            >>> print(retrieved.incr)
            0.1
        """
        return Integrator.get_integrator(tag)

    def remove_integrator(self, tag: int) -> None:
        """Deletes an integrator by its tag and re-tags remaining integrators.

        Args:
            tag: The unique integer tag of the integrator to delete.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> manager.clear_all()
            >>> lc1 = manager.create_integrator("LoadControl", incr=0.1)
            >>> lc2 = manager.create_integrator("LoadControl", incr=0.2)
            >>> print(len(manager.get_all_integrators()))
            2
            >>> manager.remove_integrator(lc1.tag)
            >>> print(len(manager.get_all_integrators()))
            1
            >>> print(manager.get_all_integrators()[1].incr) # Second integrator is now tag 1
            0.2
        """
        Integrator.remove_integrator(tag)

    def get_all_integrators(self) -> Dict[int, Integrator]:
        """Retrieves all created integrator instances.

        Returns:
            dict[int, Integrator]: A dictionary where keys are unique integrator
                tags and values are the corresponding integrator instances.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> manager.clear_all()
            >>> _ = manager.create_integrator("Newmark", gamma=0.5, beta=0.25)
            >>> _ = manager.create_integrator("LoadControl", incr=0.1)
            >>> all_ints = manager.get_all_integrators()
            >>> print(len(all_ints))
            2
            >>> print(isinstance(all_ints, dict))
            True
        """
        return Integrator.get_all_integrators()

    def get_available_types(self) -> List[str]:
        """Returns a list of all globally registered integrator types.

        Returns:
            list[str]: A list of string names for all available integrator types.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> types = manager.get_available_types()
            >>> print('newmark' in types)
            True
            >>> print('loadcontrol' in types)
            True
        """
        return Integrator.get_available_types()
    
    def get_static_types(self) -> List[str]:
        """Returns a list of all registered static integrator types.

        Returns:
            list[str]: A list of string names for available static integrator types.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> static_types = manager.get_static_types()
            >>> print('loadcontrol' in static_types)
            True
            >>> print('newmark' in static_types)
            False
        """
        return StaticIntegrator.get_static_types()
    
    def get_transient_types(self) -> List[str]:
        """Returns a list of all registered transient integrator types.

        Returns:
            list[str]: A list of string names for available transient
                integrator types.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> transient_types = manager.get_transient_types()
            >>> print('newmark' in transient_types)
            True
            >>> print('loadcontrol' in transient_types)
            False
        """
        return TransientIntegrator.get_transient_types()
    
    def clear_all(self):
        """Clears all created integrator instances and resets tags.

        This method removes all registered integrator objects and resets the
        internal tag counter, effectively resetting the integrator system.

        Example:
            >>> from femora.analysis.integrators import IntegratorManager
            >>> manager = IntegratorManager()
            >>> _ = manager.create_integrator("Newmark", gamma=0.5, beta=0.25)
            >>> print(len(manager.get_all_integrators()))
            1
            >>> manager.clear_all()
            >>> print(len(manager.get_all_integrators()))
            0
        """
        Integrator.clear_all()


# Register all integrators
Integrator.register_integrator('loadcontrol', LoadControlIntegrator)
Integrator.register_integrator('displacementcontrol', DisplacementControlIntegrator)
Integrator.register_integrator('paralleldisplacementcontrol', ParallelDisplacementControlIntegrator)
Integrator.register_integrator('minunbaldispnorm', MinUnbalDispNormIntegrator)
Integrator.register_integrator('arclength', ArcLengthIntegrator)
Integrator.register_integrator('centraldifference', CentralDifferenceIntegrator)
Integrator.register_integrator('newmark', NewmarkIntegrator)
Integrator.register_integrator('hht', HHTIntegrator)
Integrator.register_integrator('generalizedalpha', GeneralizedAlphaIntegrator)
Integrator.register_integrator('trbdf2', TRBDF2Integrator)
Integrator.register_integrator('explicitdifference', ExplicitDifferenceIntegrator)
Integrator.register_integrator('pfem', PFEMIntegrator)