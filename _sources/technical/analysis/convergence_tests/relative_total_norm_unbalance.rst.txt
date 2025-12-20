Relative Total Norm Unbalance Convergence Test
==============================================

The Relative Total Norm Unbalance test checks convergence based on the ratio of the norm of the unbalanced force vector to the norm of the total applied force vector.

Description
-----------

This test is particularly suitable for:

* Force-controlled problems with cumulative loading
* Cases where total force history is important
* Nonlinear static analysis
* Problems with significant material nonlinearity

The test calculates the ratio of the unbalanced force norm to the total applied force norm and compares it to a specified tolerance.

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
     
    
    # Create a Relative Total Norm Unbalance convergence test
    fm.analysis.test.create_test("RelativeTotalNormUnbalance", tol=1.0e-6, maxIter=10, printFlag=0, normType=2) 