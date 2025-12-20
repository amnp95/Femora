Material 
---------------------------------

Understanding the MaterialManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``MaterialManager`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing material objects throughout the mesh generation process. It implements the Singleton pattern to ensure a single, consistent point of material management across the entire application.

Materials defined in Femora are automatically tracked, tagged, and organized by the MaterialManager, simplifying the process of creating complex models with multiple material definitions.

Accessing the MaterialManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the MaterialManager in your code:

1. **Direct Access**: Import and use the MaterialManager class directly
   
   .. code-block:: python
      
      from femora.components.Material.materialBase import MaterialManager
      
      # Get the singleton instance
      material_manager = MaterialManager.get_instance()
      
      # Use the material manager directly
      material_manager.create_material(...)

2. **Through Femora** (Recommended): Access via the Femora class's .material property
   
   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the MaterialManager through the .material property
      fm.material.create_material(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How MaterialManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MaterialManager provides several key capabilities:

1. **Material Creation**: Creates material objects of various types with appropriate parameters
2. **Material Tracking**: Keeps track of all materials by both tag and name
3. **Material Tagging**: Automatically assigns sequential tags to materials for use in analysis
4. **Material Management**: Provides methods to retrieve, update, and delete materials

When a material is created, the MaterialManager:

1. Assigns a unique numeric tag automatically (used by solvers like OpenSees)
2. Registers it with the user-provided name (which must be unique)
3. Validates that all required parameters are present and valid

.. note::
   Each material must have a unique name. The MaterialManager uses this name as a key
   to retrieve materials later. If you try to create a material with a name that already
   exists, the MaterialManager will raise an error.

Material Tagging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MaterialManager implements an intelligent tagging system that:

* Assigns sequential tags to materials starting from 1 (or a user-defined starting value)
* Automatically retags materials when one is deleted to maintain sequential numbering
* Ensures uniqueness of tags across the model
* Maps between material objects and their assigned tags

.. code-block:: python

   # Example of setting a custom tag starting point
   material_manager = MaterialManager.get_instance()
   material_manager.set_material_tag_start(1000)  # All new materials will start from tag 1000

MaterialManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.Material.materialBase.MaterialManager

Material Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating materials is one of the primary functions of the MaterialManager. There are two recommended approaches for material creation.
When creating a material, you need to specify several key parameters:

1. **material_category**: Defines the broad category of the material. Common categories include:
   - ``nDMaterial``: For multi-dimensional materials (1D, 2D, or 3D)
   - ``uniaxialMaterial``: For materials defined along a single axis


2. **material_type**: Specifies the specific material model within the category. For example:
   - For ``nDMaterial``: ElasticIsotropic, J2Plasticity, etc.
   - For ``uniaxialMaterial``: Elastic, Steel01, Concrete01, etc.

3. **user_name**: A unique identifier you assign to the material for later retrieval or working with it. This name must be unique across all materials in the model.

4. **Material-specific parameters**: Each material type requires specific parameters (like E, nu, rho for ElasticIsotropic materials)

The MaterialManager handles all the details of creating the appropriate material object based on these parameters, ensuring type safety and parameter validation.

Available Material Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   materials/nd/index
   materials/uniaxial/index

The material types available in Femora are organized by category. Follow the links above to explore the various material models available in each category.

* **nDMaterial**: Multi-dimensional materials for 2D and 3D analysis
* **uniaxialMaterial**: One-dimensional materials for truss, beam, and spring elements

Each material type has its own documentation page with detailed parameter descriptions and usage examples.