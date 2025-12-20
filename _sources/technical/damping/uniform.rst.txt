Uniform Damping
===============

The ``UniformDamping`` class implements a damping model that provides consistent damping across a specified frequency range.

Parameters
----------

- ``dampingRatio``: Target equivalent viscous damping ratio (float between 0 and 1) [required]
- ``freql``: Lower bound of the frequency range in Hz (float greater than 0) [required]
- ``freq2``: Upper bound of the frequency range in Hz (float greater than 0) [required]
- ``Ta``: Time when the damping is activated (float) [optional]
- ``Td``: Time when the damping is deactivated (float) [optional]
- ``tsTagScaleFactorVsTime``: Time series tag identifying the scale factor of the damping versus time (int) [optional]

Usage
-----

.. code-block:: python

    from femora.components.Damping import DampingManager
    
    damping_manager = DampingManager()
    uniform_damping = damping_manager.create_damping(
        'uniform',
        dampingRatio=0.05,   # 5% damping
        freql=1.0,           # 1 Hz lower bound
        freq2=15.0,          # 15 Hz upper bound
        Ta=0.0               # Activate from the start
    )

Advanced Usage
--------------

Specifying activation and deactivation times allows for time-dependent damping behavior:

.. code-block:: python

    uniform_damping = damping_manager.create_damping(
        'uniform',
        dampingRatio=0.05,
        freql=1.0,
        freq2=15.0,
        Ta=5.0,              # Activate at 5 seconds
        Td=20.0              # Deactivate at 20 seconds
    )

References
----------

- `OpenSees Uniform Damping <https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/elementalDamping/UniformDamping.html>`_