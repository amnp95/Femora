DRM
---------------------------------

Understanding the DRM Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``DRM`` (Domain Reduction Method) component is a specialized part of the Femora library designed for seismic wave propagation analysis. It provides functionality for implementing the Domain Reduction Method, which is used to efficiently model seismic wave propagation in large domains by reducing the computational domain size.

The DRM component provides functionality to:
- Create default analysis processes for DRM simulations
- Add absorbing layers to the model boundary
- Configure proper boundary conditions for wave propagation
- Set up appropriate patterns and recorders
- Manage the integration of DRM with other analysis components

Domain Reduction Method is particularly useful for:
- Seismic wave propagation analysis
- Site-specific earthquake simulations
- Soil-structure interaction problems
- Analysis of wave scattering effects

Accessing the DRM Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DRM component can only be accessed through the Femora class's analysis.drm property:

.. code-block:: python
   
   import Femora as fm
   
   # Create a Femora instance
    
   
   # Access the DRM component through the analysis.drm property
   fm.analysis.drm.createDefaultProcess(dT=0.01, finalTime=10.0)

How DRM Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Domain Reduction Method allows efficient modeling of seismic wave propagation by:

1. **Domain Reduction**: Reducing the computational domain size by focusing on a specific region of interest
2. **Wave Propagation**: Properly propagating seismic waves from a source to the structure
3. **Absorbing Boundaries**: Preventing artificial wave reflections at domain boundaries
4. **Efficient Analysis**: Enabling more detailed analysis of the region of interest

The DRM component in Femora provides tools to set up:

1. **Absorbing Layers**: Add PML (Perfectly Matched Layer) or Rayleigh-damped absorbing boundaries
2. **Analysis Process**: Create preconfigured analysis processes for DRM simulations
3. **H5DRM Patterns**: Configure special loading patterns for the DRM method
4. **Boundary Conditions**: Set appropriate boundary conditions for wave propagation

Technical Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DRM component is implemented as a singleton class to ensure consistent state throughout an analysis. This means that only one instance of the DRM class exists at any time, accessible through the Femora's analysis property.

The implementation includes several key aspects:

1. **Singleton Pattern**: The DRM class uses a singleton pattern to maintain a single, consistent state across all references:

   .. code-block:: python
   
      def __new__(cls, *args, **kwargs):
          if cls._instance is None:
              cls._instance = super(DRM, cls).__new__(cls)
              cls._instance._initialized = False
          return cls._instance

2. **H5DRM Pattern Integration**: The component integrates with specialized H5DRM patterns for applying seismic loads:

   .. code-block:: python
   
      def set_pattern(self, pattern: H5DRMPattern):
          self.h5drmpattern = pattern

3. **Multi-Stage Analysis Process**: The DRM analysis process typically involves multiple stages:
   - Gravity equilibrium (elastic phase)
   - Gravity equilibrium (plastic phase)
   - Dynamic analysis with seismic inputs

4. **Mesh Manipulation**: Extensive use of PyVista for mesh operations and KDTree for efficient spatial searches

Key Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DRM component includes several key features:

1. **Create Default Process**: Generate a complete analysis process for DRM simulations with a single function call
2. **Add Absorbing Layers**: Add absorbing boundaries to the model to prevent wave reflections
3. **Pattern Integration**: Set up H5DRM patterns for realistic seismic loading
4. **Domain Preparation**: Configure the domain properly for wave propagation analysis

Creating a DRM Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Setting up a DRM analysis typically involves the following steps:

1. **Create or load a model**: Set up your finite element model
2. **Set up an H5DRM pattern**: Create and configure an H5DRM pattern
3. **Set the pattern in the DRM component**: Provide the pattern to the DRM component
4. **Add absorbing layers**: Add absorbing boundaries to prevent reflections
5. **Create the analysis process**: Generate the complete analysis process

Example of creating a DRM analysis:

.. code-block:: python

   import Femora as fm
   
   # Create a Femora instance
    
   
   # Assume a model has been set up already...
   
   # Create an H5DRM pattern
   drm_pattern = fm.pattern.create_pattern("h5drm", 
                                        h5file="seismicData.h5", 
                                        timeScaleFactor=1.0)
   
   # Set the pattern in the DRM component
   fm.analysis.drm.set_pattern(drm_pattern)
   
   # Add absorbing layers (PML in this case)
   fm.analysis.drm.addAbsorbingLayer(numLayers=2, 
                                   numPartitions=4, 
                                   partitionAlgo="kd-tree", 
                                   geometry="Rectangular", 
                                   rayleighDamping=0.95, 
                                   type="PML")
   
   # Create the default DRM analysis process
   fm.analysis.drm.createDefaultProcess(dT=0.01, finalTime=10.0)
   
   # Generate TCL script for the process
   tcl_script = fm.process.to_tcl()

Default Analysis Process Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you call ``createDefaultProcess``, the DRM component sets up a complete analysis process with multiple steps:

1. **Boundary Condition Setup**: Fixes appropriate degrees of freedom on model boundaries
2. **Recorder Setup**: Creates VTK/HDF5 recorders to capture simulation results
3. **Analysis Sequence Setup**: Creates a sequence of analysis steps:
   - Gravity-Elastic analysis (initial equilibrium)
   - Gravity-Plastic analysis (material stabilization)
   - Time reset to zero
   - Dynamic analysis (seismic simulation)

The default process uses a range of pre-configured solvers and algorithms:

- **Constraint Handler**: Plain constraint handler
- **Numberer**: ParallelRCM for optimized node numbering
- **System**: MUMPS sparse solver with optimized parameters (icntl14=200, icntl7=7)
- **Algorithm**: Modified Newton algorithm with initial factorization
- **Test**: Energy increment test with specified tolerance (default 1e-4)
- **Integrator**: Newmark method for time integration (gamma=0.5, beta=0.25)

The process is fully customizable through option dictionaries:

.. code-block:: python

   import Femora as fm

   # Custom configuration for gravity elastic phase
   elastic_options = {
       "constraint_handler": my_custom_constraint,
       "numberer": my_custom_numberer,
       "system": my_custom_system,
       "algorithm": my_custom_algorithm,
       "test": my_custom_test,
       "integrator": my_custom_integrator,
       "dt": 0.005,
       "num_steps": 30
   }

   # Custom configuration for dynamic analysis
   dynamic_options = {
       "system": my_custom_system,
       "algorithm": my_custom_algorithm,
       "final_time": 15.0
   }

   # Create process with custom options
   fm.drm.createDefaultProcess(
       dT=0.01, 
       finalTime=15.0,
       vtkhdfrecorder_delta_t=0.05,
       vtkhdfrecorder_resp_types=["disp", "vel", "accel"],
       GravityElasticOptions=elastic_options,
       DynamicAnalysisOptions=dynamic_options
   )

Absorbing Layer Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding absorbing layers is a critical aspect of DRM analysis to prevent artificial wave reflections. The implementation process is detailed and involves several steps:

1. **Boundary Detection**: The code identifies the boundaries of the computational domain
2. **Region Classification**: Classifies boundary cells into different regions (faces, edges, corners)
3. **Layer Generation**: Creates multiple absorbing layers extending outward from the boundary
4. **Property Assignment**: Assigns appropriate material properties and element types to the absorbing layers
5. **Mesh Integration**: Merges the absorbing layers with the original mesh
6. **Constraint Setup**: For PML elements, creates multi-point constraints to link the original mesh with the PML elements

The absorbing layer algorithm supports different geometries:

- **Rectangular**: Box-shaped domain with layers on all sides (currently implemented)
- **Cylindrical**: Cylindrical domain with radial absorbing layers (planned for future implementation)

Absorbing Layer Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DRM component supports several types of absorbing layers:

1. **PML (Perfectly Matched Layer)**:
   - Uses specialized PML elements with 9 degrees of freedom per node
   - Most effective at absorbing waves of all frequencies and incident angles
   - Requires careful implementation at interfaces (automatic multi-point constraints)
   - Uses specially formulated PML3D elements with absorption parameters
   - Automatically creates equal DOF constraints at the interface between standard and PML elements

2. **Rayleigh Damping**:
   - Uses standard elements with increased Rayleigh damping
   - Simpler to implement but less effective than PML
   - Works with standard 3-DOF nodes
   - No special constraints required at the interface
   - Particularly useful for models with complex material properties

3. **ASDA (to be implemented)**:
   - Advanced absorbing boundary condition based on stiffness and damping adjustment
   - Will be implemented in future versions

Partitioning and Parallelization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For large models, the DRM component supports partitioning of the absorbing layer for parallel processing:

1. **KD-Tree Partitioning**: Spatial partitioning using KD-Tree algorithm for balanced domain decomposition
2. **METIS Partitioning**: Graph-based partitioning for optimized load balancing (planned for future implementation)

Partitioning helps distribute the computational load across multiple processors for more efficient analysis of large models.

Technical Details of PML Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The PML (Perfectly Matched Layer) implementation includes several sophisticated features:

1. **Element Conversion**: Standard brick elements at the boundary are converted to specialized PML3D elements
2. **Material Compatibility**: Checks for compatible material properties in the original elements
3. **Parameter Configuration**: Sets up PML parameters based on the geometry and desired absorption characteristics
4. **Multi-Point Constraints**: Automatically creates equal DOF constraints at the interface between regular and PML elements

PML elements use 9 degrees of freedom per node (compared to 3 DOF for standard elements) to capture both the primary wave field and its derivatives, enabling more effective wave absorption.

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using the DRM component, consider the following performance aspects:

1. **Number of Layers**: More absorbing layers provide better absorption but increase computational cost
2. **Partitioning**: For large models, partitioning the absorbing layers can significantly improve performance
3. **Element Types**: PML elements are more effective but more computationally intensive than Rayleigh-damped elements
4. **Mesh Resolution**: Finer meshes in the absorbing layers improve wave absorption but increase computational cost

API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.DRM.DRM.DRM 
   :members: createDefaultProcess, addAbsorbingLayer, set_pattern, set_meshmaker
   :undoc-members:
   :show-inheritance: