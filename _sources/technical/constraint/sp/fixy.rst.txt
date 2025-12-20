FixY Constraint
===============

The ``fixY`` constraint is a coordinate-based constraint that applies constraints to all nodes located at a specific Y-coordinate.

Description
-----------

The fixY constraint targets nodes based on their Y-coordinate position. This is particularly useful for applying boundary conditions to an entire face or plane of nodes in the Y direction without needing to specify each node individually.

Parameters
----------

* **yCoordinate** (float): The y-coordinate of nodes to be constrained
* **dofs** (List[int]): List of DOF constraint values (0 or 1)
  * 0 = unconstrained (free)
  * 1 = constrained (fixed)
* **tol** (float, optional): Tolerance for coordinate comparison (default: 1e-10)
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Fix all nodes at Y=0 (e.g., front face of a model)
   # Fix translations (DOFs 1,2,3) but allow rotations (DOFs 4,5,6)
   fm.constraint.sp.fixY(yCoordinate=0.0, dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix only Y direction movement for nodes at Y=5.0 (e.g., middle plane)
   fm.constraint.sp.fixY(yCoordinate=5.0, dofs=[0, 1, 0, 0, 0, 0], tol=1e-6)

