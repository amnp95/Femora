ElasticIsotropicMaterial
""""""""""""""""""""""""""""

A 3D isotropic elastic material defined by:

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **E**
      - Young's modulus (required)
      - float
    * - **nu**
      - Poisson's ratio (required)
      - float
    * - **rho**
      - Mass density (default = 0.0)
      - float


.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Material.materialsOpenSees import ElasticIsotropicMaterial
        elastic_material = ElasticIsotropicMaterial("Concrete", E=30e6, nu=0.2, rho=2400)

        or 

        # Via Femora
        import femora as fm
         
        fm.material.create_material("nDMaterial", "ElasticIsotropic", "Concrete", E=30e6, nu=0.2, rho=2400)