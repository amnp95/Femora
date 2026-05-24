Damping
=======

Understanding the DampingManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``DampingManager`` is a core component of the Femora library that serves as a centralized, local system for creating, retrieving, tracking, and managing damping objects. Each ``Model`` instance owns its local ``DampingManager``, avoiding any global state or singleton registries and keeping the runtime clean and modular.

Damping models defined in Femora are automatically tracked, tagged, and organized by the DampingManager.

Accessing the DampingManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You access the DampingManager via the Model instance's ``damping`` property:

.. code-block:: python
   
   import Femora as fm
   
   # Access the DampingManager and create a Rayleigh damping instance
   rayleigh_damp = fm.damping.rayleigh(alphaM=0.1, betaK=0.2)

How DampingManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DampingManager provides several key capabilities:

1. **Damping Creation**: Provides dedicated factory methods for each concrete damping type
2. **Damping Tracking**: Keeps track of all damping instances locally by tag
3. **Damping Tagging**: Automatically assigns sequential tags to damping models using a compact retag policy
4. **Damping Management**: Provides methods to retrieve, update, and delete damping instances

When a damping model is created, the DampingManager:

1. Assigns a unique numeric tag automatically
2. Validates that all required parameters are present and valid
3. Registers it for use in the dynamic analysis

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

Creating damping models is done using dedicated factory methods on the DampingManager:

* ``rayleigh(**kwargs)``: Classical Rayleigh damping
* ``modal(**kwargs)``: Modal damping for specific modes
* ``frequency_rayleigh(**kwargs)``: Rayleigh damping specified by target frequencies
* ``uniform(**kwargs)``: Uniform damping across a frequency range
* ``secant_stiffness_proportional(**kwargs)``: Damping proportional to secant stiffness

The DampingManager handles all the details of creating the appropriate damping object based on these parameters, ensuring type safety and parameter validation.

Usage Example
-------------

.. code-block:: python

   # Access the DampingManager instance from your Femora model
   damping_manager = fm.damping
   
   # Create a Rayleigh damping instance
   rayleigh_damping = damping_manager.rayleigh(
       alphaM=0.1, 
       betaK=0.2, 
       betaKInit=0.0, 
       betaKComm=0.0
   )
   
   # Create a modal damping instance
   modal_damping = damping_manager.modal(
       numberofModes=3,
       dampingFactors="0.02,0.03,0.04"
   )
   
   # Access an existing damping instance by tag
   damping = damping_manager.get(1)
   
   # Remove a damping instance
   damping_manager.remove(2)

Available Damping Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   
   damping/index

The damping models available in Femora provide various approaches to energy dissipation in dynamic analysis. Follow the link above to explore the different damping models available.

Each damping type has its own documentation page with detailed parameter descriptions and usage examples.