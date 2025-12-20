Penalty constraint handler
==========================

The Penalty constraint handler enforces constraints approximately by adding large stiffness terms to the system matrix for constrained degrees of freedom.

Parameters
----------

``alpha_s`` : float, default=1.0e6
    The penalty value for single-point constraints.

``alpha_m`` : float, default=1.0e6
    The penalty value for multi-point constraints.

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Penalty constraint handler with default parameters
    fm.analysis.constraint.create_handler("Penalty")
    
    # Create a Penalty constraint handler with custom parameters
    fm.analysis.constraint.create_handler("Penalty", alpha_s=1.0e7, alpha_m=1.0e8) 