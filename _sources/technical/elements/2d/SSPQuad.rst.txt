SSPQuad
""""""""""""""""""""""""""""

A Stabilized Single-Point (SSP) quadrilateral element for 2D analysis with enhanced stability.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **Type**
      - Type of element, either "PlaneStrain" or "PlaneStress"
      - string
    * - **Thickness**
      - Thickness of the element in out-of-plane direction
      - float
    * - **b1**
      - Constant body forces in global x direction
      - float
    * - **b2**
      - Constant body forces in global y direction
      - float

**Material Compatibility:**
- Compatible with 2D (nDMaterial) type materials

**Degrees of Freedom:**
- 2 DOFs per node

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Element.elementsOpenSees import SSPQuadElement
        from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial

        # Create a material first
        material = ElasticIsotropicMaterial(user_name="Steel", E=200e9, nu=0.3, rho=7850)

        # Create the element
        quad_element = SSPQuadElement(
            ndof=2,
            material=material,
            Type="PlaneStress",
            Thickness=0.1,
            b1=0.0,
            b2=-9.81  # Gravity in y-direction
        )

        # Via Femora
        import femora as fm
         

        # Create material
        steel = fm.material.create_material(
            material_category="nDMaterial",
            material_type="ElasticIsotropic",
            user_name="Steel",
            E=200e9,
            nu=0.3,
            rho=7850
        )

        # Create element
        quad = fm.element.create_element(
            element_type="SSPQuad",
            ndof=2,
            material="Steel",
            Type="PlaneStress",
            Thickness=0.1,
            b1=0.0,
            b2=-9.81
        )