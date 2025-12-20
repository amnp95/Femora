Secant Stiffness Proportional Damping
=====================================

The ``SecantStiffnessProportional`` class implements a damping model that is proportional to the secant stiffness of the structure.

Mathematical Formulation
------------------------

The damping force is calculated as:

.. math::

    f_{damping} = \text{dampingFactor} \times K_{secant} \times \dot{u}

Where:
- :math:`f_{damping}` is the damping force
- :math:`K_{secant}` is the secant stiffness matrix
- :math:`\dot{u}` is the velocity vector

Parameters
----------

- ``dampingFactor``: Coefficient used in the secant stiffness-proportional damping (float between 0 and 1) [required]
- ``Ta``: Time when the damping is activated (float) [optional]
- ``Td``: Time when the damping is deactivated (float) [optional]
- ``tsTagScaleFactorVsTime``: Time series tag identifying the scale factor of the damping versus time (int) [optional]

Usage
-----

.. code-block:: python

    from femora.components.Damping import DampingManager
    
    damping_manager = DampingManager()
    secstiff_damping = damping_manager.create_damping(
        'secant stiffness proportional',
        dampingFactor=0.03    # 3% damping proportional to secant stiffness
    )

Advanced Usage
--------------

With time-dependent activation:

.. code-block:: python

    secstiff_damping = damping_manager.create_damping(
        'secant stiffness proportional',
        dampingFactor=0.03,
        Ta=2.0,               # Activate at 2 seconds
        Td=15.0               # Deactivate at 15 seconds
    )

Notes
-----

- This damping model is especially useful for nonlinear analyses
- The secant stiffness is recalculated at each time step, making this model more computationally intensive but potentially more accurate for nonlinear systems

References
----------

- `OpenSees Secant Stiffness Damping <https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/elementalDamping/SecStifDamping.html>`_