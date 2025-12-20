Macro-Based Constraints
=======================

Macro-based constraints are specialized constraints that reference OpenSees TCL macros that define model dimensions. These constraints are especially useful when you want to apply constraints at the boundaries of a model without knowing the exact coordinate values.

Description
-----------

Instead of using fixed coordinate values, macro-based constraints reference predefined macro variables in the OpenSees TCL file that represent model dimensions:

* **X_MIN, X_MAX**: Minimum and maximum X coordinates of the model
* **Y_MIN, Y_MAX**: Minimum and maximum Y coordinates of the model
* **Z_MIN, Z_MAX**: Minimum and maximum Z coordinates of the model

These macros are typically defined in the TCL file based on model dimensions.

Available Macro Constraints
---------------------------

Femora provides six types of macro-based constraints:

1. **fixMacroXmin**: Apply constraints at the minimum X coordinate
2. **fixMacroXmax**: Apply constraints at the maximum X coordinate
3. **fixMacroYmin**: Apply constraints at the minimum Y coordinate
4. **fixMacroYmax**: Apply constraints at the maximum Y coordinate
5. **fixMacroZmin**: Apply constraints at the minimum Z coordinate
6. **fixMacroZmax**: Apply constraints at the maximum Z coordinate

Parameters
----------

All macro constraint methods take the same parameters:

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
   
   # Fix the base of the model (Z_MIN)
   # Fix all translations (DOFs 1,2,3) but allow rotations (DOFs 4,5,6)
   fm.constraint.sp.fixMacroZmin(dofs=[1, 1, 1, 0, 0, 0])
   
   # Fix the X direction at the maximum X boundary (X_MAX)
   fm.constraint.sp.fixMacroXmax(dofs=[1, 0, 0, 0, 0, 0])
   
   # Fix the Y direction at both Y boundaries (Y_MIN and Y_MAX)
   fm.constraint.sp.fixMacroYmin(dofs=[0, 1, 0, 0, 0, 0])
   fm.constraint.sp.fixMacroYmax(dofs=[0, 1, 0, 0, 0, 0])

OpenSees TCL Output
-------------------

The macro constraints generate TCL code that uses OpenSees macro variables:

.. code-block:: tcl

   # Z-minimum constraint (base of model)
   fixZ $Z_MIN 1 1 1 0 0 0 -tol 1e-10;
   
   # X-maximum constraint (right face of model)
   fixX $X_MAX 1 0 0 0 0 0 -tol 1e-10;
   
   # Y-minimum and Y-maximum constraints (front and back faces)
   fixY $Y_MIN 0 1 0 0 0 0 -tol 1e-10;
   fixY $Y_MAX 0 1 0 0 0 0 -tol 1e-10;

