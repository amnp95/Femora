from typing import List, Dict, Union, Optional
import weakref

# Import your existing component classes
from femora.components.Constraint.mpConstraint import mpConstraint
from femora.components.Constraint.spConstraint import SPConstraint
from femora.components.Pattern.patternBase import Pattern
from femora.components.Recorder.recorderBase import Recorder
from femora.components.Analysis.analysis import Analysis
from femora.components.Actions.action import Action

# Define a union type for all components that can be used in the process
ProcessComponent = Union[SPConstraint, mpConstraint, Pattern, Recorder, Analysis, Action]

class ProcessManager:
    """Singleton class to manage the sequence of operations in structural analysis.

    This class maintains an ordered list of analysis steps, where each step
    references a component object (constraint, pattern, recorder, analysis, or action).
    Steps are stored as weak references to prevent circular dependencies, except
    for Action objects which use strong references.

    Attributes:
        steps: List of step dictionaries, each containing a component reference
            and optional description.
        current_step: Index of the currently executing step (-1 if not started).

    Example:
        >>> from femora.components.Process.process import ProcessManager
        >>> # Get the singleton instance
        >>> process = ProcessManager()
        >>> # Add steps to the process
        >>> # process.add_step(my_constraint, "Apply boundary conditions")
        >>> # process.add_step(my_pattern, "Apply loads")
        >>> # process.add_step(my_analysis, "Run static analysis")
        >>> # Get total number of steps
        >>> num_steps = len(process)
        >>> # Generate TCL script
        >>> # tcl_script = process.to_tcl()
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initializes the ProcessManager singleton instance.

        This method only initializes the instance on first creation. Subsequent
        calls return the existing instance without re-initialization.
        """
        if not self._initialized:
            self.steps = []
            self.current_step = -1
            self._initialized = True


    def __iter__(self):
        """Returns an iterator over the steps.

        Returns:
            Iterator over the steps list.
        """
        return iter(self.steps)


    def __len__(self):
        """Returns the number of steps in the process.

        Returns:
            Number of steps currently in the process.
        """
        return len(self.steps)

    def add_step(self, component: ProcessComponent, description: str = "") -> int:
        """Adds a step to the end of the process.

        This method appends a new step to the process. Components are stored
        as weak references (except Action objects which use strong references)
        to prevent circular dependencies.

        Args:
            component: The component object to use in this step. Must be one
                of the allowed component types (SPConstraint, mpConstraint,
                Pattern, Recorder, Analysis, or Action).
            description: Optional description of the step. Defaults to empty string.

        Returns:
            Index of the newly added step.

        Raises:
            TypeError: If component is not one of the allowed types.
        """
        # Store a weak reference to the component
        if not isinstance(component, Action):
            # If the component is not an Action, store a weak reference
            component_ref = weakref.ref(component)
        elif isinstance(component, Action):
            # If the component is an Action, store a strong reference
            # This is because Actions are not expected to be weakly referenced
            # and should be kept alive for the duration of the process
            component_ref = component
        else:
            raise TypeError("Invalid component type. Must be one of the allowed types.")



        step = {
            "component": component_ref,
            "description": description
        }

        self.steps.append(step)
        return len(self.steps) - 1

    def insert_step(self, index: int, component: ProcessComponent, description: str = "") -> bool:
        """Inserts a step at a specific position in the process.

        This method allows insertion at any position, including negative indexing
        (where -1 refers to the last position). The current step index is
        automatically adjusted if necessary.

        Args:
            index: Position to insert the step. Negative indices are supported
                (e.g., -1 inserts before the last step).
            component: The component object to use in this step. Must be one
                of the allowed component types.
            description: Optional description of the step. Defaults to empty string.

        Returns:
            True if insertion was successful, False if index is out of range.

        Raises:
            TypeError: If component is not one of the allowed types.
        """
        # Adjust negative index to positive index
        if index < 0:
            index += len(self.steps) + 1

        if 0 <= index <= len(self.steps):

            if not isinstance(component, Action):
                # If the component is not an Action, store a weak reference
                component_ref = weakref.ref(component)
            elif isinstance(component, Action):
                # If the component is an Action, store a strong reference
                # This is because Actions are not expected to be weakly referenced
                # and should be kept alive for the duration of the process
                component_ref = component
            else:
                raise TypeError("Invalid component type. Must be one of the allowed types.")


            step = {
                "component": component_ref,
                "description": description
            }

            self.steps.insert(index, step)

            # Adjust current step if needed
            if index <= self.current_step:
                self.current_step += 1

            return True
        return False


    def remove_step(self, index: int) -> bool:
        """Removes a step at a specific position.

        The current step index is automatically adjusted if the removed step
        is at or before the current position.

        Args:
            index: Position of the step to remove (0-based indexing).

        Returns:
            True if removal was successful, False if index is out of range.
        """
        if 0 <= index < len(self.steps):
            del self.steps[index]

            # Adjust current step if needed
            if index <= self.current_step:
                self.current_step -= 1

            return True
        return False

    def clear_steps(self) -> None:
        """Clears all steps from the process.

        This method removes all steps and resets the current step index to -1.
        """
        self.steps.clear()
        self.current_step = -1

    def get_steps(self) -> List[Dict]:
        """Gets all steps in the process.

        Returns:
            List of step dictionaries, each containing 'component' and
                'description' keys.
        """
        return self.steps

    def get_step(self, index: int) -> Optional[Dict]:
        """Gets a step at a specific position.

        Args:
            index: Position of the step to retrieve (0-based indexing).

        Returns:
            The step dictionary if index is valid, None otherwise. Each step
                dictionary contains 'component' and 'description' keys.
        """
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    def to_tcl(self):
        """Converts the process to a TCL script for OpenSees.

        This method iterates through all steps and generates a complete TCL
        script by calling the to_tcl() method on each component. Weak references
        are automatically resolved.

        Returns:
            String containing the complete TCL script with comments separating
                each step.
        """
        tcl_script = ""
        for step in self.steps:
            component = step["component"]
            if isinstance(component, weakref.ref):
                # If it's a weak reference, resolve it
                component = component()
            description = step["description"]
            tcl_script += f"# {description} ======================================\n\n"
            tcl_script += f"{component.to_tcl()}\n\n\n"
        return tcl_script
