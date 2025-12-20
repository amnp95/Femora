Profile SPD System
==================

The Profile SPD (Symmetric Positive Definite) system solver uses a skyline storage scheme that stores only the elements from the first non-zero entry in each column up to the diagonal. This can be more efficient than band storage for matrices with irregular profiles.

Description
-----------

The Profile SPD system:
- Uses skyline (profile) matrix storage
- Optimized for symmetric positive definite matrices
- Stores only non-zero elements up to diagonal
- Adapts to irregular matrix profiles
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
    

   # Create a Profile SPD system solver
   fm.analysis.system.create_system("ProfileSPD")

Notes
-----

- More efficient than Band SPD for matrices with irregular profiles
- Memory usage adapts to actual matrix structure
- Requires matrix to be symmetric positive definite
- Performance depends on the quality of node numbering
- Works well with RCM numbering scheme
- Good choice for problems with irregular mesh patterns
- Not suitable for non-symmetric or indefinite matrices 