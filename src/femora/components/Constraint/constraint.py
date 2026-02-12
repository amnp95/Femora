from femora.components.Constraint.mpConstraint import mpConstraintManager
from femora.components.Constraint.spConstraint import SPConstraintManager

class Constraint:
    """Singleton class for managing structural constraints in MeshMaker.

    This class provides a unified interface for applying boundary conditions and constraints
    to MeshMaker models. It manages two types of constraints:

    1. MP (Multi-Point) Constraints: Create relationships between multiple nodes.
    2. SP (Single-Point) Constraints: Fix or control degrees of freedom at specific nodes.

    SP constraints should typically be created after assembling the whole mesh, as they are applied
    directly to nodes in the assembled mesh.

    Attributes:
        _instance: Class-level attribute holding the singleton instance.
        initialized: Indicates whether the instance has been initialized.
        mp: Instance of mpConstraintManager for managing multi-point constraints.
        sp: Instance of SPConstraintManager for managing single-point constraints.

    Example:
        ```python
        from femora.components.Constraint.constraint import Constraint

        # Direct access to the Constraint manager
        # constraint_instance = Constraint()

        # Access through MeshMaker (recommended approach)
        from femora.components.MeshMaker import MeshMaker
        mk = MeshMaker()
        constraint_manager = mk.constraint

        # Using the SP constraint manager
        sp_manager = constraint_manager.sp

        # Add a fixed constraint to node 10, DOF 1 (X-direction)
        sp_manager.add_constraint(node_id=10, dof=1, value=0.0, constraint_type="fix")

        # Available SP constraint types include:
        # - "fix": Fix a degree of freedom to a specified value
        # - "disp": Apply a prescribed displacement
        # - "vel": Apply a prescribed velocity
        # - "accel": Apply a prescribed acceleration
        ```
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Creates a new instance or returns the existing singleton instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The singleton instance of the Constraint class.
        """
        if not cls._instance:
            cls._instance = super(Constraint, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initializes the singleton instance and sets up the constraint managers.

        This method only initializes on first creation. Subsequent calls have no effect.
        """
        if not hasattr(self, 'initialized'):
            self.initialized = True
            # Initialize your singleton class here
            self.mp = mpConstraintManager()
            self.sp = SPConstraintManager()