UMFPACK System
==============

The UMFPACK system solver is a high-performance sparse direct solver that uses the UMFPACK library. It is particularly effective for unsymmetric sparse matrices and employs sophisticated ordering and pivoting strategies.

Description
-----------

The UMFPACK system:
- Uses sparse matrix storage
- Implements multifrontal LU factorization
- Optimized for unsymmetric sparse matrices
- Features advanced pivoting strategies
- Provides robust handling of ill-conditioned matrices

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``lvalue_fact``
     - float
     - Factor for L-value pivoting threshold (optional)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a UMFPACK system solver with default settings
   fm.analysis.system.create_system("Umfpack")

   # Create a UMFPACK system solver with custom L-value factor
   fm.analysis.system.create_system("Umfpack", lvalue_fact=10.0)

Notes
-----

- High-performance sparse direct solver
- Particularly effective for unsymmetric matrices
- Robust numerical stability through pivoting
- Memory usage scales with matrix sparsity
- Good choice for ill-conditioned problems
- Works well with AMD numbering scheme
- May require more memory than iterative solvers 