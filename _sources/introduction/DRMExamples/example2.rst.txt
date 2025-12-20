Example 2: Multi-layer Soil Model with Absorbing Boundaries
===========================================================

Overview
--------

This example demonstrates how to create a larger-scale soil domain with multiple layers and absorbing boundary conditions using Perfectly Matched Layers (PML). The model is designed for wave propagation analysis with domain reduction method (DRM) loading.

The model created in this example consists of:

* Six distinct soil layers with depth-varying properties
* 3D brick elements with elastic-isotropic materials
* Rayleigh damping applied to control dynamic response
* PML absorbing boundaries to prevent wave reflections
* DRM loading applied from an external file

.. figure:: ../images/femora_logo.png
   :width: 600px
   :align: center
   :alt: Multi-layer Soil Model with PML Boundaries

   Conceptual visualization of the multi-layer soil model with absorbing boundaries

Model Description
-----------------

**Soil Domain:**

* 128m × 128m domain (-64m to 64m in both X and Y directions)
* Total depth of 48m
* Six distinct soil layers, each 8m thick
* Properties that vary with depth (density, wave velocities, and damping)

**Materials:**

* Elastic-isotropic materials with properties calculated from wave velocities
* Density (rho) increasing with depth from 2142 to 2162 kg/m³
* Shear wave velocity (Vs) increasing with depth from 353 to 599 m/s
* P-wave velocity (Vp) increasing with depth from 669 to 1135 m/s
* Damping ratio decreasing with depth

**Mesh:**

* Element sizes: 4.0m × 4.0m × 4.0m uniform grid
* 32 × 32 elements in horizontal directions
* 2 elements per layer in vertical direction

**Damping:**

* Frequency-dependent Rayleigh damping
* Target frequencies: f1=3Hz and f2=15Hz
* Damping ratio varying by layer (from 2.1% to 3.0%)

**Boundary Conditions:**

* Perfectly Matched Layer (PML) absorbing boundaries
* 4 element layers in PML
* Rayleigh damping coefficient of 0.95 in PML region

**Loading:**

* Domain Reduction Method (DRM) loading
* Input from external H5DRM file
* Simulation duration: 30 seconds with 0.01s time step

Domain Reduction Method (DRM) Explained
---------------------------------------

The Domain Reduction Method (DRM) is a two-step computational approach for simulating seismic wave propagation in a localized region of interest:

1. **Background Analysis**: First, a large domain is analyzed to capture the regional seismic wave propagation from the source to the site.

2. **Local Analysis**: The results from step 1 are then used as boundary conditions for a smaller domain of interest, allowing for detailed analysis without modeling the entire domain.

Key features and benefits of DRM:

* **Computational Efficiency**: Enables detailed analysis of a small region without the computational cost of modeling the entire wave propagation path from source to site
* **Wave Input Flexibility**: Can input waves from any direction and source mechanism
* **Realistic Boundary Conditions**: Accounts for complex wave propagation effects more accurately than direct force inputs
* **Localized Refinement**: Allows for mesh refinement in the region of interest without needing to refine the entire domain

In this example, DRM is implemented through:

.. code-block:: python

    h5pattern = fm.pattern.create_pattern('h5drm',
                                        filepath='drmload.h5drm',
                                        factor=1.0,
                                        crd_scale=1.0,
                                        distance_tolerance=0.01,
                                        do_coordinate_transformation=1,
                                        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                        origin=[0.0, 0.0, 0.0])
    fm.drm.set_pattern(h5pattern)

The ``h5drm`` file contains pre-computed wave field information that is applied to the DRM boundary elements, effectively injecting the desired seismic waves into the computational domain.

Perfectly Matched Layer (PML) Explained
---------------------------------------

PML is an advanced absorbing boundary technique developed to prevent artificial reflections of waves at computational domain boundaries:

.. code-block:: python

    fm.drm.addAbsorbingLayer(numLayers=4,
                            numPartitions=8,
                            partitionAlgo="kd-tree",
                            geometry="Rectangular",
                            rayleighDamping=0.95,
                            matchDamping=False,
                            type="PML")

Key features of PML:

* **Wave Absorption**: PML gradually attenuates waves as they enter the boundary region, preventing them from reflecting back into the domain
* **Angle Independence**: Designed to have minimal reflections regardless of wave incidence angle or frequency content
* **Computational Efficiency**: More efficient than extending the physical domain to prevent reflections
* **Implementation Parameters**:
  - ``numLayers``: Controls thickness of the absorbing region (4 elements in this example)
  - ``rayleighDamping``: Sets the damping coefficient in the PML region (0.95 in this example)

PML works by creating an artificial absorbing material whose damping properties gradually increase with distance from the computational domain boundary. This gradual transition ensures waves are absorbed without creating spurious reflections at the PML interface.

Absorbing Layer Parameters in Detail
------------------------------------

The ``addAbsorbingLayer`` method creates boundary regions that absorb outgoing waves to prevent them from reflecting back into the computational domain. Let's examine each parameter in detail:

1. **numLayers** (int):

   * Defines the thickness of the absorbing boundary in terms of element layers
   * More layers typically provide better absorption but increase computational cost
   * Recommended values range from 3-8 layers, with 4 being a good balance in many cases
   * In this example, 4 layers effectively absorb most seismic waves while maintaining efficiency

2. **numPartitions** (int):

   * Controls how the boundary regions are divided for parallel processing
   * Higher values can improve load balancing but may increase overhead
   * Value should typically scale with the number of available CPU cores
   * In this example, 8 partitions are used for efficient parallel computation

3. **partitionAlgo** (str):

   * Specifies the algorithm used to divide the model for parallel processing
   * Currently implemented options:

     * "kd-tree": Spatially balanced partitioning (used in this example)
     * "metis": Graph-based partitioning for complex geometries

   * "kd-tree" is generally recommended for soil models as it provides good load balancing

4. **geometry** (str):

   * Defines the shape of the computational domain and absorbing boundaries
   * Currently only "Rectangular" is fully implemented
   * Future implementations will include:

     * "Cylindrical": For cylindrical domains
     * "Spherical": For spherical domains

   * The "Rectangular" option is appropriate for this layered soil model with a rectangular footprint

5. **rayleighDamping** (float):

   * Controls the strength of the Rayleigh damping in the absorbing layer
   * Ranges from 0.0 (no damping) to 1.0 (maximum damping)
   * Higher values (like 0.95 in this example) absorb more energy but may cause numerical issues
   * This parameter sets a scalar multiplier for the damping coefficients that increases with distance into the boundary
   * The damping strength gradually increases from the inner boundary (computational domain) to the outer boundary

6. **matchDamping** (bool):

   * When True, matches the damping properties between the computational domain and absorbing layers
   * When False (as in this example), uses the damping properties defined specifically for the absorbing layer
   * Setting to False allows for stronger damping in the absorbing layers than in the computational domain
   * This parameter is particularly relevant when the computational domain already has some level of damping

7. **type** (str):

   * Specifies the type of absorbing boundary to use
   * Currently implemented options:

     * "PML": Perfectly Matched Layer (used in this example)
     * "Rayleigh": Standard Rayleigh damping layer
     * "ASDA": Combined PML and Rayleigh approach

   **Comparing Absorbing Layer Types:**

   * **PML** (Perfectly Matched Layer):

     * More effective at absorbing waves at any angle of incidence
     * Better performance for complex wave fields
     * More computationally intensive
     * Preferred for high-precision wave propagation simulations

   * **Rayleigh** damping layers:

     * Simpler implementation
     * Less computationally demanding
     * More numerically stable than PML
     * May require more layers to achieve the same absorption quality
     * Recommended for models with stability concerns

   * **ASDA** (Combined approach):

     * Combines benefits of both PML and Rayleigh approaches
     * Can provide better stability than pure PML
     * More computationally intensive than Rayleigh alone

In this example, PML is chosen because it provides superior absorption characteristics for seismic wave propagation problems, particularly when waves may approach the boundary at various angles. However, if you experience numerical instabilities, switching to "Rayleigh" type may help stabilize the solution at the cost of some absorption efficiency.

Frequency Rayleigh Damping in Femora
------------------------------------

In this example, each soil layer is assigned its own frequency-dependent Rayleigh damping:

.. code-block:: python

    damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=3, f2=15)

Frequency Rayleigh damping is a more intuitive approach to specifying damping than conventional Rayleigh damping. Instead of directly setting the mass and stiffness proportional coefficients (αₘ and βₖ), users can specify:

1. **dampingFactor**: The target damping ratio ξ (between 0 and 1) - in our example, this varies by layer (xi_s)
2. **f1**: Lower bound target frequency in Hz (3 Hz in this model)
3. **f2**: Upper bound target frequency in Hz (15 Hz in this model)

**How Frequency Rayleigh Damping Works:**

Rayleigh damping combines mass-proportional and stiffness-proportional damping through the equation:

.. math::

    [C] = \alpha_M [M] + \beta_K [K]

Where:
- [C] is the damping matrix
- [M] is the mass matrix
- [K] is the stiffness matrix
- αₘ and βₖ are the mass and stiffness proportional coefficients

Traditional Rayleigh damping requires specifying αₘ and βₖ directly, which is not intuitive. In frequency Rayleigh damping, Femora automatically calculates these coefficients from more practical inputs:

.. math::

    \omega_1 = 2\pi f_1, \quad \omega_2 = 2\pi f_2

    \alpha_M = \frac{2\omega_1\omega_2}{\omega_1 + \omega_2}\xi

    \beta_K = \frac{2}{\omega_1 + \omega_2}\xi

This approach is implemented in Femora because:

* It's more intuitive for geotechnical engineers who think in terms of frequency ranges and damping ratios
* It automatically ensures the damping ratio equals the target value exactly at the two specified frequencies
* It simplifies the process of creating realistic energy dissipation in dynamic models
* It allows for frequency-calibrated damping that properly accounts for the predominant frequencies in seismic analysis

**Mathematical Background:**

The damping ratio at any frequency ω is given by:

.. math::

    \xi(\omega) = \frac{\alpha_M}{2\omega} + \frac{\beta_K\omega}{2}

By selecting two target frequencies (ω₁ and ω₂) and setting the damping ratio to the desired value (ξ) at these frequencies, we can solve for the Rayleigh coefficients αₘ and βₖ. This calibration ensures that the damping ratio is exactly ξ at frequencies f₁ and f₂, and varies gradually for other frequencies.

Region Assignment in Layered Soil Model
---------------------------------------

In this example, each soil layer is assigned to its own region with specific damping properties:

.. code-block:: python

    # Create frequency-dependent damping for this layer
    damp = fm.damping.create_damping("frequency rayleigh", dampingFactor=xi_s, f1=3, f2=15)
    
    # Create region with this layer's specific damping
    reg = fm.region.create_region("elementRegion", damping=damp)
    
    # Assign the region when creating the mesh part for this layer
    fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                            user_name=f"Layer{layer['layer']}",
                            element=ele,
                            region=reg,
                            # ... other parameters ...)

**Region Assignment Process:**

1. For each layer in the soil profile, we:

   * Create a layer-specific damping object with damping ratio corresponding to that layer
   * Create a new element region and associate it with this damping
   * Assign this region to the mesh part when creating the layer geometry

This workflow allows for:

1. **Layer-specific damping**: Each soil layer can have different damping properties based on its material characteristics
2. **Depth-dependent behavior**: Properties can vary with depth, reflecting real soil conditions
3. **Independent energy dissipation**: Each region's response to dynamic loading is calibrated separately

Global Region and Region Management in Femora
---------------------------------------------

All Femora models have a "global region" that serves as the default assignment when no explicit region is provided. 

**Region System Architecture in Femora:**

Femora implements a sophisticated region management system with these key components:

1. **Global Region**: 

   * Automatically created when Femora initializes
   * Has tag 0 and name "GlobalRegion"
   * Serves as a fallback when no specific region is assigned
   * Can have its own damping properties that apply model-wide

2. **Element Regions**:

   * Created explicitly with ``fm.region.create_region("elementRegion", ...)``
   * Can have specific damping assigned
   * Can be associated with specific elements or element groups

3. **Region Assignment Rules**:

   * When creating a mesh part, a region must be specified or the global region is used
   * The statement ``region=reg`` explicitly assigns a specific region to that mesh part
   * Without this assignment, all elements would use the global region's properties

**Implementation Details:**

The global region is implemented through a singleton pattern to ensure there is always exactly one global region with tag 0:

.. code-block:: python

    def __new__(cls, tag=None, damping: Type[DampingBase] = None):
        if tag in cls._regions:
            return cls._regions[tag]
        
        if tag == 0:
            cls._global_region = super().__new__(cls)
            cls._regions[0] = cls._global_region
            return cls._global_region

When creating a mesh part without specifying a region:

.. code-block:: python

    # This would implicitly use the global region
    fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                            user_name=f"SomeLayer",
                            element=ele)

In our soil model example, explicit region creation ensures that each soil layer has its own properly configured damping behavior rather than using global defaults. If we had omitted the region assignment:

.. code-block:: python

    # Without explicit region, would use global region
    fm.meshPart.create_mesh_part("Volume mesh", "Uniform Rectangular Grid",
                            user_name=f"Layer{layer['layer']}",
                            element=ele)

Then all soil layers would have inherited the same damping properties from the global region, which would not accurately represent the depth-varying damping characteristics of real soil profiles.

This region-based approach allows Femora to implement element-level, region-level, or global-level damping in a consistent way, giving users flexibility to model complex systems with varying properties in different zones while maintaining a simple default behavior through the global region.

Step-by-Step Code Walkthrough
-----------------------------

Let's examine the key components of the Example 2 code:

1. **Setting up the Environment and Layer Properties**:

   .. code-block:: python

       import femora as fm
       import os

       # Change directory to the current file's location
       os.chdir(os.path.dirname(os.path.abspath(__file__)))

       # Layer properties as a dictionary
       layers = [
           {"layer": 1, "rho": 2142.0500, "vp": 669.0500, "vs": 353.1000, "xi_s": 0.0296, "xi_p": 0.0148, "thickness": 8},
           # ... more layers
       ]

   The code begins by importing the Femora library and defining six soil layers with varying properties:
   
   - ``rho``: Material density (kg/m³)
   - ``vp``: P-wave velocity (m/s)
   - ``vs``: S-wave velocity (m/s)
   - ``xi_s``, ``xi_p``: Damping ratios for shear and pressure waves
   - ``thickness``: Layer thickness (8m each)

2. **Defining Rayleigh Damping Parameters**:

   .. code-block:: python
   
       pi = 3.1415926
       f1 = 15; # Hz
       f2 = 3; # Hz
       w1 = 2*pi*f1
       w2 = 2*pi*f2
   
   Rayleigh damping requires two target frequencies for calibration. These frequencies (3Hz and 15Hz) cover the primary frequency range of interest for seismic analysis.

3. **Creating the Soil Layers**:

   .. code-block:: python

       index = 0
       for layer in layers[::-1]:
           # Calculate elastic properties from wave velocities
           vp_vs_ratio = (vp / vs) ** 2
           nu  = (vp_vs_ratio - 2) / (2 * (vp_vs_ratio - 1))  # Poisson's ratio
           E = 2 * rho * (vs ** 2) * (1 + nu)  # Young's modulus
           
           # Create material, element, and damping objects
           mat = fm.material.create_material("nDMaterial", "ElasticIsotropic",
                                       user_name=f"Layer{layer['layer']}",
                                       E=E, nu=nu, rho=rho)
           # ... create elements and mesh

   This loop processes layers from bottom to top and:
   
   1. Converts wave velocities to mechanical properties (E and ν)
   2. Creates elastic material models
   3. Applies frequency-dependent Rayleigh damping
   4. Creates a uniform 3D mesh grid for each layer

4. **Model Assembly and Boundary Conditions**:

   .. code-block:: python

       # Create a list of mesh parts
       mesh_parts = []
       for layer in layers:
           mesh_parts.append(f"Layer{layer['layer']}")

       fm.assembler.create_section(mesh_parts, num_partitions=4)
       fm.assembler.Assemble()

       # Add absorbing boundary layers (PML)
       fm.drm.addAbsorbingLayer(numLayers=4,
                               numPartitions=8,
                               partitionAlgo="kd-tree",
                               geometry="Rectangular",
                               rayleighDamping=0.95,
                               matchDamping=False,
                               type="PML",
                               )

   After creating all layers, the code assembles all mesh parts and adds PML absorbing boundaries.

5. **Loading and Analysis Setup**:

   .. code-block:: python
   
       h5pattern = fm.pattern.create_pattern('h5drm',
                                           filepath='drmload.h5drm',
                                           factor=1.0,
                                           crd_scale=1.0,
                                           distance_tolerance=0.01,
                                           do_coordinate_transformation=1,
                                           transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
                                           origin=[0.0, 0.0, 0.0])
       fm.drm.set_pattern(h5pattern)
       fm.drm.createDefaultProcess(finalTime=30, dT=0.01)
       fm.export_to_tcl(filename="model.tcl")
       fm.gui()
   
   Finally, the code sets up DRM loading from an H5DRM file, configures the time-domain analysis (30s duration with 0.01s steps), exports the model to a TCL file for analysis, and launches the Femora GUI for visualization.

Code Access
-----------

The full source code for this example is available in the Femora repository:

.. literalinclude:: ../../../examples/DRM/Example2/femoramodel.py
   :language: python
   :caption: Example 2 - Multi-layer Soil Model with Absorbing Boundaries
   :name: example2-code

* Example directory: ``examples/Example2/``
* Python script: ``examples/Example2/femoramodel.py``
* Data file: ``drmload.h5drm`` (required for running the example)

Key Concepts Demonstrated
-------------------------

* Creating a multi-layer soil model with depth-varying properties
* Calculating material properties from wave velocities
* Implementing frequency-dependent Rayleigh damping
* Setting up PML absorbing boundaries to prevent wave reflections
* Applying DRM loading for seismic wave propagation analysis
* Organizing a large-scale soil domain for efficient computation
* Assigning regions with specific damping properties
* Understanding global region functionality in Femora