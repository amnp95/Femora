Coding Style and Naming Conventions
===================================

This library follows the official Python style guide (PEP 8) for code consistency, readability, and maintainability. Below are the naming conventions and practices used throughout the codebase.

Class Naming
------------
- Use ``PascalCase`` for class names.
- Class names are typically nouns that represent data structures or objects.

  **Examples**:
  - ``SoilProfile``
  - ``TransferFunction``
  - ``MeshGenerator``

Function and Method Naming
--------------------------
- Use ``snake_case`` for function and method names.
- Names should be descriptive and indicate the function’s purpose.

  **Examples**:
  - ``compute_tf()``
  - ``plot_profile()``
  - ``load_input_data()``

Variable Naming
---------------
- Use ``snake_case`` for variable names.
- Choose clear and meaningful names.
- Boolean variables should read like yes/no questions.

  **Examples**:
  - ``vs_profile``
  - ``input_motion``
  - ``is_valid``, ``has_converged``

Constant Naming
---------------
- Use ``ALL_CAPS_WITH_UNDERSCORES`` for constants.
- Constants are defined at the module level and not expected to change.

  **Examples**:
  - ``MAX_ITERATIONS``
  - ``DEFAULT_DAMPING_RATIO``

Module and File Naming
----------------------
- File names (modules) use ``snake_case``.
- Names are short and descriptive.
- Avoid using names that shadow Python built-in modules (e.g., ``math.py``).

  **Examples**:
  - ``transfer_function.py``
  - ``soil_profile.py``
  - ``mesh_generator.py``
  - ``io_handler.py``

Package Naming
--------------
- Package (folder) names are all lowercase and typically a single word.

  **Example**:
  - ``femora``

Private Functions and Methods
-----------------------------
- Prefix with an underscore ``_`` to indicate internal use only.

  **Example**:
  - ``_compute_internal_values()``

Dunder (Magic) Methods
----------------------
- Special Python methods use double underscores before and after.
- Use only for protocol behaviors (e.g., initialization, string representation).

  **Examples**:
  - ``__init__()``
  - ``__repr__()``
  - ``__call__()``

Following these conventions ensures the code remains intuitive, maintainable, and welcoming for contributors.
