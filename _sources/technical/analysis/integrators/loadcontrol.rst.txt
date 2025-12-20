LoadControl Integrator
======================

The LoadControl integrator is a static integration method that controls the applied load increment during analysis.

Description
-----------

This integrator is particularly suitable for:

* Static analysis with prescribed load patterns
* Cases where the load is applied in controlled increments
* Problems that require monitoring load-based response
* Nonlinear static analysis with load control

The LoadControl method applies load in predefined increments, allowing for step-by-step observation of structural response.

Parameters
----------

The LoadControl integrator requires the following parameters:

+----------+--------------------------------+--------------+-------------------------------------------+
| Parameter| Description                    | Default      | Notes                                     |
+==========+================================+==============+===========================================+
| incr     | Load factor increment          | None         | Required                                  |
+----------+--------------------------------+--------------+-------------------------------------------+
| num_iter | Number of iterations desired   | 1            | Optional                                  |
+----------+--------------------------------+--------------+-------------------------------------------+
| min_incr | Minimum step size allowed      | incr         | Optional, defaults to incr value          |
+----------+--------------------------------+--------------+-------------------------------------------+
| max_incr | Maximum step size allowed      | incr         | Optional, defaults to incr value          |
+----------+--------------------------------+--------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a LoadControl integrator with basic parameters
    integrator = fm.analysis.integrators.create_integrator("loadcontrol", incr=0.1)
    
    # Create a LoadControl integrator with custom step size limits
    integrator = fm.analysis.integrators.create_integrator("loadcontrol", 
                                                    incr=0.1, 
                                                    num_iter=5, 
                                                    min_incr=0.05, 
                                                    max_incr=0.2) 