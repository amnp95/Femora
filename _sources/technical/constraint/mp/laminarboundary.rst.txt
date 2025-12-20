Laminar Boundary Constraint
===========================

The ``laminar_boundary`` function creates a set of specialized equalDOF constraints that are particularly useful for modeling soil-structure interaction and boundary conditions in geotechnical models.

Description
-----------

The laminar boundary constraint automates the process of creating equal DOF constraints between nodes that have the same coordinate in a specified direction. This creates "layers" of nodes that are constrained to move together in specified degrees of freedom, while being free to move independently in other directions.

This constraint is particularly useful for:
- Creating periodic boundary conditions at the edges of a soil model
- Enforcing laminar deformation in soil-structure interaction problems
- Creating soil box boundary conditions for dynamic analysis

Parameters
----------

* **dofs** (List[int]): List of degrees of freedom to be constrained within each layer
* **direction** (int, optional): Direction perpendicular to the layers (1 for X, 2 for Y, 3 for Z, default=3)
* **tol** (float, optional): Tolerance for finding nodes within the same layer (default=1e-2)
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Create a laminar boundary constraint where nodes at the same Z-coordinate
   # are constrained to have the same X and Y translations
   fm.constraint.mp.create_laminar_boundary(
       dofs=[1, 2],      # Constrain x and y translations
       direction=3,      # Layers perpendicular to Z-axis
       tol=1e-2          # Tolerance for identifying nodes in the same layer
   )
   
   # Create a laminar boundary in X-direction (layers perpendicular to X-axis)
   # Constraining only Y translations
   fm.constraint.mp.create_laminar_boundary(
       dofs=[2],         # Constrain only y translations
       direction=1,      # Layers perpendicular to X-axis
       tol=1e-3          # Smaller tolerance for more precise layer identification
   )

How It Works
------------

The laminar boundary constraint works through the following process:

1. Extracts the surface mesh from the assembled model
2. Identifies points within the model boundaries (accounting for tolerance)
3. Groups nodes that have the same coordinate in the specified direction within the tolerance
4. Creates equalDOF constraints for each group, making the first node in each group the master

Internally, this creates many equalDOF constraints, one for each slave node in each identified layer.

Common Applications
-------------------

Laminar boundary constraints are commonly used in the following scenarios:

1. **Soil-structure interaction**: Creating boundary conditions that allow shear deformation
2. **Periodic boundary conditions**: For wave propagation or soil dynamics problems
3. **Soil box models**: Creating artificial boundaries for dynamic analysis
4. **Free-field boundary conditions**: For earthquake engineering analysis

Implementation Note
-------------------

Unlike the other MP constraint types that are implemented as distinct classes, the laminar boundary constraint is implemented as a function that creates multiple equalDOF constraints internally. The constraints are generated dynamically based on the mesh geometry.

Example: Soil Box Model
-----------------------

A common application is creating a soil box model for dynamic analysis:

.. code-block:: python

   # Create a soil box model
   # First create and assemble the mesh...
   
   # Apply laminar boundary conditions on all four sides
   
   # X-face constraints (nodes with same X coordinate move together in Y)
   fm.constraint.mp.create_laminar_boundary(dofs=[2], direction=1)
   
   # Y-face constraints (nodes with same Y coordinate move together in X)
   fm.constraint.mp.create_laminar_boundary(dofs=[1], direction=2)
   
   # Fix the base in X, Y, and Z directions using SP constraints
   fm.constraint.sp.fixZ(zCoordinate=0.0, dofs=[1, 1, 1, 0, 0, 0])

Function Reference
------------------

.. autofunction:: femora.components.Constraint.mpConstraint.mpConstraintManager.create_laminar_boundary
   :noindex: