RigidLink Constraint
====================

The ``rigidLink`` constraint creates a rigid connection between nodes, where slave nodes are constrained to move with the master node according to rigid body kinematics.

Description
-----------

The rigidLink constraint establishes a rigid connection between a master node and one or more slave nodes. This constraint ensures that the constrained nodes move as if they were connected by an infinitely stiff link. Femora supports two types of rigid links:

1. **bar**: Constrains only the translational degrees of freedom
2. **beam**: Constrains both translational and rotational degrees of freedom

Parameters
----------

* **type_str** (str): Type of rigid link ('bar' or 'beam')
* **master_node** (int): Tag of the master/retained node
* **slave_nodes** (List[int]): List of tags for slave/constrained nodes
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Create a rigid bar link (constrains translations only)
   fm.constraint.mp.create_rigid_link(
       type_str='bar',
       master_node=1,
       slave_nodes=[10, 11, 12]
   )
   
   # Create a rigid beam link (constrains translations and rotations)
   fm.constraint.mp.create_rigid_link(
       type_str='beam',
       master_node=5,
       slave_nodes=[20]
   )



Common Applications
-------------------

RigidLink constraints are commonly used in the following scenarios:

1. **Modeling rigid connections**: Such as stiff connections between structural elements
2. **Implementing rigid diaphragms**: For floor slabs in building models
3. **Modeling offset connections**: Where elements are not directly connected
4. **Simplifying complex connection details**: By replacing them with rigid links
5. **Modeling rigid foundations**: To ensure foundation nodes move together

Comparison of bar and beam types
--------------------------------

1. **rigidLink bar**:
   * Constrains only translational DOFs (1, 2, 3)
   * Allows independent rotation of connected nodes
   * Suitable for pin connections

2. **rigidLink beam**:
   * Constrains both translational (1, 2, 3) and rotational DOFs (4, 5, 6)
   * Connected nodes maintain the same relative orientation
   * Suitable for fully rigid connections

