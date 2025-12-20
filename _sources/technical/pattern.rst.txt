Pattern
=======

Understanding the PatternManager
--------------------------------

The ``PatternManager`` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing pattern objects. It implements the Singleton pattern to ensure a single, consistent point of pattern management across the entire application.

Patterns defined in Femora are automatically tracked, tagged, and organized by the PatternManager, simplifying the process of applying repetitive configurations or arrangements within the mesh or model.

Accessing the PatternManager
----------------------------

There are two ways to access the PatternManager in your code:

1. **Direct Access**: Import and use the PatternManager class directly

   .. code-block:: python

      from femora.components.Pattern.patternBase import PatternManager

      # Get the singleton instance
      pattern_manager = PatternManager()

      # Use the pattern manager directly
      pattern_manager.create_pattern(...)

2. **Through Femora** (Recommended): Access via the Femora class's .pattern property

   .. code-block:: python

      import femora as fm

      # Create a Femora instance
       

      # Access the PatternManager through the .pattern property
      fm.pattern.create_pattern(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How PatternManager Works
------------------------

The PatternManager provides several key capabilities:

1. **Pattern Creation**: Creates pattern objects of various types with appropriate parameters.
2. **Pattern Tracking**: Keeps track of all patterns by their tags.
3. **Pattern Tagging**: Automatically assigns sequential tags to patterns for use in analysis.
4. **Pattern Management**: Provides methods to retrieve, update, and delete patterns.

When a pattern is created, the PatternManager:

1. Assigns a unique numeric tag automatically.
2. Validates that all required parameters are present and valid.
3. Registers the pattern for use in defining repetitive configurations.

PatternManager API Reference
----------------------------

.. autoclass:: femora.components.Pattern.patternBase.PatternManager
   :members:
   :undoc-members:
   :show-inheritance:

Pattern Creation
----------------

Creating patterns is one of the primary functions of the PatternManager. When creating a pattern, you need to specify several key parameters:

1. **pattern_type**: Specifies the type of pattern (e.g., 'GridPattern', 'RadialPattern', etc.).
2. **Pattern-specific parameters**: Each pattern type requires specific parameters (like spacing, orientation, or radius).

The PatternManager handles all the details of creating the appropriate pattern object based on these parameters, ensuring type safety and parameter validation.

Usage Example
-------------

.. code-block:: python

   from femora.components.Pattern.patternBase import PatternManager

   # Get the pattern manager instance
   pattern_manager = PatternManager()

   # Create a grid pattern with specific spacing
   grid_pattern = pattern_manager.create_pattern(
       'GridPattern',
       spacing=(1.0, 1.0)
   )

   # Apply the pattern to a region
   region.apply_pattern(grid_pattern)

Available Pattern Types
------------------------

The pattern types available in Femora provide different ways to define repetitive configurations. Examples include:

.. toctree::
   :maxdepth: 2

   pattern/uniformexcitation
   pattern/h5drm

Each pattern type has its own documentation page with detailed parameter descriptions and usage examples.