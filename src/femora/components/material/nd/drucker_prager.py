"""Drucker-Prager plasticity model for OpenSees nD materials."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class DruckerPragerMaterial(Material):
    """Pressure-sensitive elastoplastic solid with combined isotropic and kinematic hardening.

    Maps to OpenSees ``DruckerPrager`` as an ``nDMaterial``. The required
    arguments ``k``, ``G``, ``sigmaY``, and ``rho`` correspond to the Tcl
    command slots for bulk modulus, shear modulus, initial yield intercept,
    and the material cohesion-like strength parameter ``rho``. In this model,
    ``rho`` is not mass density; use ``density`` for mass density effects.

    Tcl form:
        ``nDMaterial DruckerPrager <tag> k G sigmaY rho rhoBar Kinf Ko delta1 delta2 H theta density atmPressure; #``

    Notes:
        - ``rhoBar`` is constrained to ``[0, rho]`` by the current validation rules.
        - Coordinate ``atmPressure`` and ``density`` units with the bulk and
          shear modulus units used in the exported model.
        - Instances are typically created through
          :meth:`~femora.core.nd_material_manager.NDMaterialManager.drucker_prager`
          and must be managed before :meth:`to_tcl` can be called.

    Attributes:
        tag: Manager-assigned identifier after the object is added to a Femora
            manager.
        params: All validated Tcl arguments keyed by parameter name.

    Examples:
        ```python
        import femora as fm

        model = fm.MeshMaker()
        mat = model.material.nd.drucker_prager(
            user_name="dp_solid",
            k=2.0e5,
            G=9.6e4,
            sigmaY=2.5e3,
            rho=1.85,
            density=2100.0,
        )
        print(mat.tag)
        ```
    """

    def __init__(
        self,
        user_name: str = "Unnamed",
        *,
        k: float | None = None,
        G: float | None = None,
        sigmaY: float | None = None,
        rho: float | None = None,
        rhoBar: float | None = None,
        Kinf: float | None = None,
        Ko: float | None = None,
        delta1: float | None = None,
        delta2: float | None = None,
        H: float | None = None,
        theta: float | None = None,
        density: float | None = None,
        atmPressure: float | None = None,
        **_: Any,
    ) -> None:
        """Create a Drucker-Prager material with validated inputs.

        Args:
            user_name: Stored in Tcl suffix comments and enforced unique among
                managed materials.
            k: Bulk modulus analogue in the Tcl command, strictly greater than zero.
            G: Shear modulus analogue in the Tcl command, strictly greater than zero.
            sigmaY: Initial yield intercept, strictly positive.
            rho: Cohesion-like Drucker-Prager strength parameter, strictly positive.
            rhoBar: Optional cap on dilatancy evolution. Defaults to ``rho`` and
                must satisfy ``0 <= rhoBar <= rho``.
            Kinf: Optional long-run isotropic strengthening magnitude, ``>= 0``.
            Ko: Additional isotropic evolution parameter, ``>= 0``.
            delta1: Isotropic modulus expansion coefficient, ``>= 0``.
            delta2: Softening or decay coefficient, ``>= 0``.
            H: Combined hardening modulus, ``>= 0``.
            theta: Blend in ``[0, 1]`` between isotropic and kinematic mechanisms.
            density: Optional mass density, ``>= 0``.
            atmPressure: Reference pressure for modulus updates, ``>= 0``.
            **: Unused keyword placeholders for forward compatibility.

        Raises:
            ValueError: If a required parameter is missing.
            ValueError: If a numeric value cannot be converted to ``float``.
            ValueError: If any validated value falls outside the supported interval.
        """
        validated: Dict[str, float] = {}

        for param in ("k", "G", "sigmaY", "rho"):
            value = locals()[param]
            if value is None:
                raise ValueError(
                    f"DruckerPragerMaterial requires the '{param}' parameter."
                )
            try:
                vf = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid value for '{param}'. It must be a number."
                ) from exc
            if param in ("k", "G", "sigmaY") and vf <= 0:
                raise ValueError(f"'{param}' must be positive.")
            validated[param] = vf

        optional_specs: Dict[str, Dict[str, Any]] = {
            "rhoBar": {
                "value": rhoBar,
                "default": validated["rho"],
                "min": 0,
                "max": validated["rho"],
                "message": "rhoBar must be in the range [0, rho]",
            },
            "Kinf": {
                "value": Kinf,
                "default": 0.0,
                "min": 0,
                "message": "Kinf must be non-negative",
            },
            "Ko": {
                "value": Ko,
                "default": 0.0,
                "min": 0,
                "message": "Ko must be non-negative",
            },
            "delta1": {
                "value": delta1,
                "default": 0.0,
                "min": 0,
                "message": "delta1 must be non-negative",
            },
            "delta2": {
                "value": delta2,
                "default": 0.0,
                "min": 0,
                "message": "delta2 must be non-negative",
            },
            "H": {
                "value": H,
                "default": 0.0,
                "min": 0,
                "message": "H must be non-negative",
            },
            "theta": {
                "value": theta,
                "default": 0.0,
                "min": 0,
                "max": 1,
                "message": "theta must be in range [0, 1]",
            },
            "density": {
                "value": density,
                "default": 0.0,
                "min": 0,
                "message": "density must be non-negative",
            },
            "atmPressure": {
                "value": atmPressure,
                "default": 101.0,
                "min": 0,
                "message": "atmPressure must be non-negative",
            },
        }

        for param, spec in optional_specs.items():
            value = spec["value"]
            if value is None:
                value = spec["default"]
            try:
                vf = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid value for '{param}'. It must be a number."
                ) from exc
            vmin = spec.get("min")
            vmax = spec.get("max")
            if vmin is not None and vf < vmin:
                raise ValueError(spec["message"])
            if vmax is not None and vf > vmax:
                raise ValueError(spec["message"])
            validated[param] = vf

        super().__init__("nDMaterial", "DruckerPrager", user_name)
        self.params = validated

    def to_tcl(self) -> str:
        """Serialize the Tcl line with deterministic parameter ordering.

        Returns:
            str: A single Tcl command listing ``k G sigmaY rho`` plus the
            optional hardening tail ending in ``density`` and ``atmPressure``.

        Raises:
            ValueError: If the material lacks a manager-assigned tag.
        """
        order = [
            "k",
            "G",
            "sigmaY",
            "rho",
            "rhoBar",
            "Kinf",
            "Ko",
            "delta1",
            "delta2",
            "H",
            "theta",
            "density",
            "atmPressure",
        ]
        p = self.params
        params_str = " ".join(str(p[k]) for k in order)
        return (
            f"{self.material_type} DruckerPrager "
            f"{self._require_tag()} {params_str}; # {self.user_name}"
        )


__all__ = ["DruckerPragerMaterial"]