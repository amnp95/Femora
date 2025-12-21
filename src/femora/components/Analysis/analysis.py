from typing import Optional, Dict, List, Any, Union
from .base import AnalysisComponent
from .numberers import Numberer, NumbererManager
from .integrators import Integrator, IntegratorManager, StaticIntegrator, TransientIntegrator
from .algorithms import Algorithm, AlgorithmManager
from .systems import System, SystemManager
from .constraint_handlers import ConstraintHandler, ConstraintHandlerManager
from .convergenceTests import Test, TestManager


class Analysis(AnalysisComponent):
    """Main class for managing an OpenSees structural analysis.

    An Analysis object combines six essential components (constraint handler, numberer,
    system solver, solution algorithm, convergence test, and integrator) to define
    how the finite element analysis is performed. It supports static, transient,
    and variable time-step transient analyses.

    Attributes:
        tag: The unique sequential identifier for this analysis.
        name: User-specified name for the analysis (must be unique).
        analysis_type: Type of analysis ("Static", "Transient", or "VariableTransient").
        constraint_handler: The constraint handler for enforcing boundary conditions.
        numberer: The DOF numberer for equation numbering.
        system: The system solver for solving equations.
        algorithm: The solution algorithm for nonlinear iterations.
        test: The convergence test for checking solution convergence.
        integrator: The integrator for time or load stepping.
        num_steps: Number of analysis steps (required for Static).
        final_time: Final time for analysis (optional for Transient).
        dt: Time step increment (required for Transient/VariableTransient).
        dt_min: Minimum time step (required for VariableTransient).
        dt_max: Maximum time step (required for VariableTransient).
        jd: Desired iterations per step (required for VariableTransient).
        num_sublevels: Number of sublevels for analysis failure recovery.
        num_substeps: Number of substeps to try at each sublevel.

    Example:
        >>> from femora.components.Analysis.analysis import Analysis
        >>> # Create analysis components first
        >>> # handler = constraint_manager.create_handler("transformation")
        >>> # numberer = numberer_manager.create_numberer("rcm")
        >>> # system = system_manager.create_system("bandgen")
        >>> # algorithm = algorithm_manager.create_algorithm("newton")
        >>> # test = test_manager.create_test("normunbalance", tol=1e-6, max_iter=100)
        >>> # integrator = integrator_manager.create_integrator("loadcontrol", incr=0.1)
        >>> # Create a static analysis
        >>> # analysis = Analysis(
        >>> #     name="PushoverAnalysis",
        >>> #     analysis_type="Static",
        >>> #     constraint_handler=handler,
        >>> #     numberer=numberer,
        >>> #     system=system,
        >>> #     algorithm=algorithm,
        >>> #     test=test,
        >>> #     integrator=integrator,
        >>> #     num_steps=10
        >>> # )
        >>> # print(analysis.tag)
    """
    _instances = {}  # Class-level dictionary to track all created analyses
    _next_tag = 1    # Class variable to track the next tag to assign
    _names = set()   # Class-level set to track used names

    def __init__(self, name: str, analysis_type: str, constraint_handler: ConstraintHandler,
                 numberer: Numberer, system: System, algorithm: Algorithm,
                 test: Test, integrator: Integrator, num_steps: Optional[int] = None,
                 final_time: Optional[float] = None, dt: Optional[float] = None,
                 dt_min: Optional[float] = None, dt_max: Optional[float] = None,
                 jd: Optional[int] = None, num_sublevels: Optional[int] = None,
                 num_substeps: Optional[int] = None):
        """Initializes the Analysis with all required components.

        This method validates component compatibility and analysis parameters
        before creating the analysis object.

        Args:
            name: Name of the analysis for identification. Must be unique.
            analysis_type: Type of analysis. Must be one of "Static", "Transient",
                or "VariableTransient".
            constraint_handler: The constraint handler for the analysis.
            numberer: The numberer for the analysis.
            system: The system solver for the analysis.
            algorithm: The solution algorithm for the analysis.
            test: The convergence test for the analysis.
            integrator: The integrator for the analysis. Must be compatible with
                analysis_type (StaticIntegrator for Static, TransientIntegrator
                for Transient/VariableTransient).
            num_steps: Number of analysis steps. Required for Static analysis,
                optional for others (mutually exclusive with final_time).
            final_time: Final time for analysis. Optional for Transient/VariableTransient
                (mutually exclusive with num_steps).
            dt: Time step increment. Required for Transient or VariableTransient analysis.
            dt_min: Minimum time step. Required for VariableTransient analysis.
            dt_max: Maximum time step. Required for VariableTransient analysis.
            jd: Number of iterations desired at each step. Required for
                VariableTransient analysis.
            num_sublevels: Number of sublevels in case of analysis failure. Optional,
                must be provided with num_substeps.
            num_substeps: Number of substeps to try at each sublevel. Optional,
                must be provided with num_sublevels.

        Raises:
            ValueError: If integrator type is incompatible with analysis type.
            ValueError: If analysis parameters are inconsistent with analysis type.
            ValueError: If analysis name is not unique.
            ValueError: If analysis_type is not one of the valid types.
        """
        # Check if name is unique
        if name in Analysis._names:
            raise ValueError(f"Analysis name '{name}' is already in use. Names must be unique.")

        self.tag = Analysis._next_tag
        Analysis._next_tag += 1
        self.name = name
        Analysis._names.add(name)

        self.analysis_type = analysis_type

        # Validate analysis type
        if analysis_type not in ["Static", "Transient", "VariableTransient"]:
            raise ValueError(f"Unknown analysis type: {analysis_type}. Must be 'Static', 'Transient', or 'VariableTransient'.")

        # Set all components
        self.constraint_handler = constraint_handler
        self.numberer = numberer
        self.system = system
        self.algorithm = algorithm
        self.test = test

        # Validate integrator compatibility
        if analysis_type == "Static" and not isinstance(integrator, StaticIntegrator):
            raise ValueError(f"Static analysis requires a static integrator. {integrator.integrator_type} is not compatible.")

        elif analysis_type in ["Transient", "VariableTransient"] and not isinstance(integrator, TransientIntegrator):
            raise ValueError(f"Transient analysis requires a transient integrator. {integrator.integrator_type} is not compatible.")

        self.integrator = integrator

        # Validate and set analysis parameters
        if analysis_type == "Static":
            if num_steps is None:
                raise ValueError("Static analysis requires num_steps parameter.")
            if final_time is not None:
                raise ValueError("Static analysis does not use final_time parameter.")
        else:  # Transient or VariableTransient
            if num_steps is None and final_time is None:
                raise ValueError("Transient analysis requires either num_steps or final_time parameter.")
            if num_steps is not None and final_time is not None:
                raise ValueError("Only one of num_steps or final_time should be provided, not both.")

        self.num_steps = num_steps
        self.final_time = final_time

        # Time step parameters
        if analysis_type in ["Transient", "VariableTransient"] and dt is None:
            raise ValueError(f"{analysis_type} analysis requires a time step (dt).")

        self.dt = dt

        # VariableTransient specific parameters
        if analysis_type == "VariableTransient":
            if dt_min is None or dt_max is None:
                raise ValueError("VariableTransient analysis requires dt_min and dt_max parameters.")

            if jd is None:
                raise ValueError("VariableTransient analysis requires jd parameter (desired iterations per step).")

        self.dt_min = dt_min
        self.dt_max = dt_max
        self.jd = jd

        # Optional sublevel parameters (only applicable to Transient analyses)
        if analysis_type == "Static" and (num_sublevels is not None or num_substeps is not None):
            raise ValueError("num_sublevels and num_substeps are only applicable to Transient analysis.")

        if (num_sublevels is not None and num_substeps is None) or (num_sublevels is None and num_substeps is not None):
            raise ValueError("Both num_sublevels and num_substeps must be provided if either is specified.")

        self.num_sublevels = num_sublevels
        self.num_substeps = num_substeps

        # Register this analysis in the class-level tracking dictionary
        Analysis._instances[self.tag] = self

    @classmethod
    def get_analysis(cls, tag: int) -> 'Analysis':
        """Retrieves a specific analysis by its tag.

        Args:
            tag: The tag of the analysis.

        Returns:
            The analysis with the specified tag.

        Raises:
            KeyError: If no analysis with the given tag exists.
        """
        if tag not in cls._instances:
            raise KeyError(f"No analysis found with tag {tag}")
        return cls._instances[tag]

    @classmethod
    def get_all_analyses(cls) -> Dict[int, 'Analysis']:
        """Retrieves all created analyses.

        Returns:
            A dictionary of all analyses, keyed by their unique tags.
        """
        return cls._instances

    @classmethod
    def clear_all(cls) -> None:
        """Clears all analyses and resets tags.

        This method removes all registered analyses, clears all names,
        and resets the tag counter to 1.
        """
        cls._instances.clear()
        cls._names.clear()
        cls._next_tag = 1

    def validate(self) -> bool:
        """Validates that all required components are set.

        Returns:
            True if all components are set, False otherwise.
        """
        return (
            self.constraint_handler is not None and
            self.numberer is not None and
            self.system is not None and
            self.algorithm is not None and
            self.test is not None and
            self.integrator is not None
        )

    def get_missing_components(self) -> List[str]:
        """Gets a list of missing components.

        Returns:
            List of names of missing components. Empty list if all
                components are present.
        """
        missing = []
        if self.constraint_handler is None:
            missing.append("constraint handler")
        if self.numberer is None:
            missing.append("numberer")
        if self.system is None:
            missing.append("system")
        if self.algorithm is None:
            missing.append("algorithm")
        if self.test is None:
            missing.append("test")
        if self.integrator is None:
            missing.append("integrator")
        return missing

    def to_tcl(self) -> str:
        """Converts the analysis to a TCL command string for OpenSees.

        This method generates the complete TCL script for setting up and
        running the analysis, including all component definitions and the
        analysis loop.

        Returns:
            The TCL command string for all components and the analysis.

        Raises:
            ValueError: If any required component is missing.
        """
        if not self.validate():
            missing = self.get_missing_components()
            raise ValueError(f"Cannot create analysis. Missing components: {', '.join(missing)}")

        # Generate TCL commands for each component
        commands = []
        commands.append("if {$pid == 0} {" + f'puts [string repeat "=" 120] ' + "}")
        commands.append("if {$pid == 0} {" + f'puts "Starting analysis : {self.name}"' + "}")
        commands.append(commands[0])
        commands.append(self.constraint_handler.to_tcl())
        commands.append(self.numberer.to_tcl())
        commands.append(self.system.to_tcl())
        commands.append(self.algorithm.to_tcl())
        commands.append(self.test.to_tcl())
        commands.append(self.integrator.to_tcl())

        # Add analysis command
        commands.append(f"analysis {self.analysis_type}")

        # add analyze command with parameters
        if self.analysis_type == "Static":
            commands.append(f"analyze {self.num_steps}")
        elif self.analysis_type in ["Transient", "VariableTransient"]:
            if self.final_time is not None:
                commands.append("while {[getTime] < %f} {" % self.final_time)
                commands.append('\tif {$pid == 0} {puts "Time : [getTime]"}\n')
                commands.append(f"\tset Ok [analyze 1 {self.dt}]\n")
                commands.append("}")
            else:
                commands.append(f"set AnalysisStep 0")
                commands.append("while {"+f" $AnalysisStep < {self.num_steps}"+"} {")
                commands.append('\tif {$pid==0} {puts "$AnalysisStep' +f'/{self.num_steps}"' +"}")
                commands.append(f"\tset Ok [analyze 1 {self.dt}]")
                commands.append(f"\tincr AnalysisStep 1")
                commands.append("}")

        # wipe analysis command
        commands.append("wipeAnalysis")




        return "\n".join(commands)

    def get_values(self) -> Dict[str, Any]:
        """Gets the parameters defining this analysis.

        Returns:
            Dictionary of parameter values including analysis type, time stepping
                parameters, and component information.
        """
        values = {
            "name": self.name,
            "analysis_type": self.analysis_type,
            "num_steps": self.num_steps,
            "final_time": self.final_time,
            "dt": self.dt
        }

        # Add VariableTransient specific parameters if applicable
        if self.analysis_type == "VariableTransient":
            values.update({
                "dt_min": self.dt_min,
                "dt_max": self.dt_max,
                "jd": self.jd
            })

        # Add sublevel parameters if provided
        if self.num_sublevels is not None:
            values.update({
                "num_sublevels": self.num_sublevels,
                "num_substeps": self.num_substeps
            })

        # Add component info if set
        if self.constraint_handler:
            values["constraint_handler"] = {
                "tag": self.constraint_handler.tag,
                "type": self.constraint_handler.handler_type
            }

        if self.numberer:
            values["numberer"] = {
                "type": self.numberer.to_tcl().split()[1]  # Extract type from TCL command
            }

        if self.system:
            values["system"] = {
                "tag": self.system.tag,
                "type": self.system.system_type
            }

        if self.algorithm:
            values["algorithm"] = {
                "tag": self.algorithm.tag,
                "type": self.algorithm.algorithm_type
            }

        if self.test:
            values["test"] = {
                "tag": self.test.tag,
                "type": self.test.test_type
            }

        if self.integrator:
            values["integrator"] = {
                "tag": self.integrator.tag,
                "type": self.integrator.integrator_type
            }

        return values


class AnalysisManager:
    """Singleton manager class for creating and managing structural analyses.

    This class provides a unified interface for creating analyses with proper
    component management. It includes sub-managers for creating all analysis
    components (tests, constraint handlers, numberers, systems, algorithms,
    and integrators) and provides convenience methods for common analysis types.

    Attributes:
        test: TestManager instance for creating convergence tests.
        constraint: ConstraintHandlerManager instance for creating constraint handlers.
        numberer: NumbererManager instance for creating DOF numberers.
        system: SystemManager instance for creating system solvers.
        algorithm: AlgorithmManager instance for creating solution algorithms.
        integrator: IntegratorManager instance for creating integrators.

    Example:
        >>> from femora.components.Analysis.analysis import AnalysisManager
        >>> # Get the singleton instance
        >>> manager = AnalysisManager()
        >>> # Create a default transient analysis
        >>> # analysis = manager.create_default_transient_analysis(
        >>> #     username="seismic",
        >>> #     dt=0.01,
        >>> #     num_steps=1000
        >>> # )
        >>> # Or create a custom analysis
        >>> # test = manager.test.create_test("normunbalance", tol=1e-6, max_iter=100)
        >>> # handler = manager.constraint.create_handler("transformation")
        >>> # numberer = manager.numberer.create_numberer("rcm")
        >>> # system = manager.system.create_system("bandgen")
        >>> # algorithm = manager.algorithm.create_algorithm("newton")
        >>> # integrator = manager.integrator.create_integrator("loadcontrol", incr=0.1)
        >>> # custom_analysis = manager.create_analysis(
        >>> #     name="CustomStatic",
        >>> #     analysis_type="Static",
        >>> #     constraint_handler=handler,
        >>> #     numberer=numberer,
        >>> #     system=system,
        >>> #     algorithm=algorithm,
        >>> #     test=test,
        >>> #     integrator=integrator,
        >>> #     num_steps=10
        >>> # )
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalysisManager, cls).__new__(cls)
            # Initialize instance variables in __new__ since it's a singleton
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initializes the AnalysisManager singleton instance.

        This method only initializes the component managers on first creation.
        Subsequent calls return the existing instance without re-initialization.
        """
        # Only initialize the managers once
        if not self._initialized:
            self.test = TestManager()
            self.constraint = ConstraintHandlerManager()
            self.numberer = NumbererManager()
            self.system = SystemManager()
            self.algorithm = AlgorithmManager()
            self.integrator = IntegratorManager()
            self._initialized = True

    def create_default_transient_analysis(self, username: str, dt: float, num_steps: int = None,
                                         final_time: float = None,
                                         options:Dict[str, AnalysisComponent]=dict()) -> Analysis:
        """Creates a default transient analysis with predefined components.

        This convenience method creates a transient analysis with sensible defaults:
        - ParallelRCM numberer
        - Newmark integrator (gamma=0.5, beta=0.25)
        - Mumps system solver (ICNTL14=400, ICNTL7=7)
        - EnergyIncr test (tol=1e-3, max_iter=20, print_flag=2)
        - ModifiedNewton algorithm with factoronce
        - Transformation constraint handler

        Args:
            username: Username for the analysis name (creates "defualtTransient_{username}").
            dt: Time step increment.
            num_steps: Number of analysis steps. Mutually exclusive with final_time.
            final_time: Final time for analysis. Mutually exclusive with num_steps.
            options: Optional dictionary to override default components. Keys can be
                "numberer", "integrator", "system", "test", "algorithm", or
                "constraint_handler".

        Returns:
            The created transient analysis with default settings.

        Raises:
            ValueError: If neither num_steps nor final_time is provided, or if
                both are provided.
        """
        # Validate inputs
        if (num_steps is None and final_time is None) or (num_steps is not None and final_time is not None):
            raise ValueError("Exactly one of num_steps or final_time must be provided")

        # Create analysis name
        analysis_name = f"defualtTransient_{username}"

        # Create components
        numberer = options.get("numberer", self.numberer.create_numberer("parallelrcm"))
        integrator = options.get("integrator", self.integrator.create_integrator("newmark", gamma=0.5, beta=0.25))
        system = options.get("system", self.system.create_system("mumps", icntl14=400, icntl7=7))
        test = options.get("test", self.test.create_test("energyincr", tol=1e-3, max_iter=20, print_flag=2))
        algorithm = options.get("algorithm", self.algorithm.create_algorithm("modifiednewton", factor_once=True))
        constraint_handler = options.get("constraint_handler", self.constraint.create_handler("transformation"))


        # Create and return the analysis
        return self.create_analysis(
            name=analysis_name,
            analysis_type="Transient",
            constraint_handler=constraint_handler,
            numberer=numberer,
            system=system,
            algorithm=algorithm,
            test=test,
            integrator=integrator,
            num_steps=num_steps,
            final_time=final_time,
            dt=dt
        )

    def create_analysis(self, name: str, analysis_type: str, constraint_handler: ConstraintHandler,
                     numberer: Numberer, system: System, algorithm: Algorithm,
                     test: Test, integrator: Integrator, num_steps: Optional[int] = None,
                     final_time: Optional[float] = None, dt: Optional[float] = None,
                     dt_min: Optional[float] = None, dt_max: Optional[float] = None,
                     jd: Optional[int] = None, num_sublevels: Optional[int] = None,
                     num_substeps: Optional[int] = None) -> Analysis:
        """Creates a new analysis with all required components.

        Args:
            name: Name of the analysis.
            analysis_type: Type of analysis ("Static", "Transient", or "VariableTransient").
            constraint_handler: The constraint handler for the analysis.
            numberer: The numberer for the analysis.
            system: The system solver for the analysis.
            algorithm: The solution algorithm for the analysis.
            test: The convergence test for the analysis.
            integrator: The integrator for the analysis.
            num_steps: Number of analysis steps. Required for Static, optional for others.
            final_time: Final time for analysis. Optional for Transient/VariableTransient.
            dt: Time step increment. Required for Transient or VariableTransient.
            dt_min: Minimum time step. Required for VariableTransient.
            dt_max: Maximum time step. Required for VariableTransient.
            jd: Desired iterations per step. Required for VariableTransient.
            num_sublevels: Number of sublevels for failure recovery. Optional.
            num_substeps: Number of substeps per sublevel. Optional.

        Returns:
            The created analysis.

        Raises:
            ValueError: If analysis parameters are inconsistent with analysis type.
        """
        return Analysis(name, analysis_type, constraint_handler, numberer, system, algorithm,
                      test, integrator, num_steps, final_time, dt, dt_min, dt_max, jd,
                      num_sublevels, num_substeps)

    def get_analysis(self, identifier: Union[int, str, Analysis]) -> Analysis:
        """Gets analysis by tag, name, or instance.

        Args:
            identifier: Tag (int), name (str), or instance of the analysis to retrieve.

        Returns:
            The analysis.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        if isinstance(identifier, int):
            return Analysis.get_analysis(identifier)
        elif isinstance(identifier, str):
            analysis = self.find_analysis_by_name(identifier)
            if analysis is None:
                raise KeyError(f"No analysis found with name '{identifier}'")
            return analysis
        elif isinstance(identifier, Analysis):
            return identifier
        else:
            raise TypeError(f"Identifier must be an int (tag), str (name), or Analysis instance, not {type(identifier)}")

    def find_analysis_by_name(self, name: str) -> Optional[Analysis]:
        """Finds an analysis by its name (case-insensitive).

        Args:
            name: Name of the analysis to find.

        Returns:
            The analysis with the given name, or None if not found.
        """
        for analysis in Analysis.get_all_analyses().values():
            if analysis.name.lower() == name.lower():
                return analysis
        return None

    def remove_analysis(self, identifier: Union[int, str, Analysis]) -> None:
        """Removes an analysis by its tag, name, or instance.

        Args:
            identifier: Tag, name, or instance of the analysis to remove.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)

        # Remove from name set
        Analysis._names.remove(analysis.name)

        # Remove from instances dictionary
        if analysis.tag in Analysis._instances:
            del Analysis._instances[analysis.tag]

    def get_all_analyses(self) -> Dict[int, Analysis]:
        """Gets all analyses.

        Returns:
            Dictionary of all analyses, keyed by their tags.
        """
        return Analysis.get_all_analyses()

    def clear_all(self) -> None:
        """Clears all analyses.

        This method removes all registered analyses and resets the tag counter.
        """
        Analysis.clear_all()

    def update_constraint_handler(self, identifier: Union[int, str, Analysis],
                                constraint_handler: ConstraintHandler) -> None:
        """Updates the constraint handler for an analysis.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            constraint_handler: The new constraint handler.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)
        analysis.constraint_handler = constraint_handler

    def update_numberer(self, identifier: Union[int, str, Analysis],
                      numberer: Numberer) -> None:
        """Updates the numberer for an analysis.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            numberer: The new numberer.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)
        analysis.numberer = numberer

    def update_system(self, identifier: Union[int, str, Analysis],
                    system: System) -> None:
        """Updates the system solver for an analysis.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            system: The new system solver.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)
        analysis.system = system

    def update_algorithm(self, identifier: Union[int, str, Analysis],
                       algorithm: Algorithm) -> None:
        """Updates the solution algorithm for an analysis.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            algorithm: The new solution algorithm.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)
        analysis.algorithm = algorithm

    def update_test(self, identifier: Union[int, str, Analysis],
                  test: Test) -> None:
        """Updates the convergence test for an analysis.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            test: The new convergence test.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
        """
        analysis = self.get_analysis(identifier)
        analysis.test = test

    def update_integrator(self, identifier: Union[int, str, Analysis],
                        integrator: Integrator) -> None:
        """Updates the integrator for an analysis.

        This method validates that the new integrator is compatible with the
        analysis type before updating.

        Args:
            identifier: Tag, name, or instance of the analysis to modify.
            integrator: The new integrator.

        Raises:
            KeyError: If no analysis with the given tag or name exists.
            TypeError: If identifier is not a valid type.
            ValueError: If integrator type is incompatible with analysis type.
        """
        analysis = self.get_analysis(identifier)

        if analysis.analysis_type == "Static" and not isinstance(integrator, StaticIntegrator):
            raise ValueError(f"Static analysis requires a static integrator. {integrator.integrator_type} is not compatible.")

        elif analysis.analysis_type in ["Transient", "VariableTransient"] and not isinstance(integrator, TransientIntegrator):
            raise ValueError(f"Transient analysis requires a transient integrator. {integrator.integrator_type} is not compatible.")

        analysis.integrator = integrator
