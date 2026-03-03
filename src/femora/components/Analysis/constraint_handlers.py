from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import ABC, abstractmethod


class ConstraintHandler(AnalysisComponent):
    """Base abstract class for constraint handlers.

    Constraint handlers determine how constraint equations are enforced within
    the system of equations. This class provides a registration and creation
    mechanism for different handler types.

    Attributes:
        tag (int): The unique identifier for this constraint handler instance.
        handler_type (str): The string identifier for the type of this handler
            (e.g., "Plain", "Penalty").

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> fm.ConstraintHandler.register_handler('test', fm.PlainConstraintHandler)
        >>> handler = fm.ConstraintHandler.create_handler('test')
        >>> print(handler.tag) # doctest: +SKIP
        1
        >>> print(handler.handler_type)
        Plain
    """
    _handlers = {}  # Class-level dictionary to store handler types
    _created_handlers = {}  # Class-level dictionary to track all created handlers
    _next_tag = 1  # Class variable to track the next tag to assign
    
    def __init__(self, handler_type: str):
        """Initializes a ConstraintHandler instance.

        Args:
            handler_type: The string type of the constraint handler.
        """
        self.tag = ConstraintHandler._next_tag
        ConstraintHandler._next_tag += 1
        self.handler_type = handler_type
        
        # Register this handler in the class-level tracking dictionary
        ConstraintHandler._created_handlers[self.tag] = self
    
    @staticmethod
    def register_handler(name: str, handler_class: Type['ConstraintHandler']):
        """Registers a new constraint handler type with a given name.

        Args:
            name: The string name to register the handler under.
            handler_class: The class object of the handler to register.

        Example:
            >>> import femora as fm
            >>> class CustomHandler(fm.ConstraintHandler):
            ...     def __init__(self):
            ...         super().__init__("Custom")
            ...     def get_values(self):
            ...         return {"foo": "bar"}
            ...     def to_tcl(self):
            ...         return "constraints Custom"
            >>> fm.ConstraintHandler.register_handler('custom', CustomHandler)
            >>> 'custom' in fm.ConstraintHandler.get_available_types()
            True
        """
        ConstraintHandler._handlers[name.lower()] = handler_class
    
    @staticmethod
    def create_handler(handler_type: str, **kwargs) -> 'ConstraintHandler':
        """Creates a constraint handler of the specified type.

        Args:
            handler_type: The string name of the handler type to create.
            **kwargs: Additional keyword arguments passed to the handler's
                constructor.

        Returns:
            ConstraintHandler: An instance of the requested constraint handler.

        Raises:
            ValueError: If an unknown constraint handler type is requested.

        Example:
            >>> import femora as fm
            >>> fm.ConstraintHandler.clear_all()
            >>> penalty_handler = fm.ConstraintHandler.create_handler(
            ...     'penalty', alpha_s=0.5, alpha_m=1.0)
            >>> isinstance(penalty_handler, fm.PenaltyConstraintHandler)
            True
            >>> penalty_handler.get_values()
            {'alpha_s': 0.5, 'alpha_m': 1.0}
        """
        handler_type = handler_type.lower()
        if handler_type not in ConstraintHandler._handlers:
            raise ValueError(f"Unknown constraint handler type: {handler_type}")
        return ConstraintHandler._handlers[handler_type](**kwargs)
    
    @staticmethod
    def get_available_types() -> List[str]:
        """Gets a list of all currently registered constraint handler types.

        Returns:
            List[str]: A list of string names for available handler types.

        Example:
            >>> import femora as fm
            >>> fm.ConstraintHandler.clear_all()
            >>> fm.ConstraintHandler.register_handler('my_plain', fm.PlainConstraintHandler)
            >>> 'my_plain' in fm.ConstraintHandler.get_available_types()
            True
            >>> 'plain' in fm.ConstraintHandler.get_available_types() # Original registration
            True
        """
        return list(ConstraintHandler._handlers.keys())
    
    @classmethod
    def get_handler(cls, tag: int) -> 'ConstraintHandler':
        """Retrieves a specific handler by its unique tag.
        
        Args:
            tag: The unique integer tag of the handler to retrieve.
        
        Returns:
            ConstraintHandler: The handler with the specified tag.
        
        Raises:
            KeyError: If no handler with the given tag exists.

        Example:
            >>> import femora as fm
            >>> fm.ConstraintHandler.clear_all()
            >>> handler1 = fm.ConstraintHandler.create_handler('plain')
            >>> handler2 = fm.ConstraintHandler.create_handler('transformation')
            >>> retrieved_handler = fm.ConstraintHandler.get_handler(handler1.tag)
            >>> retrieved_handler.handler_type
            'Plain'
        """
        if tag not in cls._created_handlers:
            raise KeyError(f"No constraint handler found with tag {tag}")
        return cls._created_handlers[tag]


    @classmethod
    def get_all_handlers(cls) -> Dict[int, 'ConstraintHandler']:
        """Retrieves all created constraint handler instances.
        
        Returns:
            Dict[int, ConstraintHandler]: A dictionary of all active handlers,
                keyed by their unique integer tags.

        Example:
            >>> import femora as fm
            >>> fm.ConstraintHandler.clear_all()
            >>> handler1 = fm.ConstraintHandler.create_handler('plain')
            >>> handler2 = fm.ConstraintHandler.create_handler('transformation')
            >>> all_handlers = fm.ConstraintHandler.get_all_handlers()
            >>> len(all_handlers)
            2
            >>> all_handlers[handler1.tag].handler_type
            'Plain'
        """
        return cls._created_handlers
    
    @classmethod
    def clear_all(cls) -> None:
        """Clears all created constraint handler instances and resets the tag counter.

        Example:
            >>> import femora as fm
            >>> handler1 = fm.ConstraintHandler.create_handler('plain')
            >>> len(fm.ConstraintHandler.get_all_handlers())
            1
            >>> fm.ConstraintHandler.clear_all()
            >>> len(fm.ConstraintHandler.get_all_handlers())
            0
        """
        cls._created_handlers.clear()
        cls._next_tag = 1
    
    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Abstract method to get the parameters defining this handler.

        This method must be implemented by concrete constraint handler subclasses
        to return a dictionary of their specific configuration values.
        
        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary where keys are
                parameter names and values are their current settings.

        Example:
            >>> # This is an abstract method; see concrete implementations for examples.
            >>> import femora as fm
            >>> handler = fm.PenaltyConstraintHandler(alpha_s=0.1, alpha_m=0.2)
            >>> handler.get_values()
            {'alpha_s': 0.1, 'alpha_m': 0.2}
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all handlers sequentially starting from 1.

        This internal method is called after a handler is removed to ensure
        that tags remain contiguous and sequential.
        """
        new_handlers = {}
        for idx, handler in enumerate(sorted(cls._created_handlers.values(), key=lambda h: h.tag), start=1):
            handler.tag = idx
            new_handlers[idx] = handler
        cls._created_handlers = new_handlers
        cls._next_tag = len(cls._created_handlers) + 1

    @classmethod
    def remove_handler(cls, tag: int) -> None:
        """Deletes a handler by its tag and re-tags all remaining handlers sequentially.
        
        Args:
            tag: The unique integer tag of the handler to delete.

        Raises:
            KeyError: If no handler with the given tag exists.

        Example:
            >>> import femora as fm
            >>> fm.ConstraintHandler.clear_all()
            >>> handler1 = fm.ConstraintHandler.create_handler('plain') # tag 1
            >>> handler2 = fm.ConstraintHandler.create_handler('transformation') # tag 2
            >>> fm.ConstraintHandler.remove_handler(handler1.tag)
            >>> len(fm.ConstraintHandler.get_all_handlers())
            1
            >>> remaining_handler = list(fm.ConstraintHandler.get_all_handlers().values())[0]
            >>> remaining_handler.tag # Tag should be reassigned to 1
            1
            >>> remaining_handler.handler_type
            'Transformation'
            >>> # Trying to remove a non-existent handler
            >>> try:
            ...     fm.ConstraintHandler.remove_handler(999)
            ... except KeyError as e:
            ...     print(e)
            No constraint handler found with tag 999
        """
        if tag not in cls._created_handlers:
            raise KeyError(f"No constraint handler found with tag {tag}")
        del cls._created_handlers[tag]
        cls._reassign_tags()


class PlainConstraintHandler(ConstraintHandler):
    """Represents a 'Plain' constraint handler.

    This handler does not follow constraint definitions across the model's
    evolution, providing a basic, static approach to constraint enforcement.

    Attributes:
        tag (int): The unique identifier for this handler (inherited).
        handler_type (str): Always "Plain" for this handler (inherited).

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> handler = fm.ConstraintHandler.create_handler('plain')
        >>> handler.handler_type
        'Plain'
        >>> handler.to_tcl()
        'constraints Plain'
    """
    def __init__(self):
        """Initializes a PlainConstraintHandler."""
        super().__init__("Plain")
    
    def to_tcl(self) -> str:
        """Generates the OpenSees Tcl command string for this handler.

        Returns:
            str: The Tcl command string.

        Example:
            >>> import femora as fm
            >>> handler = fm.PlainConstraintHandler()
            >>> handler.to_tcl()
            'constraints Plain'
        """
        return "constraints Plain"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Returns the parameters defining this handler.

        For a `PlainConstraintHandler`, there are no specific parameters.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> handler = fm.PlainConstraintHandler()
            >>> handler.get_values()
            {}
        """
        return {}


class TransformationConstraintHandler(ConstraintHandler):
    """Represents a 'Transformation' constraint handler.

    This handler performs static condensation of the constraint degrees of
    freedom, transforming the system of equations.

    Attributes:
        tag (int): The unique identifier for this handler (inherited).
        handler_type (str): Always "Transformation" for this handler (inherited).

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> handler = fm.ConstraintHandler.create_handler('transformation')
        >>> handler.handler_type
        'Transformation'
        >>> handler.to_tcl()
        'constraints Transformation'
    """
    def __init__(self):
        """Initializes a TransformationConstraintHandler."""
        super().__init__("Transformation")
    
    def to_tcl(self) -> str:
        """Generates the OpenSees Tcl command string for this handler.

        Returns:
            str: The Tcl command string.

        Example:
            >>> import femora as fm
            >>> handler = fm.TransformationConstraintHandler()
            >>> handler.to_tcl()
            'constraints Transformation'
        """
        return "constraints Transformation"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Returns the parameters defining this handler.

        For a `TransformationConstraintHandler`, there are no specific parameters.

        Returns:
            Dict[str, Union[str, int, float, bool]]: An empty dictionary.

        Example:
            >>> import femora as fm
            >>> handler = fm.ConstraintHandler.create_handler('transformation')
            >>> handler.get_values()
            {}
        """
        return {}


class PenaltyConstraintHandler(ConstraintHandler):
    """Represents a 'Penalty' constraint handler.

    This handler uses penalty numbers to enforce constraints in the system
    of equations.

    Attributes:
        alpha_s (float): The penalty number for single-point constraints.
        alpha_m (float): The penalty number for multi-point constraints.
        tag (int): The unique identifier for this handler (inherited).
        handler_type (str): Always "Penalty" for this handler (inherited).

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> handler = fm.ConstraintHandler.create_handler('penalty', alpha_s=1e9, alpha_m=1e10)
        >>> handler.handler_type
        'Penalty'
        >>> handler.alpha_s
        1000000000.0
        >>> handler.to_tcl()
        'constraints Penalty 1000000000.0 10000000000.0'
    """
    def __init__(self, alpha_s: float, alpha_m: float):
        """Initializes a PenaltyConstraintHandler.

        Args:
            alpha_s: The penalty number used for single-point constraints.
            alpha_m: The penalty number used for multi-point constraints.
        """
        super().__init__("Penalty")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        """Generates the OpenSees Tcl command string for this handler.

        Returns:
            str: The Tcl command string including penalty numbers.

        Example:
            >>> import femora as fm
            >>> handler = fm.PenaltyConstraintHandler(alpha_s=1e5, alpha_m=1e6)
            >>> handler.to_tcl()
            'constraints Penalty 100000.0 1000000.0'
        """
        return f"constraints Penalty {self.alpha_s} {self.alpha_m}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Returns the parameters defining this handler.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary containing
                'alpha_s' and 'alpha_m'.

        Example:
            >>> import femora as fm
            >>> handler = fm.PenaltyConstraintHandler(alpha_s=0.01, alpha_m=0.02)
            >>> handler.get_values()
            {'alpha_s': 0.01, 'alpha_m': 0.02}
        """
        return {
            "alpha_s": self.alpha_s,
            "alpha_m": self.alpha_m
        }


class LagrangeConstraintHandler(ConstraintHandler):
    """Represents a 'Lagrange' multipliers constraint handler.

    This handler uses Lagrange multipliers to enforce constraints, which
    can involve adding auxiliary degrees of freedom to the system.

    Attributes:
        alpha_s (float): The penalty number for single-point constraints
            when using a penalized Lagrange multiplier approach.
        alpha_m (float): The penalty number for multi-point constraints
            when using a penalized Lagrange multiplier approach.
        tag (int): The unique identifier for this handler (inherited).
        handler_type (str): Always "Lagrange" for this handler (inherited).

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> handler = fm.ConstraintHandler.create_handler('lagrange', alpha_s=1.0, alpha_m=2.0)
        >>> handler.handler_type
        'Lagrange'
        >>> handler.alpha_s
        1.0
        >>> handler.to_tcl()
        'constraints Lagrange 1.0 2.0'
    """
    def __init__(self, alpha_s: float = 1.0, alpha_m: float = 1.0):
        """Initializes a LagrangeConstraintHandler.

        Args:
            alpha_s: Optional. The penalty number used for single-point
                constraints. Defaults to 1.0.
            alpha_m: Optional. The penalty number used for multi-point
                constraints. Defaults to 1.0.
        """
        super().__init__("Lagrange")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        """Generates the OpenSees Tcl command string for this handler.

        Returns:
            str: The Tcl command string including Lagrange multiplier parameters.

        Example:
            >>> import femora as fm
            >>> handler1 = fm.LagrangeConstraintHandler()
            >>> handler1.to_tcl()
            'constraints Lagrange 1.0 1.0'
            >>> handler2 = fm.LagrangeConstraintHandler(alpha_s=0.5)
            >>> handler2.to_tcl()
            'constraints Lagrange 0.5 1.0'
        """
        return f"constraints Lagrange {self.alpha_s} {self.alpha_m}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Returns the parameters defining this handler.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary containing
                'alpha_s' and 'alpha_m'.

        Example:
            >>> import femora as fm
            >>> handler = fm.LagrangeConstraintHandler(alpha_s=10.0, alpha_m=20.0)
            >>> handler.get_values()
            {'alpha_s': 10.0, 'alpha_m': 20.0}
        """
        return {
            "alpha_s": self.alpha_s,
            "alpha_m": self.alpha_m
        }


class AutoConstraintHandler(ConstraintHandler):
    """Represents an 'Auto' constraint handler.

    This handler automatically selects penalty values for compatibility
    constraints, simplifying the configuration process.

    Attributes:
        verbose (bool): If True, detailed information about the automatic
            penalty selection process is printed.
        auto_penalty (Optional[float]): The auto-penalty factor. If None,
            a default is used.
        user_penalty (Optional[float]): A user-defined penalty factor.
            If None, the auto-penalty mechanism is primarily used.
        tag (int): The unique identifier for this handler (inherited).
        handler_type (str): Always "Auto" for this handler (inherited).

    Example:
        >>> import femora as fm
        >>> fm.ConstraintHandler.clear_all()
        >>> handler = fm.ConstraintHandler.create_handler('auto', verbose=True, user_penalty=1e12)
        >>> handler.handler_type
        'Auto'
        >>> handler.verbose
        True
        >>> handler.to_tcl()
        'constraints Auto -verbose -userPenalty 1000000000000.0'
    """
    def __init__(self, verbose: bool = False, auto_penalty: Optional[float] = None, 
                 user_penalty: Optional[float] = None):
        """Initializes an AutoConstraintHandler.

        Args:
            verbose: Optional. If True, prints verbose output during automatic
                penalty selection. Defaults to False.
            auto_penalty: Optional. Specifies the auto-penalty factor. If None,
                the system determines a default.
            user_penalty: Optional. Specifies a user-defined penalty factor.
                If provided, this may override or influence the auto-penalty.
        """
        super().__init__("Auto")
        self.verbose = verbose
        self.auto_penalty = auto_penalty
        self.user_penalty = user_penalty
    
    def to_tcl(self) -> str:
        """Generates the OpenSees Tcl command string for this handler.

        Returns:
            str: The Tcl command string including auto-penalty options.

        Example:
            >>> import femora as fm
            >>> handler1 = fm.AutoConstraintHandler()
            >>> handler1.to_tcl()
            'constraints Auto'
            >>> handler2 = fm.AutoConstraintHandler(verbose=True, auto_penalty=1.0)
            >>> handler2.to_tcl()
            'constraints Auto -verbose -autoPenalty 1.0'
        """
        cmd = "constraints Auto"
        if self.verbose:
            cmd += " -verbose"
        if self.auto_penalty is not None:
            cmd += f" -autoPenalty {self.auto_penalty}"
        if self.user_penalty is not None:
            cmd += f" -userPenalty {self.user_penalty}"
        return cmd
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Returns the parameters defining this handler.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary containing
                'verbose', 'auto_penalty', and 'user_penalty'.

        Example:
            >>> import femora as fm
            >>> handler = fm.AutoConstraintHandler(verbose=True, auto_penalty=0.9, user_penalty=1.1)
            >>> handler.get_values()
            {'verbose': True, 'auto_penalty': 0.9, 'user_penalty': 1.1}
        """
        return {
            "verbose": self.verbose,
            "auto_penalty": self.auto_penalty,
            "user_penalty": self.user_penalty
        }


class ConstraintHandlerManager:
    """A singleton class for managing all constraint handlers.

    This manager provides a centralized interface to create, retrieve,
    and remove `ConstraintHandler` instances. It ensures that only one
    instance of the manager exists globally, facilitating consistent
    access to constraint handler operations across the application.

    Attributes:
        transformation (Type[TransformationConstraintHandler]): A class reference
            to the `TransformationConstraintHandler`.
        plain (Type[PlainConstraintHandler]): A class reference to the
            `PlainConstraintHandler`.
        penalty (Type[PenaltyConstraintHandler]): A class reference to the
            `PenaltyConstraintHandler`.
        lagrange (Type[LagrangeConstraintHandler]): A class reference to the
            `LagrangeConstraintHandler`.
        auto (Type[AutoConstraintHandler]): A class reference to the
            `AutoConstraintHandler`.

    Example:
        >>> import femora as fm
        >>> manager1 = fm.ConstraintHandlerManager()
        >>> manager2 = fm.ConstraintHandlerManager()
        >>> manager1 is manager2
        True
        >>> manager1.clear_all() # Ensure a clean slate for example
        >>> handler = manager1.create_handler('plain')
        >>> handler.handler_type
        'Plain'
        >>> manager1.remove_handler(handler.tag)
        >>> len(manager1.get_all_handlers())
        0
    """
    _instance = None
    transformation = TransformationConstraintHandler
    plain = PlainConstraintHandler
    penalty = PenaltyConstraintHandler
    lagrange = LagrangeConstraintHandler
    auto = AutoConstraintHandler

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConstraintHandlerManager, cls).__new__(cls)
        return cls._instance
        

    def create_handler(self, handler_type: str, **kwargs) -> ConstraintHandler:
        """Creates a new constraint handler instance.

        Args:
            handler_type: The string name of the handler type to create.
            **kwargs: Additional keyword arguments passed to the handler's
                constructor.

        Returns:
            ConstraintHandler: An instance of the requested constraint handler.

        Raises:
            ValueError: If an unknown constraint handler type is requested.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> manager.clear_all()
            >>> penalty_handler = manager.create_handler(
            ...     'penalty', alpha_s=0.5, alpha_m=1.0)
            >>> isinstance(penalty_handler, fm.PenaltyConstraintHandler)
            True
        """
        return ConstraintHandler.create_handler(handler_type, **kwargs)

    def get_handler(self, tag: int) -> ConstraintHandler:
        """Retrieves a specific constraint handler by its unique tag.

        Args:
            tag: The unique integer tag of the handler to retrieve.

        Returns:
            ConstraintHandler: The handler with the specified tag.

        Raises:
            KeyError: If no handler with the given tag exists.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> manager.clear_all()
            >>> handler = manager.create_handler('plain')
            >>> retrieved_handler = manager.get_handler(handler.tag)
            >>> retrieved_handler.handler_type
            'Plain'
        """
        return ConstraintHandler.get_handler(tag)

    def remove_handler(self, tag: int) -> None:
        """Removes a constraint handler by its tag.

        After removal, existing handlers may be re-tagged to maintain
        sequential numbering.

        Args:
            tag: The unique integer tag of the handler to delete.

        Raises:
            KeyError: If no handler with the given tag exists.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> manager.clear_all()
            >>> handler1 = manager.create_handler('plain') # tag 1
            >>> handler2 = manager.create_handler('transformation') # tag 2
            >>> manager.remove_handler(handler1.tag)
            >>> len(manager.get_all_handlers())
            1
            >>> remaining_handler = list(manager.get_all_handlers().values())[0]
            >>> remaining_handler.tag # Tag should be reassigned to 1
            1
        """
        ConstraintHandler.remove_handler(tag)

    def get_all_handlers(self) -> Dict[int, ConstraintHandler]:
        """Retrieves all created constraint handler instances.

        Returns:
            Dict[int, ConstraintHandler]: A dictionary of all active handlers,
                keyed by their unique integer tags.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> manager.clear_all()
            >>> handler1 = manager.create_handler('plain')
            >>> handler2 = manager.create_handler('penalty', alpha_s=1.0, alpha_m=1.0)
            >>> all_handlers = manager.get_all_handlers()
            >>> len(all_handlers)
            2
        """
        return ConstraintHandler.get_all_handlers()

    def get_available_types(self) -> List[str]:
        """Gets a list of all currently registered constraint handler types.

        Returns:
            List[str]: A list of string names for available handler types.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> 'plain' in manager.get_available_types()
            True
            >>> 'transformation' in manager.get_available_types()
            True
        """
        return ConstraintHandler.get_available_types()
    
    def clear_all(self):
        """Clears all created constraint handler instances and resets the tag counter.

        Example:
            >>> import femora as fm
            >>> manager = fm.ConstraintHandlerManager()
            >>> manager.create_handler('plain')
            >>> len(manager.get_all_handlers())
            1
            >>> manager.clear_all()
            >>> len(manager.get_all_handlers())
            0
        """  
        ConstraintHandler.clear_all()


# Register all constraint handlers
ConstraintHandler.register_handler('plain', PlainConstraintHandler)
ConstraintHandler.register_handler('transformation', TransformationConstraintHandler)
ConstraintHandler.register_handler('penalty', PenaltyConstraintHandler)
ConstraintHandler.register_handler('lagrange', LagrangeConstraintHandler)
ConstraintHandler.register_handler('auto', AutoConstraintHandler)