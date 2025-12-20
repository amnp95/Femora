EqualDOF Constraint
===================

The ``equalDOF`` constraint is a type of multi-point constraint that forces specified degrees of freedom at slave nodes to follow the same motion as the master node.

Description
-----------

The equalDOF constraint establishes a master-slave relationship between nodes. When applied, the specified degrees of freedom of the slave nodes will be constrained to follow the corresponding degrees of freedom of the master node. This is useful for ensuring that certain parts of your model move together.

Parameters
----------

* **master_node** (int): Tag of the master/retained node
* **slave_nodes** (List[int]): List of tags for slave/constrained nodes
* **dofs** (List[int]): List of degrees of freedom to be constrained (e.g., [1, 2, 3] for translations)
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Make nodes 10, 11, and 12 follow node 1 in translational DOFs
   fm.constraint.mp.create_equal_dof(
       master_node=1,
       slave_nodes=[10, 11, 12],
       dofs=[1, 2, 3]
   )
   
   # Make node 20 follow node 5 in all DOFs (translations and rotations)
   fm.constraint.mp.create_equal_dof(
       master_node=5,
       slave_nodes=[20],
       dofs=[1, 2, 3, 4, 5, 6]
   )
   
   # Make nodes follow only in X direction (DOF 1)
   fm.constraint.mp.create_equal_dof(
       master_node=1,
       slave_nodes=[30, 31, 32],
       dofs=[1]
   )


Common Applications
-------------------

EqualDOF constraints are commonly used in the following scenarios:

1. **Connecting structural elements**: Ensuring compatible deformations at connection points
2. **Creating rigid body regions**: When multiple nodes need to move together
3. **Implementing symmetry conditions**: Constraining nodes along symmetry planes
4. **Master-slave coupling**: For soil-structure interaction modeling
5. **Coupling different model components**: Such as connecting beam and shell elements

