Norm Unbalance Convergence Test
===============================

The Norm Unbalance test checks convergence based on the norm of the unbalanced force vector.

Description
-----------

This test is particularly suitable for:

* Force-controlled problems
* Cases where force equilibrium is critical
* Nonlinear static analysis
* Problems with significant material nonlinearity

The test calculates the norm of the unbalanced force vector and compares it to a specified tolerance.

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``tol``
     - float
     - Tolerance for convergence (default: 1.0e-6)
   * - ``maxIter``
     - int
     - Maximum number of iterations (default: 10)
   * - ``printFlag``
     - int
     - Print flag for convergence information (default: 0)
   * - ``normType``
     - int
     - Norm type to use: 0 for max-norm, 1 for 1-norm, 2 for 2-norm (default: 2)

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Norm Unbalance convergence test
    fm.analysis.test.create_test("NormUnbalance", tol=1.0e-6, maxIter=10, printFlag=0, normType=2) 