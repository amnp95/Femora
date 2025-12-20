GeneralizedAlpha Integrator
===========================

The GeneralizedAlpha integrator is an advanced implicit time integration method for dynamic analysis with controllable numerical damping across frequency ranges.

Description
-----------

This integrator is particularly suitable for:

* Structural dynamics problems requiring targeted numerical damping
* Cases where specific frequency content should be preserved
* Problems with high-frequency noise
* Nonlinear dynamic analysis
* Multi-physics simulations with different time scales

The GeneralizedAlpha method provides second-order accuracy and unconditional stability while allowing for controlled high-frequency damping.

Parameters
----------

The GeneralizedAlpha integrator requires the following parameters:

+----------+--------------------------------+-----------------------------+-------------------------------------------+
| Parameter| Description                    | Default                     | Notes                                     |
+==========+================================+=============================+===========================================+
| alpha_m  | Alpha_m factor                 | None                        | Required                                  |
+----------+--------------------------------+-----------------------------+-------------------------------------------+
| alpha_f  | Alpha_f factor                 | None                        | Required                                  |
+----------+--------------------------------+-----------------------------+-------------------------------------------+
| gamma    | Gamma factor                   | 0.5 + alpha_m - alpha_f     | Optional                                  |
+----------+--------------------------------+-----------------------------+-------------------------------------------+
| beta     | Beta factor                    | (1 + alpha_m - alpha_f)^2/4 | Optional                                  |
+----------+--------------------------------+-----------------------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a GeneralizedAlpha integrator with basic parameters (gamma and beta calculated automatically)
    integrator = fm.analysis.integrators.create_integrator("generalizedalpha", 
                                                    alpha_m=0.2, 
                                                    alpha_f=0.4)
    
    # Create a GeneralizedAlpha integrator with all parameters explicitly defined
    integrator = fm.analysis.integrators.create_integrator("generalizedalpha", 
                                                    alpha_m=0.2, 
                                                    alpha_f=0.4, 
                                                    gamma=0.3, 
                                                    beta=0.25) 