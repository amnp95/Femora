MP Constraints
==============

Multi-point constraints create relationships between multiple nodes in your mesh, allowing you to create master-slave relationships, rigid links, rigid diaphragms, and laminar boundary conditions.

Understanding the MP Constraint Manager
---------------------------------------

The ``MPConstraintManager`` is a core component of Femora that provides a centralized system for creating, managing, and applying multi-point constraints to your model. It implements the Singleton pattern to ensure a single, consistent point of constraint management across the entire application.

MP constraints define relationships between multiple nodes in your mesh, allowing you to:

1. Create master-slave relationships between nodes
2. Create rigid links between nodes
3. Create rigid diaphragms across sets of nodes
4. Create laminar boundary conditions on mesh surfaces

MP constraints are typically applied after assembling the mesh, as they operate on nodes in the assembled mesh.

Accessing the MP Constraint Manager
-----------------------------------

There are two ways to access the MP Constraint Manager:

1. **Direct Access**: Import and use the MPConstraintManager class directly

   .. code-block:: python
      
      from femora.components.Constraint.mpConstraint import mpConstraintManager
      
      # Get the singleton instance
      mp_manager = mpConstraintManager()
      
      # Use MP manager directly
      mp_manager.create_equal_dof(...)

2. **Through Femora** (Recommended): Access via the Femora class and the Constraint module

   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the MPConstraintManager through the constraint property
      mp_manager = fm.constraint.mp
      
      # Add constraints using the manager
      mp_manager.create_equal_dof(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.


Managing MP Constraints
-----------------------

The MP Constraint Manager provides methods to manage constraints:

.. code-block:: python

   # Get a specific constraint by tag
   constraint = mp_manager.get_constraint(tag=1)
   
   # Remove a constraint by tag
   mp_manager.remove_constraint(tag=1)
   
   # Iterate through all constraints
   for constraint in mp_manager:
       print(constraint)


Best Practices for MP Constraints
---------------------------------

1. **Create MP constraints after mesh assembly** to ensure all nodes are properly defined
2. **Choose master nodes carefully** as they control the motion of all slave nodes
3. **Avoid cyclic constraints** where nodes are both masters and slaves in different constraints
4. **Be careful with over-constrained systems** as they may lead to numerical issues
5. **Consider using laminar_boundary for soil-structure interfaces** to create appropriate boundary conditions

MP Constraint Manager API Reference
-----------------------------------

Below is the complete API reference for the MPConstraintManager class:

.. autoclass:: femora.components.Constraint.mpConstraint.mpConstraintManager
   :members:
   :undoc-members:
   :show-inheritance:

Available MP Constraint Types
-----------------------------

Femora provides several types of MP constraints:

.. toctree::
   :maxdepth: 1

   equaldof
   rigidlink
   rigiddiaphragm
   laminarboundary