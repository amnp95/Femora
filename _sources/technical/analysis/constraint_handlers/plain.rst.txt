Plain constraint handler
========================

The Plain constraint handler is the simplest form of constraint enforcement. It uses a direct elimination approach to handle single-point constraints (fixed DOFs).

Parameters
----------

No parameters required.

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Plain constraint handler
    fm.analysis.constraint.create_handler("Plain") 