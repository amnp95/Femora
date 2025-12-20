FixX Constraint
===============

The ``fixX`` constraint is a coordinate-based constraint that applies constraints to all nodes located at a specific X-coordinate.

Description
-----------

Unlike the basic fix constraint which targets specific nodes by tag, the fixX constraint targets nodes based on their X-coordinate position. This is particularly useful for applying boundary conditions to an entire face or plane of nodes without needing to specify each node individually.

Parameters
----------

* **xCoordinate** (float): The x-coordinate of nodes to be constrained
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
   
   # Fix all nodes at X=0 (e.g., left face of a model)
   # Fix translations (DOFs 1,2,3) but allow rotations (DOFs 4,5,6)
   fm.constraint.sp.fixX(xCoordinate=0.0, dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix all nodes at X=10 (e.g., right face of model)
   # Use a larger tolerance for floating-point comparison
   fm.constraint.sp.fixX(xCoordinate=10.0, dofs=[1, 0, 0, 0, 0, 0], tol=1e-6)

