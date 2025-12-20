Modal Damping
=============

The ``ModalDamping`` class implements modal damping, which applies specific damping factors directly to individual vibration modes.

Parameters
----------

- ``numberofModes``: Number of modes to consider for modal damping (integer greater than 0)
- ``dampingFactors``: Comma-separated list of damping factors for each mode (values between 0 and 1)

Usage
-----

.. code-block:: python

    from femora.components.Damping import DampingManager
    
    damping_manager = DampingManager()
    modal_damping = damping_manager.create_damping(
        'modal',
        numberofModes=3,
        dampingFactors="0.02,0.03,0.04"
    )

Notes
-----

- The length of ``dampingFactors`` must match the ``numberofModes`` parameter
- Each damping factor must be between 0 and 1
- Modal damping allows more precise control of damping characteristics compared to Rayleigh damping

References
----------

- `OpenSees Modal Damping <https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/modalDamping.html>`_
- `Be Careful with Modal Damping <https://portwooddigital.com/2019/09/12/be-careful-with-modal-damping/>`_
- `Modal and Stiffness Proportional Damping <https://portwooddigital.com/2023/01/25/modal-and-stiffness-proportional-damping/>`_