ExplicitDifference Integrator
=============================

The ExplicitDifference integrator is an explicit time integration method for dynamic analysis.

Description
-----------

This integrator is particularly suitable for:

* Dynamic problems requiring computational efficiency
* Impact and blast analyses
* Wave propagation problems
* Cases where the time step is limited by physics rather than stability
* Short-duration dynamic events

The ExplicitDifference method advances the solution without solving a system of equations at each time step, making it computationally efficient for each step.

Parameters
----------
This integrator has no parameters.

Usage Example
-------------

.. code-block:: python

    # Create an ExplicitDifference integrator
    integrator = fm.analysis.integrators.create_integrator("explicitdifference") 