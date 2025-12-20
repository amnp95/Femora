NodeRegion
==========

The ``NodeRegion`` class defines a region based on a set of specific nodes or a node range. This allows you to apply damping and other properties to particular nodes in your model.

Parameters
----------

- ``damping``: Optional damping instance to associate with the region
- ``nodes``: List of specific node IDs to include in the region
- ``node_range``: Alternative to nodes; defines a range of nodes [start_node_id, end_node_id]
- ``node_only``: Boolean flag indicating whether to include only the nodes (default: False)

Usage
-----

Creating a NodeRegion with specific nodes:

.. code-block:: python

    from femora.components.Region.regionBase import RegionManager
    
    region_manager = RegionManager()
    
    # Create a region with specific nodes
    node_region = region_manager.create_region(
        'NodeRegion',
        nodes=[1, 2, 3, 4, 5]
    )

Creating a NodeRegion with a node range:

.. code-block:: python

    # Create a region with a node range (nodes 1 through 100)
    node_range_region = region_manager.create_region(
        'NodeRegion',
        node_range=[1, 100]
    )

Associating damping with a NodeRegion:

.. code-block:: python

    from femora.components.Damping.dampingBase import DampingManager
    
    damping_manager = DampingManager()
    
    # Create a damping instance
    rayleigh_damping = damping_manager.create_damping(
        'rayleigh', 
        alphaM=0.05, 
        betaK=0.001
    )
    
    # Create a region with nodes and damping
    node_region = region_manager.create_region(
        'NodeRegion',
        damping=rayleigh_damping,
        nodes=[1, 2, 3, 4, 5],
        node_only=True
    )

Notes
-----

- You cannot specify both ``nodes`` and ``node_range`` simultaneously
- The ``node_only`` flag is used to indicate that only the nodes themselves are included
- When constructing with ``node_range``, provide exactly two values: [start_id, end_id]