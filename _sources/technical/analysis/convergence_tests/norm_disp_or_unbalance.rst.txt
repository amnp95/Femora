Norm Disp Or Unbalance Convergence Test
=======================================

The Norm Disp Or Unbalance test checks convergence based on either the norm of the displacement increment vector or the norm of the unbalanced force vector. Only one criterion needs to be satisfied for convergence.

Description
-----------

This test is particularly suitable for:

* Problems where either force or displacement convergence is sufficient
* Cases where flexibility in convergence criteria is beneficial
* Nonlinear analysis where one criterion may be more difficult to satisfy
* Problems where different physical phenomena control different aspects

The test calculates both the norm of the displacement increment vector and the norm of the unbalanced force vector, and requires only one to be within its specified tolerance.

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``tolIncr``
     - float
     - Tolerance for displacement increment norm (default: 1.0e-6)
   * - ``tolR``
     - float
     - Tolerance for unbalanced force norm (default: 1.0e-6)
   * - ``maxIter``
     - int
     - Maximum number of iterations (default: 10)
   * - ``printFlag``
     - int
     - Print flag for convergence information (default: 0)
   * - ``normType``
     - int
     - Norm type to use: 0 for max-norm, 1 for 1-norm, 2 for 2-norm (default: 2)
   * - ``maxIncr``
     - int
     - Maximum times error can increase (-1 for default behavior)

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Norm Disp Or Unbalance convergence test
    fm.analysis.test.create_test("NormDispOrUnbalance", tolIncr=1.0e-6, tolR=1.0e-6, maxIter=10, printFlag=0, normType=2, maxIncr=-1) 