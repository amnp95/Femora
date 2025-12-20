Region
======

Understanding the RegionManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``RegionManager`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing region objects. It implements the Singleton pattern to ensure a single, consistent point of region management across the entire application.

Regions defined in Femora are automatically tracked, tagged, and organized by the RegionManager, simplifying the process of defining specific parts of your model for targeted analysis and damping assignments.

Accessing the RegionManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the RegionManager in your code:

1. **Direct Access**: Import and use the RegionManager class directly
   
   .. code-block:: python
      
      from femora.components.Region.regionBase import RegionManager
      
      # Get the singleton instance
      region_manager = RegionManager()
      
      # Use the region manager directly
      region_manager.create_region(...)

2. **Through femora** (Recommended): Access via the Femora class's .region property
   
   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the RegionManager through the .region property
      fm.region.create_region(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How RegionManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The RegionManager provides several key capabilities:

1. **Region Creation**: Creates region objects of various types with appropriate parameters
2. **Region Tracking**: Keeps track of all region instances by tag
3. **Region Tagging**: Automatically assigns sequential tags to region instances
4. **Region Management**: Provides methods to retrieve, update, and delete region instances

When a region is created, the RegionManager:

1. Assigns a unique numeric tag automatically (starting from 1, as tag 0 is reserved for the GlobalRegion)
2. Validates that all required parameters are present and valid
3. Registers it for use in defining parts of the model

Global Region
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``GlobalRegion`` is a special region with tag 0 that represents the entire model. It's automatically created when the RegionManager is initialized, and there can only be one instance of GlobalRegion in the system.

This region serves as the default region for operations that don't specify a specific region, providing a convenient way to apply configurations to the entire model.

Region Tagging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The RegionManager implements an intelligent tagging system that:

* Reserves tag 0 for the GlobalRegion
* Assigns sequential tags to other regions starting from 1
* Automatically retags instances when one is removed to maintain sequential numbering
* Ensures uniqueness of tags across the model

RegionManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Key Methods:

.. autoclass:: femora.components.Region.regionBase.RegionManager
   :members:
   :undoc-members:
   :show-inheritance:

Region Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating regions is one of the primary functions of the RegionManager. When creating a region, you need to specify:

1. **regionType**: Specifies the region type to create. Available types include:
   - ``ElementRegion``: A region defined by a set of elements or element range
   - ``NodeRegion``: A region defined by a set of nodes or node range
   - ``GlobalRegion``: The global region representing the entire model (typically not created directly)

2. **damping**: Optional damping instance to associate with the region

3. **Region-specific parameters**: Each region type requires specific parameters (like elements, element_range for ElementRegion)

The RegionManager handles all the details of creating the appropriate region object based on these parameters, ensuring type safety and parameter validation.

Usage Example
-------------

.. code-block:: python

   from femora.components.Region.regionBase import RegionManager
   from femora.components.Damping.dampingBase import DampingManager
   
   # Get the region manager instance
   region_manager = RegionManager()
   
   # Get the damping manager instance
   damping_manager = DampingManager()
   
   # Create a Rayleigh damping instance
   rayleigh_damping = damping_manager.create_damping(
       'rayleigh', 
       alphaM=0.1, 
       betaK=0.2
   )
   
   # Create an element region with specific elements and the damping
   element_region = region_manager.create_region(
       'ElementRegion', 
       damping=rayleigh_damping,
       elements=[1, 2, 3, 4, 5]
   )
   
   # Create a node region with a node range
   node_region = region_manager.create_region(
       'NodeRegion',
       node_range=[1, 100]
   )
   
   # Access the global region
   global_region = region_manager.get_region(0)
   
   # Remove a region
   region_manager.remove_region(2)
   
   # Print all regions
   region_manager.print_regions()

Available Region Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   
   region/index

The region types available in Femora provide different ways to define specific parts of your model for targeted analysis and configuration. Follow the link above to explore the different region types available.

Each region type has its own documentation page with detailed parameter descriptions and usage examples.