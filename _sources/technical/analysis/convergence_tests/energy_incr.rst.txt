Energy Incr Convergence Test
============================

The Energy Incr test checks convergence based on the energy increment in the system.

Description
-----------

This test is particularly suitable for:

* Nonlinear problems with significant energy changes
* Problems with material and geometric nonlinearity
* Cases where both force and displacement convergence are important
* Dynamic analysis

The test calculates the energy increment and compares it to a specified tolerance.

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

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create an Energy Incr convergence test
    fm.analysis.test.create_test("EnergyIncr", tol=1.0e-6, maxIter=10, printFlag=0) 