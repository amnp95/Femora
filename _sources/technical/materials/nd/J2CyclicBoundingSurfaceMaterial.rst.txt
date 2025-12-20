J2CyclicBoundingSurfaceMaterial
"""""""""""""""""""""""""""""""""

A material model that implements the J2 Cyclic Bounding Surface plasticity model, useful for modeling cyclical response in soil and other materials with complex hardening behavior.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **G**
      - Shear modulus (required)
      - float
    * - **K**
      - Bulk modulus (required)
      - float
    * - **Su**
      - Undrained shear strength (required)
      - float
    * - **Den**
      - Mass density (required)
      - float
    * - **h**
      - Hardening parameter (required)
      - float
    * - **m**
      - Hardening exponent (required)
      - float
    * - **h0**
      - Initial hardening parameter (required)
      - float
    * - **chi**
      - Initial damping (viscous). chi = 2*dr_o/omega (dr_o = damping ratio at zero strain, omega = angular frequency) (required)
      - float
    * - **beta**
      - Integration variable (0 = explicit, 1 = implicit, 0.5 = midpoint rule) (default = 0.5)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Material.materialsOpenSees import J2CyclicBoundingSurfaceMaterial
        j2_material = J2CyclicBoundingSurfaceMaterial(
            user_name="Clay",
            G=1.3e6,       # Shear modulus (Pa)
            K=2.6e6,       # Bulk modulus (Pa)
            Su=18000,      # Undrained shear strength (Pa)
            Den=1800,      # Mass density (kg/m³)
            h=1.5,         # Hardening parameter
            m=0.6,         # Hardening exponent
            h0=0.5,        # Initial hardening parameter
            chi=0.1,       # Initial damping
            beta=0.5       # Integration variable (midpoint rule)
        )

        or 

        # Via Femora
        import femora as fm
         
        fm.material.create_material(
            material_category="nDMaterial",
            material_type="J2CyclicBoundingSurface", 
            user_name="Clay", 
            G=1.3e6, 
            K=2.6e6, 
            Su=18000, 
            Den=1800, 
            h=1.5, 
            m=0.6, 
            h0=0.5, 
            chi=0.1
        )