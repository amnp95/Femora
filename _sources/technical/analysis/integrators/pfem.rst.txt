PFEM Integrator
===============

The PFEM integrator is a specialized integration method for fluid-structure interaction analysis using the Particle Finite Element Method.

Description
-----------

This integrator is particularly suitable for:

* Fluid-structure interaction problems
* Free-surface flows
* Large deformation problems
* Multi-physics simulations
* Problems involving fluid sloshing and splashing

The PFEM integrator is specifically designed to handle the coupled physics in fluid-structure interaction problems using the Particle Finite Element Method.

Parameters
----------

The PFEM integrator accepts the following parameters:

+----------+--------------------------------+--------------+-------------------------------------------+
| Parameter| Description                    | Default      | Notes                                     |
+==========+================================+==============+===========================================+
| gamma    | Gamma factor                   | 0.5          | Optional                                  |
+----------+--------------------------------+--------------+-------------------------------------------+
| beta     | Beta factor                    | 0.25         | Optional                                  |
+----------+--------------------------------+--------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a PFEM integrator with default parameters
    integrator = fm.analysis.integrators.create_integrator("pfem")
    
    # Create a PFEM integrator with custom parameters
    integrator = fm.analysis.integrators.create_integrator("pfem", 
                                                    gamma=0.6, 
                                                    beta=0.3) 