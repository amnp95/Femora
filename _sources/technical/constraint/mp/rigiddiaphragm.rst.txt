RigidDiaphragm Constraint
=========================

The ``rigidDiaphragm`` constraint creates a rigid planar constraint that forces a group of slave nodes to maintain their relative positions in a plane perpendicular to the specified direction.

Description
-----------

The rigidDiaphragm constraint is commonly used to model floor diaphragms in structural models. It constrains all slave nodes to move as a rigid body in the plane perpendicular to the specified direction, while allowing them to move independently along the specified direction.

This constraint is particularly useful for structural models where floor slabs can be approximated as infinitely rigid in their own plane but flexible out-of-plane.

Parameters
----------

* **direction** (int): Direction perpendicular to the rigid plane (1 for YZ plane, 2 for XZ plane, 3 for XY plane)
* **master_node** (int): Tag of the master/retained node
* **slave_nodes** (List[int]): List of tags for slave/constrained nodes
  
Usage
-----

.. code-block:: python

   import femora as fm
   
   # Create Femora instance
    
   
   # First assemble the mesh
   fm.assembler.Assemble(merge_points=True)
   
   # Create a rigid diaphragm in the XY plane (perpendicular to Z-axis)
   # This is commonly used for floor diaphragms in building models
   fm.constraint.mp.create_rigid_diaphragm(
       direction=3,  # 3 for Z-direction (perpendicular to XY plane)
       master_node=100,
       slave_nodes=[101, 102, 103, 104, 105, 106]
   )
   
   # Create a rigid diaphragm in the XZ plane (perpendicular to Y-axis)
   fm.constraint.mp.create_rigid_diaphragm(
       direction=2,  # 2 for Y-direction (perpendicular to XZ plane)
       master_node=200,
       slave_nodes=[201, 202, 203, 204]
   )


Meaning of Direction Parameter
------------------------------

The direction parameter specifies which coordinate direction is perpendicular to the rigid plane:

1. **direction=1**: Creates a rigid constraint in the YZ plane (perpendicular to X-axis)
   * Constrains Y and Z translations, and rotations about X
   * Allows movement in X direction

2. **direction=2**: Creates a rigid constraint in the XZ plane (perpendicular to Y-axis)
   * Constrains X and Z translations, and rotations about Y
   * Allows movement in Y direction

3. **direction=3**: Creates a rigid constraint in the XY plane (perpendicular to Z-axis)
   * Constrains X and Y translations, and rotations about Z
   * Allows movement in Z direction

Common Applications
-------------------

RigidDiaphragm constraints are commonly used in the following scenarios:

1. **Modeling floor diaphragms**: In building models to represent in-plane rigidity of floor slabs
2. **Modeling deck structures**: In bridge models
3. **Creating constraint planes**: For symmetry or other boundary conditions
4. **Idealized rigid surfaces**: When surface flexibility can be neglected

