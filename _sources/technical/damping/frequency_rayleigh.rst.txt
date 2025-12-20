Frequency Rayleigh Damping
==========================

The ``FrequencyRayleighDamping`` class extends the Rayleigh damping model by allowing users to specify damping in terms of target frequencies rather than directly setting the proportionality factors.

Mathematical Formulation
------------------------

Given two target frequencies (f₁, f₂) and a desired damping ratio (ξ), the Rayleigh coefficients are calculated as:

.. math::

    \omega_1 = 2\pi f_1, \quad \omega_2 = 2\pi f_2

    \alpha_M = \frac{2\omega_1\omega_2}{\omega_1 + \omega_2}\xi

    \beta_K = \frac{2}{\omega_1 + \omega_2}\xi

    \beta_{KInit} = 0, \quad \beta_{KComm} = 0

Where ω₁ and ω₂ are the angular frequencies corresponding to f₁ and f₂.

Parameters
----------

- ``dampingFactor``: Target damping ratio ξ (float between 0 and 1) [required]
- ``f1``: Lower bound target frequency in Hz (float greater than 0) [default: 0.2]
- ``f2``: Upper bound target frequency in Hz (float greater than 0) [default: 20]

Usage
-----

.. code-block:: python

    from femora.components.Damping import DampingManager
    
    damping_manager = DampingManager()
    freq_rayleigh = damping_manager.create_damping(
        'frequency rayleigh',
        dampingFactor=0.05,  # 5% damping
        f1=1.0,              # 1 Hz lower bound
        f2=10.0              # 10 Hz upper bound
    )

Notes
-----

- This approach is often more intuitive than directly specifying the Rayleigh coefficients
- The damping ratio is exactly equal to the specified dampingFactor at the two target frequencies f₁ and f₂
- Between these frequencies, the damping ratio is less than the specified value, and outside this range, it exceeds the specified value
- The damping matrix uses only mass and stiffness proportional components (αₘM + βₖK)