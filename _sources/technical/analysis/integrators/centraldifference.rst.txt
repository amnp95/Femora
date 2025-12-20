CentralDifference Integrator
============================

The CentralDifference integrator is an explicit time integration method for dynamic analysis.

Description
-----------

This integrator is particularly suitable for:

* Wave propagation problems
* Impact analysis
* Highly nonlinear dynamic problems
* Cases where computational efficiency per time step is important
* Systems with distributed mass matrices

The CentralDifference method is a second-order explicit method that computes the response at time t+Δt based on the equilibrium at time t.

Parameters
----------
This integrator has no parameters.

Usage Example
-------------

.. code-block:: python

    # Create a CentralDifference integrator
    integrator = fm.analysis.integrators.create_integrator("centraldifference") 