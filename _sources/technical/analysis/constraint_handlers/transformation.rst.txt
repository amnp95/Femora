Transformation constraint handler
=================================

The Transformation constraint handler enforces constraints exactly by using a transformation matrix method. It effectively removes constrained degrees of freedom from the system of equations.

Parameters
----------

No parameters required.

Usage Example
-------------

.. code-block:: python

    # Create a Femora instance
     
    
    # Create a Transformation constraint handler
    fm.analysis.constraint.create_handler("Transformation") 