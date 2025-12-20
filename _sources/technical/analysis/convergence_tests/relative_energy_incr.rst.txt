Relative Energy Incr Convergence Test
=====================================

The Relative Energy Incr test checks convergence based on the ratio of the energy increment to the total energy in the system.

Description
-----------

This test is particularly suitable for:

* Nonlinear problems with varying energy levels
* Cases where relative energy changes are important
* Problems with both material and geometric nonlinearity
* Dynamic analysis with energy conservation

The test calculates the ratio of the energy increment to the total energy and compares it to a specified tolerance.

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
     
    
    # Create a Relative Energy Incr convergence test
    fm.analysis.test.create_test("RelativeEnergyIncr", tol=1.0e-6, maxIter=10, printFlag=0) 