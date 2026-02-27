from typing import List, Dict, Optional, Union, Type
from .base import AnalysisComponent
from abc import abstractmethod

class Algorithm(AnalysisComponent):
    """Base abstract class for algorithms, which determine how the constraint equations are enforced
    in the system of equations.

    This class provides a common interface and management utilities for different
    numerical algorithms used in structural analysis. It also handles the
    automatic assignment of unique tags to created algorithms.

    Attributes:
        tag (int): The unique identifier for this algorithm instance.
        algorithm_type (str): A string indicating the specific type of the algorithm (e.g., "Linear", "Newton").
    """
    _algorithms = {}  # Class-level dictionary to store algorithm types
    _created_algorithms = {}  # Class-level dictionary to track all created algorithms
    _next_tag = 1  # Class variable to track the next tag to assign

    def __init__(self, algorithm_type: str):
        """Initializes an Algorithm instance.

        Args:
            algorithm_type: The string identifier for the type of algorithm.

        Example:
            >>> import femora as fm
            >>> linear_alg = fm.algorithms.LinearAlgorithm()
            >>> print(linear_alg.tag)
            1
            >>> newton_alg = fm.algorithms.NewtonAlgorithm()
            >>> print(newton_alg.tag)
            2
        """
        self.tag = Algorithm._next_tag
        Algorithm._next_tag += 1
        self.algorithm_type = algorithm_type

        # Register this algorithm in the class-level tracking dictionary
        Algorithm._created_algorithms[self.tag] = self

    @staticmethod
    def register_algorithm(name: str, algorithm_class: Type['Algorithm']):
        """Registers an algorithm class with a given name.

        This allows the algorithm to be created dynamically using its string name.

        Args:
            name: The string name to register the algorithm under. This will be
                converted to lowercase for lookup.
            algorithm_class: The class object of the algorithm to register.

        Example:
            >>> import femora as fm
            >>> class CustomAlgorithm(fm.algorithms.Algorithm):
            ...     def __init__(self): super().__init__("Custom")
            ...     def get_values(self): return {}
            ...     def to_tcl(self): return "algorithm Custom"
            >>> fm.algorithms.Algorithm.register_algorithm('custom', CustomAlgorithm)
            >>> custom_alg = fm.algorithms.Algorithm.create_algorithm('custom')
            >>> print(custom_alg.algorithm_type)
            Custom
        """
        Algorithm._algorithms[name.lower()] = algorithm_class

    @staticmethod
    def create_algorithm(algorithm_type: str, **kwargs) -> 'Algorithm':
        """Creates an algorithm of the specified type.

        Args:
            algorithm_type: The string identifier for the type of algorithm to create.
            **kwargs: Additional keyword arguments to pass to the algorithm's constructor.

        Returns:
            Algorithm: An instance of the requested algorithm type.

        Raises:
            ValueError: If an unknown `algorithm_type` is provided.

        Example:
            >>> import femora as fm
            >>> linear_alg = fm.algorithms.Algorithm.create_algorithm('linear')
            >>> print(isinstance(linear_alg, fm.algorithms.LinearAlgorithm))
            True
            >>> newton_alg = fm.algorithms.Algorithm.create_algorithm('newton', initial=True)
            >>> print(newton_alg.initial)
            True
        """
        algorithm_type = algorithm_type.lower()
        if algorithm_type not in Algorithm._algorithms:
            raise ValueError(f"Unknown algorithm type: {algorithm_type}")
        return Algorithm._algorithms[algorithm_type](**kwargs)

    @staticmethod
    def get_available_types() -> List[str]:
        """Gets a list of all currently registered algorithm types.

        Returns:
            List[str]: A list of strings representing the available algorithm types.

        Example:
            >>> import femora as fm
            >>> types = fm.algorithms.Algorithm.get_available_types()
            >>> print('linear' in types)
            True
            >>> print('newton' in types)
            True
        """
        return list(Algorithm._algorithms.keys())

    @classmethod
    def get_algorithm(cls, tag: int) -> 'Algorithm':
        """Retrieves a specific algorithm by its unique tag.

        Args:
            tag: The unique integer tag of the algorithm to retrieve.

        Returns:
            Algorithm: The algorithm instance with the specified tag.

        Raises:
            KeyError: If no algorithm with the given `tag` exists.

        Example:
            >>> import femora as fm
            >>> fm.algorithms.Algorithm.clear_all()
            >>> alg1 = fm.algorithms.LinearAlgorithm()
            >>> alg2 = fm.algorithms.NewtonAlgorithm()
            >>> retrieved_alg = fm.algorithms.Algorithm.get_algorithm(alg1.tag)
            >>> print(retrieved_alg.algorithm_type)
            Linear
        """
        if tag not in cls._created_algorithms:
            raise KeyError(f"No algorithm found with tag {tag}")
        return cls._created_algorithms[tag]

    @classmethod
    def get_all_algorithms(cls) -> Dict[int, 'Algorithm']:
        """Retrieves all created algorithm instances.

        Returns:
            Dict[int, Algorithm]: A dictionary where keys are the unique integer tags
                and values are the corresponding algorithm instances.

        Example:
            >>> import femora as fm
            >>> fm.algorithms.Algorithm.clear_all()
            >>> alg1 = fm.algorithms.LinearAlgorithm()
            >>> alg2 = fm.algorithms.NewtonAlgorithm()
            >>> all_algs = fm.algorithms.Algorithm.get_all_algorithms()
            >>> print(len(all_algs))
            2
            >>> print(all_algs[alg1.tag].algorithm_type)
            Linear
        """
        return cls._created_algorithms

    @classmethod
    def clear_all(cls) -> None:
        """Clears all created algorithm instances and resets the tag counter.

        This effectively removes all algorithms from the system's memory.

        Example:
            >>> import femora as fm
            >>> _ = fm.algorithms.LinearAlgorithm()
            >>> print(len(fm.algorithms.Algorithm.get_all_algorithms()))
            1
            >>> fm.algorithms.Algorithm.clear_all()
            >>> print(len(fm.algorithms.Algorithm.get_all_algorithms()))
            0
        """
        cls._created_algorithms.clear()
        cls._next_tag = 1

    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Abstract method to get the parameters defining this algorithm.

        This method should be implemented by concrete algorithm classes to return
        a dictionary of their specific configuration values.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary where keys are
                parameter names and values are their current settings.
        """
        pass

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all algorithms sequentially starting from 1.

        This is a helper method used internally after an algorithm has been removed
        to maintain sequential and unique tags.
        """
        new_algorithms = {}
        for idx, algorithm in enumerate(sorted(cls._created_algorithms.values(), key=lambda h: h.tag), start=1):
            algorithm.tag = idx
            new_algorithms[idx] = algorithm
        cls._created_algorithms = new_algorithms
        cls._next_tag = len(cls._created_algorithms) + 1

    @classmethod
    def remove_algorithm(cls, tag: int) -> None:
        """Deletes an algorithm by its tag and re-tags all remaining algorithms sequentially.

        Args:
            tag: The unique integer tag of the algorithm to delete.

        Example:
            >>> import femora as fm
            >>> fm.algorithms.Algorithm.clear_all()
            >>> alg1 = fm.algorithms.LinearAlgorithm() # tag 1
            >>> alg2 = fm.algorithms.NewtonAlgorithm() # tag 2
            >>> fm.algorithms.Algorithm.remove_algorithm(alg1.tag)
            >>> print(len(fm.algorithms.Algorithm.get_all_algorithms()))
            1
            >>> remaining_alg = fm.algorithms.Algorithm.get_algorithm(1) # alg2 is now tag 1
            >>> print(remaining_alg.algorithm_type)
            Newton
        """
        if tag in cls._created_algorithms:
            del cls._created_algorithms[tag]
            cls._reassign_tags()


class LinearAlgorithm(Algorithm):
    """Represents a linear algorithm for solving the system of equations.

    This algorithm typically takes only one iteration to solve the system,
    assuming linear behavior.

    Attributes:
        initial (bool): Indicates if the initial stiffness is used for iterations.
        factor_once (bool): Indicates if the system matrix is set up and factored only once.
    """
    def __init__(self, initial: bool = False, factor_once: bool = False):
        """Initializes a LinearAlgorithm.

        Args:
            initial: If True, uses initial stiffness for the analysis.
            factor_once: If True, the system matrix is set up and factored only once
                at the beginning of the analysis.

        Example:
            >>> import femora as fm
            >>> linear_alg = fm.algorithms.LinearAlgorithm(initial=True)
            >>> print(linear_alg.to_tcl())
            algorithm Linear -initial
        """
        super().__init__("Linear")
        self.initial = initial
        self.factor_once = factor_once

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this LinearAlgorithm.

        Example:
            >>> import femora as fm
            >>> linear_alg = fm.algorithms.LinearAlgorithm(initial=True, factor_once=False)
            >>> print(linear_alg.to_tcl())
            algorithm Linear -initial
            >>> linear_alg_default = fm.algorithms.LinearAlgorithm()
            >>> print(linear_alg_default.to_tcl())
            algorithm Linear
        """
        cmd = "algorithm Linear"
        if self.initial:
            cmd += " -initial"
        if self.factor_once:
            cmd += " -factorOnce"
        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this LinearAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'initial' and 'factor_once'.
        """
        return {
            "initial": self.initial,
            "factor_once": self.factor_once
        }


class NewtonAlgorithm(Algorithm):
    """Represents a Newton-Raphson algorithm for solving nonlinear residual equations.

    This algorithm uses the Newton-Raphson method for iterative solutions.

    Attributes:
        initial (bool): Indicates if the initial stiffness is used for iterations.
        initial_then_current (bool): Indicates if initial stiffness is used on the
            first step, then current stiffness for subsequent steps.
    """
    def __init__(self, initial: bool = False, initial_then_current: bool = False):
        """Initializes a NewtonAlgorithm.

        Args:
            initial: If True, uses the initial stiffness matrix throughout the analysis.
            initial_then_current: If True, uses the initial stiffness matrix for the
                first iteration and then switches to the current stiffness matrix
                for subsequent iterations.

        Raises:
            ValueError: If both `initial` and `initial_then_current` are set to True,
                as they are mutually exclusive.

        Example:
            >>> import femora as fm
            >>> newton_alg = fm.algorithms.NewtonAlgorithm(initial=True)
            >>> print(newton_alg.to_tcl())
            algorithm Newton -initial
            >>> newton_alg_hybrid = fm.algorithms.NewtonAlgorithm(initial_then_current=True)
            >>> print(newton_alg_hybrid.to_tcl())
            algorithm Newton -initialThenCurrent
        """
        super().__init__("Newton")
        self.initial = initial
        self.initial_then_current = initial_then_current

        # Check for incompatible options
        if self.initial and self.initial_then_current:
            raise ValueError("Cannot specify both -initial and -initialThenCurrent flags")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this NewtonAlgorithm.

        Example:
            >>> import femora as fm
            >>> newton_alg = fm.algorithms.NewtonAlgorithm(initial=True)
            >>> print(newton_alg.to_tcl())
            algorithm Newton -initial
        """
        cmd = "algorithm Newton"
        if self.initial:
            cmd += " -initial"
        if self.initial_then_current:
            cmd += " -initialThenCurrent"
        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this NewtonAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'initial' and 'initial_then_current'.
        """
        return {
            "initial": self.initial,
            "initial_then_current": self.initial_then_current
        }


class ModifiedNewtonAlgorithm(Algorithm):
    """Represents a Modified Newton-Raphson algorithm for solving nonlinear residual equations.

    This algorithm uses the modified Newton-Raphson method, where the tangent stiffness
    matrix is reformed less frequently than in the full Newton method.

    Attributes:
        initial (bool): Indicates if the initial stiffness is used for iterations.
        factor_once (bool): Indicates if the system matrix is set up and factored only once.
    """
    def __init__(self, initial: bool = False, factor_once: bool = False):
        """Initializes a ModifiedNewtonAlgorithm.

        Args:
            initial: If True, uses the initial stiffness matrix for all iterations.
            factor_once: If True, the system matrix is set up and factored only once
                at the beginning of the analysis.

        Example:
            >>> import femora as fm
            >>> mod_newton_alg = fm.algorithms.ModifiedNewtonAlgorithm(initial=True)
            >>> print(mod_newton_alg.to_tcl())
            algorithm ModifiedNewton -initial
        """
        super().__init__("ModifiedNewton")
        self.initial = initial
        self.factor_once = factor_once

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this ModifiedNewtonAlgorithm.

        Example:
            >>> import femora as fm
            >>> mod_newton_alg = fm.algorithms.ModifiedNewtonAlgorithm(factor_once=True)
            >>> print(mod_newton_alg.to_tcl())
            algorithm ModifiedNewton -factoronce
        """
        cmd = "algorithm ModifiedNewton"
        if self.initial:
            cmd += " -initial"
        if self.factor_once:
            cmd += " -factoronce"
        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this ModifiedNewtonAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'initial' and 'factor_once'.
        """
        return {
            "initial": self.initial,
            "factor_once": self.factor_once
        }


class NewtonLineSearchAlgorithm(Algorithm):
    """Represents a Newton-Raphson algorithm with line search.

    This algorithm enhances the standard Newton-Raphson method by incorporating
    a line search procedure to improve convergence, especially for highly nonlinear problems.

    Attributes:
        type_search (str): The type of line search algorithm to use (e.g., "InitialInterpolated").
        tol (float): The tolerance for the line search.
        max_iter (int): The maximum number of iterations allowed for the line search.
        min_eta (float): The minimum eta (step size reduction factor) value.
        max_eta (float): The maximum eta (step size reduction factor) value.
    """
    def __init__(self, type_search: str = "InitialInterpolated", tol: float = 0.8,
                 max_iter: int = 10, min_eta: float = 0.1, max_eta: float = 10.0):
        """Initializes a NewtonLineSearchAlgorithm.

        Args:
            type_search: The specific line search algorithm type to employ.
                Valid types include "Bisection", "Secant", "RegulaFalsi", and
                "InitialInterpolated".
            tol: The tolerance criterion for the line search to determine
                an acceptable step.
            max_iter: The maximum number of line search iterations to attempt
                before failing.
            min_eta: The minimum allowable step size reduction factor.
            max_eta: The maximum allowable step size reduction factor.

        Raises:
            ValueError: If an invalid `type_search` is provided.

        Example:
            >>> import femora as fm
            >>> line_search_alg = fm.algorithms.NewtonLineSearchAlgorithm(type_search="Bisection", tol=0.5)
            >>> print(line_search_alg.to_tcl())
            algorithm NewtonLineSearch -type Bisection -tol 0.5
        """
        super().__init__("NewtonLineSearch")
        self.type_search = type_search
        self.tol = tol
        self.max_iter = max_iter
        self.min_eta = min_eta
        self.max_eta = max_eta

        # Validate search type
        valid_search_types = ["Bisection", "Secant", "RegulaFalsi", "InitialInterpolated"]
        if self.type_search not in valid_search_types:
            raise ValueError(f"Invalid search type: {self.type_search}. "
                           f"Valid types are: {', '.join(valid_search_types)}")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this NewtonLineSearchAlgorithm.

        Example:
            >>> import femora as fm
            >>> default_alg = fm.algorithms.NewtonLineSearchAlgorithm()
            >>> print(default_alg.to_tcl())
            algorithm NewtonLineSearch -type InitialInterpolated
            >>> custom_alg = fm.algorithms.NewtonLineSearchAlgorithm(type_search="Secant", max_iter=20)
            >>> print(custom_alg.to_tcl())
            algorithm NewtonLineSearch -type Secant -maxIter 20
        """
        cmd = f"algorithm NewtonLineSearch -type {self.type_search}"

        # Add other parameters if they're not default values
        if self.tol != 0.8:
            cmd += f" -tol {self.tol}"
        if self.max_iter != 10:
            cmd += f" -maxIter {self.max_iter}"
        if self.min_eta != 0.1:
            cmd += f" -minEta {self.min_eta}"
        if self.max_eta != 10.0:
            cmd += f" -maxEta {self.max_eta}"

        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this NewtonLineSearchAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'type_search', 'tol', 'max_iter', 'min_eta', and 'max_eta'.
        """
        return {
            "type_search": self.type_search,
            "tol": self.tol,
            "max_iter": self.max_iter,
            "min_eta": self.min_eta,
            "max_eta": self.max_eta
        }


class KrylovNewtonAlgorithm(Algorithm):
    """Represents a Krylov-Newton algorithm.

    This algorithm uses a modified Newton method combined with Krylov subspace
    acceleration to improve convergence for large-scale nonlinear problems.

    Attributes:
        tang_iter (str): The tangent to iterate on, either "current", "initial", or "noTangent".
        tang_incr (str): The tangent to increment on, either "current", "initial", or "noTangent".
        max_dim (int): The maximum number of iterations before the tangent matrix is reformed.
    """
    def __init__(self, tang_iter: str = "current", tang_incr: str = "current", max_dim: int = 3):
        """Initializes a KrylovNewtonAlgorithm.

        Args:
            tang_iter: Specifies the tangent used for iteration. Valid options are
                "current", "initial", or "noTangent".
            tang_incr: Specifies the tangent used for incrementation. Valid options are
                "current", "initial", or "noTangent".
            max_dim: The maximum dimension of the Krylov subspace, which also controls
                how often the tangent matrix is reformed.

        Raises:
            ValueError: If an invalid `tang_iter` or `tang_incr` type is provided.

        Example:
            >>> import femora as fm
            >>> krylov_alg = fm.algorithms.KrylovNewtonAlgorithm(tang_iter="initial", max_dim=5)
            >>> print(krylov_alg.to_tcl())
            algorithm KrylovNewton -iterate initial -maxDim 5
        """
        super().__init__("KrylovNewton")
        self.tang_iter = tang_iter
        self.tang_incr = tang_incr
        self.max_dim = max_dim

        # Validate tangent options
        valid_tangent_options = ["current", "initial", "noTangent"]
        if self.tang_iter not in valid_tangent_options:
            raise ValueError(f"Invalid tangent iteration type: {self.tang_iter}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
        if self.tang_incr not in valid_tangent_options:
            raise ValueError(f"Invalid tangent increment type: {self.tang_incr}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this KrylovNewtonAlgorithm.

        Example:
            >>> import femora as fm
            >>> default_alg = fm.algorithms.KrylovNewtonAlgorithm()
            >>> print(default_alg.to_tcl())
            algorithm KrylovNewton
            >>> custom_alg = fm.algorithms.KrylovNewtonAlgorithm(tang_iter="initial", tang_incr="noTangent", max_dim=5)
            >>> print(custom_alg.to_tcl())
            algorithm KrylovNewton -iterate initial -increment noTangent -maxDim 5
        """
        cmd = "algorithm KrylovNewton"

        # Add parameters if they're not default values
        if self.tang_iter != "current":
            cmd += f" -iterate {self.tang_iter}"
        if self.tang_incr != "current":
            cmd += f" -increment {self.tang_incr}"
        if self.max_dim != 3:
            cmd += f" -maxDim {self.max_dim}"

        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this KrylovNewtonAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'tang_iter', 'tang_incr', and 'max_dim'.
        """
        return {
            "tang_iter": self.tang_iter,
            "tang_incr": self.tang_incr,
            "max_dim": self.max_dim
        }


class SecantNewtonAlgorithm(Algorithm):
    """Represents a Secant Newton algorithm.

    This algorithm uses the two-term update (e.g., Broyden-Fletcher-Goldfarb-Shanno)
    to accelerate convergence in the Newton method.

    Attributes:
        tang_iter (str): The tangent to iterate on, either "current", "initial", or "noTangent".
        tang_incr (str): The tangent to increment on, either "current", "initial", or "noTangent".
        max_dim (int): The maximum number of iterations before the tangent matrix is reformed.
    """
    def __init__(self, tang_iter: str = "current", tang_incr: str = "current", max_dim: int = 3):
        """Initializes a SecantNewtonAlgorithm.

        Args:
            tang_iter: Specifies the tangent used for iteration. Valid options are
                "current", "initial", or "noTangent".
            tang_incr: Specifies the tangent used for incrementation. Valid options are
                "current", "initial", or "noTangent".
            max_dim: The maximum number of iterations before the tangent matrix is reformed,
                affecting the subspace dimension.

        Raises:
            ValueError: If an invalid `tang_iter` or `tang_incr` type is provided.

        Example:
            >>> import femora as fm
            >>> secant_alg = fm.algorithms.SecantNewtonAlgorithm(tang_iter="initial", max_dim=5)
            >>> print(secant_alg.to_tcl())
            algorithm SecantNewton -iterate initial -maxDim 5
        """
        super().__init__("SecantNewton")
        self.tang_iter = tang_iter
        self.tang_incr = tang_incr
        self.max_dim = max_dim

        # Validate tangent options
        valid_tangent_options = ["current", "initial", "noTangent"]
        if self.tang_iter not in valid_tangent_options:
            raise ValueError(f"Invalid tangent iteration type: {self.tang_iter}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")
        if self.tang_incr not in valid_tangent_options:
            raise ValueError(f"Invalid tangent increment type: {self.tang_incr}. "
                           f"Valid types are: {', '.join(valid_tangent_options)}")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this SecantNewtonAlgorithm.

        Example:
            >>> import femora as fm
            >>> default_alg = fm.algorithms.SecantNewtonAlgorithm()
            >>> print(default_alg.to_tcl())
            algorithm SecantNewton
            >>> custom_alg = fm.algorithms.SecantNewtonAlgorithm(tang_iter="initial", tang_incr="noTangent", max_dim=5)
            >>> print(custom_alg.to_tcl())
            algorithm SecantNewton -iterate initial -increment noTangent -maxDim 5
        """
        cmd = "algorithm SecantNewton"

        # Add parameters if they're not default values
        if self.tang_iter != "current":
            cmd += f" -iterate {self.tang_iter}"
        if self.tang_incr != "current":
            cmd += f" -increment {self.tang_incr}"
        if self.max_dim != 3:
            cmd += f" -maxDim {self.max_dim}"

        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this SecantNewtonAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'tang_iter', 'tang_incr', and 'max_dim'.
        """
        return {
            "tang_iter": self.tang_iter,
            "tang_incr": self.tang_incr,
            "max_dim": self.max_dim
        }


class BFGSAlgorithm(Algorithm):
    """Represents a BFGS (Broyden-Fletcher-Goldfarb-Shanno) algorithm.

    This algorithm is a quasi-Newton method that performs successive rank-two updates
    of the tangent stiffness matrix, typically used for symmetric systems.

    Attributes:
        count (int): The number of iterations before the tangent matrix is explicitly reformed.
    """
    def __init__(self, count: int):
        """Initializes a BFGSAlgorithm.

        Args:
            count: The number of iterations for which the BFGS update is applied
                before the tangent matrix is reformed. Must be a positive integer.

        Raises:
            ValueError: If `count` is not a positive integer.

        Example:
            >>> import femora as fm
            >>> bfgs_alg = fm.algorithms.BFGSAlgorithm(count=5)
            >>> print(bfgs_alg.to_tcl())
            algorithm BFGS 5
        """
        super().__init__("BFGS")
        self.count = count

        # Validate count
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError("Count must be a positive integer")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this BFGSAlgorithm.

        Example:
            >>> import femora as fm
            >>> bfgs_alg = fm.algorithms.BFGSAlgorithm(count=10)
            >>> print(bfgs_alg.to_tcl())
            algorithm BFGS 10
        """
        return f"algorithm BFGS {self.count}"

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this BFGSAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'count'.
        """
        return {
            "count": self.count
        }


class BroydenAlgorithm(Algorithm):
    """Represents a Broyden algorithm.

    This algorithm is a quasi-Newton method that performs successive rank-one updates
    of the tangent stiffness matrix, suitable for general unsymmetric systems.

    Attributes:
        count (int): The number of iterations before the tangent matrix is explicitly reformed.
    """
    def __init__(self, count: int):
        """Initializes a BroydenAlgorithm.

        Args:
            count: The number of iterations for which the Broyden update is applied
                before the tangent matrix is reformed. Must be a positive integer.

        Raises:
            ValueError: If `count` is not a positive integer.

        Example:
            >>> import femora as fm
            >>> broyden_alg = fm.algorithms.BroydenAlgorithm(count=5)
            >>> print(broyden_alg.to_tcl())
            algorithm Broyden 5
        """
        super().__init__("Broyden")
        self.count = count

        # Validate count
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError("Count must be a positive integer")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this BroydenAlgorithm.

        Example:
            >>> import femora as fm
            >>> broyden_alg = fm.algorithms.BroydenAlgorithm(count=10)
            >>> print(broyden_alg.to_tcl())
            algorithm Broyden 10
        """
        return f"algorithm Broyden {self.count}"

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this BroydenAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'count'.
        """
        return {
            "count": self.count
        }


class ExpressNewtonAlgorithm(Algorithm):
    """Represents an Express Newton algorithm.

    This algorithm accepts the solution after a constant number of iterations,
    providing a fixed-iteration approach to solving nonlinear systems.

    Attributes:
        iter_count (int): The constant number of iterations to perform.
        k_multiplier (float): A multiplier applied to the system stiffness matrix.
        initial_tangent (bool): Indicates if the initial tangent stiffness matrix is used.
        current_tangent (bool): Indicates if the current tangent stiffness matrix is used.
        factor_once (bool): Indicates if the system matrix is factored only once.
    """
    def __init__(self, iter_count: int = 2, k_multiplier: float = 1.0,
                 initial_tangent: bool = False, current_tangent: bool = True,
                 factor_once: bool = False):
        """Initializes an ExpressNewtonAlgorithm.

        Args:
            iter_count: The fixed number of iterations to perform in each step.
                Must be a positive integer.
            k_multiplier: A scalar multiplier to be applied to the system stiffness matrix.
            initial_tangent: If True, uses the initial tangent stiffness matrix.
                Mutually exclusive with `current_tangent`.
            current_tangent: If True, uses the current tangent stiffness matrix.
                Mutually exclusive with `initial_tangent`.
            factor_once: If True, the system matrix is set up and factored only once
                at the beginning of the analysis.

        Raises:
            ValueError: If `iter_count` is not a positive integer, or if both
                `initial_tangent` and `current_tangent` are set to True.

        Example:
            >>> import femora as fm
            >>> express_alg = fm.algorithms.ExpressNewtonAlgorithm(iter_count=3, k_multiplier=0.9, initial_tangent=True)
            >>> print(express_alg.to_tcl())
            algorithm ExpressNewton 3 0.9 -initialTangent
        """
        super().__init__("ExpressNewton")
        self.iter_count = iter_count
        self.k_multiplier = k_multiplier
        self.initial_tangent = initial_tangent
        self.current_tangent = current_tangent
        self.factor_once = factor_once

        # Validate iter_count
        if not isinstance(self.iter_count, int) or self.iter_count < 1:
            raise ValueError("Iteration count must be a positive integer")

        # Check for incompatible options
        if self.initial_tangent and self.current_tangent:
            raise ValueError("Cannot specify both -initialTangent and -currentTangent flags")

    def to_tcl(self) -> str:
        """Converts the algorithm configuration to an OpenSees TCL command string.

        Returns:
            str: The TCL command string representing this ExpressNewtonAlgorithm.

        Example:
            >>> import femora as fm
            >>> default_alg = fm.algorithms.ExpressNewtonAlgorithm()
            >>> print(default_alg.to_tcl())
            algorithm ExpressNewton 2 1.0 -currentTangent
            >>> custom_alg = fm.algorithms.ExpressNewtonAlgorithm(iter_count=5, k_multiplier=1.2, factor_once=True, initial_tangent=True, current_tangent=False)
            >>> print(custom_alg.to_tcl())
            algorithm ExpressNewton 5 1.2 -initialTangent -factorOnce
        """
        cmd = f"algorithm ExpressNewton {self.iter_count} {self.k_multiplier}"

        # Add optional flags
        if self.initial_tangent:
            cmd += " -initialTangent"
        if self.current_tangent and not self.initial_tangent:
            cmd += " -currentTangent"
        if self.factor_once:
            cmd += " -factorOnce"

        return cmd

    def get_values(self) -> Dict[str, Union[str, int, float, bool]]:
        """Gets the parameters defining this ExpressNewtonAlgorithm.

        Returns:
            Dict[str, Union[str, int, float, bool]]: A dictionary of parameter values,
                including 'iter_count', 'k_multiplier', 'initial_tangent',
                'current_tangent', and 'factor_once'.
        """
        return {
            "iter_count": self.iter_count,
            "k_multiplier": self.k_multiplier,
            "initial_tangent": self.initial_tangent,
            "current_tangent": self.current_tangent,
            "factor_once": self.factor_once
        }


class AlgorithmManager:
    """Manages all algorithm instances in the Femora project as a singleton.

    This class provides a centralized point of access for creating, retrieving,
    and managing various numerical algorithms used in structural analysis.
    It ensures that only one instance of the manager exists throughout the application.

    Attributes:
        _instance (AlgorithmManager): The singleton instance of the AlgorithmManager.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlgorithmManager, cls).__new__(cls)
        return cls._instance

    def create_algorithm(self, algorithm_type: str, **kwargs) -> Algorithm:
        """Creates a new algorithm instance of the specified type.

        Args:
            algorithm_type: The string identifier for the type of algorithm to create.
            **kwargs: Additional keyword arguments to pass to the algorithm's constructor.

        Returns:
            Algorithm: The newly created algorithm instance.

        Raises:
            ValueError: If an unknown `algorithm_type` is provided.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> linear_alg = manager.create_algorithm('linear')
            >>> print(isinstance(linear_alg, fm.algorithms.LinearAlgorithm))
            True
            >>> newton_alg = manager.create_algorithm('newton', initial=True)
            >>> print(newton_alg.initial)
            True
        """
        return Algorithm.create_algorithm(algorithm_type, **kwargs)

    def get_algorithm(self, tag: int) -> Algorithm:
        """Retrieves a specific algorithm instance by its unique tag.

        Args:
            tag: The unique integer tag of the algorithm to retrieve.

        Returns:
            Algorithm: The algorithm instance with the specified tag.

        Raises:
            KeyError: If no algorithm with the given `tag` exists.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> manager.clear_all() # Ensure a clean state for example
            >>> alg = manager.create_algorithm('linear')
            >>> retrieved_alg = manager.get_algorithm(alg.tag)
            >>> print(retrieved_alg.algorithm_type)
            Linear
        """
        return Algorithm.get_algorithm(tag)

    def remove_algorithm(self, tag: int) -> None:
        """Removes an algorithm instance from the manager by its tag.

        After removal, all remaining algorithms are re-tagged sequentially.

        Args:
            tag: The unique integer tag of the algorithm to remove.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> manager.clear_all()
            >>> alg1 = manager.create_algorithm('linear') # tag 1
            >>> alg2 = manager.create_algorithm('newton') # tag 2
            >>> manager.remove_algorithm(alg1.tag)
            >>> print(len(manager.get_all_algorithms()))
            1
            >>> remaining_alg = manager.get_algorithm(1) # alg2 is now tag 1
            >>> print(remaining_alg.algorithm_type)
            Newton
        """
        Algorithm.remove_algorithm(tag)

    def get_all_algorithms(self) -> Dict[int, Algorithm]:
        """Retrieves all created algorithm instances managed by the system.

        Returns:
            Dict[int, Algorithm]: A dictionary where keys are unique integer tags
                and values are the corresponding algorithm instances.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> manager.clear_all()
            >>> alg1 = manager.create_algorithm('linear')
            >>> alg2 = manager.create_algorithm('newton')
            >>> all_algs = manager.get_all_algorithms()
            >>> print(len(all_algs))
            2
            >>> print(all_algs[alg1.tag].algorithm_type)
            Linear
        """
        return Algorithm.get_all_algorithms()

    def get_available_types(self) -> List[str]:
        """Gets a list of all currently registered algorithm types.

        Returns:
            List[str]: A list of strings representing the available algorithm types.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> types = manager.get_available_types()
            >>> print('linear' in types)
            True
            >>> print('newton' in types)
            True
        """
        return Algorithm.get_available_types()

    def clear_all(self):
        """Clears all created algorithm instances and resets the tag counter.

        This effectively removes all algorithms from the system's memory.

        Example:
            >>> import femora as fm
            >>> manager = fm.algorithms.AlgorithmManager()
            >>> _ = manager.create_algorithm('linear')
            >>> print(len(manager.get_all_algorithms()))
            1
            >>> manager.clear_all()
            >>> print(len(manager.get_all_algorithms()))
            0
        """
        Algorithm.clear_all()


# Register all algorithms
Algorithm.register_algorithm('linear', LinearAlgorithm)
Algorithm.register_algorithm('newton', NewtonAlgorithm)
Algorithm.register_algorithm('modifiednewton', ModifiedNewtonAlgorithm)
Algorithm.register_algorithm('newtonlinesearch', NewtonLineSearchAlgorithm)
Algorithm.register_algorithm('krylovnewton', KrylovNewtonAlgorithm)
Algorithm.register_algorithm('secantnewton', SecantNewtonAlgorithm)
Algorithm.register_algorithm('bfgs', BFGSAlgorithm)
Algorithm.register_algorithm('broyden', BroydenAlgorithm)
Algorithm.register_algorithm('expressnewton', ExpressNewtonAlgorithm)