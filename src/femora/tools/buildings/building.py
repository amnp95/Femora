# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

from femora.core.time_series_base import TimeSeries

import numpy as np
import pyvista as pv


class Building:
    """Abstract public contract for Femora building archetypes.

    Subclasses implement the model-specific construction and setup methods.
    This class owns shared modal parsing, table printing, error filtering, and
    PyVista plotting helpers used by building archetype implementations.
    """

    def build(self, model, material, material_density: float = 0.0):
        """Create this building in ``model`` and return its mesh part."""
        raise NotImplementedError

    def get_modes(
        self,
        num_modes: int,
        *,
        opensees_exe: Optional[str] = None,
        print_results: bool = False,
        plot: bool = False,
        plot_scale: Optional[float] = None,
    ) -> Dict[str, np.ndarray]:
        """Return modal frequencies, periods, and eigenvectors."""
        raise NotImplementedError

    def get_recorders(
        self,
        model,
        *,
        file_name: Optional[str] = None,
        delta_t: Optional[float] = None,
        element_responses: Optional[List[str]] = None,
        node_responses: Optional[List[str]] = None,
    ):
        """Return recorder objects for this building."""
        raise NotImplementedError

    def export_metadata(self, model, path, **kwargs):
        """Explicitly export structure-specific interpretation metadata after assembly."""
        raise NotImplementedError

    def get_results(self, source, **kwargs):
        """Return this structure's response object; implementations define its semantics."""
        raise NotImplementedError

    def create_rigid_diaphragms(self, model, verbose: bool = True) -> None:
        """Create rigid diaphragm constraints if supported by this building."""
        raise NotImplementedError

    def create_gravity_pattern(self, model, g: float):
        """Create and return a gravity load pattern if supported."""
        raise NotImplementedError

    def create_pushover_pattern(
        self,
        model,
        *,
        time_series: TimeSeries,
        base_shear: float,
        direction: Union[str, float] = "x",
        distribution: Union[str, Sequence[float]] = "mass_height",
        mode_shape: Optional[Sequence[float]] = None,
        eccentricity: Tuple[float, float] = (0.0, 0.0),
    ):
        """Return a reference lateral-force pattern; do not run an analysis.

        Building implementations choose appropriate load application nodes.
        ``time_series`` must be supplied by the caller. ``base_shear`` is the
        positive reference resultant, not the final force in a scaled analysis.
        ``direction`` is X, Y, or an angle in degrees counterclockwise from X.
        """
        raise NotImplementedError

    def apply_fixed_base(self, model, tol: float = 1e-4) -> None:
        """Apply fixed-base boundary conditions if supported by this building."""
        raise NotImplementedError

    @staticmethod
    def _resolve_modal_material(
        model,
        *,
        material: Optional[Union[Dict[str, object], Callable]],
        material_density: Optional[float],
        default_name: str,
        default_E: float,
        default_nu: float,
        default_density: float,
    ):
        if material is None:
            created = model.material.nd.elastic_isotropic(
                default_name,
                E=default_E,
                nu=default_nu,
                rho=default_density,
            )
            return created, float(default_density if material_density is None else material_density)

        if callable(material):
            created = material(model)
            density = material_density
            if density is None:
                density = Building._infer_material_density(created)
            if density is None:
                density = default_density
            return created, float(density)

        if isinstance(material, dict):
            material_type = str(material.get("type", "elastic_isotropic")).lower()
            if material_type in {"elastic", "steel01"}:
                parameters = {key: value for key, value in material.items()
                              if key not in {"type", "name", "user_name", "rho"}}
                name = str(material.get("name", material.get("user_name", default_name)))
                created = getattr(model.material.uniaxial, material_type)(user_name=name, **parameters)
                density = material.get("rho", default_density) if material_density is None else material_density
                return created, float(density)
            if material_type not in {"elastic_isotropic", "elasticisotropic"}:
                raise ValueError("Supported modal material definitions are elastic_isotropic, Elastic, and Steel01; use a factory for other laws.")
            name = str(material.get("name", material.get("user_name", default_name)))
            if "E" not in material:
                raise ValueError("Material definition for get_modes() must include 'E'.")
            nu = float(material.get("nu", default_nu))
            rho = float(material.get("rho", default_density))
            created = model.material.nd.elastic_isotropic(
                name,
                E=float(material["E"]),
                nu=nu,
                rho=rho,
            )
            return created, float(rho if material_density is None else material_density)

        raise TypeError(
            "material must be None, a material definition dict, or a callable "
            "material factory accepting the isolated Model."
        )

    @staticmethod
    def _infer_material_density(material) -> Optional[float]:
        for attr in ("rho", "density"):
            value = getattr(material, attr, None)
            if value is not None:
                return float(value)
        params = getattr(material, "params", None)
        if isinstance(params, dict):
            for key in ("rho", "density"):
                if key in params:
                    return float(params[key])
        return None

    @staticmethod
    def _parse_eigen_stdout(
        stdout: str,
        *,
        num_modes: int,
        start_node: int,
        end_node: int,
    ) -> Dict[str, np.ndarray]:
        frequencies = np.full(num_modes, np.nan, dtype=float)
        periods = np.full(num_modes, np.nan, dtype=float)
        node_tags = np.arange(start_node, end_node + 1, dtype=int)
        vectors: Dict[Tuple[int, int], List[float]] = {}
        ndof: Optional[int] = None

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("FEMORA_EIGENVALUE "):
                parts = line.split()
                mode = int(parts[1])
                frequencies[mode - 1] = float(parts[3])
                periods[mode - 1] = float(parts[4])
            elif line.startswith("FEMORA_EIGENVECTOR "):
                parts = line.split()
                mode = int(parts[1])
                node_tag = int(parts[2])
                values = [float(value) for value in parts[3:]]
                if ndof is None:
                    ndof = len(values)
                vectors[(mode, node_tag)] = values

        if np.isnan(frequencies).all():
            Building._print_error_lines(stdout)
            raise RuntimeError("OpenSees completed but no FEMORA_EIGENVALUE lines were parsed.")
        if ndof is None:
            Building._print_error_lines(stdout)
            raise RuntimeError("OpenSees completed but no FEMORA_EIGENVECTOR lines were parsed.")

        eigenvectors = np.zeros((num_modes, len(node_tags), ndof), dtype=float)
        for mode in range(1, num_modes + 1):
            for node_index, node_tag in enumerate(node_tags):
                values = vectors.get((mode, int(node_tag)))
                if values is None:
                    raise RuntimeError(f"Missing eigenvector for mode {mode}, node {node_tag}.")
                eigenvectors[mode - 1, node_index, :] = values

        return {
            "frequencies": frequencies,
            "periods": periods,
            "node_tags": node_tags,
            "eigenvectors": eigenvectors,
        }

    @staticmethod
    def _print_modal_table(
        frequencies: np.ndarray,
        periods: np.ndarray,
        title: str,
    ) -> None:
        border = "+" + "-" * 8 + "+" + "-" * 18 + "+" + "-" * 18 + "+"
        print()
        print(title)
        print(border)
        print(f"| {'Mode':>4}   | {'Frequency (Hz)':>14}   | {'Period (s)':>14}   |")
        print(border)
        for mode, (frequency, period) in enumerate(zip(frequencies, periods), start=1):
            frequency_text = "nan" if np.isnan(frequency) else f"{frequency:.6g}"
            period_text = "nan" if np.isnan(period) else f"{period:.6g}"
            print(f"| {mode:>4}   | {frequency_text:>14}   | {period_text:>14}   |")
        print(border)
        print()

    @staticmethod
    def _plot_modal_shapes(
        mesh: Optional[pv.DataSet],
        result: Dict[str, np.ndarray],
        *,
        scale: Optional[float],
    ) -> None:
        if mesh is None:
            raise ValueError("Building mesh is not available for modal plotting.")

        eigenvectors = result["eigenvectors"]
        frequencies = result["frequencies"]
        periods = result["periods"]
        num_modes = eigenvectors.shape[0]
        if num_modes == 0:
            return

        translations = eigenvectors[:, :, :3]
        if translations.shape[1] != mesh.n_points:
            raise ValueError(
                "Eigenvector node count does not match the building mesh point count."
            )

        if scale is None:
            bounds = np.asarray(mesh.bounds, dtype=float)
            spans = bounds[1::2] - bounds[0::2]
            model_size = float(np.linalg.norm(spans))
            max_component = float(np.nanmax(np.abs(translations)))
            scale = 0.05 * model_size / max_component if max_component > 0.0 else 1.0

        columns = min(3, num_modes)
        rows = int(np.ceil(num_modes / columns))
        plotter = pv.Plotter(shape=(rows, columns), window_size=(420 * columns, 360 * rows))

        try:
            for mode_index in range(num_modes):
                row = mode_index // columns
                col = mode_index % columns
                plotter.subplot(row, col)

                warped = mesh.copy()
                warped.points = mesh.points + translations[mode_index] * scale
                frequency = frequencies[mode_index]
                period = periods[mode_index]
                label = (
                    f"Mode {mode_index + 1}\n"
                    f"f = {frequency:.4g} Hz\n"
                    f"T = {period:.4g} s"
                )

                plotter.add_text(label, font_size=10)
                plotter.add_mesh(mesh, style="wireframe", color="black", opacity=0.25)
                plotter.add_mesh(warped, color="steelblue", show_edges=True)
                plotter.view_isometric()

            plotter.show()
        finally:
            plotter.close()

    @staticmethod
    def _print_error_lines(output: str) -> None:
        """Print only useful error lines from captured setup/OpenSees output."""
        if not output:
            return
        keywords = ("error", "warning", "failed", "exception", "traceback")
        lines = [
            line for line in output.splitlines()
            if any(keyword in line.lower() for keyword in keywords)
        ]
        if lines:
            print("\n".join(lines))
