TRBDF2 Integrator
=================

The TRBDF2 integrator is an implicit time integration method that combines the Trapezoidal Rule and Backward Differentiation Formula for improved accuracy and stability.

Description
-----------

This integrator is particularly suitable for:

* Stiff differential equations
* Problems requiring high accuracy
* Nonlinear dynamic analysis
* Problems with varying time scales
* Cases where stability is critical

The TRBDF2 method uses a two-stage approach, first applying the Trapezoidal Rule and then the Backward Differentiation Formula.

Parameters
----------
This integrator has no parameters. 

Usage Example
-------------

.. code-block:: python

    # Create a TRBDF2 integrator
    integrator = fm.analysis.integrators.create_integrator("trbdf2")



