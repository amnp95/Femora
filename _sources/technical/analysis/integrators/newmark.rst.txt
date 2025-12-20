Newmark Integrator
==================

The Newmark integrator is a widely used implicit time integration method for dynamic analysis.

Description
-----------

This integrator is particularly suitable for:

* Linear and nonlinear dynamic analysis
* Problems with moderate to high frequency content
* Cases requiring unconditional stability
* Structural dynamics problems
* Earthquake engineering applications

The Newmark method uses a weighted average of acceleration and velocity to advance the solution in time.

Parameters
----------

The Newmark integrator requires the following parameters:

+----------+-------------------------------+---------------+-------------------------------------------+
| Parameter| Description                   | Default       | Notes                                     |
+==========+===============================+===============+===========================================+
| gamma    | Gamma factor                  | None          | Required                                  |
+----------+-------------------------------+---------------+-------------------------------------------+
| beta     | Beta factor                   | None          | Required                                  |
+----------+-------------------------------+---------------+-------------------------------------------+
| form     | Primary variable flag         | "D"           | Options: "D" (displacement), "V"          |
|          |                               |               | (velocity), or "A" (acceleration)         |
+----------+-------------------------------+---------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a Newmark integrator
    integrator = fm.analysis.integrators.create_integrator("newmark", gamma=0.5, beta=0.25)
    
    # Create a Newmark integrator with velocity as primary variable
    integrator = fm.analysis.integrators.create_integrator("newmark", gamma=0.5, beta=0.25, form="V")

