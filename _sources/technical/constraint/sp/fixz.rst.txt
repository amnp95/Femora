FixZ Constraint
===============

The ``fixZ`` constraint is a coordinate-based constraint that applies constraints to all nodes located at a specific Z-coordinate.

Description
-----------

The fixZ constraint targets nodes based on their Z-coordinate position. This is particularly useful for applying boundary conditions to an entire horizontal plane of nodes, such as the base or top of a model, without needing to specify each node individually.

Parameters
----------

* **zCoordinate** (float): The z-coordinate of nodes to be constrained
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
   
   # Fix all nodes at Z=0 (typically the base of a model)
   # Fix all translations but allow rotations
   fm.constraint.sp.fixZ(zCoordinate=0.0, dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix only vertical movement for nodes at Z=10.0 (top surface)
   fm.constraint.sp.fixZ(zCoordinate=10.0, dofs=[0, 0, 1, 0, 0, 0], tol=1e-6)

