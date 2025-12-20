Newton Algorithm
================

The Newton algorithm implements the Newton-Raphson method to solve the nonlinear residual equation. It is one of the most commonly used algorithms in structural analysis due to its quadratic convergence rate when close to the solution.

Description
-----------

The Newton algorithm:
- Uses the current tangent stiffness matrix to solve for the displacement increment
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Can optionally use initial stiffness or switch between initial and current stiffness

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
   * - ``initial_then_current``
     - bool
     - If True, uses initial stiffness on first step and then current stiffness (default: False)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Newton algorithm with default settings
   fm.analysis.algorithm.create_algorithm("Newton")

   # Create a Newton algorithm using initial stiffness
   fm.analysis.algorithm.create_algorithm("Newton", initial=True)

   # Create a Newton algorithm that switches from initial to current stiffness
   fm.analysis.algorithm.create_algorithm("Newton", initial_then_current=True)

Notes
-----

- The Newton algorithm is generally the most efficient algorithm for well-behaved problems
- It requires the computation of the tangent stiffness matrix at each iteration
- It may fail to converge if the initial guess is too far from the solution
- The ``initial`` and ``initial_then_current`` options are mutually exclusive 