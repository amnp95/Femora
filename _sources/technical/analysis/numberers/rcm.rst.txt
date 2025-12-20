RCM Numberer
============

The Reverse Cuthill-McKee (RCM) numberer implements the RCM algorithm to reduce the bandwidth of the system matrix by optimizing the equation numbering scheme.

Description
-----------

The RCM numberer:
- Uses graph theory to minimize matrix bandwidth
- Reorders DOFs to create a more compact matrix structure
- Reduces memory requirements and computational cost
- Implemented as a singleton to ensure consistent numbering across the model

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
     - This numberer doesn't take any parameters

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Get an RCM numberer
   fm.analysis.numberer.get_numberer("RCM")

Notes
-----

- Optimizes matrix bandwidth through node reordering
- Particularly effective for problems with regular mesh patterns
- Can significantly reduce memory requirements
- May require more setup time than Plain numberer
- Recommended for medium to large-scale problems
- Especially beneficial when using direct solvers 