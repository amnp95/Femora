Secant Newton Algorithm
=======================

The Secant Newton algorithm is a quasi-Newton method that uses the two-term update formula to approximate the inverse of the Jacobian matrix. It provides an alternative to the standard Newton method with potentially better performance for certain problem types.

Description
-----------

The Secant Newton algorithm:
- Builds an approximation to the Jacobian matrix using the secant update formula
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Can control the tangent matrix used for iterations and increments

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``tang_iter``
     - str
     - Tangent matrix to use for iterations: "current", "initial", or "noTangent" (default: "current")
   * - ``tang_incr``
     - str
     - Tangent matrix to use for increments: "current", "initial", or "noTangent" (default: "current")
   * - ``max_dim``
     - int
     - Maximum dimension for the Secant approximation (default: 3)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Secant Newton algorithm with default settings
   fm.analysis.algorithm.create_algorithm("SecantNewton")

   # Create a Secant Newton algorithm with custom settings
   fm.analysis.algorithm.create_algorithm(
       "SecantNewton",
       tang_iter="initial",
       tang_incr="current",
       max_dim=5
   )

Notes
-----

- The Secant Newton algorithm can be more efficient than standard Newton for problems where the tangent is expensive to compute
- It builds an approximation to the Jacobian matrix using secant updates
- The convergence rate may be slower than standard Newton but each iteration may be less expensive
- The ``max_dim`` parameter controls the trade-off between accuracy and computational cost
- A larger ``max_dim`` value generally leads to better convergence but uses more memory 