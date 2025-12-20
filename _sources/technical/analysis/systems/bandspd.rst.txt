Band SPD System
===============

The Band SPD (Symmetric Positive Definite) system solver is optimized for symmetric positive definite matrices with a banded structure. It uses only half the band storage of Band General and specialized algorithms for SPD matrices.

Description
-----------

The Band SPD system:
- Uses symmetric banded matrix storage
- Optimized for symmetric positive definite matrices
- Reduces memory usage by storing only half the band
- Uses specialized Cholesky factorization

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
    

   # Create a Band SPD system solver
   fm.analysis.system.create_system("BandSPD")

Notes
-----

- More efficient than Band General for SPD matrices
- Uses approximately half the memory of Band General
- Requires matrix to be symmetric positive definite
- Performance depends on the quality of node numbering
- Works well with RCM numbering scheme
- Common choice for linear elastic analysis
- Not suitable for non-symmetric or indefinite matrices 