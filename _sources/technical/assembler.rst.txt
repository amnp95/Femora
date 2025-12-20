Assembler
=========

Introduction
------------

The ``Assembler`` component in Femora is responsible for combining multiple mesh parts into a unified model, partitioning the model for parallel computing, and managing the combined mesh. It provides a centralized system for creating and managing assembly sections, which are groups of mesh parts that are combined into a single mesh.

The Assembler system consists of two main classes:

1. ``Assembler``: A singleton class that manages multiple ``AssemblySection`` instances
2. ``AssemblySection``: A class that represents a group of mesh parts combined into a single mesh

Understanding the Assembler
---------------------------

The ``Assembler`` class implements the Singleton pattern, ensuring that only one instance exists throughout the application. This provides a centralized point for managing assembly sections and accessing the assembled mesh.

Accessing the Assembler
~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the Assembler:

1. **Direct Access**:

   .. code-block:: python
      
      from femora.components.Assemble.Assembler import Assembler
      
      # Get the singleton instance
      assembler = Assembler()
      
      # Or use the class method
      assembler = Assembler.get_instance()

2. **Through Femora** (recommended):

   .. code-block:: python
      
      import femora as fm
      
      # Create a Femora instance
       
      
      # Access the Assembler through femora
      assembler = fm.assembler

The second approach is recommended as it ensures proper initialization of dependencies.

Structure of the Assembler
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Assembler maintains:

- A dictionary of AssemblySection instances, each with a unique tag
- A reference to the completely assembled mesh
- Methods for creating, retrieving, and managing assembly sections

Key features of the Assembler include:

- **Automatic tagging**: Each assembly section receives a unique numeric tag
- **Tag management**: When sections are deleted, remaining sections are retagged to maintain sequential numbering
- **Mesh merging**: Combines all sections into a unified mesh
- **Partitioning**: Divides the mesh for parallel processing

Understanding Assembly Sections
-------------------------------

An ``AssemblySection`` represents a collection of mesh parts that are combined into a single mesh. Each section has its own mesh, which can be partitioned for parallel computing.

Creating Assembly Sections
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to create an AssemblySection:

1. **Directly through the Assembler** (recommended):

   .. code-block:: python
   
      # Create an assembly section with two mesh parts
      section = assembler.create_section(
          meshparts=["cube1", "cube2"],
          num_partitions=4,
          partition_algorithm="kd-tree",
          merging_points=True
      )

2. **Creating an AssemblySection instance**:

   .. code-block:: python
   
      from femora.components.Assemble.Assembler import AssemblySection
      
      # Create an assembly section with two mesh parts
      section = AssemblySection(
          meshparts=["cube1", "cube2"],
          num_partitions=4,
          partition_algorithm="kd-tree",
          merging_points=True
      )

The first approach is recommended as it ensures proper registration with the Assembler.

Merging Points in Assembly Sections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When combining mesh parts, the ``merging_points`` parameter controls whether overlapping or close points should be merged:

- **merging_points=True**: Points that are within a tolerance distance are merged into a single point, creating a continuous mesh. This is useful when mesh parts share boundaries.
  
- **merging_points=False**: All points are preserved, even if they overlap. This can be useful when mesh parts should remain distinct or when degrees of freedom differ.

Partitioning Strategies
~~~~~~~~~~~~~~~~~~~~~~~

The ``AssemblySection`` supports partitioning the mesh for parallel processing using different algorithms:

- **kd-tree**: Divides the mesh into regions based on spatial coordinates using a k-dimensional tree. This creates balanced partitions based on geometry.

The ``num_partitions`` parameter controls how many partitions are created. For the ``kd-tree`` algorithm, the actual number of partitions will be rounded up to the next power of 2 (e.g., if you specify 3, you'll get 4 partitions).

Assembled Mesh Structure
~~~~~~~~~~~~~~~~~~~~~~~~

When mesh parts are assembled, the resulting mesh includes several data arrays:

- **ElementTag**: Identifies the element type for each cell
- **MaterialTag**: Identifies the material assigned to each cell
- **Region**: Identifies the region each cell belongs to
- **ndf**: Number of degrees of freedom for each point
- **Core**: Identifies which partition each cell belongs to (only when partitioned)

Assembling the Complete Mesh
----------------------------

After creating assembly sections, you can combine all sections into a single mesh using the ``Assemble`` method:

.. code-block:: python

   # Assemble all sections into a single mesh
   assembler.Assemble(merge_points=True)
   
   # Access the assembled mesh
   mesh = assembler.AssembeledMesh

This creates a unified mesh from all assembly sections, with consistent cell data and optional point merging.

API Reference
-------------

.. autoclass:: femora.components.Assemble.Assembler.Assembler
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: femora.components.Assemble.Assembler.AssemblySection
    :members:
    :undoc-members:
    :show-inheritance:

Best Practices
--------------

1. **Create assembly sections through the Assembler** for proper registration
2. **Use merge_points=True** when mesh parts share boundaries
3. **Choose partition numbers that are powers of 2** for the kd-tree algorithm
4. **Check for consistent degrees of freedom** when merging points

Use Cases
---------

- **Combined Models**: Assembling individual parts into a complete structural model
- **Parallel Analysis**: Partitioning large models for distributed computing
- **Multi-Material Models**: Combining regions with different material properties
- **Component Analysis**: Analyzing interactions between different parts of a model