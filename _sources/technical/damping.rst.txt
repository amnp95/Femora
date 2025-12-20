Damping
=======

Understanding the DampingManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``DampingManager`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing damping objects. It implements the Singleton pattern to ensure a single, consistent point of damping management across the entire application.

Damping models defined in Femora are automatically tracked, tagged, and organized by the DampingManager, simplifying the process of creating models with appropriate energy dissipation mechanisms.

Accessing the DampingManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the DampingManager in your code:

1. **Direct Access**: Import and use the DampingManager class directly
   
   .. code-block:: python
      
      from Femora.components.Damping import DampingManager
      
      # Get the singleton instance
      damping_manager = DampingManager()
      
      # Use the damping manager directly
      damping_manager.create_damping(...)

2. **Through Femora** (Recommended): Access via the Femora class's .damping property
   
   .. code-block:: python
      
      import Femora as fm
      
      # Create a Femora instance
       
      
      # Access the DampingManager through the .damping property
      fm.damping.create_damping(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How DampingManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DampingManager provides several key capabilities:

1. **Damping Creation**: Creates damping objects of various types with appropriate parameters
2. **Damping Tracking**: Keeps track of all damping instances by tag
3. **Damping Tagging**: Automatically assigns sequential tags to damping models
4. **Damping Management**: Provides methods to retrieve, update, and delete damping instances

When a damping model is created, the DampingManager:

1. Assigns a unique numeric tag automatically
2. Validates that all required parameters are present and valid
3. Registers it for use in dynamic analyses

Damping Tagging System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DampingManager implements an intelligent tagging system that:

* Assigns sequential tags to damping instances starting from 1
* Automatically retags instances when one is deleted to maintain sequential numbering
* Ensures uniqueness of tags across the model

DampingManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.Damping.dampingBase.DampingManager
   :members:
   :undoc-members:
   :show-inheritance:

Damping Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating damping models is one of the primary functions of the DampingManager. When creating a damping model, you need to specify:

1. **damping_type**: Specifies the damping model to create. Available types include:
   - ``rayleigh``: Classical Rayleigh damping
   - ``modal``: Modal damping for specific modes
   - ``frequency rayleigh``: Rayleigh damping specified by target frequencies
   - ``uniform``: Uniform damping across a frequency range
   - ``secant stiffness proportional``: Damping proportional to secant stiffness

2. **Damping-specific parameters**: Each damping type requires specific parameters (like alphaM, betaK for Rayleigh damping)

The DampingManager handles all the details of creating the appropriate damping object based on these parameters, ensuring type safety and parameter validation.

Usage Example
-------------

.. code-block:: python

   from Femora.components.Damping import DampingManager
   
   # Get the damping manager instance
   damping_manager = DampingManager()
   
   # Create a Rayleigh damping instance
   rayleigh_damping = damping_manager.create_damping(
       'rayleigh', 
       alphaM=0.1, 
       betaK=0.2, 
       betaKInit=0.0, 
       betaKComm=0.0
   )
   
   # Create a modal damping instance
   modal_damping = damping_manager.create_damping(
       'modal',
       numberofModes=3,
       dampingFactors="0.02,0.03,0.04"
   )
   
   # Access an existing damping instance by tag
   damping = damping_manager.get_damping(1)
   
   # Remove a damping instance
   damping_manager.remove_damping(2)
   
   # Get all available damping types
   available_types = damping_manager.get_available_types()
   print(available_types)  # ['frequency rayleigh', 'rayleigh', 'modal', ...]

Available Damping Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   
   damping/index

The damping models available in Femora provide various approaches to energy dissipation in dynamic analysis. Follow the link above to explore the different damping models available.

Each damping type has its own documentation page with detailed parameter descriptions and usage examples.