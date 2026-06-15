# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

"""Uniaxial Steel01 hysteretic material wrapping OpenSees ``Steel01``."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class Steel01Material(Material):
    """Bilinear steel plasticity with kinematic hardening and optional isotropic growth.

    Implements the OpenSees ``Steel01`` rule for truss, fiber, or spring
    elements. Yield force is set by ``Fy`` with initial elastic stiffness
    ``E0`` and strain-hardening ratio ``b``. Optional parameters ``a1`` to
    ``a4`` enable isotropic expansion of the yield surface and must be
    provided together or omitted entirely.

    Tcl form:
        ``uniaxialMaterial Steel01 <tag> Fy E0 b [a1 a2 a3 a4]; #``

    Note:
        - When all four isotropic parameters exist, they emit after ``b`` exactly
          as OpenSees expects.
        - If the isotropic hardening set is omitted, the Tcl command ends after ``b``.
        - Stray keyword arguments are ignored to keep factory calls forward compatible.

    Attributes:
        params: Holds ``Fy``, ``E0``, ``b``, and optional ``a1`` to ``a4``.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        mat = model.material.uniaxial.steel01(
            user_name="A992",
            Fy=345.0,
            E0=200000.0,
            b=0.01,
        )
        print(mat.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        Fy: float | None = None,
        E0: float | None = None,
        b: float | None = None,
        a1: float | None = None,
        a2: float | None = None,
        a3: float | None = None,
        a4: float | None = None,
        **_: Any,
    ) -> None:
        """Create a Steel01 material with validated inputs.

        Args:
            user_name: Unique Femora and OpenSees material label surfaced in Tcl.
            Fy: Yield strength, strictly positive after coercion.
            E0: Initial elastic modulus, strictly positive.
            b: Post-yield stiffness ratio ``E_ep / E0``, non-negative.
            a1: Isotropic coefficient for compression envelope widening.
            a2: Isotropic exponent paired with ``a1``.
            a3: Isotropic coefficient for tension envelope widening.
            a4: Isotropic exponent paired with ``a3``.
            **_: Ignored keyword cushioning.

        Raises:
            ValueError: If ``Fy``, ``E0``, or ``b`` is missing.
            ValueError: If a numeric parameter cannot be converted correctly.
            ValueError: If a validated value falls outside the supported range.
            ValueError: If only part of the isotropic hardening set is provided.
        """
        params: Dict[str, float] = {}
        for key in ("Fy", "E0", "b"):
            value = {"Fy": Fy, "E0": E0, "b": b}[key]
            if value is None:
                raise ValueError(f"Steel01 requires '{key}'.")
            try:
                vf = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid value for '{key}'. Must be numeric."
                ) from exc
            if key in ("Fy", "E0") and vf <= 0:
                raise ValueError(f"'{key}' must be positive.")
            if key == "b" and vf < 0:
                raise ValueError("'b' must be non-negative.")
            params[key] = vf

        iso_keys = ("a1", "a2", "a3", "a4")
        provided = {"a1": a1, "a2": a2, "a3": a3, "a4": a4}
        provided = {k: v for k, v in provided.items() if v is not None}
        if len(provided) not in (0, 4):
            raise ValueError(
                "If specifying isotropic parameters, provide all of a1, a2, a3, a4."
            )
        for key in iso_keys:
            if key not in provided:
                continue
            value = provided[key]
            try:
                vf = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid value for '{key}'. Must be numeric."
                ) from exc
            if vf < 0:
                raise ValueError(f"'{key}' must be non-negative.")
            params[key] = vf

        super().__init__("uniaxialMaterial", "Steel01", user_name)
        self.params = params

    def to_tcl(self) -> str:
        """Render this component as an OpenSees Tcl command.

        Returns:
            str: Tcl text including ``Fy E0 b`` and the four optional isotropic
            parameters when all were supplied at construction.

        Raises:
            ValueError: If the material has not been registered with a manager.
        """
        p = self.params
        parts = [
            self.material_type,
            "Steel01",
            str(self._require_tag()),
            str(p["Fy"]),
            str(p["E0"]),
            str(p["b"]),
        ]
        if all(k in p for k in ("a1", "a2", "a3", "a4")):
            parts.extend([str(p["a1"]), str(p["a2"]), str(p["a3"]), str(p["a4"])])
        return " ".join(parts) + f"; # {self.user_name}"


__all__ = ["Steel01Material"]