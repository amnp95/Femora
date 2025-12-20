Relative Total Norm Disp Incr Convergence Test
==============================================

The Relative Total Norm Disp Incr test checks convergence based on the ratio of the norm of the displacement increment vector to the norm of the total displacement vector.

Description
-----------

This test is particularly suitable for:

* Problems with cumulative displacement changes
* Cases where total displacement history is important
* Nonlinear static analysis
* Problems with significant geometric changes

The test calculates the ratio of the displacement increment norm to the total displacement norm and compares it to a specified tolerance.

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
     
    
    # Create a Relative Total Norm Disp Incr convergence test
    fm.analysis.test.create_test("RelativeTotalNormDispIncr", tol=1.0e-6, maxIter=10, printFlag=0, normType=2) 