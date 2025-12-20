MUMPS System
============

The MUMPS (MUltifrontal Massively Parallel sparse direct Solver) system solver is a state-of-the-art parallel sparse direct solver. It provides robust performance for both symmetric and unsymmetric matrices and includes advanced features for controlling memory usage and ordering.

Description
-----------

The MUMPS system:
- Uses sparse matrix storage
- Implements multifrontal parallel factorization
- Supports both symmetric and unsymmetric matrices
- Provides multiple ordering options
- Features memory estimation and control
- Designed for parallel execution

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``icntl14``
     - float
     - Controls the percentage increase in the estimated working space
   * - ``icntl7``
     - int
     - Specifies the ordering strategy (0=AMD, 2=AMF, 3=SCOTCH, 4=PORD, 5=Metis, 6=AMD with QAMD, 7=automatic)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a MUMPS system solver with default settings
   fm.analysis.system.create_system("Mumps")

   # Create a MUMPS system solver with custom settings
   fm.analysis.system.create_system(
       "Mumps",
       icntl14=20.0,  # 20% increase in working space
       icntl7=5       # Use Metis ordering
   )

Notes
-----

- State-of-the-art parallel sparse direct solver
- Excellent performance for large-scale problems
- Multiple ordering options for different matrix types
- Advanced memory control features
- Good scalability on parallel systems
- Robust for ill-conditioned problems
- Particularly effective with complex structural analyses 