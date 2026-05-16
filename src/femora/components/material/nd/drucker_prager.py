I’ll review the target file plus related material manager/base context, then rewrite only its docstrings to match the Femora standard and return the full updated file.

I’ve gathered context from the base material and nD manager, and I’ll now update only the target file’s docstrings to the required Femora format.

"""Drucker-Prager plasticity model for OpenSees nD materials."""

from __future__ import annotations

from typing import Any, Dict

from femora.core.material_base import Material


class DruckerPragerMaterial(Material):
    """Pressure-sensitive elastoplastic continuum with mixed hardening response.

    This class represents the OpenSees ``DruckerPrager`` nD material model for
    pressure-dependent plasticity. It combines isotropic and kinematic
    hardening controls and stores validated parameter values for deterministic
    Tcl export.

    Tcl form:
        ``nDMaterial DruckerPrager <tag> k G sigmaY rho rhoBar Kinf Ko delta1 delta2 H theta density atmPressure; #``

    Notes:
        - ``rho`` is the Drucker-Prager strength parameter, not mass density.
          Use ``density`` for inertial mass effects.
        - ``rhoBar`` is constrained to ``[0, rho]`` by the validation rules.
        - Coordinate ``atmPressure`` and ``density`` units with the bulk and
          shear modulus units used in the exported model.
        - Instances are typically created through
          :meth:`~femora.core.nd_material_manager.NDMaterialManager.drucker_prager`
          and must be managed before :meth:`to_tcl` can be called.

    Attributes:
        tag: Manager-assigned identifier after registration with the owning
            material manager.
        params: Validated Tcl arguments keyed by parameter name.

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
        """Create a Drucker-Prager material with validated constitutive parameters.

        Args:
            user_name: Label stored on the material and appended to the emitted
                Tcl comment.
            k: Bulk modulus parameter. Must be positive.
            G: Shear modulus parameter. Must be positive.
            sigmaY: Initial yield intercept. Must be positive.
            rho: Drucker-Prager strength parameter.
            rhoBar: Optional dilatancy cap. Defaults to ``rho`` and must satisfy
                ``0 <= rhoBar <= rho``.
            Kinf: Optional isotropic hardening magnitude. Must be non-negative.
            Ko: Optional isotropic evolution parameter. Must be non-negative.
            delta1: Optional isotropic expansion coefficient. Must be non-negative.
            delta2: Optional softening or decay coefficient. Must be non-negative.
            H: Optional hardening modulus. Must be non-negative.
            theta: Optional isotropic-kinematic blend factor in ``[0, 1]``.
            density: Optional mass density. Must be non-negative.
            atmPressure: Optional reference pressure. Must be non-negative.
            **_: Additional keyword arguments accepted and ignored for
                forward-compatible factory calls.

        Raises:
            ValueError: If a required argument is missing, if a numeric argument
                cannot be converted to ``float``, or if a value violates the
                enforced parameter bounds.
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
        """Render the OpenSees ``nDMaterial DruckerPrager`` Tcl command.

        Returns:
            str: Tcl command string with parameters emitted in fixed OpenSees
                order.

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
