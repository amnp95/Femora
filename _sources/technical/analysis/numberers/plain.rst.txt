Plain Numberer
==============

The Plain numberer is the simplest equation numbering scheme that assigns equation numbers to degrees of freedom (DOFs) based on the order in which nodes are created in the model.

Description
-----------

The Plain numberer:
- Assigns equation numbers sequentially based on node creation order
- Does not attempt to optimize matrix structure
- Is suitable for small problems or when matrix structure is not a concern
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
    

   # Get a Plain numberer
   fm.analysis.numberer.get_numberer("Plain")

Notes
-----

- Simplest and fastest numbering scheme to set up
- Does not optimize matrix bandwidth or profile
- May result in larger computational costs during analysis
- Best suited for small problems or educational purposes
- Not recommended for large-scale problems where matrix structure affects performance 