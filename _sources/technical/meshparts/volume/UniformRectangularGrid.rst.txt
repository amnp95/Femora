Uniform Rectangular Grid
========================

The ``Uniform Rectangular Grid`` mesh part type (implemented as ``StructuredRectangular3D`` in the code) creates a three-dimensional rectangular grid mesh with uniform spacing in each direction. It is one of the most commonly used mesh types for creating simple rectangular domains with regular spacing.

Parameters
----------

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter Name
     - Description
   * - X Min
     - Minimum X coordinate (float)
   * - X Max
     - Maximum X coordinate (float)
   * - Y Min
     - Minimum Y coordinate (float)
   * - Y Max
     - Maximum Y coordinate (float)
   * - Z Min
     - Minimum Z coordinate (float)
   * - Z Max
     - Maximum Z coordinate (float)
   * - Nx Cells
     - Number of cells in X direction (integer)
   * - Ny Cells
     - Number of cells in Y direction (integer)
   * - Nz Cells
     - Number of cells in Z direction (integer)

All parameters are required.



Compatible Elements
-------------------

This mesh part type is compatible with the following elements:

- stdBrick
- bbarBrick
- SSPbrick
- PML3D

Usage Example
-------------

The following example demonstrates how to create a simple 3D rectangular domain using the Uniform Rectangular Grid mesh part type:

.. code-block:: python

   import femora as fm
   
   # Create a Femora instance
    
   
   # Create a material
   material = fm.material.create_material(
       material_category="nDMaterial", 
       material_type="ElasticIsotropic", 
       user_name="Soil",
       E=30e3, 
       nu=0.3, 
       rho=1.8e-9
   )
   
   # Create an element using this material
   element = fm.element.create_element(
       element_type="stdBrick", 
       ndof=3, 
       material=material, 
       b1=0, 
       b2=0, 
       b3=-9.81*1.8e-9
   )
   
   # Create a region with damping
   damping = fm.damping.create_damping("frequency rayleigh", dampingFactor=0.05, f1=1, f2=10)
   region = fm.region.create_region("elementRegion", damping=damping)
   
   # Create the uniform rectangular grid mesh part
   fm.meshPart.create_mesh_part(
       "Volume mesh", 
       "Uniform Rectangular Grid", 
       user_name="SoilBlock", 
       element=element, 
       region=region, 
       **{
           'X Min': -50, 'X Max': 50,
           'Y Min': -50, 'Y Max': 50, 
           'Z Min': -20, 'Z Max': 0,
           'Nx Cells': 10, 'Ny Cells': 10, 'Nz Cells': 5
       }
   )

Notes
-----

- Used for creating regular 3D meshes with equal spacing in each direction
- Suitable for simple geometries where uniform mesh density is desired
- Efficient for problems requiring regular grid structures
- Consider mesh density requirements for accuracy (number of cells in each direction)
- The same element type and material will be applied to all cells in the mesh
