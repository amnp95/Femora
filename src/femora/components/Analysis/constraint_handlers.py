from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import ABC, abstractmethod


class ConstraintHandler(AnalysisComponent):
    """
    Base abstract class for constraint handlers, which determine how the constraint equations are enforced
    in the system of equations
    """
    _handlers = {}  # Class-level dictionary to store handler types
    _created_handlers = {}  # Class-level dictionary to track all created handlers
    _next_tag = 1  # Class variable to track the next tag to assign
    
    def __init__(self, handler_type: str):
        """
        Initialize a constraint handler
        
        Args:
            handler_type (str): Type of the constraint handler
        """
        self.tag = ConstraintHandler._next_tag
        ConstraintHandler._next_tag += 1
        self.handler_type = handler_type
        
        # Register this handler in the class-level tracking dictionary
        ConstraintHandler._created_handlers[self.tag] = self
    
    @staticmethod
    def register_handler(name: str, handler_class: Type['ConstraintHandler']):
        """Register a constraint handler type"""
        ConstraintHandler._handlers[name.lower()] = handler_class
    
    @staticmethod
    def create_handler(handler_type: str, **kwargs) -> 'ConstraintHandler':
        """Create a constraint handler of the specified type"""
        handler_type = handler_type.lower()
        if handler_type not in ConstraintHandler._handlers:
            raise ValueError(f"Unknown constraint handler type: {handler_type}")
        return ConstraintHandler._handlers[handler_type](**kwargs)
    
    @staticmethod
    def get_available_types() -> List[str]:
        """Get available constraint handler types"""
        return list(ConstraintHandler._handlers.keys())
    
    @classmethod
    def get_handler(cls, tag: int) -> 'ConstraintHandler':
        """
        Retrieve a specific handler by its tag.
        
        Args:
            tag (int): The tag of the handler
        
        Returns:
            ConstraintHandler: The handler with the specified tag
        
        Raises:
            KeyError: If no handler with the given tag exists
        """
        if tag not in cls._created_handlers:
            raise KeyError(f"No constraint handler found with tag {tag}")
        return cls._created_handlers[tag]


    @classmethod
    def get_all_handlers(cls) -> Dict[int, 'ConstraintHandler']:
        """
        Retrieve all created handlers.
        
        Returns:
            Dict[int, ConstraintHandler]: A dictionary of all handlers, keyed by their unique tags
        """
        return cls._created_handlers
    
    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all handlers and reset tags.
        """
        cls._created_handlers.clear()
        cls._next_tag = 1
    
    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """
        Get the parameters defining this handler
        
        Returns:
            Dict[str, Union[str, int, float, bool]]: Dictionary of parameter values
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """
        Reassign tags to all handlers sequentially starting from 1.
        """
        new_handlers = {}
        for idx, handler in enumerate(sorted(cls._created_handlers.values(), key=lambda h: h.tag), start=1):
            handler.tag = idx
            new_handlers[idx] = handler
        cls._created_handlers = new_handlers
        cls._next_tag = len(cls._created_handlers) + 1

    @classmethod
    def remove_handler(cls, tag: int) -> None:
        """
        Delete a handler by its tag and re-tag all remaining handlers sequentially.
        
        Args:
            tag (int): The tag of the handler to delete
        """
        if tag in cls._created_handlers:
            del cls._created_handlers[tag]
            cls._reassign_tags()


class PlainConstraintHandler(ConstraintHandler):
    """
    Plain constraint handler, does not follow the constraint definitions across the model evolution
    """
    def __init__(self):
        super().__init__("Plain")
    
    def to_tcl(self) -> str:
        return "constraints Plain"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        return {}


class TransformationConstraintHandler(ConstraintHandler):
    """
    Transformation constraint handler, performs static condensation of the constraint degrees of freedom
    """
    def __init__(self):
        super().__init__("Transformation")
    
    def to_tcl(self) -> str:
        return "constraints Transformation"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        return {}


class PenaltyConstraintHandler(ConstraintHandler):
    """
    Penalty constraint handler, uses penalty numbers to enforce constraints
    """
    def __init__(self, alpha_s: float, alpha_m: float):
        super().__init__("Penalty")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        return f"constraints Penalty {self.alpha_s} {self.alpha_m}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        return {
            "alpha_s": self.alpha_s,
            "alpha_m": self.alpha_m
        }


class LagrangeConstraintHandler(ConstraintHandler):
    """
    Lagrange multipliers constraint handler, uses Lagrange multipliers to enforce constraints
    """
    def __init__(self, alpha_s: float = 1.0, alpha_m: float = 1.0):
        super().__init__("Lagrange")
        self.alpha_s = alpha_s
        self.alpha_m = alpha_m
    
    def to_tcl(self) -> str:
        return f"constraints Lagrange {self.alpha_s} {self.alpha_m}"
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        return {
            "alpha_s": self.alpha_s,
            "alpha_m": self.alpha_m
        }


class AutoConstraintHandler(ConstraintHandler):
    """
    Automatic constraint handler, automatically selects the penalty value for compatibility constraints
    """
    def __init__(self, verbose: bool = False, auto_penalty: Optional[float] = None, 
                 user_penalty: Optional[float] = None):
        super().__init__("Auto")
        self.verbose = verbose
        self.auto_penalty = auto_penalty
        self.user_penalty = user_penalty
    
    def to_tcl(self) -> str:
        cmd = "constraints Auto"
        if self.verbose:
            cmd += " -verbose"
        if self.auto_penalty is not None:
            cmd += f" -autoPenalty {self.auto_penalty}"
        if self.user_penalty is not None:
            cmd += f" -userPenalty {self.user_penalty}"
        return cmd
    
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        return {
            "verbose": self.verbose,
            "auto_penalty": self.auto_penalty,
            "user_penalty": self.user_penalty
        }


class ConstraintHandlerManager:
    """
    Singleton class for managing constraint handlers
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
        """Create a new constraint handler"""
        return ConstraintHandler.create_handler(handler_type, **kwargs)

    def get_handler(self, tag: int) -> ConstraintHandler:
        """Get constraint handler by tag"""
        return ConstraintHandler.get_handler(tag)

    def remove_handler(self, tag: int) -> None:
        """Remove constraint handler by tag"""
        ConstraintHandler.remove_handler(tag)

    def get_all_handlers(self) -> Dict[int, ConstraintHandler]:
        """Get all constraint handlers"""
        return ConstraintHandler.get_all_handlers()

    def get_available_types(self) -> List[str]:
        """Get list of available constraint handler types"""
        return ConstraintHandler.get_available_types()
    
    def clear_all(self):
        """Clear all constraint handlers"""  
        ConstraintHandler.clear_all()


# Register all constraint handlers
ConstraintHandler.register_handler('plain', PlainConstraintHandler)
ConstraintHandler.register_handler('transformation', TransformationConstraintHandler)
ConstraintHandler.register_handler('penalty', PenaltyConstraintHandler)
ConstraintHandler.register_handler('lagrange', LagrangeConstraintHandler)
ConstraintHandler.register_handler('auto', AutoConstraintHandler)