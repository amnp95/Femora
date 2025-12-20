SuperLU System
==============

The SuperLU system solver is a high-performance sparse direct solver that uses the SuperLU library. It is designed for large sparse matrices and can handle both symmetric and non-symmetric systems efficiently.

Description
-----------

The SuperLU system:
- Uses sparse matrix storage
- Implements supernodal LU factorization
- Optimized for large sparse matrices
- Handles both symmetric and non-symmetric systems
- Automatically detects and exploits matrix structure

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
    

   # Create a SuperLU system solver
   fm.analysis.system.create_system("SuperLU")

Notes
-----

- High-performance sparse direct solver
- Memory usage scales with matrix sparsity
- Very efficient for large sparse problems
- Can handle non-symmetric matrices
- Good choice for general-purpose sparse solving
- Particularly effective with AMD numbering scheme
- May require more memory than iterative solvers 