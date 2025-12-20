Linear Algorithm
================

The Linear algorithm is a simple solution algorithm that performs just one iteration to solve the system of equations. It is suitable for linear problems or as a single-iteration approach in nonlinear problems.

Description
-----------

The Linear algorithm:
- Solves the system of equations in one iteration
- Can use either the initial or current stiffness matrix
- Can optionally factor the stiffness matrix only once
- Does not iterate to convergence, making it suitable only for linear or linearized problems

Parameters
----------

.. list-table::
   :widths: 25 10 65
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``initial``
     - bool
     - If True, uses the initial stiffness matrix (default: False)
   * - ``factor_once``
     - bool
     - If True, only sets up and factors the matrix once (default: False)

Usage Example
-------------

.. code-block:: python

   # Create a Femora instance
    

   # Create a Linear algorithm with default settings
   fm.analysis.algorithm.create_algorithm("Linear")

   # Create a Linear algorithm using initial stiffness
   fm.analysis.algorithm.create_algorithm("Linear", initial=True)

   # Create a Linear algorithm that factors the matrix only once
   fm.analysis.algorithm.create_algorithm("Linear", factor_once=True)

   # Create a Linear algorithm with both options
   fm.analysis.algorithm.create_algorithm("Linear", initial=True, factor_once=True)

Notes
-----

- The Linear algorithm is the simplest and fastest algorithm
- It is only suitable for linear problems or for specific nonlinear analysis approaches
- It does not iterate to convergence
- The ``initial`` option uses the initial stiffness matrix for all time steps
- The ``factor_once`` option can improve performance by factoring the matrix only once 