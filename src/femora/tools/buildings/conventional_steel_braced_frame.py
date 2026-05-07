from __future__ import annotations

import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pyvista as pv

from femora.components.Material.materialBase import Material
from femora.components.Mesh.meshPartInstance import CompositeMesh
from femora.components.element.elastic_beam_column import ElasticBeamColumnElement
from femora.components.element.ghost_node import GhostNodeElement
from femora.components.element.truss import TrussElement
from femora.components.section.section_opensees import ElasticSection
from femora.components.Region.regionBase import RegionBase
from femora.components.transformation.transformation import GeometricTransformation3D
from femora.constants import FEMORA_MAX_NDF
from femora.core.element_base import Element
from femora.core.pattern_base import Pattern
from femora.tools.sections import aisc


class ConventionalSteelBracedFrame:
    """Generic conventional concentrically braced steel building archetype.

    The default model is a symmetric 5-story, 24 m by 24 m braced frame intended
    for SSI/DRM studies. It is deliberately separate from
    ``FEMA_SAC_SteelFrame`` and represents a stiffer conventional building whose
    target fixed-base period follows ``T1 ~= 0.1 * num_stories``.
    """

    VALID_BRACE_PATTERNS = {"x", "single_diagonal", "chevron", "inverted_v"}

    def __init__(
        self,
        name_prefix: str = "conventional_steel_braced_frame",
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
        brace_area: Optional[float] = None,
        brace_E: Optional[float] = None,
        n_ele_col: int = 1,
        n_ele_beam: int = 1,
        length_unit_system: str = "m",
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        opensees_exe: Optional[str] = None,
    ):
        """Create the braced-frame archetype definition.

        Args:
            name_prefix: Mesh part and recorder name prefix.
            num_stories: Number of stories. Defaults to ``5``.
            x_bays: X-direction bay widths. Defaults to three 8 m bays.
            y_bays: Y-direction bay widths. Defaults to three 8 m bays.
            story_heights: Story heights. Defaults to ``[4.0, 3.5, ...]``.
            floor_masses: True masses at floor COM nodes. Defaults to
                ``0.0`` per floor in SI unit systems.
            brace_bays_x: Braced X-bay indices on ``front`` and ``back`` lines.
            brace_bays_y: Braced Y-bay indices on ``left`` and ``right`` lines.
            brace_pattern: ``x``, ``single_diagonal``, ``chevron``, or
                ``inverted_v``.
            brace_area_scale: Multiplier applied to brace section/direct area.
            target_period: Optional calibration target. Defaults to ``0.1N``.
            column_sections: Section override for columns.
            beam_sections: Section override for beams.
            brace_sections: Section override for braces.
            brace_area: Direct brace area used when not using AISC sections.
            brace_E: Elastic modulus for direct-area brace material. If omitted,
                the supplied steel material modulus is used when available.
            n_ele_col: Number of elements per column member.
            n_ele_beam: Number of elements per beam member.
            length_unit_system: Unit system passed to AISC section creation.
            origin: Building origin.
            opensees_exe: Optional OpenSees executable path for validation.
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
        if self.brace_area_scale <= 0.0:
            raise ValueError("brace_area_scale must be positive")
        self.target_period = float(target_period) if target_period is not None else 0.1 * self.num_stories

        self.column_sections = column_sections if column_sections is not None else "W14X90"
        self.beam_sections = beam_sections if beam_sections is not None else "W18X35"
        self.brace_sections = brace_sections if brace_sections is not None else "HSS8X8X3/8"
        self.brace_area = brace_area
        self.brace_E = brace_E
        self.opensees_exe = opensees_exe

        self.building_region: Optional[RegionBase] = None
        self._brace_elements: List[TrussElement] = []
        self._com_node_tags: List[int] = []
        self._last_period_result: Optional[Dict[str, object]] = None
        self._last_material: Optional[Material] = None
        self._last_material_density = 0.0

        self._validate_brace_layout()

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

    def build(self, model, material: Material, material_density: float = 0.0) -> CompositeMesh:
        """Build columns, beams, braces, and COM nodes as a Femora mesh part."""
        self._last_material = material
        self._last_material_density = float(material_density)
        self._brace_elements = []

        x_coords, y_coords, z_coords = self.get_coordinates()
        elements_cache: Dict[Tuple[str, str], Element] = {}
        all_points: List[List[float]] = []
        all_cells: List[int] = []
        cell_element_tags: List[int] = []
        current_point_id = 0

        transf_col_x = GeometricTransformation3D("Linear", 1, 0, 0, description="CBF_Column_Transf_X")
        transf_col_y = GeometricTransformation3D("Linear", 0, 1, 0, description="CBF_Column_Transf_Y")
        transf_beam = GeometricTransformation3D("Linear", 0, 0, 1, description="CBF_Beam_Transf")

        def get_or_create_beam_element(category: str, section_name: str) -> ElasticBeamColumnElement:
            key = (category, section_name)
            if key in elements_cache:
                return elements_cache[key]  # type: ignore[return-value]
            try:
                try:
                    section = model.section.get_section(section_name)
                except KeyError:
                    section = aisc.create_section(
                        section_name,
                        model,
                        material,
                        type="Elastic",
                        unit_system=self.length_unit_system,
                    )
            except Exception as exc:
                raise ValueError(f"Could not create section '{section_name}' for {category}: {exc}") from exc

            transformation = transf_beam
            if category == "Column_X":
                transformation = transf_col_x
            elif category == "Column_Y":
                transformation = transf_col_y
            element = ElasticBeamColumnElement(ndof=6, section=section, transformation=transformation)
            elements_cache[key] = element
            return element

        brace_section = self._get_or_create_brace_section(model, material)
        brace_element = TrussElement(ndof=6, section=brace_section, rho=0.0)
        self._brace_elements.append(brace_element)

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
            for k in range(n):
                add_element_segment(element, p_start_arr + vector * (k / n), p_start_arr + vector * ((k + 1) / n))

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
                    element = get_or_create_beam_element("Beam", section)
                    add_member(element, [x_coords[i], y_coords[j], z], [x_coords[i + 1], y_coords[j], z], self.n_ele_beam)
            for i in range(self.num_x_grid):
                for j in range(len(self.y_bays)):
                    section = self._section_for(self.beam_sections, story, i, j, direction="Y", default="W18X35")
                    element = get_or_create_beam_element("Beam", section)
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
                        brace_element,
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
                        brace_element,
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
        grid = self._add_center_of_mass_nodes(grid)

        self.building_region = model.region.create_region("ElementRegion")
        return CompositeMesh(user_name=self.name_prefix, mesh=grid, region=self.building_region)

    def create_rigid_diaphragms(self, model) -> None:
        """Create floor rigid diaphragms to COM nodes and fix COM vertical/rocking DOFs."""
        mesh = model.assembler.AssembeledMesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating rigid diaphragms.")

        points = mesh.points
        ndfs = mesh.point_data["ndf"]
        start_node_tag = model._start_nodetag
        x_coords, y_coords, z_coords = self.get_coordinates()
        x_set = {round(float(value), 4) for value in x_coords}
        y_set = {round(float(value), 4) for value in y_coords}
        self._com_node_tags = []

        for story in range(1, self.num_stories + 1):
            z_floor = float(z_coords[story])
            floor_indices = np.where(np.abs(points[:, 2] - z_floor) < 1e-4)[0]
            if not len(floor_indices):
                print(f"  [Floor {story}] Warning: no floor nodes found at z={z_floor:.3f}")
                continue

            floor_ndfs = ndfs[floor_indices]
            com_candidates = np.where(floor_ndfs >= 1000)[0]
            if not len(com_candidates):
                print(f"  [Floor {story}] Warning: no COM ghost node found.")
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
                model.constraint.mp.create_rigid_diaphragm(
                    direction=3,
                    master_node=master_tag,
                    slave_nodes=[slave_tag],
                )
            model.constraint.sp.fix(master_tag, [0, 0, 1, 1, 1, 0])
            print(f"  [Floor {story}] Created diaphragm: Master={master_tag}, Slaves={len(slave_tags)}")

    def apply_fixed_base(self, model, tol: float = 1e-4) -> None:
        """Fix all base structural grid nodes for fixed-base period checks."""
        mesh = model.assembler.AssembeledMesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before fixing base nodes.")
        z_base = float(self.get_coordinates()[2][0])
        ndfs = mesh.point_data["ndf"]
        for idx, point in enumerate(mesh.points):
            if abs(float(point[2]) - z_base) > tol or int(ndfs[idx]) >= 1000:
                continue
            model.constraint.sp.fix(int(idx + model._start_nodetag), [1, 1, 1, 1, 1, 1])

    def gravity_pattern(self, model, g: float) -> Pattern:
        """Create a plain gravity load pattern using true floor masses times ``g``."""
        mesh = model.assembler.AssembeledMesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating gravity loads.")

        x_coords, y_coords, z_coords = self.get_coordinates()
        x_set = {round(float(v), 4) for v in x_coords}
        y_set = {round(float(v), 4) for v in y_coords}
        ndfs = mesh.point_data["ndf"]

        ts = model.timeSeries.create_time_series("constant", factor=1.0)
        pattern = model.pattern.create_pattern("plain", time_series=ts, factor=1.0)
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

    def get_recorders(
        self,
        model,
        *,
        file_name: Optional[str] = None,
        delta_t: Optional[float] = None,
        element_responses: List[str] = ["force"],
        node_responses: List[str] = ["displacement", "acceleration"],
    ):
        """Return an MPCO recorder scoped to this building region."""
        if self.building_region is None:
            raise ValueError("Building region not found. Call build() first.")
        mesh = model.assembler.AssembeledMesh
        if mesh is None:
            raise ValueError("Mesh must be assembled before creating recorders")
        if file_name is None:
            file_name = f"{self.name_prefix}.mpco"

        cores_arg = None
        cores_arr = mesh.cell_data.get("Core")
        region_arr = mesh.cell_data.get("Region")
        meshpart_arr = mesh.cell_data.get("MeshPartTag_celldata")
        if cores_arr is not None and region_arr is not None:
            mask = region_arr == int(self.building_region.tag)
            if meshpart_arr is not None:
                mask = mask & (meshpart_arr != 0)
            selected = np.unique(cores_arr[mask])
            selected = [int(core) for core in selected if int(core) >= 0]
            if selected:
                cores_arg = selected[0] if len(selected) == 1 else selected

        recorder = model.recorder.mpco(
            file_name=file_name,
            element_responses=element_responses,
            node_responses=node_responses,
            regions=[self.building_region],
            delta_t=delta_t,
            cores=cores_arg,
        )
        return [recorder]

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
        """Iteratively scale brace area to match the target fixed-base period."""
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
                    self._scale_elastic_section_geometry(sec, scale_factor)

        result = self.estimate_fixed_base_period(model, opensees_exe=opensees_exe)
        self._print_validation_summary(result, target)
        return result

    def summarize_archetype(self) -> Dict[str, object]:
        """Return a dictionary summary of geometry, layout, masses, and calibration state."""
        l_x, l_y = self.plan_dimensions
        return {
            "archetype_name": "ConventionalSteelBracedFrame",
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
                return source.get((story, direction, i, j), default)
            return source.get((story, i, j), default)
        if isinstance(source, Sequence):
            return str(source[min(story - 1, len(source) - 1)])
        return default

    def _resolve_brace_E(self, material: Material) -> float:
        """Young's modulus for a directly specified brace area (Elastic section)."""
        if self.brace_E is not None:
            return float(self.brace_E)
        e_val = getattr(material, "E", None)
        if e_val is None and hasattr(material, "params"):
            e_val = material.params.get("E")
        if e_val is None:
            raise ValueError("brace_E must be provided when using direct brace_area without material E.")
        return float(e_val)

    @staticmethod
    def _scale_elastic_section_geometry(section: ElasticSection, factor: float) -> None:
        """Scale area and inertias for period calibration (axial stiffness ∝ EA)."""
        p = dict(section.params)
        for key in ("A", "Iz", "Iy", "J"):
            if key in p:
                p[key] = float(p[key]) * factor
        section.update_values(p)

    def _get_or_create_brace_section(self, model, material: Material) -> ElasticSection:
        """Elastic brace section referenced by ``trussSection`` elements."""
        if self.brace_area is not None:
            E_val = self._resolve_brace_E(material)
            A0 = float(self.brace_area) * self.brace_area_scale
            r2 = 1e-6
            Iz0 = max(A0 * r2, 1e-18)
            G_val = E_val / 2.6
            params = dict(E=E_val, A=A0, Iz=Iz0, Iy=Iz0, G=G_val, J=2.0 * Iz0)
            user_name = f"{self.name_prefix}_cbf_brace"
            try:
                existing = model.section.get_section(user_name)
                if isinstance(existing, ElasticSection):
                    existing.update_values(params)
                    return existing
            except Exception:
                pass
            return model.section.create_section("Elastic", user_name=user_name, **params)

        section_name = self._section_for(self.brace_sections, 1, 0, 0, default="HSS8X8X3/8")
        try:
            try:
                section = model.section.get_section(section_name)
            except KeyError:
                section = aisc.create_section(
                    section_name,
                    model,
                    material,
                    type="Elastic",
                    unit_system=self.length_unit_system,
                )
        except Exception as exc:
            raise ValueError(
                f"Could not resolve brace section '{section_name}'. "
                "Provide brace_area and optional brace_E to use direct brace properties."
            ) from exc

        if not isinstance(section, ElasticSection):
            raise ValueError("Brace sections for trussSection must be Elastic sections.")

        if self.brace_area_scale != 1.0:
            self._scale_elastic_section_geometry(section, self.brace_area_scale)
        return section

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

    def _add_member_self_mass(self, grid: pv.UnstructuredGrid, model, material_density: float) -> None:
        rho = float(material_density)
        if rho == 0.0:
            return
        for cell_idx in range(grid.n_cells):
            start = grid.offset[cell_idx]
            end = grid.offset[cell_idx + 1]
            if end - start != 2:
                continue
            pid1, pid2 = grid.cell_connectivity[start:end]
            p1 = grid.points[pid1]
            p2 = grid.points[pid2]
            length = float(np.linalg.norm(p1 - p2))
            element = model.element.get_element(int(grid.cell_data["ElementTag"][cell_idx]))
            area = 0.0
            if element is not None and element.get_section() is not None:
                area = float(element.get_section().get_area())
            mass = rho * area * length
            for pid in (pid1, pid2):
                grid.point_data["Mass"][pid, 0] += mass / 2.0
                grid.point_data["Mass"][pid, 1] += mass / 2.0
                grid.point_data["Mass"][pid, 2] += mass / 2.0

    def _add_center_of_mass_nodes(self, grid: pv.UnstructuredGrid) -> pv.UnstructuredGrid:
        x_coords, y_coords, z_coords = self.get_coordinates()
        x_center = (x_coords[0] + x_coords[-1]) / 2.0
        y_center = (y_coords[0] + y_coords[-1]) / 2.0
        lx = x_coords[-1] - x_coords[0]
        ly = y_coords[-1] - y_coords[0]

        com_coords = []
        com_tags = []
        for story in range(1, self.num_stories + 1):
            com_element = GhostNodeElement(ndof=6)
            com_coords.append([x_center, y_center, z_coords[story]])
            com_tags.append(com_element.tag)

        com_grid = pv.PolyData(np.asarray(com_coords, dtype=float)).cast_to_unstructured_grid()
        com_grid.cell_data["ElementTag"] = np.asarray(com_tags, dtype=np.uint16)
        com_grid.point_data["ndf"] = np.asarray(
            [Element.get_element_by_tag(tag).get_ndof() for tag in com_tags],
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
        mesh = model.assembler.AssembeledMesh
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
        print("\nConventionalSteelBracedFrame validation")
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
