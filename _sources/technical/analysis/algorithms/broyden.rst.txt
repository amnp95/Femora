Broyden Algorithm
=================

The Broyden algorithm is a quasi-Newton method that builds an approximation to the inverse Jacobian matrix. It is a simpler alternative to the BFGS algorithm, using less memory but potentially with slower convergence.

Description
-----------

The Broyden algorithm:
- Builds an approximation to the inverse Jacobian matrix
- Updates the geometry and internal forces based on the displacement increment
- Repeats until convergence is achieved
- Uses a specified number of vectors to store the Jacobian approximation

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
     - Number of vectors to store the Jacobian approximation

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Broyden algorithm with default settings
   fm.analysis.algorithm.create_algorithm("Broyden", count=3)

   # Create a Broyden algorithm with more vectors
   fm.analysis.algorithm.create_algorithm("Broyden", count=5)

Notes
-----

- The Broyden algorithm is a quasi-Newton method
- It does not require the computation of the tangent stiffness matrix
- It uses less memory than the BFGS algorithm but may converge more slowly
- The ``count`` parameter controls the memory usage and accuracy of the Jacobian approximation
- A larger ``count`` value generally leads to better convergence but uses more memory 