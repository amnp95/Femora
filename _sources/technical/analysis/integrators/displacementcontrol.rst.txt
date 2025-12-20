DisplacementControl Integrator
==============================

The DisplacementControl integrator is a static integration method that controls the displacement at a specific degree of freedom during analysis.

Description
-----------

This integrator is particularly suitable for:

* Static analysis with prescribed displacement targets
* Post-peak analysis in nonlinear structures
* Cases where load-based control becomes unstable
* Studies of structural behavior under specific displacement thresholds
* Pushover analysis of structures

The DisplacementControl method applies load in a manner to achieve the target displacement increment at a specified node and degree of freedom.

Parameters
----------

The DisplacementControl integrator requires the following parameters:

+----------+---------------------------------------+--------------+-------------------------------------------+
| Parameter| Description                           | Default      | Notes                                     |
+==========+=======================================+==============+===========================================+
| node_tag | Tag of the controlling node           | None         | Required                                  |
+----------+---------------------------------------+--------------+-------------------------------------------+
| dof      | Degree of freedom at the node (1-ndf) | None         | Required                                  |
+----------+---------------------------------------+--------------+-------------------------------------------+
| incr     | First displacement increment          | None         | Required                                  |
+----------+---------------------------------------+--------------+-------------------------------------------+
| num_iter | Number of iterations desired          | 1            | Optional                                  |
+----------+---------------------------------------+--------------+-------------------------------------------+
| min_incr | Minimum step size allowed             | incr         | Optional, defaults to incr value          |
+----------+---------------------------------------+--------------+-------------------------------------------+
| max_incr | Maximum step size allowed             | incr         | Optional, defaults to incr value          |
+----------+---------------------------------------+--------------+-------------------------------------------+

Usage Example
-------------

.. code-block:: python

    # Create a DisplacementControl integrator with basic parameters
    integrator = fm.analysis.integrators.create_integrator("displacementcontrol", 
                                                    node_tag=3, 
                                                    dof=1, 
                                                    incr=0.01)
    
    # Create a DisplacementControl integrator with custom step size limits
    integrator = fm.analysis.integrators.create_integrator("displacementcontrol", 
                                                    node_tag=3, 
                                                    dof=1, 
                                                    incr=0.01, 
                                                    num_iter=5, 
                                                    min_incr=0.005, 
                                                    max_incr=0.02) 