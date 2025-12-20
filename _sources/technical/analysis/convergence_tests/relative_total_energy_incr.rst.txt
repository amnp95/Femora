Relative Total Energy Incr Convergence Test
===========================================

The Relative Total Energy Incr test checks convergence based on the ratio of the energy increment to the total energy accumulated in the system.

Description
-----------

This test is particularly suitable for:

* Nonlinear problems with cumulative energy changes
* Cases where total energy history is important
* Problems with both material and geometric nonlinearity
* Dynamic analysis with energy conservation

The test calculates the ratio of the energy increment to the total accumulated energy and compares it to a specified tolerance.

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
     
    
    # Create a Relative Total Energy Incr convergence test
    fm.analysis.test.create_test("RelativeTotalEnergyIncr", tol=1.0e-6, maxIter=10, printFlag=0) 