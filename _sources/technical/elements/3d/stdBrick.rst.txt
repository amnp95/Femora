stdBrick
""""""""""""""""""""""""""""

A standard 8-node brick element for 3D continuum modeling.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **b1**
      - Constant body forces in global x direction
      - float
    * - **b2**
      - Constant body forces in global y direction
      - float
    * - **b3**
      - Constant body forces in global z direction
      - float

**Material Compatibility:**
- Compatible with 3D (nDMaterial) type materials

**Degrees of Freedom:**
- 3 DOFs per node

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Element.elementsOpenSees import stdBrickElement
        from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial

        # Create a material first
        material = ElasticIsotropicMaterial(user_name="Concrete", E=30e9, nu=0.2, rho=2400)

        # Create the element
        brick_element = stdBrickElement(
            ndof=3,
            material=material,
            b1=0.0,
            b2=-9.81,  # Gravity in y-direction
            b3=0.0
        )

        # Via Femora
        import femora as fm
         

        # Create material
        concrete = fm.material.create_material(
            material_category="nDMaterial",
            material_type="ElasticIsotropic",
            user_name="Concrete",
            E=30e9,
            nu=0.2,
            rho=2400
        )

        # Create element
        brick = fm.element.create_element(
            element_type="stdBrick",
            ndof=3,
            material="Concrete",
            b1=0.0,
            b2=-9.81,
            b3=0.0
        )