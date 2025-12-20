Fixed Num Iter Convergence Test
===============================

The Fixed Num Iter test performs a fixed number of iterations regardless of convergence status.

Description
-----------

This test is particularly suitable for:

* Problems where a specific number of iterations is required
* Cases where convergence criteria are not critical
* Testing and debugging purposes
* Problems with known iteration requirements

The test simply performs the specified number of iterations without checking convergence criteria.

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``numIter``
     - int
     - Fixed number of iterations to perform

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Fixed Num Iter convergence test
    fm.analysis.test.create_test("FixedNumIter", numIter=5) 