MeshPart 
---------------------------------

Understanding the MeshPartManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``MeshPartManager`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing mesh part objects throughout the mesh generation process. Similar to the MaterialManager and ElementRegistry, it implements the Singleton pattern to ensure a single, consistent point of mesh part management across the entire application.

Mesh parts defined in Femora are automatically tracked, categorized, and organized by the MeshPartManager, simplifying the process of creating complex models with multiple mesh geometries.

Accessing the MeshPartManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the MeshPartManager in your code:

1. **Direct Access**: Import and use the MeshPartManager class directly
   
   .. code-block:: python
      
      from femora.components.Mesh.meshPartBase import MeshPartManager
      
      # Create a manager instance
      manager = MeshPartManager()
      
      # Access the manager directly
      mesh_part_types = manager._registry.get_mesh_part_categories()
      
      # Create a mesh part using the manager
      my_mesh_part = manager.create_mesh_part(...)

2. **Through Femora** (Recommended): Access via the Femora class's .meshPart property
   
   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the MeshPartManager through the .meshPart property
      mesh_part_types = fm.meshPart.get_mesh_part_categories()
      my_mesh_part = fm.meshPart.create_mesh_part(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How MeshPartManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MeshPartManager provides several key capabilities:

1. **Mesh Part Creation**: Creates mesh part objects of various types with appropriate parameters
2. **Mesh Part Tracking**: Keeps track of all mesh parts by their unique user-assigned names
3. **Mesh Part Management**: Provides methods to retrieve, update, and delete mesh parts
4. **Mesh Part Categorization**: Organizes mesh parts by categories (Volume mesh, Surface mesh, etc.)
5. **Mesh Part Filtering**: Filters mesh parts by category, region, or element type
6. **Mesh Part Operations**: Provides advanced operations like renaming, cloning, and merging mesh parts
7. **Mesh Part Validation**: Validates mesh parts for errors or issues
8. **Batch Operations**: Supports updating parameters and exporting multiple mesh parts at once

When a mesh part is created, the MeshPartManager:

1. Validates that all required parameters are present and valid
2. Associates the mesh part with an appropriate element and region
3. Automatically generates the mesh geometry based on the specified parameters
4. Registers it with a user-provided name (which must be unique)
5. Provides detailed operation status feedback

.. note::
   Each mesh part must have a unique name. The MeshPartManager uses this name as a key
   to retrieve mesh parts later. If you try to create a mesh part with a name that already
   exists, the MeshPartManager will raise an error.

MeshPart Class System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MeshPart base class implements an object-oriented design that:

* Provides a standardized interface for all mesh part types
* Enforces validation of parameters for each mesh part type
* Manages the lifecycle of mesh parts from creation to deletion
* Maps between mesh part objects and their assigned names
* Associates elements and regions with mesh parts

.. code-block:: python

   # Example of creating a simple volumetric mesh part
    
   
   # Create element and region first
   element = fm.element.create_element(...)
   region = fm.region.create_region(...)
   
   # Create the mesh part
   fm.meshPart.create_mesh_part(
       "Volume mesh",                  # Category
       "Uniform Rectangular Grid",     # Mesh part type
       "MyMeshPart",                   # Unique user name
       element=element,                # Element to assign
       region=region,                  # Region to assign
       **{                             # Type-specific parameters
          'X Min': -10, 'X Max': 10,
          'Y Min': -10, 'Y Max': 10,
          'Z Min': -5, 'Z Max': 0,
          'Nx Cells': 20, 'Ny Cells': 20, 'Nz Cells': 5
       }
   )

MeshPartManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.Mesh.meshPartBase.MeshPartManager
   :noindex:
   :members:
   :undoc-members:
   :special-members: __init__
   :show-inheritance:

Mesh Part Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating mesh parts is one of the primary functions of the MeshPartManager. When creating a mesh part, you need to specify several key parameters:

1. **category**: Defines the broad category of the mesh part. Common categories include:
   - ``Volume mesh``: For three-dimensional volume meshes
   - ``Surface mesh``: For two-dimensional surface meshes
   - ``Line mesh``: For one-dimensional line meshes
   - ``Point mesh``: For zero-dimensional point meshes

2. **mesh_part_type**: Specifies the specific mesh geometry within the category. For example:
   - For ``Volume mesh``: Uniform Rectangular Grid, Custom Rectangular Grid, etc.

3. **user_name**: A unique identifier you assign to the mesh part for later retrieval or working with it. This name must be unique across all mesh parts in the model.

4. **element**: The element type to associate with this mesh part.

5. **region**: The region to associate with this mesh part for properties like damping.

6. **Type-specific parameters**: Each mesh part type requires specific parameters (like X Min, X Max, Nx Cells for Uniform Rectangular Grid meshes)

The MeshPartManager handles all the details of creating the appropriate mesh part object based on these parameters, ensuring type safety and parameter validation.

Available Mesh Part Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   
   meshparts/volume/index
..    meshparts/surface/index
..    meshparts/line/index
..    meshparts/point/index

The mesh part types available in Femora are organized by their geometric dimensionality. Follow the links above to explore the various mesh part types available in each category.

* **Volume mesh**: Three-dimensional mesh parts for modeling solid domains
* **Surface mesh**: Two-dimensional mesh parts for modeling surface structures 
* **Line mesh**: One-dimensional mesh parts for modeling linear structures
* **Point mesh**: Zero-dimensional mesh parts for modeling point structures

Each mesh part type has its own documentation page with detailed parameter descriptions and usage examples.