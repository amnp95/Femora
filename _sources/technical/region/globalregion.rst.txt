GlobalRegion
============

The ``GlobalRegion`` class represents the entire model and is automatically created when the RegionManager is initialized. There can only be one instance of GlobalRegion in the system, which always has a tag of 0.

This special region serves as the default region for operations that don't specify a specific region, providing a convenient way to apply configurations to the entire model.

Parameters
----------

- ``damping``: Optional damping instance to associate with the region

Usage
-----

.. code-block:: python

    from femora.components.Region.regionBase import RegionManager
    from femora.components.Damping.dampingBase import DampingManager
    
    # Get the region manager instance
    region_manager = RegionManager()
    
    # Get the damping manager instance
    damping_manager = DampingManager()
    
    # Create a damping instance
    rayleigh_damping = damping_manager.create_damping(
        'rayleigh', 
        alphaM=0.05, 
        betaK=0.001
    )
    
    # Access the global region
    global_region = region_manager.get_region(0)
    
    # Assign the damping to the global region
    global_region.damping = rayleigh_damping
    
    # Alternatively, you can access the global region through the RegionManager
    global_region = RegionManager().get_region(0)

Component Assignment
--------------------

The GlobalRegion can represent the entire model or specific components. You can assign components to the GlobalRegion using the ``setComponent`` method:

.. code-block:: python

    # Set specific elements
    global_region.setComponent("element", [1, 2, 3, 4, 5])
    
    # Set an element range
    global_region.setComponent("elementRange", [1, 100])
    
    # Set specific nodes
    global_region.setComponent("node", [1, 2, 3, 4, 5])
    
    # Set a node range
    global_region.setComponent("nodeRange", [1, 100])

Notes
-----

- The GlobalRegion is created automatically when the RegionManager is initialized
- You cannot remove the GlobalRegion (attempting to do so will raise a ValueError)
- Any damping assigned to the GlobalRegion will apply to all elements or nodes not covered by more specific regions