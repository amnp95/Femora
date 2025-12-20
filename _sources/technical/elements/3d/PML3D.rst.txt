PML3D
""""""""""""""""""""""""""""

A Perfectly Matched Layer (PML) element for absorbing waves at domain boundaries in 3D analysis.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **PML_Thickness**
      - Thickness of the PML layer
      - float
    * - **meshType**
      - Type of mesh for the PML layer (1:"General", 2:"Box")
      - string
    * - **meshTypeParameters**
      - Parameters for the mesh type (comma separated)
      - string
    * - **gamma**
      - Newmark integration parameter (default=1./2.)
      - float
    * - **beta**
      - Newmark integration parameter (default=1./4.)
      - float
    * - **eta**
      - Newmark integration parameter (default=1./12.)
      - float
    * - **ksi**
      - Newmark integration parameter (default=1./48.)
      - float
    * - **m**
      - Newmark integration parameter (default=2.0)
      - float
    * - **R**
      - Newmark integration parameter (default=1e-8)
      - float
    * - **Cp**
      - Newmark integration parameter (optional)
      - float
    * - **alpha0**
      - PML parameter (optional)
      - float
    * - **beta0**
      - PML parameter (optional)
      - float

**Material Compatibility:**
- Compatible with 3D (nDMaterial) type materials that are ElasticIsotropic

**Degrees of Freedom:**
- 9 DOFs per node

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Element.elementsOpenSees import PML3DElement
        from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial

        # Create a material first
        material = ElasticIsotropicMaterial(user_name="Soil", E=5e7, nu=0.25, rho=1800)

        # Create the element
        pml_element = PML3DElement(
            ndof=9,
            material=material,
            PML_Thickness=2.0,
            meshType="Box",
            meshTypeParameters="0.0, 0.0, 0.0, 10.0, 10.0, 10.0",
            gamma=0.5,
            beta=0.25,
            eta=1/12,
            ksi=1/48,
            m=2.0,
            R=1e-8
        )

        # Via femora
        import femora as fm
         

        # Create material
        soil = fm.material.create_material(
            material_category="nDMaterial",
            material_type="ElasticIsotropic",
            user_name="Soil",
            E=5e7,
            nu=0.25,
            rho=1800
        )

        # Create element
        pml = fm.element.create_element(
            element_type="PML3D",
            ndof=9,
            material="Soil",
            PML_Thickness=2.0,
            meshType="Box",
            meshTypeParameters="0.0, 0.0, 0.0, 10.0, 10.0, 10.0",
            gamma=0.5,
            beta=0.25,
            eta=1/12,
            ksi=1/48,
            m=2.0,
            R=1e-8
        )