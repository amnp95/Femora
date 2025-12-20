Modified Newton Algorithm
=========================

The Modified Newton algorithm is a variation of the Newton-Raphson method that uses the same tangent stiffness matrix for multiple iterations. This can be more efficient for problems where the tangent stiffness matrix is expensive to compute.

Description
-----------

The Modified Newton algorithm:
- Uses the same tangent stiffness matrix for multiple iterations
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Can optionally use initial stiffness or factor the matrix only once

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``initial``
     - bool
     - If True, uses the initial stiffness matrix for all iterations (default: False)
   * - ``factor_once``
     - bool
     - If True, factors the matrix only once and reuses it (default: False)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Modified Newton algorithm with default settings
   fm.analysis.algorithm.create_algorithm("ModifiedNewton")

   # Create a Modified Newton algorithm using initial stiffness
   fm.analysis.algorithm.create_algorithm("ModifiedNewton", initial=True)

   # Create a Modified Newton algorithm that factors the matrix only once
   fm.analysis.algorithm.create_algorithm("ModifiedNewton", factor_once=True)

Notes
-----

- The Modified Newton algorithm is generally less efficient than the standard Newton algorithm
- It can be more efficient for problems where the tangent stiffness matrix is expensive to compute
- It may require more iterations to converge than the standard Newton algorithm
- The ``initial`` and ``factor_once`` options can be used together 