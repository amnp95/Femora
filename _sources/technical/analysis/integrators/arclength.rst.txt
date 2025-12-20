ArcLength Integrator
====================

The ArcLength integrator is a static integration method that follows the equilibrium path using the arc length method.

Description
-----------

This integrator is particularly suitable for:

* Post-buckling analysis of structures
* Problems with snap-through or snap-back behavior
* Tracing complex load-displacement paths
* Cases where load or displacement control fails
* Highly nonlinear structural problems

The ArcLength method uses a constraint equation based on the arc length along the load-displacement path, allowing it to navigate both load and displacement reversals.

Parameters
----------

The ArcLength integrator requires the following parameters:

+----------+--------------------------------+--------------+-------------------------------------------+
| Parameter| Description                    | Default      | Notes                                     |
+==========+================================+==============+===========================================+
| s        | Arc length                     | None         | Required                                  |
+----------+--------------------------------+--------------+-------------------------------------------+
| alpha    | Scaling factor on reference    | None         | Required                                  |
|          | loads                          |              |                                           |
+----------+--------------------------------+--------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create an ArcLength integrator
    integrator = fm.analysis.integrators.create_integrator("arclength", 
                                                    s=1.0, 
                                                    alpha=0.1) 