Band General System
===================

The Band General system solver uses a banded matrix storage scheme that stores only the elements within a band around the diagonal. This reduces memory usage for matrices with a regular band structure.

Description
-----------

The Band General system:
- Uses banded matrix storage
- Optimized for matrices with regular bandwidth
- Reduces memory usage compared to full storage
- Efficient for problems with regular mesh patterns

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
    

   # Create a Band General system solver
   fm.analysis.system.create_system("BandGeneral")

Notes
-----

- More efficient than Full General for banded matrices
- Memory usage depends on matrix bandwidth
- Performance depends on the quality of node numbering
- Works well with RCM numbering scheme
- Suitable for medium-sized problems with regular structure
- Not optimal for matrices with irregular sparsity patterns 