Element 
---------------------------------

Understanding the ElementRegistry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``ElementRegistry`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing element objects throughout the mesh generation process. Similar to the MaterialManager, it implements the Singleton pattern to ensure a single, consistent point of element management across the entire application.

Elements defined in Femora are automatically tracked, tagged, and organized by the ElementRegistry, simplifying the process of creating complex models with multiple element types.

Accessing the ElementRegistry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the ElementRegistry in your code:

1. **Direct Access**: Import and use the ElementRegistry class directly
   
   .. code-block:: python
      
      from femora.components.Element.elementBase import ElementRegistry
      
      # Access the registry directly
      element_types = ElementRegistry.get_element_types()
      
      # Create an element using the registry
      my_element = ElementRegistry.create_element(...)

2. **Through Femora** (Recommended): Access via the Femora class's .element property
   
   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the ElementRegistry through the .element property
      element_types = fm.element.get_element_types()
      my_element = fm.element.create_element(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How ElementRegistry Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ElementRegistry provides several key capabilities:

1. **Element Creation**: Creates element objects of various types with appropriate parameters
2. **Element Tracking**: Keeps track of all elements by their tags
3. **Element Tagging**: Automatically assigns sequential tags to elements for use in analysis
4. **Element Management**: Provides methods to retrieve, update, and delete elements

When an element is created, the ElementRegistry:

1. Assigns a unique numeric tag automatically (used by solvers like OpenSees)
2. Validates that all required parameters are present and valid
3. Associates the element with an appropriate material
4. Sets the degrees of freedom (DOF) for the element

.. note::
   Each element has a unique tag that is used for identification during mesh generation and analysis. The ElementRegistry ensures that these tags remain unique and sequential.

Element Tagging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Element class implements an intelligent tagging system that:

* Assigns sequential tags to elements starting from 1.
* Automatically retags elements when one is deleted to maintain sequential numbering
* Ensures uniqueness of tags across the model
* Maps between element objects and their assigned tags

.. code-block:: python

   # Example of setting a custom tag starting point
   from femora.components.Element.elementBase import Element

ElementRegistry API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.Element.elementBase.ElementRegistry

Element Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating elements is one of the primary functions of the ElementRegistry. When creating an element, you need to specify several key parameters:

1. **element_type**: Specifies the type of element (e.g., 'SSPQuad', 'stdBrick', etc.)
2. **ndof**: Number of degrees of freedom per node for this element
3. **material**: The material to associate with the element (can be a Material object, material tag, or material name)
4. **Element-specific parameters**: Each element type requires specific parameters

The ElementRegistry handles all the details of creating the appropriate element object based on these parameters, ensuring type safety and parameter validation.

Available Element Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The element types available in Femora are organized by their geometric dimensionality and characteristics. Follow the links above to explore the various element models available in each category.

* **3D Elements**: For three-dimensional continuum modeling
* **2D Elements**: For two-dimensional plane stress/strain problems

Each element type has its own documentation page with detailed parameter descriptions and usage examples.

.. toctree::
    :maxdepth: 2

    elements/3d/index
    elements/2d/index
