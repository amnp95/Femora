Custom Rectangular Grid
=======================

The ``Custom Rectangular Grid`` mesh part type (implemented as ``CustomRectangularGrid3D`` in the code) creates a three-dimensional rectangular grid mesh with custom spacing in each direction. Unlike the Uniform Rectangular Grid, this mesh type allows you to specify the exact coordinates of grid points in each direction, enabling non-uniform spacing.

Parameters
----------

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter Name
     - Description
   * - x_coords
     - List of X coordinates (comma-separated list of float values)
   * - y_coords
     - List of Y coordinates (comma-separated list of float values)
   * - z_coords
     - List of Z coordinates (comma-separated list of float values)

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

The following example demonstrates how to create a 3D rectangular domain with custom spacing using the Custom Rectangular Grid mesh part type:

.. code-block:: python

   import femora as fm
   
   # Create a Femora instance
    
   
   # Create a material
   material = fm.material.create_material(
       material_category="nDMaterial", 
       material_type="ElasticIsotropic", 
       user_name="Rock",
       E=50e3, 
       nu=0.25, 
       rho=2.5e-9
   )
   
   # Create an element using this material
   element = fm.element.create_element(
       element_type="stdBrick", 
       ndof=3, 
       material=material, 
       b1=0, 
       b2=0, 
       b3=-9.81*2.5e-9
   )
   
   # Create a region with damping
   damping = fm.damping.create_damping("frequency rayleigh", dampingFactor=0.03, f1=2, f2=15)
   region = fm.region.create_region("elementRegion", damping=damping)
   
   # Create the custom rectangular grid mesh part with non-uniform spacing
   fm.meshPart.create_mesh_part(
       "Volume mesh", 
       "Custom Rectangular Grid", 
       user_name="RockFormation", 
       element=element, 
       region=region, 
       **{
           # Finer spacing near the center in X direction
           'x_coords': "-50,-40,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,40,50",
           # Uniform spacing in Y direction
           'y_coords': "-50,-40,-30,-20,-10,0,10,20,30,40,50",
           # Finer spacing near the surface in Z direction 
           'z_coords': "-20,-18,-16,-14,-12,-10,-8,-6,-4,-2,-1,-0.5,0"
       }
   )

Notes
-----

- Used for creating 3D meshes with variable spacing in each direction
- Suitable for problems requiring non-uniform mesh density
- Useful when specific grid point locations are needed
- Allows for refinement in areas of interest without increasing the overall mesh density
- Consider gradual transitions in spacing for better numerical results

