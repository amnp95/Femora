NormDispAndUnbalance Convergence Test
=====================================

The NormDispAndUnbalance convergence test is a combined test that checks both displacement increment norms and unbalanced force norms.

Description
-----------

This convergence test is particularly suitable for:

* Problems requiring both displacement and force criteria to be satisfied
* Cases where neither displacement nor force alone is sufficient
* Ensuring both equilibrium and deformation criteria are met
* Nonlinear problems with complex convergence behavior

The NormDispAndUnbalance test combines the criteria from both NormDisp and NormUnbalance tests, requiring both to be satisfied for convergence.

Parameters
----------

The NormDispAndUnbalance convergence test requires the following parameters:

* ``tolerance1`` (float): Tolerance for displacement norm
* ``tolerance2`` (float): Tolerance for unbalanced force norm
* ``max_iterations`` (int): Maximum number of iterations allowed
* ``norm_type`` (int, optional): Type of norm to use (default: 2)
* ``print_flag`` (int, optional): Flag to print information during test (default: 0)

Usage Example
-------------

.. code-block:: python

    # Create a NormDispAndUnbalance convergence test
    test = fm.analysis.convergence_tests.create_test("normdispandunbalance", 
                                              tolerance1=1.0e-6, 
                                              tolerance2=1.0e-8,
                                              max_iterations=25) 