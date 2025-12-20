ElasticUniaxialMaterial
"""""""""""""""""""""""""

A uniaxial elastic material with optional damping and different moduli in tension and compression.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **E**
      - Tangent (required)
      - float
    * - **eta**
      - Damping tangent (optional, default=0.0)
      - float
    * - **Eneg**
      - Tangent in compression (optional, default=E)
      - float


.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.Material.materialsOpenSees import ElasticUniaxialMaterial
        elastic_material = ElasticUniaxialMaterial("Steel", E=200e9, eta=0.05, Eneg=200e9)

        # Via Femora
        import femora as fm
         
        fm.material.create_material("uniaxialMaterial", "Elastic", "Steel", E=200e9, eta=0.05, Eneg=200e9)