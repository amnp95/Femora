Norm Disp Incr Convergence Test
===============================

The Norm Disp Incr test checks convergence based on the norm of the displacement increment vector.

Description
-----------

This test is particularly suitable for:

* Linear and nonlinear static analysis
* Problems where displacement convergence is critical
* Cases where force equilibrium is less important
* Problems with well-defined displacement patterns

The test calculates the norm of the displacement increment vector and compares it to a specified tolerance.

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
     
    
    # Create a Norm Disp Incr convergence test
    fm.analysis.test.create_test("NormDispIncr", tol=1.0e-6, maxIter=10, printFlag=0, normType=2) 