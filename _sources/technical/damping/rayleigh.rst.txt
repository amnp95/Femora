Rayleigh Damping
================

The ``RayleighDamping`` class implements classical Rayleigh damping, which defines the damping matrix as a linear combination of the mass and stiffness matrices.

Mathematical Formulation
------------------------

The Rayleigh damping matrix is defined as:

.. math::

    C = \alpha_M M + \beta_K K + \beta_{KInit} K_{init} + \beta_{KComm} K_{comm}

Where:

- :math:`C` is the damping matrix
- :math:`M` is the mass matrix
- :math:`K` is the stiffness matrix
- :math:`K_{init}` is the initial stiffness matrix
- :math:`K_{comm}` is the committed (last converged) stiffness matrix
- :math:`\alpha_M`, :math:`\beta_K`, :math:`\beta_{KInit}`, :math:`\beta_{KComm}` are the proportionality factors

Parameters
----------

- ``alphaM``: Factor applied to the mass matrix (default: 0.0)
- ``betaK``: Factor applied to the stiffness matrix (default: 0.0)
- ``betaKInit``: Factor applied to the initial stiffness matrix (default: 0.0)
- ``betaKComm``: Factor applied to the committed stiffness matrix (default: 0.0)

Usage
-----

.. code-block:: python

    from femora.components.Damping import DampingManager
    
    damping_manager = DampingManager()
    rayleigh_damping = damping_manager.create_damping(
        'rayleigh', 
        alphaM=0.05, 
        betaK=0.001, 
        betaKInit=0.0, 
        betaKComm=0.0
    )

Notes
-----

- At least one of the proportionality factors must be greater than zero
- All factors must be between 0 and 1
- The usage of Rayleigh damping may provide incorrect results when used with non-linear time history analysis using concentrated plasticity models

References
----------

- `OpenSees Rayleigh Damping <https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/rayleigh.html>`_
- `OpenSees Wiki - Rayleigh Damping Command <https://opensees.berkeley.edu/wiki/index.php/Rayleigh_Damping_Command>`_