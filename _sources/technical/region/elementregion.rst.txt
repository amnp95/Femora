ElementRegion
=============

The ``ElementRegion`` class defines a region based on a set of specific elements or an element range. This allows you to apply damping and other properties to particular finite elements in your model.

Parameters
----------

- ``damping``: Optional damping instance to associate with the region
- ``elements``: List of specific element IDs to include in the region
- ``element_range``: Alternative to elements; defines a range of elements [start_element_id, end_element_id]
- ``element_only``: Boolean flag indicating whether to include only the elements (default: False)

Usage
-----

Creating an ElementRegion with specific elements:

.. code-block:: python

    from femora.components.Region.regionBase import RegionManager
    
    region_manager = RegionManager()
    
    # Create a region with specific elements
    element_region = region_manager.create_region(
        'ElementRegion',
        elements=[1, 2, 3, 4, 5]
    )

Creating an ElementRegion with an element range:

.. code-block:: python

    # Create a region with an element range (elements 1 through 100)
    element_range_region = region_manager.create_region(
        'ElementRegion',
        element_range=[1, 100]
    )

Associating damping with an ElementRegion:

.. code-block:: python

    from femora.components.Damping.dampingBase import DampingManager
    
    damping_manager = DampingManager()
    
    # Create a damping instance
    rayleigh_damping = damping_manager.create_damping(
        'rayleigh', 
        alphaM=0.05, 
        betaK=0.001
    )
    
    # Create a region with elements and damping
    element_region = region_manager.create_region(
        'ElementRegion',
        damping=rayleigh_damping,
        elements=[1, 2, 3, 4, 5],
        element_only=True
    )

Notes
-----

- You cannot specify both ``elements`` and ``element_range`` simultaneously
- The ``element_only`` flag is used to indicate that only the elements themselves are included (not associated nodes)
- When constructing with ``element_range``, provide exactly two values: [start_id, end_id]