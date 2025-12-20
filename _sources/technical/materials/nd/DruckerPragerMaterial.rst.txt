DruckerPragerMaterial
""""""""""""""""""""""""""""

A multi-dimensional material model for Drucker-Prager plasticity defined by:

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **k**
      - Bulk modulus (required)
      - float
    * - **G**
      - Shear modulus (required)
      - float
    * - **sigmaY**
      - Yield stress (required)
      - float
    * - **rho**
      - Frictional strength parameter (required)
      - float
    * - **rhoBar**
      - Controls evolution of plastic volume change: 0 ≤ rhoBar ≤ rho (default = rho)
      - float
    * - **Kinf**
      - Nonlinear isotropic strain hardening parameter: Kinf ≥ 0 (default = 0.0)
      - float
    * - **Ko**
      - Nonlinear isotropic strain hardening parameter: Ko ≥ 0 (default = 0.0)
      - float
    * - **delta1**
      - Nonlinear isotropic strain hardening parameter: delta1 ≥ 0 (default = 0.0)
      - float
    * - **delta2**
      - Tension softening parameter: delta2 ≥ 0 (default = 0.0)
      - float
    * - **H**
      - Linear strain hardening parameter: H ≥ 0 (default = 0.0)
      - float
    * - **theta**
      - Controls relative proportions of isotropic and kinematic hardening: 0 ≤ theta ≤ 1 (default = 0.0)
      - float
    * - **density**
      - Mass density of the material (default = 0.0)
      - float
    * - **atmPressure**
      - Atmospheric pressure for updating elastic bulk and shear moduli (default = 101 kPa)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Material.materialsOpenSees import DruckerPragerMaterial
        dp_material = DruckerPragerMaterial(
            user_name="Sand",
            k=8.33e6,      # Bulk modulus (Pa)
            G=3.85e6,      # Shear modulus (Pa)
            sigmaY=3000,   # Yield stress (Pa)
            rho=0.45,      # Frictional strength parameter
            rhoBar=0.4,    # Plastic volume evolution control
            Kinf=0.0,      # Isotropic hardening parameter
            Ko=0.0,        # Isotropic hardening parameter
            delta1=0.0,    # Isotropic hardening parameter
            delta2=0.0,    # Tension softening parameter
            H=500,         # Linear hardening parameter
            theta=0.5,     # Isotropic/kinematic hardening proportion
            density=1650   # Mass density (kg/m³)
        )

        or 

        # Via Femora
        import femora as fm
         
        fm.material.create_material(
            material_category="nDMaterial",
            material_type="DruckerPrager", 
            user_name="Sand", 
            k=8.33e6, 
            G=3.85e6, 
            sigmaY=3000, 
            rho=0.45,
            H=500,
            density=1650
        )

