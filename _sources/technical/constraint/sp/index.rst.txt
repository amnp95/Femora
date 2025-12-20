SP Constraints
===============

Single-point constraints fix or control degrees of freedom at specific nodes.

Understanding the SP Constraint Manager
---------------------------------------

The ``SPConstraintManager`` is a core component of Femora that provides a centralized system for creating, managing, and applying single-point constraints to your model. It implements the Singleton pattern to ensure a single, consistent point of constraint management across the entire application.

SP constraints should typically be created after assembling the whole mesh, as they are applied directly to nodes in the assembled mesh.

Accessing the SP Constraint Manager
-----------------------------------

There are two ways to access the SP Constraint Manager:

1. **Direct Access**: Import and use the SPConstraintManager class directly

   .. code-block:: python
      
      from femora.components.Constraint.spConstraint import SPConstraintManager
      
      # Get the singleton instance
      sp_manager = SPConstraintManager()
      
      # Use SP manager directly
      sp_manager.fix(node_tag=1, dofs=[1, 1, 1, 0, 0, 0])

2. **Through Femora** (Recommended): Access via the Femora class and the Constraint module

   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the SPConstraintManager through the constraint property
      sp_manager = fm.constraint.sp
      
      # Add constraints using the manager
      sp_manager.fix(node_tag=1, dofs=[1, 1, 1, 0, 0, 0])

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How SP Constraint Manager Works
-------------------------------

The SP Constraint Manager provides several key capabilities:

1. **Constraint Creation**: Creates single-point constraint objects with appropriate parameters
2. **Constraint Registry**: Maintains an internal registry of all constraints
3. **Constraint Management**: Allows retrieving and removing constraints by tag
4. **TCL Generation**: Transforms constraint definitions into OpenSees TCL commands

Creating SP Constraints
-----------------------

To create SP constraints, you must first assemble your mesh, as constraints are applied to nodes in the assembled model:

.. code-block:: python

   # First, assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   

   # Now add constraints to nodes
   # Fix translations (DOFs 1-3) but allow rotations (DOFs 4-6) at node 10
   fm.constraint.sp.fix(node_tag=10, dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix all DOFs at a specific X coordinate
   fm.constraint.sp.fixX(xCoordinate=0.0, dofs=[1, 1, 1, 1, 1, 1])

DOF Specification Format
------------------------

All constraint methods take a ``dofs`` parameter that specifies which degrees of freedom to constrain. The format is a list of 0s and 1s:

- **0**: Unconstrained (free) degree of freedom
- **1**: Constrained (fixed) degree of freedom

For example:

.. code-block:: python

   # Fix X, Y, Z translations (1,2,3) but free rotations (4,5,6)
   dofs = [1, 1, 1, 0, 0, 0]
   
   # Fix only X direction
   dofs = [1, 0, 0, 0, 0, 0]
   
   # Fix all degrees of freedom
   dofs = [1, 1, 1, 1, 1, 1]

Best Practices for SP Constraints
---------------------------------

1. **Create SP constraints after mesh assembly** to ensure nodes are properly merged
2. **Use coordinate-based constraints** (fixX, fixY, fixZ) for applying boundary conditions to planar surfaces
3. **Use macro-based constraints** when generating TCL scripts that use model dimension variables
4. **Be careful with overconstrained systems** as they may lead to numerical issues
5. **Verify boundary conditions** visually by inspecting constrained nodes

SP Constraint Manager API Reference
-----------------------------------

Below is the complete API reference for the SPConstraintManager class:

.. autoclass:: femora.components.Constraint.spConstraint.SPConstraintManager
   :members:
   :undoc-members:
   :show-inheritance:

SP Constraint Types
-------------------

.. toctree::
   :maxdepth: 1

   fix
   fixmacro
   fixx
   fixy
   fixz
