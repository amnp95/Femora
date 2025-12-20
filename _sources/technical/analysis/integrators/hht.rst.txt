HHT Integrator
==============

The HHT (Hilber-Hughes-Taylor) integrator is an implicit time integration method for dynamic analysis with controllable numerical damping.

Description
-----------

This integrator is particularly suitable for:

* Structural dynamics problems requiring numerical damping
* Cases where high-frequency noise should be filtered out
* Nonlinear dynamic analysis
* Long duration dynamic simulations
* Problems with stiff differential equations

The HHT method is an extension of the Newmark method that introduces controlled numerical damping while maintaining second-order accuracy.

Parameters
----------

The HHT integrator requires the following parameters:

+----------+--------------------------------+---------------------+-------------------------------------------+
| Parameter| Description                    | Default             | Notes                                     |
+==========+================================+=====================+===========================================+
| alpha    | Alpha factor                   | None                | Required, controls numerical damping      |
+----------+--------------------------------+---------------------+-------------------------------------------+
| gamma    | Gamma factor                   | 1.5 - alpha         | Optional, defaults to 1.5 - alpha         |
+----------+--------------------------------+---------------------+-------------------------------------------+
| beta     | Beta factor                    | (2-alpha)^2/4       | Optional, defaults to (2-alpha)^2/4       |
+----------+--------------------------------+---------------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create an HHT integrator with only alpha specified (gamma and beta calculated automatically)
    integrator = fm.analysis.integrators.create_integrator("hht", alpha=-0.1)
    
    # Create an HHT integrator with all parameters explicitly defined
    integrator = fm.analysis.integrators.create_integrator("hht", 
                                                    alpha=-0.1, 
                                                    gamma=0.6, 
                                                    beta=0.3025) 