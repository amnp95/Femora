Full General System
===================

The Full General system solver uses a complete, unoptimized matrix storage scheme. It stores and operates on the entire matrix without any special optimization for sparsity or structure.

Description
-----------

The Full General system:
- Uses full matrix storage (no optimization)
- Suitable for small, dense matrices
- Simple and straightforward implementation
- High memory usage for large problems

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - None
     - 
     - This system solver doesn't take any parameters

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Full General system solver
   fm.analysis.system.create_system("FullGeneral")

Notes
-----

- Simplest matrix storage scheme
- Uses the most memory of all solvers
- Not recommended for large or sparse problems
- Can be useful for educational purposes or debugging
- Best suited for very small problems with dense matrices 