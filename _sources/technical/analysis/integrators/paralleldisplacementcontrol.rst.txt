ParallelDisplacementControl Integrator
======================================

The ParallelDisplacementControl integrator is a static integration method that controls the displacement at a specific degree of freedom during analysis, optimized for parallel processing.

Description
-----------

This integrator is particularly suitable for:

* Static analysis with prescribed displacement targets in parallel computing environments
* Large-scale models that require distributed processing
* Post-peak analysis in nonlinear structures with parallel computing
* High-performance computing applications

The ParallelDisplacementControl method is similar to DisplacementControl but is designed specifically for efficient parallel processing.

Parameters
----------

The ParallelDisplacementControl integrator requires the following parameters:

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

    # Create a ParallelDisplacementControl integrator with basic parameters
    integrator = fm.analysis.integrators.create_integrator("paralleldisplacementcontrol", 
                                                    node_tag=3, 
                                                    dof=1, 
                                                    incr=0.01)
    
    # Create a ParallelDisplacementControl integrator with custom step size limits
    integrator = fm.analysis.integrators.create_integrator("paralleldisplacementcontrol", 
                                                    node_tag=3, 
                                                    dof=1, 
                                                    incr=0.01, 
                                                    num_iter=5, 
                                                    min_incr=0.005, 
                                                    max_incr=0.02) 