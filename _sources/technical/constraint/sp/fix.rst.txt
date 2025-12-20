Fix Constraint
==============

The ``fix`` constraint is the most basic type of single-point constraint in Femora. It applies constraints to specific degrees of freedom at individual nodes.

Description
-----------

The fix constraint works by directly specifying which degrees of freedom should be constrained at a particular node. Each degree of freedom can be set as either free (0) or fixed (1).

Parameters
----------

* **node_tag** (int): The tag (ID) of the node to be constrained
* **dofs** (List[int]): List of DOF constraint values (0 or 1)
  * 0 = unconstrained (free)
  * 1 = constrained (fixed)
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Apply fix constraint to node 10
   # Fix translations (DOFs 1,2,3) but allow rotations (DOFs 4,5,6)
   fm.constraint.sp.fix(node_tag=10, dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix all degrees of freedom at node 20
   fm.constraint.sp.fix(node_tag=20, dofs=[1, 1, 1, 1, 1, 1])
   
   # Fix only X direction at node 30
   fm.constraint.sp.fix(node_tag=30, dofs=[1, 0, 0, 0, 0, 0])

