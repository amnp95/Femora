Analysis
---------------------------------

Understanding the Analysis Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``Analysis`` component is a core part of the Femora library that manages the configuration and execution of OpenSees analyses. It implements a comprehensive system for defining and controlling various types of structural analyses, including static, transient, and variable transient analyses.

The Analysis component combines several key subcomponents to define how an analysis is performed:
- Constraint Handler: Manages how constraints are handled in the analysis
- Numberer: Determines the equation numbering scheme
- System: Defines the system of equations to be solved
- Algorithm: Specifies the solution algorithm
- Test: Defines the convergence criteria
- Integrator: Controls the time integration scheme

Accessing the Analysis Component
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the Analysis component in your code:

1. **Direct Access**: Import and use the AnalysisManager class directly
   
   .. code-block:: python
      
      from femora.components.Analysis.analysis import AnalysisManager
      
      # Get the singleton instance
      analysis_manager = AnalysisManager()
      
      # Use the analysis manager directly
      analysis_manager.create_analysis(...)

2. **Through Femora** (Recommended): Access via the Femora class's .analysis property
   
   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the AnalysisManager through the .analysis property
      fm.analysis.create_analysis(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How Analysis Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Analysis component provides several key capabilities:

1. **Analysis Creation**: Creates analysis objects of various types with appropriate parameters
2. **Analysis Tracking**: Keeps track of all analyses by both tag and name
3. **Analysis Management**: Provides methods to retrieve, update, and delete analyses
4. **TCL Generation**: Converts analysis configurations to OpenSees TCL commands

When an analysis is created, the Analysis component:

1. Validates that all required components are present and compatible
2. Assigns a unique numeric tag automatically
3. Registers it with the user-provided name (which must be unique)
4. Validates that all required parameters are present and valid for the analysis type

.. note::
   Each analysis must have a unique name. The Analysis component uses this name as a key
   to retrieve analyses later. If you try to create an analysis with a name that already
   exists, the Analysis component will raise an error.

Analysis Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Analysis component supports three main types of analyses:

1. **Static Analysis**
   - Used for static loading conditions
   - Requires number of steps parameter
   - Uses static integrators

2. **Transient Analysis**
   - Used for dynamic loading conditions
   - Requires time step (dt) parameter
   - Can use either number of steps or final time
   - Uses transient integrators

3. **Variable Transient Analysis**
   - Used for dynamic loading with adaptive time stepping
   - Requires time step parameters (dt, dt_min, dt_max)
   - Requires desired iterations per step (jd)
   - Uses transient integrators

Analysis Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each analysis requires six key components:

1. **Constraint Handler**
   - Manages how constraints are handled in the analysis
   - Available types: Plain, Lagrange, Penalty, Transformation

2. **Numberer**
   - Determines the equation numbering scheme
   - Available types: Plain, RCM, AMD

3. **System**
   - Defines the system of equations to be solved
   - Available types: BandGeneral, BandSPD, ProfileSPD, SparseGeneral, SparseSPD

4. **Algorithm**
   - Specifies the solution algorithm
   - Available types: Newton, ModifiedNewton, KrylovNewton, BFGS, Broyden

5. **Test**
   - Defines the convergence criteria
   - Available types: NormDispIncr, NormUnbalance, EnergyIncr

6. **Integrator**
   - Controls the time integration scheme
   - Static types: LoadControl, DisplacementControl
   - Transient types: Newmark, HHT, CentralDifference

AnalysisManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.Analysis.analysis.AnalysisManager

Analysis Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating analyses is one of the primary functions of the AnalysisManager. There are two main approaches:

1. **Default Analysis Creation**
   - Creates a pre-configured analysis with default components
   - Useful for quick setup of common analysis types

2. **Custom Analysis Creation**
   - Allows full control over all analysis components and parameters
   - Required for specialized or complex analyses

Example of creating a custom analysis:

.. code-block:: python

   from femora.components.Analysis.analysis import AnalysisManager
   from femora.components.Analysis.constraint_handlers import PlainHandler
   from femora.components.Analysis.numberers import PlainNumberer
   from femora.components.Analysis.systems import BandGeneral
   from femora.components.Analysis.algorithms import Newton
   from femora.components.Analysis.convergenceTests import NormDispIncr
   from femora.components.Analysis.integrators import LoadControl

   # Get the analysis manager
   analysis_manager = AnalysisManager()

   # Create components
   constraint_handler = PlainHandler()
   numberer = PlainNumberer()
   system = BandGeneral()
   algorithm = Newton()
   test = NormDispIncr(1.0e-6, 10)
   integrator = LoadControl(1.0)

   # Create the analysis
   analysis = analysis_manager.create_analysis(
       name="my_static_analysis",
       analysis_type="Static",
       constraint_handler=constraint_handler,
       numberer=numberer,
       system=system,
       algorithm=algorithm,
       test=test,
       integrator=integrator,
       num_steps=10
   )

Available Analysis Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 3

   analysis/integrators/index



.. toctree::
   :maxdepth: 2

   analysis/constraint_handlers/index
   analysis/numberers/index
   analysis/systems/index
   analysis/algorithms/index
   analysis/convergence_tests/index


Each analysis component type has its own documentation page with detailed parameter descriptions and usage examples. 