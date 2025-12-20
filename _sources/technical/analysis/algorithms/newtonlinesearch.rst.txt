Newton Line Search Algorithm
============================

The Newton Line Search algorithm enhances the Newton-Raphson method by introducing a line search to determine the optimal step size. This can improve convergence when the standard Newton method struggles.

Description
-----------

The Newton Line Search algorithm:
- Uses the Newton-Raphson method to determine the search direction
- Performs a line search to find the optimal step size
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Offers multiple line search strategies to adapt to different problem characteristics

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``type_search``
     - str
     - Line search algorithm type: "Bisection", "Secant", "RegulaFalsi", or "InitialInterpolated" (default: "InitialInterpolated")
   * - ``tol``
     - float
     - Tolerance for search (default: 0.8)
   * - ``max_iter``
     - int
     - Maximum number of iterations to try (default: 10)
   * - ``min_eta``
     - float
     - Minimum η value (default: 0.1)
   * - ``max_eta``
     - float
     - Maximum η value (default: 10.0)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Newton Line Search algorithm with default settings
   fm.analysis.algorithm.create_algorithm("NewtonLineSearch")

   # Create a Newton Line Search algorithm with custom settings
   fm.analysis.algorithm.create_algorithm(
       "NewtonLineSearch",
       type_search="Bisection",
       tol=0.5,
       max_iter=20,
       min_eta=0.05,
       max_eta=5.0
   )

Notes
-----

- The Newton Line Search algorithm can be more robust than standard Newton for difficult problems
- It may require more computational effort per iteration, but often requires fewer iterations
- Different search types may be more effective for different problem types
- The "InitialInterpolated" search type is generally a good starting choice
- The tolerance parameter controls the line search accuracy (smaller values are more accurate but may require more iterations) 