Geometric Rectangular Grid
==========================

The ``Geometric Rectangular Grid`` mesh part type (implemented as ``GeometricStructuredRectangular3D`` in the code) creates a three-dimensional rectangular grid mesh with geometric spacing in each direction. This mesh type allows you to create a grid with progressively increasing or decreasing cell sizes based on geometric ratios, which is useful for creating refined meshes in areas of interest.

Parameters
----------

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter Name
     - Description
   * - x_min
     - Minimum X coordinate (float)
   * - x_max
     - Maximum X coordinate (float)
   * - y_min
     - Minimum Y coordinate (float)
   * - y_max
     - Maximum Y coordinate (float)
   * - z_min
     - Minimum Z coordinate (float)
   * - z_max
     - Maximum Z coordinate (float)
   * - nx
     - Number of cells in X direction (integer)
   * - ny
     - Number of cells in Y direction (integer)
   * - nz
     - Number of cells in Z direction (integer)
   * - x_ratio
     - Ratio of cell increment in X direction (float, optional, default=1)
   * - y_ratio
     - Ratio of cell increment in Y direction (float, optional, default=1)
   * - z_ratio
     - Ratio of cell increment in Z direction (float, optional, default=1)

Required parameters are: x_min, x_max, y_min, y_max, z_min, z_max, nx, ny, and nz.
Optional parameters are: x_ratio, y_ratio, and z_ratio, which default to 1.0 if not specified.



Compatible Elements
-------------------

This mesh part type is compatible with the following elements:

- stdBrick
- bbarBrick
- SSPbrick
- PML3D

Usage Example
-------------

The following example demonstrates how to create a 3D rectangular domain with geometric spacing using the Geometric Rectangular Grid mesh part type:

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
   
   # Create the geometric rectangular grid mesh part
   # Cells will progressively get larger in the z-direction (from surface down)
   fm.meshPart.create_mesh_part(
       "Volume mesh", 
       "Geometric Rectangular Grid", 
       user_name="SoilLayer", 
       element=element, 
       region=region, 
       **{
           'x_min': -50, 'x_max': 50,
           'y_min': -50, 'y_max': 50, 
           'z_min': -20, 'z_max': 0,
           'nx': 10, 'ny': 10, 'nz': 8,
           'x_ratio': 1.0,   # Uniform spacing in x-direction
           'y_ratio': 1.0,   # Uniform spacing in y-direction
           'z_ratio': 1.25   # Each cell is 1.25x larger than the previous one in z-direction
       }
   )

Geometric Ratio Effect
----------------------

The geometric ratio parameters control how cell sizes vary across the mesh:

- **Ratio = 1.0**: Uniform spacing (cells have equal size)
- **Ratio > 1.0**: Cell size increases in the positive direction (cells get larger)
- **Ratio < 1.0**: Cell size decreases in the positive direction (cells get smaller)

For example, with a ratio of 1.25 in the z-direction, each cell will be 1.25 times larger than the previous cell when moving from z_min to z_max.

Notes
-----

- Used for creating 3D meshes with variable spacing in each direction based on geometric progression
- Suitable for problems requiring refined mesh in specific regions
- Useful for boundary layer meshing or capturing gradients near interfaces
- More efficient than uniform grids when different resolution is needed in different regions
- Consider the appropriate ratio values for your specific application needs

