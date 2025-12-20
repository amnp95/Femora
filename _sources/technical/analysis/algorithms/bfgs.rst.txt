BFGS Algorithm
==============

The BFGS (Broyden-Fletcher-Goldfarb-Shanno) algorithm is a quasi-Newton method that builds an approximation to the inverse Hessian matrix. It is particularly useful for problems where the tangent stiffness matrix is difficult to compute.

Description
-----------

The BFGS algorithm:
- Builds an approximation to the inverse Hessian matrix
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Uses a specified number of vectors to store the Hessian approximation

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``count``
     - int
     - Number of vectors to store the Hessian approximation

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a BFGS algorithm with default settings
   fm.analysis.algorithm.create_algorithm("BFGS", count=3)

   # Create a BFGS algorithm with more vectors
   fm.analysis.algorithm.create_algorithm("BFGS", count=5)

Notes
-----

- The BFGS algorithm is a quasi-Newton method
- It does not require the computation of the tangent stiffness matrix
- It can be more efficient for problems where the tangent stiffness matrix is difficult to compute
- The ``count`` parameter controls the memory usage and accuracy of the Hessian approximation
- A larger ``count`` value generally leads to better convergence but uses more memory 