Krylov Newton Algorithm
=======================

The Krylov Newton algorithm is a memory-efficient variation of the Newton-Raphson method that uses a Krylov subspace to approximate the solution. It is particularly useful for large-scale problems where memory usage is a concern.

Description
-----------

The Krylov Newton algorithm:
- Uses a Krylov subspace to approximate the solution
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
     - Tangent matrix to use for iterations ("current" or "initial") (default: "current")
   * - ``tang_incr``
     - str
     - Tangent matrix to use for increments ("current" or "initial") (default: "current")
   * - ``max_dim``
     - int
     - Maximum dimension of the Krylov subspace (default: 3)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Krylov Newton algorithm with default settings
   fm.analysis.algorithm.create_algorithm("KrylovNewton")

   # Create a Krylov Newton algorithm with custom settings
   fm.analysis.algorithm.create_algorithm(
       "KrylovNewton",
       tang_iter="initial",
       tang_incr="current",
       max_dim=5
   )

Notes
-----

- The Krylov Newton algorithm is memory-efficient compared to standard Newton
- It is particularly useful for large-scale problems
- The convergence rate may be slower than standard Newton
- The ``max_dim`` parameter controls the trade-off between memory usage and convergence rate 