# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

import contextlib
import copy
import io
import math
import os
import subprocess
import tempfile
import weakref
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pyvista as pv

from femora.core.material_base import Material
from femora.components.mesh.general_meshparts import CompositeMesh
from femora.components.element.elastic_beam_column import ElasticBeamColumnElement
from femora.components.element.ghost_node import GhostNodeElement
from femora.components.element.truss import TrussElement
from femora.core.region_base import RegionBase
from femora.constants import FEMORA_MAX_NDF
from femora.core.element_base import Element
from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries
from femora.tools.sections import aisc
from femora.tools.buildings.building import Building


class SteelConcentricallyBracedFrame3D(Building):
    """Create a rectangular 3D steel frame with perimeter axial braces.

    Columns occupy every plan-grid intersection; beams connect adjacent grid
    points at each elevated floor. Story heights and X/Y bay widths control
    geometry independently. Members have six DOFs per node. The defaults are
    five stories, three 8 m bays in each direction, W14X90 columns, W18X35
    beams, and HSS8X8X3/8 X braces in the middle perimeter bays.

    Note:
        **Floors and supports.** Supplied floor masses are concentrated at
        auxiliary nodes at the rectangular plan's geometric center. The center
        is not calculated from member masses. No slab or shell elements are
        generated. Call ``create_rigid_diaphragms()`` after assembly to connect
        floor translations and in-plane rotation. Fixed-base constraints are
        also explicit: call ``apply_fixed_base()`` for a standalone building,
        or connect the base to a foundation in a soil-structure model.

        **Material-driven fiber workflow.** Pass a managed uniaxial material,
        G, and material_density to build(). Beams/columns automatically use
        force-based fiber sections; braces use the same material axially.
        Uniaxial Elastic stays elastic, while Steel01 can yield. AISC supplies
        section geometry and J; user G supplies elastic torsion GJ. Density
        supplies translational mass and rotational inertia independently of
        the constitutive law. No nD reference material or initial-tangent
        extraction is required. This model does not include brace buckling,
        local plate buckling, fracture, or fatigue.
        ``displacement_based`` is not currently a supported building option.

        **Local axes.** Local x follows the member. AISC strong-axis ``Ix`` maps
        to local ``Iy``; AISC weak-axis ``Iy`` maps to local ``Iz``. Fiber depth
        follows local z. Both beam directions have strong-axis vertical bending.
        ``Column_X`` members are strong under global X loading; ``Column_Y``
        members are strong under global Y loading. Columns on the front/back
        grid lines use ``Column_X``; remaining columns use ``Column_Y``.

        **Units and loads.** All inputs must use one consistent unit system.
        ``length_unit_system`` converts AISC geometry only, not materials,
        masses, or loads. With m, kN, tonne, s, steel E is about ``200e6`` and
        yield stress about ``345000``. Floor gravity loads and member inertia
        are separate: ``create_gravity_pattern()`` loads supplied floor masses;
        ``material_density`` in ``build()`` adds member self-mass, not self-weight.

    Examples:
        Build and assemble a fixed-base elastic building:

        ```python
        from femora import Model
        from femora.tools.buildings import SteelConcentricallyBracedFrame3D

        model = Model()
        elastic = model.material.uniaxial.elastic(user_name="steel", E=200e6)
        frame = SteelConcentricallyBracedFrame3D(
            num_stories=3, x_bays=[6.0, 6.0], y_bays=[8.0, 8.0],
            story_heights=[4.0, 3.5, 3.5], floor_masses=[180, 180, 150],
            column_sections=["W14X90", "W14X90", "W14X68"],
        )
        frame.build(model, material=elastic, G=76.923e6, material_density=7.85)
        model.assembler.create_section(
            meshparts=[frame.name_prefix], num_partitions=1,
            partition_algorithm="kd-tree",
        )
        model.assembler.assemble(merge_points=True)
        frame.apply_fixed_base(model)
        frame.create_rigid_diaphragms(model)
        gravity = frame.create_gravity_pattern(model, g=9.81)
        model.process.add_step(gravity, "Apply floor gravity")
        # Add a static analysis step to equilibrate gravity before lateral loading.
        ```

        Use Steel01 in the same fiber workflow. Override a category's material,
        shear modulus, or density without changing other members:

        ```python
        model = Model()
        steel = model.material.uniaxial.steel01(
            user_name="steel", Fy=150000, E0=200e6, b=0.01,
        )
        elastic_beams = model.material.uniaxial.elastic(user_name="beams", E=200e6)
        frame = SteelConcentricallyBracedFrame3D(
            floor_masses=[250, 250, 250, 250, 200],
            member_options={
                "Beam_X": {"material": elastic_beams, "G": 76.923e6, "material_density": 7.85},
                "Brace": {"material_density": 7.85},
            },
        )
        frame.build(model, material=steel, G=76.923e6, material_density=7.85)
        ```

        Supply custom sections without changing the building layout. A factory
        receives keyword arguments and must return a section managed by the
        supplied model. It takes precedence over automatic AISC generation:

        ```python
        from femora.tools.sections import aisc

        def custom_section(*, model, section_name, material, category, unit_system):
            return aisc.create_section(
                section_name, model, material, type="Fiber", GJ=76.923e6 * aisc.get_section_properties(section_name, unit_system)["J"],
                unit_system=unit_system, user_name=f"{category}_{section_name}",
            )

        frame = SteelConcentricallyBracedFrame3D(
            member_formulation="force_based", section_factory=custom_section,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "build", "get_coordinates", "total_height",
                    "plan_dimensions", "apply_fixed_base", "create_rigid_diaphragms",
                    "create_gravity_pattern", "create_pushover_pattern", "get_modes",
                    "get_recorders", "get_results", "export_metadata", "view_story", "estimate_fixed_base_period",
                    "calibrate_to_target_period", "summarize_archetype"],
    }

    VALID_BRACE_PATTERNS = {"x", "single_diagonal", "chevron", "inverted_v"}

    def __init__(
        self,
        name_prefix: str = "steel_concentrically_braced_frame_3d",
        num_stories: int = 5,
        x_bays: Optional[Sequence[float]] = None,
        y_bays: Optional[Sequence[float]] = None,
        story_heights: Optional[Sequence[float]] = None,
        floor_masses: Optional[Sequence[float]] = None,
        brace_bays_x: Optional[Dict[str, Sequence[int]]] = None,
        brace_bays_y: Optional[Dict[str, Sequence[int]]] = None,
        brace_pattern: str = "x",
        brace_area_scale: float = 1.0,
        target_period: Optional[float] = None,
        column_sections: Optional[Union[str, Sequence[str], Dict[Tuple[int, int, int], str]]] = None,
        beam_sections: Optional[Union[str, Sequence[str], Dict[Tuple[int, str, int, int], str]]] = None,
        brace_sections: Optional[Union[str, Sequence[str], Dict[Tuple[str, int, int], str]]] = None,
        n_ele_col: int = 1,
        n_ele_beam: int = 1,
        length_unit_system: str = "m",
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        opensees_exe: Optional[str] = None,
        member_formulation: str = "force_based",
        integration_points: int = 5,
        geometric_transformation: str = "Linear",
        section_factory: Optional[Callable] = None,
        member_options: Optional[Dict[str, dict]] = None,
        flange_fibers: Tuple[int, int] = (12, 4),
        web_fibers: Tuple[int, int] = (4, 16),
        element_max_iterations: int = 10,
        element_tolerance: float = 1e-12,
        brace_properties: Optional[Dict[str, float]] = None,
    ):
        """Create the braced-frame archetype definition.

        Args:
            name_prefix: Mesh part and recorder name prefix.
            num_stories: Number of stories. Defaults to ``5``.
            x_bays: X-direction bay widths. Defaults to three 8 m bays.
            y_bays: Y-direction bay widths. Defaults to three 8 m bays.
            story_heights: Story heights. Defaults to ``[4.0, 3.5, ...]``.
            floor_masses: Masses (not weights) at floor COM nodes, ordered
                bottom to top. Defaults to ``0.0`` per floor. Exclude member
                self-mass here when also providing ``material_density`` to build.
            brace_bays_x: Braced X-bay indices on ``front`` and ``back`` lines.
            brace_bays_y: Braced Y-bay indices on ``left`` and ``right`` lines.
            brace_pattern: ``x``, ``single_diagonal``, ``chevron``, or
                ``inverted_v``.
            brace_area_scale: Multiplier applied to brace area and inertias,
                including custom brace_properties.
            target_period: Optional calibration target. Defaults to ``0.1N``.
            column_sections: AISC name for all columns, a bottom-to-top list
                (last entry repeats), or mapping ``(story, i, j) -> name``.
                Stories start at 1; plan-grid indices start at 0. Missing mapping
                entries use W14X90.
            beam_sections: AISC name, bottom-to-top list, or mapping
                ``(story, direction, i, j) -> name``, where direction is
                ``"x"`` or ``"y"``. Missing entries use W18X35.
            brace_sections: AISC name, bottom-to-top list, or mapping
                ``(line_name, story, bay) -> name`` in the uniaxial workflow.
                Stories start at 1, bays at 0; missing entries use HSS8X8X3/8.
            n_ele_col: Number of elements per column member.
            n_ele_beam: Number of elements per beam member.
            length_unit_system: Unit system passed to AISC section creation.
            origin: Building origin.
            opensees_exe: Optional OpenSees executable path for validation.
            member_formulation: ``"force_based"``. Beams and columns use
                force-based beam-column elements with fiber sections.
            integration_points: Integer 2-10; default 5. Number of Lobatto
                section evaluation points per force-based element, including
                its ends. These are not mesh nodes or cross-section fibers.
            geometric_transformation: ``"Linear"`` (default), ``"PDelta"``,
                or ``"Corotational"`` for beams/columns. Geometry nonlinearity
                does not itself introduce steel yielding.
            section_factory: Optional callable receiving ``model``,
                ``section_name``, ``material``, ``category``, ``unit_system``
                as keywords. Called once per category/section-name pair during
                each build. Must return a section managed by that model.
                Nonelastic sections require force-based members.
            member_options: Overrides keyed by ``"Beam_X"``, ``"Beam_Y"``,
                ``"Column_X"``, ``"Column_Y"``. Accepted keys are
                ``formulation``, ``integration_points``, ``transformation``,
                ``section_factory``,
                ``flange_fibers``, ``web_fibers``, ``max_iterations``,
                ``tolerance``, ``material``, ``G``, ``material_density``. The
                latter three override build inputs in the uniaxial workflow.
                ``Brace`` also accepts material and material_density; its
                axial response does not use G. Unlisted settings inherit defaults.
                These select whole member categories, not individual members.
            flange_fibers: ``(ny, nz)``, default ``(12, 4)``: subdivisions across
                flange width and through thickness. For HSS, top/bottom walls.
            web_fibers: ``(ny, nz)``, default ``(4, 16)``: subdivisions through web
                thickness and along depth. For HSS, the two side walls. Counts
                are per patch, per integration point, not member mesh divisions.
            element_max_iterations: Default 10. Internal force-based compatibility
                iterations, separate from the global analysis iteration limit.
            element_tolerance: Default ``1e-12``. Internal force-based convergence
                tolerance; distinct from the global analysis convergence test.
            brace_properties: Optional shared custom brace geometry with exactly
                ``A``, ``Iy``, and ``Iz``. A must be positive; inertias must be
                nonnegative, and all values finite. Use model units (length
                squared for A, length to the fourth for inertias); these values
                are not converted by length_unit_system. Replaces AISC brace
                lookup and cannot be combined with explicit brace_sections.
                A controls axial stiffness and self-mass. Iy and Iz control
                rotational inertia, not brace bending: braces remain axial
                truss elements. Density comes from build() or the Brace category
                override. J is not needed for axial braces. Floor masses are
                unchanged. For example, with metre-based geometry:

                ```python
                frame = SteelConcentricallyBracedFrame3D(
                    brace_properties={"A": 0.01, "Iy": 1e-5, "Iz": 1e-5},
                    brace_area_scale=1.5,
                )
                ```

        Raises:
            ValueError: Story data, brace layout, member categories, or modeling
                options are invalid or a fiber/element combination is unsupported.

        Note:
            The constructor defines a building; it does not build, assemble,
            apply supports, run gravity, or launch OpenSees. ``target_period``
            stores a calibration target; it does not automatically tune stiffness.
            Use ``n_ele_col``/``n_ele_beam`` to subdivide members, fiber counts to
            refine cross-sections, and ``integration_points`` to sample along
            each force-based element. These are three independent controls.
        """
        self.name_prefix = name_prefix
        self.num_stories = int(num_stories)
        if self.num_stories < 1:
            raise ValueError("num_stories must be positive")

        self.x_bays = list(x_bays) if x_bays is not None else [8.0, 8.0, 8.0]
        self.y_bays = list(y_bays) if y_bays is not None else [8.0, 8.0, 8.0]
        self.story_heights = (
            list(story_heights)
            if story_heights is not None
            else [4.0] + [3.5] * (self.num_stories - 1)
        )
        if len(self.story_heights) != self.num_stories:
            raise ValueError("story_heights length must match num_stories")

        self.num_x_grid = len(self.x_bays) + 1
        self.num_y_grid = len(self.y_bays) + 1
        self.origin = origin
        self.length_unit_system = length_unit_system
        self.n_ele_col = int(n_ele_col)
        self.n_ele_beam = int(n_ele_beam)

        self.floor_masses = (
            list(floor_masses)
            if floor_masses is not None
            else [0.0] * self.num_stories
        )
        if len(self.floor_masses) != self.num_stories:
            raise ValueError("floor_masses length must match num_stories")

        mid_x = max((len(self.x_bays) - 1) // 2, 0)
        mid_y = max((len(self.y_bays) - 1) // 2, 0)
        self.brace_bays_x = {
            "front": list(brace_bays_x.get("front", [])) if brace_bays_x else [mid_x],
            "back": list(brace_bays_x.get("back", [])) if brace_bays_x else [mid_x],
        }
        self.brace_bays_y = {
            "left": list(brace_bays_y.get("left", [])) if brace_bays_y else [mid_y],
            "right": list(brace_bays_y.get("right", [])) if brace_bays_y else [mid_y],
        }

        brace_pattern = brace_pattern.lower()
        if brace_pattern == "x-bracing":
            brace_pattern = "x"
        if brace_pattern not in self.VALID_BRACE_PATTERNS:
            raise ValueError(f"brace_pattern must be one of {sorted(self.VALID_BRACE_PATTERNS)}")
        self.brace_pattern = brace_pattern

        self.brace_area_scale = float(brace_area_scale)
        if not math.isfinite(self.brace_area_scale) or self.brace_area_scale <= 0.0:
            raise ValueError("brace_area_scale must be finite and positive")
        self.brace_properties = None
        if brace_properties is not None:
            if brace_sections is not None:
                raise ValueError("Provide brace_properties or brace_sections, not both")
            if not isinstance(brace_properties, dict) or set(brace_properties) != {"A", "Iy", "Iz"}:
                raise ValueError("brace_properties requires exactly A, Iy, and Iz")
            properties = {key: float(value) for key, value in brace_properties.items()}
            if (not all(math.isfinite(value) for value in properties.values())
                    or properties["A"] <= 0 or properties["Iy"] < 0 or properties["Iz"] < 0):
                raise ValueError("brace_properties requires finite positive A and nonnegative Iy and Iz")
            self.brace_properties = properties
        self.target_period = float(target_period) if target_period is not None else 0.1 * self.num_stories

        self.column_sections = column_sections if column_sections is not None else "W14X90"
        self.beam_sections = beam_sections if beam_sections is not None else "W18X35"
        self.brace_sections = brace_sections if brace_sections is not None else "HSS8X8X3/8"
        self.opensees_exe = opensees_exe
        self.member_formulation = member_formulation
        self.integration_points = integration_points
        self.geometric_transformation = geometric_transformation
        self.section_factory = section_factory
        # Preserve model-managed objects; copying them breaks material identity.
        if any(not isinstance(value, dict) for value in (member_options or {}).values()):
            raise ValueError("member_options values must be dictionaries")
        self.member_options = {key: dict(value) for key, value in (member_options or {}).items()}
        self.flange_fibers = flange_fibers
        self.web_fibers = web_fibers
        self.element_max_iterations = element_max_iterations
        self.element_tolerance = element_tolerance
        allowed = {"formulation", "integration_points", "transformation", "section_factory",
                   "flange_fibers", "web_fibers",
                   "max_iterations", "tolerance", "material", "G", "material_density"}
        categories = {"Beam_X", "Beam_Y", "Column_X", "Column_Y"}
        for category, options in self.member_options.items():
            supported = {"material", "material_density"} if category == "Brace" else allowed
            if category not in categories | {"Brace"} or not isinstance(options, dict) or set(options) - supported:
                raise ValueError("member_options requires frame categories and supported modeling options")
            if "material_density" in options:
                density = float(options["material_density"])
                if not math.isfinite(density) or density < 0:
                    raise ValueError("material_density must be finite and nonnegative")
            if "G" in options and (not math.isfinite(float(options["G"])) or float(options["G"]) <= 0):
                raise ValueError("G must be finite and positive")
        for category in categories:
            options = self._member_settings(category)
            iterations = options["max_iterations"]
            if isinstance(iterations, bool) or not isinstance(iterations, (int, np.integer)) or iterations < 1:
                raise ValueError("max_iterations must be a positive integer")
            if not math.isfinite(options["tolerance"]) or options["tolerance"] <= 0:
                raise ValueError("tolerance must be finite and positive")
            if options["formulation"] != "force_based":
                raise ValueError("formulation must be force_based")
            n = options["integration_points"]
            if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or not 2 <= n <= 10:
                raise ValueError("integration_points must be an integer from 2 through 10")
            if options["transformation"] not in {"Linear", "PDelta", "Corotational"}:
                raise ValueError("Unsupported geometric transformation")
            if options["section_factory"] is not None and not callable(options["section_factory"]):
                raise ValueError("section_factory must be callable")

        self.building_region: Optional[RegionBase] = None
        self._brace_elements: List[TrussElement] = []
        self._com_node_tags: List[int] = []
        self._last_period_result: Optional[Dict[str, object]] = None
        self._last_material: Optional[Material] = None
        self._last_material_density = 0.0

        self._validate_brace_layout()

    def _member_settings(self, category):
        settings = dict(formulation=self.member_formulation,
                        integration_points=self.integration_points,
                        transformation=self.geometric_transformation,
                        section_factory=self.section_factory)
        settings.update(flange_fibers=self.flange_fibers, web_fibers=self.web_fibers,
                        max_iterations=self.element_max_iterations, tolerance=self.element_tolerance)
        settings.update(self.member_options.get(category, {}))
        return settings

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return X, Y, and Z coordinate arrays for grid and floor elevations."""
        x_coords = np.cumsum([0.0] + list(self.x_bays)) + self.origin[0]
        y_coords = np.cumsum([0.0] + list(self.y_bays)) + self.origin[1]
        z_coords = np.cumsum([0.0] + list(self.story_heights)) + self.origin[2]
        return x_coords, y_coords, z_coords

    @property
    def total_height(self) -> float:
        """Total building height."""
        return float(sum(self.story_heights))

    @property
    def plan_dimensions(self) -> Tuple[float, float]:
        """Plan dimensions ``(Lx, Ly)``."""
        return float(sum(self.x_bays)), float(sum(self.y_bays))

    def build(self, model, material: Material, material_density: float = 0.0, *, G: Optional[float] = None) -> CompositeMesh:
        """Create members and floor-mass nodes as a registered mesh part.

        Args:
            model (Model): Femora model receiving materials, sections, transformations,
                element definitions, and the named building mesh part.
            material: Managed uniaxial material for the fiber workflow. Elastic
                gives elastic fibers; Steel01 or another compatible uniaxial law
                gives nonlinear fibers. No separate E or initial tangent is
                required. nD materials are not accepted.
            material_density: Mass density for additional member translational
                and rotational inertia. Defaults to zero. This is separate from
                floor masses and does not create member gravity loads.
            G: Positive shear modulus for the uniaxial workflow. Torsional
                stiffness is G times the AISC-tabulated J. G is not inferred
                from the uniaxial material. Category overrides may supply G.

        Returns:
            CompositeMesh registered under ``name_prefix``. Assemble its mesh
            part with ``merge_points=True`` to connect coincident member ends.

        Raises:
            ValueError: AISC sections cannot be resolved, a custom section belongs
                to another model, or fiber/brace materials are invalid.

        Note:
            Call this before assembly. Supports, diaphragms, patterns, recorders,
            and analysis steps are separate API calls. Built-in fibers use
            rectangular flange/web or HSS-wall patches with elastic torsion;
            rolled fillets and rounded corners are not included.
            In the uniaxial workflow, member masses and rotational inertias use
            AISC area/inertias, including nonlinear axial braces. Density
            overrides apply per category. Fiber stiffness follows the actual
            fiber geometry, which can differ slightly from tabulated geometry.
        """
        density = float(material_density)
        if not math.isfinite(density) or density < 0:
            raise ValueError("material_density must be finite and nonnegative")
        if G is not None and (not math.isfinite(float(G)) or float(G) <= 0):
            raise ValueError("G must be finite and positive")
        if getattr(material, "material_type", None) != "uniaxialMaterial":
            raise ValueError("material must be a managed uniaxial material")
        if model.material.get(material.tag) is not material:
            raise ValueError("material must belong to the supplied model")
        self._last_G = None if G is None else float(G)
        self._member_densities = {}
        self._mass_geometry = {}
        self._last_material = material
        self._last_material_density = float(material_density)
        self._results_model = weakref.ref(model)
        self._member_definitions = []
        element_categories = {}
        self._brace_elements = []

        x_coords, y_coords, z_coords = self.get_coordinates()
        elements_cache: Dict[Tuple[str, str], Element] = {}
        fiber_material_cache = {}
        all_points: List[List[float]] = []
        all_cells: List[int] = []
        cell_element_tags: List[int] = []
        current_point_id = 0

        transf_col_x = model.transformation.transformation3d("Linear", 1, 0, 0, description="CBF_Column_Transf_X")
        transf_col_y = model.transformation.transformation3d("Linear", 0, 1, 0, description="CBF_Column_Transf_Y")
        transf_beam_x = model.transformation.transformation3d("Linear", 0, 0, 1, description="CBF_Beam_Transf_X")
        transf_beam_y = model.transformation.transformation3d("Linear", 0, 0, 1, description="CBF_Beam_Transf_Y")

        def get_or_create_beam_element(category: str, section_name: str) -> Element:
            key = (category, section_name)
            if key in elements_cache:
                return elements_cache[key]  # type: ignore[return-value]
            settings = self._member_settings(category)
            try:
                factory = settings["section_factory"]
                if factory is not None:
                    section = factory(model=model, section_name=section_name, material=material,
                                      category=category, unit_system=self.length_unit_system)
                    if section is None or model.section.get(section.tag) is not section:
                        raise ValueError("section_factory must return a section belonging to this model")
                else:
                    fiber_material = settings.get("material", material)
                    if callable(fiber_material):
                        factory_key = id(fiber_material)
                        if factory_key not in fiber_material_cache:
                            fiber_material_cache[factory_key] = fiber_material(model)
                        fiber_material = fiber_material_cache[factory_key]
                    if (getattr(fiber_material, "material_type", None) != "uniaxialMaterial"
                            or model.material.get(fiber_material.tag) is not fiber_material):
                        raise ValueError("member material must be a managed uniaxial material")
                    properties = aisc.get_section_properties(section_name, self.length_unit_system)
                    shear_modulus = settings.get("G", G)
                    if shear_modulus is None:
                        raise ValueError("G is required globally or in member_options")
                    section = aisc.create_section(
                        section_name, model, fiber_material, type="Fiber",
                        unit_system=self.length_unit_system,
                        user_name=f"{self.name_prefix}_{category}_{section_name}_fiber",
                        GJ=float(shear_modulus) * properties["J"],
                        flange_fibers=settings["flange_fibers"], web_fibers=settings["web_fibers"])
            except Exception as exc:
                raise ValueError(f"Could not create section '{section_name}' for {category}: {exc}") from exc

            if category == "Beam_X":
                transformation = transf_beam_x
            elif category == "Beam_Y":
                transformation = transf_beam_y
            elif category == "Column_X":
                transformation = transf_col_x
            elif category == "Column_Y":
                transformation = transf_col_y
            else:
                raise ValueError(f"Unknown frame member category: {category}")
            if settings["transformation"] != "Linear":
                vector = (0, 0, 1) if category.startswith("Beam") else (
                    (1, 0, 0) if category == "Column_X" else (0, 1, 0))
                transformation = model.transformation.transformation3d(
                    settings["transformation"], *vector, description=f"CBF_{category}_Transf")
            element = model.element.beam.force(
                ndof=6, section=section, transformation=transformation,
                numIntgrPts=settings["integration_points"],
                maxIters=settings["max_iterations"], tol=settings["tolerance"])
            elements_cache[key] = element
            element_categories[element.tag] = category
            self._member_densities[element.tag] = float(settings.get("material_density", density))
            if settings["section_factory"] is None:
                self._mass_geometry[element.tag] = aisc.get_section_properties(section_name, self.length_unit_system)
            return element

        brace_name = ("custom" if self.brace_properties is not None else
                      self._section_for(self.brace_sections, 1, 0, 0, default="HSS8X8X3/8"))
        brace_geometry = (dict(self.brace_properties) if self.brace_properties is not None else
                          aisc.get_section_properties(brace_name, self.length_unit_system))
        for key in ("A", "Iy", "Iz"):
            brace_geometry[key] *= self.brace_area_scale
        brace_material = self.member_options.get("Brace", {}).get("material", material)
        if callable(brace_material):
            key = id(brace_material)
            if key not in fiber_material_cache:
                fiber_material_cache[key] = brace_material(model)
            brace_material = fiber_material_cache[key]
        if (getattr(brace_material, "material_type", None) != "uniaxialMaterial"
                or model.material.get(brace_material.tag) is not brace_material):
            raise ValueError("Brace material must be a managed uniaxial material")
        brace_section = model.section.fiber.section(
            user_name=f"{self.name_prefix}_brace_axial", GJ=1.0)
        brace_section.add_fiber(0., 0., brace_geometry["A"], brace_material)
        brace_element = model.element.beam.truss(ndof=6, section=brace_section, rho=0.0)
        self._member_densities[brace_element.tag] = float(
            self.member_options.get("Brace", {}).get("material_density", density))
        self._mass_geometry[brace_element.tag] = brace_geometry
        self._brace_elements.append(brace_element)
        brace_cache = {brace_name: brace_element}

        def brace_for(story_number, line_name, bay):
            if self.brace_properties is not None:
                return brace_element
            if isinstance(self.brace_sections, dict):
                name = self.brace_sections.get((line_name, story_number, bay), "HSS8X8X3/8")
            else:
                name = self._section_for(self.brace_sections, story_number, 0, 0, default="HSS8X8X3/8")
            if name not in brace_cache:
                properties = aisc.get_section_properties(name, self.length_unit_system)
                for key in ("A", "Iy", "Iz", "J"):
                    properties[key] *= self.brace_area_scale
                section = model.section.fiber.section(
                    user_name=f"{self.name_prefix}_brace_{name}", GJ=1.0)
                section.add_fiber(0., 0., properties["A"], brace_material)
                element = model.element.beam.truss(ndof=6, section=section, rho=0.0)
                brace_cache[name] = element
                self._brace_elements.append(element)
                self._mass_geometry[element.tag] = properties
                self._member_densities[element.tag] = self._member_densities[brace_element.tag]
                element_categories[element.tag] = "Brace"
            return brace_cache[name]

        def add_element_segment(element: Element, p1: Sequence[float], p2: Sequence[float]) -> None:
            nonlocal current_point_id
            all_points.append(list(map(float, p1)))
            all_points.append(list(map(float, p2)))
            all_cells.extend([2, current_point_id, current_point_id + 1])
            current_point_id += 2
            cell_element_tags.append(element.tag)

        def add_member(element: Element, p_start: Sequence[float], p_end: Sequence[float], n_ele: int) -> None:
            p_start_arr = np.asarray(p_start, dtype=float)
            p_end_arr = np.asarray(p_end, dtype=float)
            vector = p_end_arr - p_start_arr
            n = max(int(n_ele), 1)
            category = "Brace" if element is brace_element else element_categories[element.tag]
            member = dict(member=len(self._member_definitions)+1,
                          kind="brace" if category == "Brace" else ("beam" if category.startswith("Beam") else "column"),
                          category=category, story=story, definition=element.tag,
                          section=element.get_section().tag,
                          material_density=self._member_densities[element.tag], segments=[])
            for k in range(n):
                p1, p2 = p_start_arr + vector * (k / n), p_start_arr + vector * ((k + 1) / n)
                add_element_segment(element, p1, p2)
                member["segments"].append((p1.copy(), p2.copy()))
            self._member_definitions.append(member)

        # Columns at all grid intersections.
        for story in range(1, self.num_stories + 1):
            for i in range(self.num_x_grid):
                for j in range(self.num_y_grid):
                    category = "Column_X" if (j == 0 or j == self.num_y_grid - 1) else "Column_Y"
                    section = self._section_for(self.column_sections, story, i, j, default="W14X90")
                    element = get_or_create_beam_element(category, section)
                    p1 = [x_coords[i], y_coords[j], z_coords[story - 1]]
                    p2 = [x_coords[i], y_coords[j], z_coords[story]]
                    add_member(element, p1, p2, self.n_ele_col)

        # Floor beams in both directions at every elevated floor.
        for story in range(1, self.num_stories + 1):
            z = z_coords[story]
            for j in range(self.num_y_grid):
                for i in range(len(self.x_bays)):
                    section = self._section_for(self.beam_sections, story, i, j, direction="X", default="W18X35")
                    element = get_or_create_beam_element("Beam_X", section)
                    add_member(element, [x_coords[i], y_coords[j], z], [x_coords[i + 1], y_coords[j], z], self.n_ele_beam)
            for i in range(self.num_x_grid):
                for j in range(len(self.y_bays)):
                    section = self._section_for(self.beam_sections, story, i, j, direction="Y", default="W18X35")
                    element = get_or_create_beam_element("Beam_Y", section)
                    add_member(element, [x_coords[i], y_coords[j], z], [x_coords[i], y_coords[j + 1], z], self.n_ele_beam)

        # Selected braced bays.
        for story in range(1, self.num_stories + 1):
            z_bot = z_coords[story - 1]
            z_top = z_coords[story]
            for line_name, bay_indices in self.brace_bays_x.items():
                j = 0 if line_name == "front" else self.num_y_grid - 1
                for bay in bay_indices:
                    self._add_brace_pattern(
                        add_member,
                        brace_for(story, line_name, bay),
                        [x_coords[bay], y_coords[j], z_bot],
                        [x_coords[bay + 1], y_coords[j], z_bot],
                        [x_coords[bay], y_coords[j], z_top],
                        [x_coords[bay + 1], y_coords[j], z_top],
                    )
            for line_name, bay_indices in self.brace_bays_y.items():
                i = 0 if line_name == "left" else self.num_x_grid - 1
                for bay in bay_indices:
                    self._add_brace_pattern(
                        add_member,
                        brace_for(story, line_name, bay),
                        [x_coords[i], y_coords[bay], z_bot],
                        [x_coords[i], y_coords[bay + 1], z_bot],
                        [x_coords[i], y_coords[bay], z_top],
                        [x_coords[i], y_coords[bay + 1], z_top],
                    )

        points_array = np.asarray(all_points, dtype=float)
        cells_array = np.asarray(all_cells)
        cell_types = np.asarray([pv.CellType.LINE] * len(cell_element_tags))
        grid = pv.UnstructuredGrid(cells_array, cell_types, points_array)
        grid.cell_data["ElementTag"] = np.asarray(cell_element_tags, dtype=np.uint16)
        grid = grid.clean(tolerance=1e-5)

        if "Mass" not in grid.point_data:
            grid.point_data["Mass"] = np.zeros((grid.n_points, FEMORA_MAX_NDF), dtype=np.float32)
        if "ndf" not in grid.point_data:
            grid.point_data["ndf"] = np.full(grid.n_points, 6, dtype=np.uint16)
        self._add_member_self_mass(grid, model, material_density)
        grid = self._add_center_of_mass_nodes(grid, model)

        self.building_region = model.region.element()
        return model.meshpart.general.composite(
            user_name=self.name_prefix,
            mesh=grid,
            region=self.building_region,
        )

    def create_rigid_diaphragms(self, model, verbose: bool = True) -> None:
        """Connect each floor's structural grid nodes to its auxiliary mass node.

        Args:
            model (Model): Assembled model containing this building.
            verbose: Print a floor-by-floor constraint summary; default True.

        Raises:
            ValueError: The building mesh has not been assembled.

        Note:
            Constraints act in the global XY plane. The auxiliary mass node
            retains Ux, Uy, Rz; its Uz, Rx, Ry are fixed. Structural floor joints
            retain their own vertical displacement and bending rotations.
            This creates in-plane rigid floor behavior, not a slab mesh.
            Use a compatible analysis constraint handler, such as Transformation.
            Call before creating a pushover pattern at the floor mass nodes.
        """
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating rigid diaphragms.")

        points = mesh.points
        ndfs = mesh.point_data["ndf"]
        start_node_tag = model._start_nodetag
        x_coords, y_coords, z_coords = self.get_coordinates()
        x_set = {round(float(value), 4) for value in x_coords}
        y_set = {round(float(value), 4) for value in y_coords}
        x_min = float(min(x_coords)) - 1e-4
        x_max = float(max(x_coords)) + 1e-4
        y_min = float(min(y_coords)) - 1e-4
        y_max = float(max(y_coords)) + 1e-4
        self._com_node_tags = []
        structure_name = getattr(self, "name_prefix", None) or self.__class__.__name__

        if verbose:
            border = "-" * 66
            print(f"\n[{structure_name}] Rigid diaphragm creation")
            print(border)
            print(f"{'Story':<8}{'Status':<12}{'Master':<12}{'Slaves':<10}{'Z':<12}")
            print(border)

        for story in range(1, self.num_stories + 1):
            z_floor = float(z_coords[story])
            floor_mask = np.abs(points[:, 2] - z_floor) < 1e-4
            footprint_mask = (
                (points[:, 0] >= x_min)
                & (points[:, 0] <= x_max)
                & (points[:, 1] >= y_min)
                & (points[:, 1] <= y_max)
            )
            floor_indices = np.where(floor_mask & footprint_mask)[0]
            if not len(floor_indices):
                if verbose:
                    print(f"{story:>5d}   {'skipped':<12}{'-':<12}{'-':<10}{z_floor:<12.3f}")
                continue

            floor_ndfs = ndfs[floor_indices]
            com_candidates = np.where(floor_ndfs >= 1000)[0]
            if not len(com_candidates):
                if verbose:
                    print(f"{story:>5d}   {'no COM':<12}{'-':<12}{'-':<10}{z_floor:<12.3f}")
                continue

            com_global_idx = int(floor_indices[com_candidates[0]])
            master_tag = int(com_global_idx + start_node_tag)
            self._com_node_tags.append(master_tag)
            slave_tags: List[int] = []

            for local_idx, global_idx in enumerate(floor_indices):
                if int(global_idx) == com_global_idx:
                    continue
                px = round(float(points[global_idx, 0]), 4)
                py = round(float(points[global_idx, 1]), 4)
                if px in x_set and py in y_set and int(ndfs[global_idx]) < 1000:
                    slave_tags.append(int(global_idx + start_node_tag))

            for slave_tag in slave_tags:
                model.constraint.mp.rigid_diaphragm(
                    direction=3,
                    master_node=master_tag,
                    slave_nodes=[slave_tag],
                )
            model.constraint.sp.fix(master_tag, [0, 0, 1, 1, 1, 0])
            if verbose:
                print(f"{story:>5d}   {'created':<12}{master_tag:<12}{len(slave_tags):<10}{z_floor:<12.3f}")

        if verbose:
            print(border)

    def apply_fixed_base(self, model, tol: float = 1e-4) -> None:
        """Fix all base structural grid nodes for fixed-base period checks."""
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before fixing base nodes.")
        z_base = float(self.get_coordinates()[2][0])
        ndfs = mesh.point_data["ndf"]
        for idx, point in enumerate(mesh.points):
            if abs(float(point[2]) - z_base) > tol or int(ndfs[idx]) >= 1000:
                continue
            model.constraint.sp.fix(int(idx + model._start_nodetag), [1, 1, 1, 1, 1, 1])

    def create_gravity_pattern(self, model, g: float) -> Pattern:
        """Create downward floor loads using the nonnegative gravity magnitude ``g``.

        Pass ``g=9.81`` for gravity in m/s2. The negative Z sign is applied
        internally. Negative or nonfinite values raise ``ValueError``.

        Args:
            model (Model): Assembled Femora model containing the building.
            g: Finite nonnegative acceleration magnitude. Zero is permitted.

        Returns:
            Managed Plain pattern with a constant time series. Each supplied
            floor weight is shared equally among its structural plan-grid nodes.
            The pattern is not automatically added to the process.

        Raises:
            ValueError: g is negative/nonfinite or the mesh is not assembled.

        Note:
            These loads use ``floor_masses`` only. Member self-mass added during
            build is not automatically converted to additional weight. Run a
            static analysis after adding this pattern; hold gravity with
            ``model.actions.load_const()`` before starting a conventional pushover.

        Example:
            ```python
            gravity = frame.create_gravity_pattern(model, g=9.81)
            model.process.add_step(gravity, "Apply floor weights")
            # Add the gravity static analysis, then load_const, then lateral loads.
            ```
        """
        g = float(g)
        if not math.isfinite(g) or g < 0.0:
            raise ValueError(
                "g must be a finite, nonnegative gravity magnitude (e.g. 9.81); "
                "the downward negative-Z sign is applied internally."
            )
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating gravity loads.")

        x_coords, y_coords, z_coords = self.get_coordinates()
        x_set = {round(float(v), 4) for v in x_coords}
        y_set = {round(float(v), 4) for v in y_coords}
        ndfs = mesh.point_data["ndf"]

        ts = model.time_series.constant(factor=1.0)
        pattern = model.pattern.plain(time_series=ts, factor=1.0)
        n_per_floor = self.num_x_grid * self.num_y_grid
        for story in range(1, self.num_stories + 1):
            floor_mass = float(self.floor_masses[story - 1])
            if floor_mass == 0.0:
                continue
            fz = -(floor_mass * float(g)) / float(n_per_floor)
            floor_indices = np.where(np.abs(mesh.points[:, 2] - z_coords[story]) < 1e-4)[0]
            selected_ids: List[int] = []
            for idx in floor_indices:
                px = round(float(mesh.points[idx, 0]), 4)
                py = round(float(mesh.points[idx, 1]), 4)
                if px in x_set and py in y_set and int(ndfs[idx]) < 1000:
                    selected_ids.append(int(idx))
            if not selected_ids:
                continue
            node_mask = model.mask.nodes.by_ids(selected_ids)
            if not node_mask.is_empty():
                pattern.add_load.node(node_mask=node_mask, values=[0.0, 0.0, fz, 0.0, 0.0, 0.0])
        return pattern

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
    ) -> Pattern:
        """Create reference horizontal loads at this frame's floor mass nodes.

        Assemble the model and call ``create_rigid_diaphragms()`` first. Each
        floor resultant acts at the auxiliary node at the rectangular plan's
        geometric center, where the supplied floor mass is concentrated.

        Args:
            model (Model): Assembled Femora model containing this building.
            time_series: Mandatory time series managed by this model. Use a
                linear series for conventional displacement-controlled pushover.
                A constant series does not supply an adjustable load factor.
            base_shear: Positive reference total horizontal force, in the
                model's force units, before time-series scaling.
            direction: ``"x"``, ``"y"``, or degrees counterclockwise from
                global X toward Y. Use 180 or 270 for the negative directions.
            distribution: ``"mass"`` (alias ``"uniform"``),
                ``"mass_height"`` (alias ``"triangular"``), ``"modal"``,
                or one nonnegative relative force weight per floor. Mass-based
                patterns use the supplied ``floor_masses``, excluding member
                self-mass. Heights are measured above the building base.
            mode_shape: For ``"modal"`` only, one horizontal modal amplitude
                per floor, already projected onto the loading direction.
                Forces are proportional to mass times amplitude. Signed
                profiles are supported unless their net resultant is zero.
                No solver is launched and no mode is selected automatically.
            eccentricity: Global ``(ex, ey)`` offset from each floor mass node,
                in model length units. Adds ``Mz = ex*Fy - ey*Fx``.

        Returns:
            Managed Plain load pattern with six-component nodal loads. Add it
            to ``model.process`` separately from the static analysis. Forces
            sum to ``base_shear`` along the selected direction at unit series
            factor; this is a net signed resultant for modal distributions.

        Raises:
            ValueError: Inputs are invalid, floor nodes are missing or
                ambiguous, or rigid diaphragms have not been created.

        Example:
            ```python
            pattern = building.create_pushover_pattern(
                model,
                time_series=model.time_series.linear(),
                base_shear=1000.0,
                direction="x",
                distribution="mass_height",
            )
            model.process.add_step(pattern, "Apply lateral reference loads")
            ```
        """
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating pushover loads.")
        if (not isinstance(time_series, TimeSeries) or time_series.tag is None
                or model.time_series.get(time_series.tag) is not time_series):
            raise ValueError("time_series must be managed by this model.")
        base_shear = float(base_shear)
        if not math.isfinite(base_shear) or base_shear <= 0.0:
            raise ValueError("base_shear must be positive and finite; use direction to reverse loading.")
        if isinstance(direction, str):
            if direction.lower() not in {"x", "y"}:
                raise ValueError("direction must be 'x', 'y', or a finite angle in degrees.")
            angle = 0.0 if direction.lower() == "x" else 90.0
        else:
            angle = float(direction)
            if not math.isfinite(angle):
                raise ValueError("direction angle must be finite.")
        unit = np.array([math.cos(math.radians(angle % 360)), math.sin(math.radians(angle % 360))])
        unit[np.abs(unit) < 1e-14] = 0.0
        offsets = np.asarray(eccentricity, dtype=float)
        if offsets.shape != (2,) or not np.isfinite(offsets).all():
            raise ValueError("eccentricity must contain two finite global XY offsets.")
        masses = np.asarray(self.floor_masses, dtype=float)
        x, y, z = self.get_coordinates()
        heights = np.asarray(z[1:] - z[0], dtype=float)
        if not np.isfinite(masses).all() or np.any(masses < 0):
            raise ValueError("floor_masses must be finite and nonnegative.")
        if not np.isfinite(heights).all() or np.any(np.diff(z) <= 0):
            raise ValueError("Floor elevations must be finite and strictly increasing.")
        if isinstance(distribution, str):
            kind = distribution.lower()
            if mode_shape is not None and kind != "modal":
                raise ValueError("mode_shape is only used with distribution='modal'.")
            if kind in {"mass", "uniform"}:
                weights = masses.copy()
            elif kind in {"mass_height", "triangular"}:
                weights = masses * heights
            elif kind == "modal":
                amplitudes = np.asarray(mode_shape, dtype=float)
                if amplitudes.shape != (self.num_stories,) or not np.isfinite(amplitudes).all():
                    raise ValueError("mode_shape must contain one finite horizontal amplitude per floor.")
                weights = masses * amplitudes
            else:
                raise ValueError("Unknown distribution; use mass, mass_height, modal, or floor weights.")
        else:
            if mode_shape is not None:
                raise ValueError("mode_shape cannot be combined with custom floor weights.")
            weights = np.asarray(distribution, dtype=float)
            if np.any(weights < 0):
                raise ValueError("Custom floor weights must be nonnegative.")
        if weights.shape != (self.num_stories,) or not np.isfinite(weights).all():
            raise ValueError("Distribution must contain one finite weight per floor.")
        maximum = np.max(np.abs(weights))
        if maximum == 0:
            raise ValueError("Load distribution must have a nonzero resultant.")
        scaled = weights / maximum
        total = scaled.sum()
        if abs(total) <= 1e-12 * np.abs(scaled).sum():
            raise ValueError("Load distribution has a zero or near-zero net resultant.")
        forces = (base_shear * (scaled / total))[:, None] * unit
        moments = offsets[0] * forces[:, 1] - offsets[1] * forces[:, 0]
        if not np.isfinite(forces).all() or not np.isfinite(moments).all():
            raise ValueError("Reference loads exceed the finite numeric range.")

        if len(self._com_node_tags) != self.num_stories:
            raise ValueError("Call create_rigid_diaphragms(model) before creating pushover loads.")
        center = [(x[0] + x[-1]) / 2.0, (y[0] + y[-1]) / 2.0]
        node_ids = []
        for floor, elevation in enumerate(z[1:]):
            expected = np.array([*center, elevation])
            candidates = np.flatnonzero(
                (np.max(np.abs(mesh.points - expected), axis=1) < 1e-4)
                & (mesh.point_data["ndf"] >= 1000)
            )
            if len(candidates) != 1 or int(candidates[0] + model._start_nodetag) != self._com_node_tags[floor]:
                raise ValueError("Floor mass nodes do not match this building; recreate its rigid diaphragms.")
            node_ids.append(int(candidates[0]))

        # Validate every input and target before registering any new model objects.
        pattern = model.pattern.plain(time_series=time_series, factor=1.0)
        for node_id, (fx, fy), mz in zip(node_ids, forces, moments):
            pattern.add_load.node(
                node_mask=model.mask.nodes.by_ids([node_id]),
                values=[float(fx), float(fy), 0.0, 0.0, 0.0, float(mz)],
            )
        return pattern

    def get_modes(
        self,
        num_modes: int,
        *,
        material: Optional[Union[Dict[str, object], Callable]] = None,
        material_density: Optional[float] = None,
        opensees_exe: Optional[str] = None,
        print_results: bool = False,
        plot: bool = False,
        plot_scale: Optional[float] = None,
        G: Optional[float] = None,
    ) -> Dict[str, np.ndarray]:
        """Return modal frequencies, periods, and eigenvectors.

        This method builds a copy of the braced frame in a separate temporary
        ``Model`` instance, applies fixed-base and rigid-diaphragm constraints,
        runs OpenSees from a temporary Tcl script, and parses modal data from
        OpenSees output.

        Args:
            num_modes: Number of eigen modes to request from OpenSees.
            material: Material definition for the isolated modal model. Use
                ``None`` to create a default uniaxial Elastic steel material.
                Pass a dictionary with ``type="Elastic"`` or ``type="Steel01"``
                and the corresponding material parameters. Pass a
                callable when the material must be created manually inside the
                temporary modal model.
            material_density: Density used by ``build()`` to compute member
                self-mass. This is separate from the material object because
                member mass is a building-generation calculation, while
                ``rho`` on the material is an OpenSees material parameter. If
                omitted, Femora uses ``material["rho"]`` for dict materials,
                attempts to infer density from callable-created materials, and
                otherwise falls back to the default A992 density.
            opensees_exe: Optional OpenSees executable path. If omitted, the
                ``FEMORA_OPENSEES`` environment variable is used.
            print_results: If ``True``, print a formatted table of modal
                frequencies and periods.
            plot: If ``True``, show PyVista mode-shape plots for the requested
                modes using the isolated building mesh.
            plot_scale: Optional deformation scale for plotting. If omitted,
                a scale is estimated from the mesh size and eigenvector
                magnitudes.
            G: Shear modulus for modal builds using a uniaxial material. Supply
                a material dictionary such as ``{"type": "Elastic", "E": 200e6}``
                or a factory creating any compatible uniaxial law in the modal
                model. Density remains a separate input. No tangent accessor
                is required. G selects the same fiber workflow as build().

        Returns:
            Dictionary with ``frequencies``, ``periods``, ``node_tags``,
            ``node_coordinates``, ``node_ndf``, and ``eigenvectors``. Coordinates follow the
            returned node-tag order. The eigenvector array has shape
            ``(num_modes, num_nodes, ndof)``.
            ``node_ndf`` retains the mesh's DOF markers, including auxiliary
            COM markers, to distinguish coincident structural and mass nodes.

        !!! note "Material ownership"

            ``get_modes()`` builds a separate temporary ``Model()`` so modal
            analysis cannot accidentally mutate the user's active model. For
            that reason, do not pass a ``Material`` object from another model.
            Use a material dictionary or a callable factory so the material is
            created inside the temporary modal model with the correct managers
            and tags.

            Returned modes
            describe the tangent state reached by this method's gravity setup,
            not an assumed amplitude-independent mode of a yielding structure.

        Examples:
            Use the same fiber workflow for elastic modes:

            ```python
            result = frame.get_modes(
                num_modes=6,
                material={"type": "Elastic", "E": 200e6},
                G=76.923e6,
                material_density=7.85,
                opensees_exe=opensees_path,
                plot=True,
            )
            ```
        """
        if num_modes < 1:
            raise ValueError("num_modes must be a positive integer")
        if G is None or not math.isfinite(float(G)) or float(G) <= 0:
            raise ValueError("get_modes requires finite positive G")
        if isinstance(material, dict) and str(material.get("type", "")).lower() not in {"elastic", "steel01"}:
            raise ValueError("Modal material dictionaries require type='Elastic' or 'Steel01'; use a factory for other uniaxial laws")
        for options in self.member_options.values():
            if options.get("material") is not None and not callable(options["material"]):
                raise ValueError("get_modes member material overrides must be factories")

        executable = opensees_exe or os.environ.get("FEMORA_OPENSEES")
        if not executable:
            raise RuntimeError(
                "OpenSees executable was not provided. Pass opensees_exe or set FEMORA_OPENSEES."
            )

        import femora as fm

        cloned_frame = SteelConcentricallyBracedFrame3D(
            name_prefix=self.name_prefix,
            num_stories=self.num_stories,
            x_bays=copy.deepcopy(self.x_bays),
            y_bays=copy.deepcopy(self.y_bays),
            story_heights=copy.deepcopy(self.story_heights),
            floor_masses=copy.deepcopy(self.floor_masses),
            brace_bays_x=copy.deepcopy(self.brace_bays_x),
            brace_bays_y=copy.deepcopy(self.brace_bays_y),
            brace_pattern=self.brace_pattern,
            brace_area_scale=self.brace_area_scale,
            target_period=self.target_period,
            column_sections=copy.deepcopy(self.column_sections),
            beam_sections=copy.deepcopy(self.beam_sections),
            brace_sections=(None if self.brace_properties is not None else
                            copy.deepcopy(self.brace_sections)),
            brace_properties=copy.deepcopy(self.brace_properties),
            n_ele_col=self.n_ele_col,
            n_ele_beam=self.n_ele_beam,
            length_unit_system=self.length_unit_system,
            origin=copy.deepcopy(self.origin),
            opensees_exe=executable,
            flange_fibers=self.flange_fibers,
            web_fibers=self.web_fibers,
            element_max_iterations=self.element_max_iterations,
            element_tolerance=self.element_tolerance,
            member_formulation=self.member_formulation,
            integration_points=self.integration_points,
            geometric_transformation=self.geometric_transformation,
            section_factory=self.section_factory,
            member_options=self.member_options,
        )

        with tempfile.TemporaryDirectory(prefix="femora_modes_") as tmpdir:
            setup_output = io.StringIO()
            try:
                with contextlib.redirect_stdout(setup_output), contextlib.redirect_stderr(setup_output):
                    run_dir = Path(tmpdir)
                    model = fm.Model()
                    model.clear_model()
                    model.set_results_folder((run_dir / "Results").as_posix())

                    kip = 4.44822
                    inch = 0.0254
                    lb = 0.453592
                    ft = 12.0 * inch
                    default_density = 490.0 * lb / (ft * ft * ft) / 1000.0
                    modal_material = material
                    if material is None:
                        modal_material = dict(type="Elastic", E=29000.0 * kip / (inch * inch))
                    steel_material, resolved_density = self._resolve_modal_material(
                        model,
                        material=modal_material,
                        material_density=material_density,
                        default_name="Steel_A992",
                        default_E=29000.0 * kip / (inch * inch),
                        default_nu=0.3,
                        default_density=default_density,
                    )

                    building_part = cloned_frame.build(
                        model=model, material=steel_material,
                        material_density=resolved_density, G=G)
                    first_mode_frequency = (
                        1.0 / cloned_frame.target_period
                        if cloned_frame.target_period > 0.0
                        else 0.34
                    )
                    damping = model.damping.uniform(
                        dampingRatio=0.05,
                        freql=first_mode_frequency,
                        freq2=10.0 * first_mode_frequency,
                    )
                    building_part.set_damping(damping)

                    model.assembler.create_section(
                        [cloned_frame.name_prefix],
                        num_partitions=0,
                        merge_points=True,
                        partition_algorithm="kd-tree",
                    )
                    model.assembler.assemble(merge_points=False)
                    cloned_frame.apply_fixed_base(model, tol=0.01)
                    cloned_frame.create_rigid_diaphragms(model, verbose=False)

                    gravity_load = cloned_frame.create_gravity_pattern(model, g=9.81)
                    constraint_handler = model.analysis.constraint.transformation()
                    numberer = model.analysis.numberer.rcm()
                    system = model.analysis.system.bandgeneral()
                    algorithm = model.analysis.algorithm.newton()
                    test = model.analysis.test.energyincr(tol=1e-4, max_iter=10, print_flag=5)
                    integrator = model.analysis.integrator.newmark(gamma=0.6, beta=0.3025)
                    gravity = model.analysis.transient(
                        name="gravity",
                        constraint_handler=constraint_handler,
                        numberer=numberer,
                        system=system,
                        algorithm=algorithm,
                        test=test,
                        integrator=integrator,
                        dt=0.1,
                        num_steps=300,
                    )

                    start_node = model.get_start_node_tag()
                    end_node = model.get_max_node_tag()
                    eigen_tcl = f"""
wipeAnalysis
constraints Transformation
numberer RCM
system FullGeneral
test NormDispIncr 1.0e-8 10 0
algorithm Linear
integrator LoadControl 0.0
analysis Static
set numModes {num_modes}
set eigenvalues [eigen -fullGenLapack $numModes]
for {{set i 1}} {{$i <= [llength $eigenvalues]}} {{incr i}} {{
    set lambda [lindex $eigenvalues [expr {{$i - 1}}]]
    if {{$lambda <= 0.0}} {{
        puts "FEMORA_EIGENVALUE $i $lambda nan nan"
    }} else {{
        set frequency [expr {{sqrt($lambda) / (2.0 * 3.141592653589793)}}]
        set period [expr {{1.0 / $frequency}}]
        puts "FEMORA_EIGENVALUE $i $lambda $frequency $period"
    }}
}}
for {{set mode 1}} {{$mode <= $numModes}} {{incr mode}} {{
    for {{set nodeTag {start_node}}} {{$nodeTag <= {end_node}}} {{incr nodeTag}} {{
        set values [nodeEigenvector $nodeTag $mode]
        puts "FEMORA_EIGENVECTOR $mode $nodeTag $values"
    }}
}}
wipeAnalysis
"""

                    model.process.add_step(gravity_load, description="Apply gravity load")
                    model.process.add_step(gravity, description="Gravity analysis")
                    model.process.add_step(
                        model.actions.tcl("loadConst -time 0.0"),
                        description="Hold gravity loads",
                    )
                    model.process.add_step(model.actions.tcl(eigen_tcl), description="Eigen analysis")

                    tcl_file = run_dir / "model.tcl"
                    model.export_to_tcl(tcl_file.as_posix())
            except Exception:
                self._print_error_lines(setup_output.getvalue())
                raise

            completed = subprocess.run(
                [executable, tcl_file.as_posix()],
                cwd=run_dir,
                capture_output=True,
                text=True,
            )
            opensees_output = "\n".join(
                output for output in (completed.stdout, completed.stderr) if output
            )
            if completed.returncode != 0:
                if opensees_output:
                    self._print_error_lines(opensees_output)
                raise RuntimeError(f"OpenSees failed with exit code {completed.returncode}")

            result = self._parse_eigen_stdout(
                opensees_output,
                num_modes=num_modes,
                start_node=start_node,
                end_node=end_node,
            )
            result["node_coordinates"] = np.asarray(model.assembler.get_mesh().points, dtype=float).copy()
            result["node_ndf"] = np.asarray(model.assembler.get_mesh().point_data["ndf"]).copy()
            if print_results:
                self._print_modal_table(
                    result["frequencies"],
                    result["periods"],
                    title="Steel Concentrically Braced Frame 3D Modal Results",
                )
            if plot:
                mesh = model.assembler.get_mesh()
                self._plot_modal_shapes(mesh, result, scale=plot_scale)

            return result

    def get_recorders(
        self,
        model,
        *,
        file_name: Optional[str] = None,
        delta_t: Optional[float] = None,
        element_responses: Optional[List[str]] = None,
        node_responses: Optional[List[str]] = None,
        whole_model: bool = False,
        acceleration_basis: str = "unspecified",
        abscissa: str = "time_s",
    ):
        """Return one managed VTKHDF recorder, never a list or fallback recorder.

        Args:
            model (Model): Model containing the assembled building.
            file_name: Output base name; defaults to the building name plus
                .vtkhdf extension. VTKHDF adds the MPI rank to the name.
            delta_t: Optional recording interval; None records every step.
            element_responses: VTKHDF defaults to ``force3D`` and
                ``localForce3D``. ``force``/``globalForce`` alias ``force3D``;
                ``localForce`` aliases ``localForce3D``.
            node_responses: Defaults to displacement, velocity, acceleration.
                VTKHDF accepts these names or ``disp``, ``vel``, ``accel``.
            whole_model: False filters by this building's region. True records
                the entire domain. Use True in standalone examples to retain
                auxiliary floor-mass nodes that are not connected to a
                VTK-supported structural element. Do not use whole-model
                scope unintentionally for large soil-structure models.
            acceleration_basis: ``relative`` for uniform excitation,
                ``absolute`` for absolute-response input, or ``unspecified``.
                Describes the output; it does not transform recorded values.
            abscissa: Index label, normally ``time_s`` or ``load_factor`` for
                static pushover. This labels result tables, not solver behavior.

        Returns:
            One managed VTKHDF recorder. Add it to ``model.process`` before
            the analysis; creating them does not start recording.

        Raises:
            ValueError: Model is not assembled, the building is missing,
                acceleration basis is unknown, or responses are unsupported.

        Note:
            ``force3D`` uses global element-end forces; ``localForce3D`` uses
            element-local forces. Each stores 12 components: Fx, Fy, Fz, Mx,
            My, Mz at end i followed by the same at end j. Truss moments are
            zero. Unsupported element responses may also be written as zeros;
            zero output does not prove an element implements that response.
            Force fields require an OpenSees binary with VTKHDF force support;
            inspect the resulting CellData fields, not just the exported command.
            Fiber strains/stresses require separate section/fiber recorders:
            continuum ``stress3D6``/``strain3D6`` are not beam-fiber output.

        Example:
            ```python
            recorder = frame.get_recorders(
                model, whole_model=True,
                file_name="building.vtkhdf", delta_t=0.01,
            )
            model.process.add_step(recorder, "Record building response")
            ```
        """
        if self.building_region is None:
            raise ValueError("Building region not found. Call build() first.")
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating recorders")
        if acceleration_basis not in {"relative", "absolute", "unspecified"}:
            raise ValueError("acceleration_basis must be relative, absolute, or unspecified")
        if file_name is None:
            file_name = f"{self.name_prefix}.vtkhdf"
        aliases = {"displacement": "disp", "velocity": "vel", "acceleration": "accel",
                   "force": "force3D", "globalForce": "force3D", "localForce": "localForce3D"}
        responses = list(node_responses if node_responses is not None else ["disp", "vel", "accel"]) + list(
            element_responses if element_responses is not None else ["force3D", "localForce3D"])
        responses = list(dict.fromkeys(aliases.get(value, value) for value in responses))
        options = {} if whole_model else {"region": self.building_region}
        recorder = model.recorder.vtkhdf(file_base_name=file_name, resp_types=responses, delta_t=delta_t, **options)
        self._recording_spec = dict(file_name=file_name, responses=responses, delta_t=delta_t,
                                    acceleration_basis=acceleration_basis, abscissa=abscissa)
        return recorder

    def _results_metadata(self, model, *, units=None, acceleration_basis=None, abscissa=None):
        mesh = model.assembled_mesh
        if mesh is None:
            raise ValueError("Assemble the building before obtaining structural metadata")
        region = np.asarray(mesh.cell_data["Region"])
        candidates = {}
        for index in np.flatnonzero(region == self.building_region.tag):
            cell = mesh.get_cell(int(index))
            if cell.n_points != 2:
                continue
            key = (int(mesh.cell_data["ElementTag"][index]),
                   tuple(sorted(tuple(np.round(mesh.points[i], 8)) for i in cell.point_ids)))
            candidates.setdefault(key, []).append(int(index))
        used, members, element_tags, connectivity, node_ids = set(), [], [], [], set()
        sections, materials, transformations = {}, {}, {}
        for definition in self._member_definitions:
            member = {key: value for key, value in definition.items() if key != "segments"}
            member["elements"] = []
            element = model.element.get(definition["definition"])
            section = element.get_section()
            if str(section.tag) not in sections:
                sections[str(section.tag)] = dict(name=section.user_name, type=type(section).__name__,
                    area=float(section.get_area()), Iy=float(section.get_Iy()), Iz=float(section.get_Iz()),
                    materials=[int(mat.tag) for mat in section.get_materials()],
                    properties={name: float(getattr(section, name)) for name in ("E", "G", "J", "GJ")
                                if getattr(section, name, None) is not None})
                for mat in section.get_materials():
                    materials[str(mat.tag)] = dict(name=mat.user_name, type=mat.material_name, params=mat.params)
            transformation = getattr(element, "_transformation", None)
            if transformation is not None:
                transformations[str(transformation.tag)] = transformation.to_tcl()
                member["transformation"] = int(transformation.tag)
            for p1, p2 in definition["segments"]:
                key = (definition["definition"], tuple(sorted((tuple(np.round(p1, 8)), tuple(np.round(p2, 8))))))
                available = [i for i in candidates.get(key, []) if i not in used]
                if len(available) != 1:
                    raise ValueError("Cannot uniquely resolve a constructed member after assembly")
                index = available[0]
                used.add(index)
                tag = int(model._start_ele_tag + index)
                node_indices = list(map(int, mesh.get_cell(index).point_ids))
                member["elements"].append(tag)
                element_tags.append(tag)
                connectivity.append([model._start_nodetag+i for i in node_indices])
                node_ids.update(node_indices)
            members.append(member)
        node_ids = sorted(node_ids)
        floor_nodes = []
        x_grid, y_grid, _ = self.get_coordinates()
        for z in self.get_coordinates()[2]:
            floor_nodes.append([int(model._start_nodetag+i) for i in node_ids
                if abs(mesh.points[i, 2]-z) < 1e-7 and int(mesh.point_data["ndf"][i]) < 1000
                and np.any(np.isclose(mesh.points[i, 0], x_grid, rtol=0, atol=1e-7))
                and np.any(np.isclose(mesh.points[i, 1], y_grid, rtol=0, atol=1e-7))])
        if any(not nodes for nodes in floor_nodes):
            raise ValueError("Cannot identify structural floor joints from constructed membership")
        recording = getattr(self, "_recording_spec", {})
        unit_labels = dict(length=self.length_unit_system, force="model_force_units",
                           moment="model_moment_units", acceleration="model_acceleration_units")
        unit_labels.update(units or {})
        return dict(node_tags=np.asarray([model._start_nodetag+i for i in node_ids], dtype=np.int64),
                    coordinates=np.asarray(mesh.points[node_ids], dtype=float),
                    element_tags=np.asarray(element_tags, dtype=np.int64),
                    connectivity=np.asarray(connectivity, dtype=np.int64), members=members,
                    floor_nodes=floor_nodes, floor_elevations=self.get_coordinates()[2].tolist(),
                    moment_reference=[self.origin[0]+self.plan_dimensions[0]/2,
                                      self.origin[1]+self.plan_dimensions[1]/2, self.origin[2]],
                    name=self.name_prefix, structure_type=type(self).__name__,
                    sections=sections, materials=materials, transformations=transformations,
                    shear_modulus=getattr(self, "_last_G", None),
                    units=unit_labels, acceleration_basis=acceleration_basis or recording.get("acceleration_basis", "unspecified"),
                    abscissa=abscissa or recording.get("abscissa", "time_s"), recorder=recording)

    def export_metadata(self, model, path, *, units=None, acceleration_basis=None, abscissa=None):
        """Explicitly export a compressed HDF5 structural index, not a Python model.

        Call after assembly. Stores physical members, actual tags, floor joints,
        unique section/material descriptions, local transformations, and units.
        No histories are stored. ``export_to_tcl()`` never calls this method.
        Supply units such as ``dict(length="m", force="kN", moment="kN*m",
        acceleration="m/s^2")``; force units cannot be inferred from geometry.

        Args:
            model (Model): Assembled model containing this building.
            path (str | Path): Explicit output HDF5 filename; overwritten if present.
            units (dict | None): Unit labels, without any numerical conversion.
            acceleration_basis (str | None): Relative/absolute/unspecified;
                defaults to the basis supplied to get_recorders().
            abscissa (str | None): Table index name, e.g. time_s or load_factor.

        Example:
            ```python
            model.export_to_tcl("model.tcl")
            frame.export_metadata(
                model, "building.structure.h5",
                units=dict(length="m", force="kN", moment="kN*m", acceleration="m/s^2"),
            )
            ```
        """
        from femora.results.building import write_building_metadata
        write_building_metadata(path, self._results_metadata(model, units=units,
            acceleration_basis=acceleration_basis, abscissa=abscissa))

    def get_results(self, source, *, model=None, units=None, acceleration_basis=None, abscissa=None):
        """Open BuildingResults using this live building's explicit membership.

        ``model`` defaults to the model used by build(), which must still be
        alive and assembled. This call creates no metadata files. For a separate
        Python session, use ``BuildingResults.open(source, metadata=path)``
        with an explicitly exported structural index instead.

        Args:
            source (str | Path | list): VTKHDF filename, glob, or partition paths.
            model (Model | None): Optional explicit assembled model.
            units (dict | None): Unit labels; values are not converted.
            acceleration_basis (str | None): Recorded acceleration convention.
            abscissa (str | None): Recorded time/load-factor index label.

        Returns:
            BuildingResults: A lazy structure-specific wrapper around ResultSet.
                Close it explicitly or use a context manager.

        Example:
            ```python
            with frame.get_results("results/building*.vtkhdf") as results:
                drift = results.interstory_drift(direction="x")
                peaks = results.summary()
            ```
        """
        from femora.results import BuildingResults
        if model is None:
            model = getattr(self, "_results_model", lambda: None)()
        if model is None:
            raise ValueError("Supply the assembled model or open BuildingResults with exported metadata")
        return BuildingResults.open(source, metadata=self._results_metadata(model, units=units,
            acceleration_basis=acceleration_basis, abscissa=abscissa))

    def view_story(self, story: int, mode: str = "text") -> None:
        """Print or plot a story layout with braced bay locations."""
        if not 1 <= story <= self.num_stories:
            raise ValueError(f"story must be between 1 and {self.num_stories}")
        x_coords, y_coords, _ = self.get_coordinates()
        if mode == "text":
            print(f"\nConventional Steel Braced Frame - Story {story}")
            print("=" * 56)
            print(f"Columns: {self.num_x_grid} x {self.num_y_grid} grid intersections")
            print(f"X beams: {len(self.x_bays)} bays on {self.num_y_grid} frame lines")
            print(f"Y beams: {len(self.y_bays)} bays on {self.num_x_grid} frame lines")
            print(f"X braces: {self.brace_bays_x}")
            print(f"Y braces: {self.brace_bays_y}")
            print(f"Brace pattern: {self.brace_pattern}")
            return
        if mode != "plot":
            raise ValueError("mode must be 'text' or 'plot'")

        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 8))
        for x in x_coords:
            ax.plot([x, x], [y_coords[0], y_coords[-1]], "k-", alpha=0.4)
        for y in y_coords:
            ax.plot([x_coords[0], x_coords[-1]], [y, y], "k-", alpha=0.4)
        for line_name, bays in self.brace_bays_x.items():
            y = y_coords[0] if line_name == "front" else y_coords[-1]
            for bay in bays:
                ax.plot([x_coords[bay], x_coords[bay + 1]], [y, y], "r-", lw=4)
        for line_name, bays in self.brace_bays_y.items():
            x = x_coords[0] if line_name == "left" else x_coords[-1]
            for bay in bays:
                ax.plot([x, x], [y_coords[bay], y_coords[bay + 1]], "b-", lw=4)
        ax.set_title(f"{self.name_prefix} Story {story}")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        plt.show()

    def estimate_fixed_base_period(
        self,
        model,
        opensees_exe: Optional[str] = None,
        num_modes: int = 6,
        work_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, object]:
        """Run a fixed-base OpenSees eigen check and return periods/mode types."""
        exe = opensees_exe or self.opensees_exe or os.environ.get("OPENSEES_EXE") or os.environ.get("OPENSEES")
        if not exe:
            raise FileNotFoundError("Set opensees_exe or OPENSEES_EXE to run fixed-base eigen validation")

        if not self._com_node_tags:
            self._com_node_tags = self._find_com_node_tags(model)
        if not self._com_node_tags:
            raise ValueError("COM node tags not found. Call create_rigid_diaphragms(model) first.")

        with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
            tmp_path = Path(tmp)
            tcl_file = tmp_path / "fixed_base_eigen.tcl"
            output_file = tmp_path / "fixed_base_periods.txt"
            action = model.actions.tcl(self._eigen_tcl(output_file, self._com_node_tags, num_modes))
            original_steps = list(model.process.steps)
            try:
                model.process.add_step(action, description="Fixed-base eigen period check")
                model.export_to_tcl(str(tcl_file))
            finally:
                model.process.steps = original_steps
            completed = subprocess.run(
                [str(exe), str(tcl_file)],
                cwd=str(tmp_path),
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "OpenSees fixed-base eigen analysis failed:\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
            result = self._parse_eigen_output(output_file)
            self._last_period_result = result
            return result

    def calibrate_to_target_period(
        self,
        model,
        target_period: Optional[float] = None,
        direction: str = "x",
        tolerance: float = 0.10,
        max_iterations: int = 8,
        opensees_exe: Optional[str] = None,
    ) -> Dict[str, object]:
        """Scale brace geometry toward a fixed-base period target.

        Use an Elastic uniaxial material for period calibration. This changes
        axial stiffness while holding the already assembled nodal masses fixed;
        it is not a nonlinear capacity calibration.
        """
        target = float(target_period if target_period is not None else self.target_period)
        direction = direction.lower()
        if direction not in ("x", "y"):
            raise ValueError("direction must be 'x' or 'y'")

        result: Dict[str, object] = {}
        for _ in range(max_iterations):
            result = self.estimate_fixed_base_period(model, opensees_exe=opensees_exe)
            mode = self._first_mode_for_direction(result, direction)
            if mode is None:
                raise RuntimeError(f"Could not identify a translational {direction.upper()} mode")
            old_period = float(mode["period"])
            if abs(old_period - target) / target <= tolerance:
                break
            scale_factor = (old_period / target) ** 2
            self.brace_area_scale *= scale_factor
            for element in self._brace_elements:
                sec = element.get_section()
                if sec is not None:
                    for fiber in sec.fibers:
                        fiber.area *= scale_factor

        result = self.estimate_fixed_base_period(model, opensees_exe=opensees_exe)
        self._print_validation_summary(result, target)
        return result

    def summarize_archetype(self) -> Dict[str, object]:
        """Return a dictionary summary of geometry, layout, masses, and calibration state."""
        l_x, l_y = self.plan_dimensions
        return {
            "archetype_name": "SteelConcentricallyBracedFrame3D",
            "name_prefix": self.name_prefix,
            "num_stories": self.num_stories,
            "total_height": self.total_height,
            "plan_dimensions": (l_x, l_y),
            "brace_bays_x": self.brace_bays_x,
            "brace_bays_y": self.brace_bays_y,
            "brace_pattern": self.brace_pattern,
            "total_floor_mass": float(sum(self.floor_masses)),
            "target_period": self.target_period,
            "brace_area_scale": self.brace_area_scale,
            "brace_properties": copy.deepcopy(self.brace_properties),
            "last_period_result": self._last_period_result,
        }

    def _validate_brace_layout(self) -> None:
        for name, bays in self.brace_bays_x.items():
            if name not in ("front", "back"):
                raise ValueError("brace_bays_x keys must be 'front' and/or 'back'")
            for bay in bays:
                if bay < 0 or bay >= len(self.x_bays):
                    raise ValueError(f"Invalid X brace bay index {bay}")
        for name, bays in self.brace_bays_y.items():
            if name not in ("left", "right"):
                raise ValueError("brace_bays_y keys must be 'left' and/or 'right'")
            for bay in bays:
                if bay < 0 or bay >= len(self.y_bays):
                    raise ValueError(f"Invalid Y brace bay index {bay}")

    def _section_for(self, source, story: int, i: int, j: int, default: str, direction: Optional[str] = None) -> str:
        if isinstance(source, str):
            return source
        if isinstance(source, dict):
            if direction is not None:
                return source.get((story, direction, i, j),
                                  source.get((story, direction.lower(), i, j), default))
            return source.get((story, i, j), default)
        if isinstance(source, Sequence):
            return str(source[min(story - 1, len(source) - 1)])
        return default

    def _add_brace_pattern(self, add_member, brace_element, bl, br, tl, tr) -> None:
        if self.brace_pattern == "x":
            add_member(brace_element, bl, tr, 1)
            add_member(brace_element, br, tl, 1)
        elif self.brace_pattern == "single_diagonal":
            add_member(brace_element, bl, tr, 1)
        elif self.brace_pattern == "chevron":
            mid_top = ((np.asarray(tl) + np.asarray(tr)) / 2.0).tolist()
            add_member(brace_element, bl, mid_top, 1)
            add_member(brace_element, br, mid_top, 1)
        elif self.brace_pattern == "inverted_v":
            mid_bottom = ((np.asarray(bl) + np.asarray(br)) / 2.0).tolist()
            add_member(brace_element, mid_bottom, tl, 1)
            add_member(brace_element, mid_bottom, tr, 1)

    @staticmethod
    def _explicit_rot_mass_kind_for_truss(p1: np.ndarray, p2: np.ndarray) -> str:
        """Map brace axis to the same branches as :class:`FEMA_SAC_SteelFrame` mass logic."""
        d = np.abs(p2.astype(float) - p1.astype(float))
        if d[2] >= d[0] and d[2] >= d[1]:
            return "column"
        if d[0] >= d[1]:
            return "beam_x"
        return "beam_y"

    @staticmethod
    def _add_half_rotational_explicit_mass(
        grid: pv.UnstructuredGrid,
        pid: int,
        M_rot_torsion: float,
        M_rot_iy: float,
        M_rot_iz: float,
        kind: str,
    ) -> None:
        """Distribute half the member rotational mass inertia to ``pid`` (global Rx,Ry,Rz)."""
        h = 0.5
        m = grid.point_data["Mass"]
        if kind == "column":
            m[pid, 3] += M_rot_iz * h
            m[pid, 4] += M_rot_iy * h
            m[pid, 5] += M_rot_torsion * h
        elif kind == "beam_x":
            m[pid, 3] += M_rot_torsion * h
            m[pid, 4] += M_rot_iy * h
            m[pid, 5] += M_rot_iz * h
        elif kind == "beam_y":
            m[pid, 3] += M_rot_iy * h
            m[pid, 4] += M_rot_torsion * h
            m[pid, 5] += M_rot_iz * h

    def _add_member_self_mass(self, grid: pv.UnstructuredGrid, model, material_density: float) -> None:
        """Lumped translational + rotational mass per line member (explicit dynamics), matching steel_frame."""
        for cell_idx in range(grid.n_cells):
            start = grid.offset[cell_idx]
            end = grid.offset[cell_idx + 1]
            if end - start != 2:
                continue
            pid1, pid2 = grid.cell_connectivity[start:end]
            p1 = grid.points[pid1]
            p2 = grid.points[pid2]
            element = model.element.get(int(grid.cell_data["ElementTag"][cell_idx]))
            if element is None:
                continue
            rho = self._member_densities.get(element.tag, float(material_density))
            if rho == 0:
                continue

            section = element.get_section()
            properties = self._mass_geometry.get(element.tag)
            if section is None and properties is None:
                continue

            L = float(np.linalg.norm(np.asarray(p1, dtype=float) - np.asarray(p2, dtype=float)))
            if L <= 0.0:
                continue

            A = float(properties["A"] if properties is not None else section.get_area())
            Iy = float(properties["Iy"] if properties is not None else section.get_Iy())
            Iz = float(properties["Iz"] if properties is not None else section.get_Iz())

            M_trans = rho * A * L
            M_rot_torsion = rho * (Iy + Iz) * L
            M_rot_iy = rho * Iy * L
            M_rot_iz = rho * Iz * L

            kind: str
            if isinstance(element, TrussElement):
                kind = self._explicit_rot_mass_kind_for_truss(p1, p2)
            else:
                transf_name = getattr(element._transformation, "description", "")
                if "Column" in transf_name:
                    kind = "column"
                elif "Beam_X" in transf_name:
                    kind = "beam_x"
                elif "Beam_Y" in transf_name:
                    kind = "beam_y"
                else:
                    kind = self._explicit_rot_mass_kind_for_truss(p1, p2)

            for pid in (pid1, pid2):
                m = grid.point_data["Mass"]
                m[pid, 0] += M_trans / 2.0
                m[pid, 1] += M_trans / 2.0
                m[pid, 2] += M_trans / 2.0
                self._add_half_rotational_explicit_mass(
                    grid, pid, M_rot_torsion, M_rot_iy, M_rot_iz, kind
                )

    def _add_center_of_mass_nodes(self, grid: pv.UnstructuredGrid, model) -> pv.UnstructuredGrid:
        x_coords, y_coords, z_coords = self.get_coordinates()
        x_center = (x_coords[0] + x_coords[-1]) / 2.0
        y_center = (y_coords[0] + y_coords[-1]) / 2.0
        lx = x_coords[-1] - x_coords[0]
        ly = y_coords[-1] - y_coords[0]

        com_coords = []
        com_tags = []
        for story in range(1, self.num_stories + 1):
            com_element = model.element.special.ghost_node(ndof=6)
            com_coords.append([x_center, y_center, z_coords[story]])
            com_tags.append(com_element.tag)

        com_grid = pv.PolyData(np.asarray(com_coords, dtype=float)).cast_to_unstructured_grid()
        com_grid.cell_data["ElementTag"] = np.asarray(com_tags, dtype=np.uint16)
        com_grid.point_data["ndf"] = np.asarray(
            [model.element.get(tag).get_ndof() for tag in com_tags],
            dtype=np.uint16,
        )
        mass = np.zeros((len(com_coords), FEMORA_MAX_NDF), dtype=np.float32)
        for idx, floor_mass in enumerate(self.floor_masses):
            fm = float(floor_mass)
            mass[idx, 0] = fm
            mass[idx, 1] = fm
            mass[idx, 2] = fm
            mass[idx, 3] = fm * ly**2 / 12.0
            mass[idx, 4] = fm * lx**2 / 12.0
            mass[idx, 5] = fm * (lx**2 + ly**2) / 12.0
        com_grid.point_data["Mass"] = mass
        return grid.merge(com_grid, merge_points=False)

    def _find_com_node_tags(self, model) -> List[int]:
        mesh = model.assembled_mesh
        if mesh is None:
            return []
        tags: List[int] = []
        _, _, z_coords = self.get_coordinates()
        for story in range(1, self.num_stories + 1):
            mask = np.abs(mesh.points[:, 2] - z_coords[story]) < 1e-4
            candidates = np.where(mask & (mesh.point_data["ndf"] >= 1000))[0]
            if len(candidates):
                tags.append(int(candidates[0] + model._start_nodetag))
        return tags

    def _eigen_tcl(self, output_file: Path, com_node_tags: Sequence[int], num_modes: int) -> str:
        output_path = str(output_file).replace("\\", "/")
        modes = " ".join(str(i) for i in range(1, num_modes + 1))
        com_nodes = " ".join(str(tag) for tag in com_node_tags)
        return f"""
        constraints Transformation
        numberer RCM
        system BandGeneral
        algorithm Linear
        set lambdas [eigen {num_modes}]
        set out [open "{output_path}" "w"]
        puts $out "PERIODS"
        foreach lambda $lambdas {{
            if {{$lambda > 0.0}} {{
                puts $out [expr {{2.0*acos(-1.0)/sqrt($lambda)}}]
            }} else {{
                puts $out "nan"
            }}
        }}
        set comNodes {{{com_nodes}}}
        foreach mode {{{modes}}} {{
            puts $out "MODE $mode"
            foreach node $comNodes {{
                set ux [nodeEigenvector $node $mode 1]
                set uy [nodeEigenvector $node $mode 2]
                set rz [nodeEigenvector $node $mode 6]
                puts $out "$node $ux $uy $rz"
            }}
        }}
        close $out
        wipeAnalysis
        """

    def _parse_eigen_output(self, output_file: Path) -> Dict[str, object]:
        lines = output_file.read_text().splitlines()
        periods: List[float] = []
        mode_vectors: Dict[int, List[Tuple[int, float, float, float]]] = {}
        idx = 0
        if not lines or lines[0].strip() != "PERIODS":
            raise RuntimeError("Could not parse fixed-base eigen output")
        idx = 1
        while idx < len(lines) and not lines[idx].startswith("MODE"):
            try:
                periods.append(float(lines[idx]))
            except ValueError:
                periods.append(float("nan"))
            idx += 1
        while idx < len(lines):
            header = lines[idx].split()
            if len(header) == 2 and header[0] == "MODE":
                mode_num = int(header[1])
                mode_vectors[mode_num] = []
                idx += 1
                while idx < len(lines) and not lines[idx].startswith("MODE"):
                    parts = lines[idx].split()
                    if len(parts) == 4:
                        mode_vectors[mode_num].append((int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])))
                    idx += 1
            else:
                idx += 1

        modes = []
        for mode_num, period in enumerate(periods, start=1):
            vectors = mode_vectors.get(mode_num, [])
            sx = sum(abs(v[1]) for v in vectors)
            sy = sum(abs(v[2]) for v in vectors)
            srz = sum(abs(v[3]) for v in vectors)
            if srz > 1.2 * max(sx, sy, 1e-16):
                mode_type = "torsion"
            elif sx >= sy:
                mode_type = "x"
            else:
                mode_type = "y"
            modes.append({"mode": mode_num, "period": period, "type": mode_type, "x_score": sx, "y_score": sy, "torsion_score": srz})
        return {"periods": periods, "modes": modes}

    def _first_mode_for_direction(self, result: Dict[str, object], direction: str) -> Optional[Dict[str, object]]:
        for mode in result.get("modes", []):
            if mode["type"] == direction:
                return mode
        return None

    def _print_validation_summary(self, result: Dict[str, object], target_period: float) -> None:
        summary = self.summarize_archetype()
        modes = result.get("modes", [])
        first_type = modes[0]["type"] if modes else "unknown"
        print("\nSteelConcentricallyBracedFrame3D validation")
        print("=" * 48)
        print(f"archetype name: {summary['archetype_name']}")
        print(f"number of stories: {self.num_stories}")
        print(f"total height: {self.total_height}")
        print(f"plan dimensions: {self.plan_dimensions}")
        print(f"braced frame layout X: {self.brace_bays_x}")
        print(f"braced frame layout Y: {self.brace_bays_y}")
        print(f"brace pattern: {self.brace_pattern}")
        print(f"total floor mass: {sum(self.floor_masses)}")
        print(f"first 6 periods: {result.get('periods', [])[:6]}")
        print(f"target period: {target_period}")
        print(f"brace_area_scale: {self.brace_area_scale}")
        print(f"first mode type: {first_type}")
        if first_type == "torsion":
            print("WARNING: torsion is the first mode; rebalance or add braced bays.")
