MinUnbalDispNorm Integrator
===========================

The MinUnbalDispNorm integrator is a static integration method that uses a minimum unbalanced displacement norm criterion to determine step size.

Description
-----------

This integrator is particularly suitable for:

* Nonlinear static analysis with adaptive step size
* Problems with varying degrees of nonlinearity
* Cases where automatic step size control is beneficial
* Analysis with potential numerical difficulties

The MinUnbalDispNorm method attempts to find a suitable load increment by minimizing the unbalanced displacement norm.

Parameters
----------

The MinUnbalDispNorm integrator requires the following parameters:

+------------+---------------------------------------------+--------------+-------------------------------------------+
| Parameter  | Description                                 | Default      | Notes                                     |
+============+=============================================+==============+===========================================+
| dlambda1   | First load increment (pseudo-time step)     | None         | Required                                  |
+------------+---------------------------------------------+--------------+-------------------------------------------+
| jd         | Factor for subsequent time steps            | 1            | Optional                                  |
+------------+---------------------------------------------+--------------+-------------------------------------------+
| min_lambda | Minimum load increment                      | dlambda1     | Optional, defaults to dlambda1 value      |
+------------+---------------------------------------------+--------------+-------------------------------------------+
| max_lambda | Maximum load increment                      | dlambda1     | Optional, defaults to dlambda1 value      |
+------------+---------------------------------------------+--------------+-------------------------------------------+
| det        | Flag to use determinant of tangent          | False        | Optional                                  |
+------------+---------------------------------------------+--------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a MinUnbalDispNorm integrator with basic parameters
    integrator = fm.analysis.integrators.create_integrator("minunbaldispnorm", 
                                                    dlambda1=0.1)
    
    # Create a MinUnbalDispNorm integrator with custom parameters
    integrator = fm.analysis.integrators.create_integrator("minunbaldispnorm", 
                                                    dlambda1=0.1, 
                                                    jd=3, 
                                                    min_lambda=0.05, 
                                                    max_lambda=0.2, 
                                                    det=True) 