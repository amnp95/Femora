
import numpy as np
import pyvista as pv
from typing import List, Dict, Union, Optional, Tuple

from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Mesh.meshPartInstance import CompositeMesh
from femora.components.element.elastic_beam_column import ElasticBeamColumnElement
from femora.components.element.ghost_node import GhostNodeElement
from femora.components.Material.materialBase import Material
from femora.tools.sections import aisc
from femora.components.transformation.transformation import GeometricTransformation3D
from femora.core.element_base import Element
from femora.constants import FEMORA_MAX_NDF

class FEMA_SAC_SteelFrame:
    """
    Represents a FEMA/SAC Steel Frame benchmark building.
    
    Defaults to the SAC 9-Story (LA9) configuration if no geometry is provided,
    but can be initialized with custom bays, stories, and sections.
    """
    def __init__(
        self,
        name_prefix: str = "FEMA_SAC_Frame",
        x_bays: Optional[List[float]] = None,
        y_bays: Optional[List[float]] = None,
        story_heights: Optional[List[float]] = None,
        section_map: Optional[Dict[str, List[Union[str, Tuple]]]] = None,
        defaults: Optional[Dict[str, str]] = None,
        n_ele_col: int = 5,
        n_ele_beam: int = 5,
        section_unit_system: str = 'in',
        origin: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        floor_masses: Optional[List[float]] = None
    ):
        # --- 1. Geometry Setup ---
        # Default to SAC 9-Story (LA9) geometry if not provided
        if x_bays is None:
            self.x_bays = [240.0] * 3
        else:
            self.x_bays = x_bays
            
        if y_bays is None:
            self.y_bays = [240.0] * 2
        else:
            self.y_bays = y_bays
            
        if story_heights is None:
            self.story_heights = [180.0] + [156.0] * 8
        else:
            self.story_heights = story_heights
            
        self.name_prefix = name_prefix
        self.n_ele_col = n_ele_col
        self.n_ele_beam = n_ele_beam
        self.section_unit_system = section_unit_system
        self.origin = origin
        self.floor_masses = floor_masses
        
        # Derived Geometry Stats
        self.num_x_grid = len(self.x_bays) + 1
        self.num_y_grid = len(self.y_bays) + 1
        self.num_stories = len(self.story_heights)

        # --- 2. Section Storage (The Grids) ---
        # Initialize defaults
        self.defaults = {
            'grav_column': 'W14X90', 
            'mom_column': 'W14X90', 
            'mom_girder': 'W24X55'
        }
        if defaults:
            self.defaults.update(defaults)
            self._user_provided_defaults = True
        else:
            self._user_provided_defaults = False

        # Grids to store specific section assignments
        # Keys: 
        #   Col: (story_1_based, x_idx, y_idx)
        #   BeamX: (story_1_based, y_idx, x_bay_idx) -> Beam along X at y_idx, starting at x_bay_idx
        #   BeamY: (story_1_based, x_idx, y_bay_idx) -> Beam along Y at x_idx, starting at y_bay_idx
        self.col_sections: Dict[Tuple[int, int, int], str] = {}
        self.beam_x_sections: Dict[Tuple[int, int, int], str] = {}
        self.beam_y_sections: Dict[Tuple[int, int, int], str] = {}
        
        # Use provided map or None
        self.section_map = section_map
        
        self._initialize_sections()

    def _is_perimeter(self, i, j):
        return i == 0 or i == self.num_x_grid - 1 or j == 0 or j == self.num_y_grid - 1

    def _is_valid_column(self, story, i, j):
        return (1 <= story <= self.num_stories) and (0 <= i < self.num_x_grid) and (0 <= j < self.num_y_grid)

    def _is_valid_beam(self, story, direction, i, j):
        """
        Validates if a beam exists at this location based on FEMA/SAC pinwheel logic.
        """
        if not (1 <= story <= self.num_stories):
            return False
            
        Nx = self.num_x_grid
        Ny = self.num_y_grid

        if direction == 'X':
            # X-Beams exist on Front (j=0) and Back (j=Ny-1) faces only.
            # Front: Skips Bay 0. Valid i: 1 to Nx-2
            if j == 0:
                return 1 <= i < (Nx - 1)
            # Back: Skips Last Bay. Valid i: 0 to Nx-3
            elif j == Ny - 1:
                return 0 <= i < (Nx - 2)
            else:
                return False # Interior X-Beam

        elif direction == 'Y':
            # Y-Beams exist on Left (i=0) and Right (i=Nx-1) faces only.
            # Left: Skips Last Bay. Valid j: 0 to Ny-3
            if i == 0:
                return 0 <= j < (Ny - 2)
            # Right: Skips First Bay. Valid j: 1 to Ny-2
            elif i == Nx - 1:
                return 1 <= j < (Ny - 1)
            else:
                return False # Interior Y-Beam
                
        return False

    def set_column(self, story, x_grid, y_grid, section):
        """Set a specific column section."""
        if not self._is_valid_column(story, x_grid, y_grid):
            print(f"Warning: Column at Story {story}, Grid ({x_grid}, {y_grid}) is out of bounds. Ignoring.")
            return
        self.col_sections[(story, x_grid, y_grid)] = section

    def set_beam(self, story, direction, i, j, section):
        """Set a specific beam section."""
        if not self._is_valid_beam(story, direction, i, j):
            print(f"Warning: Beam '{direction}' at Story {story}, Start Grid ({i}, {j}) is invalid/skipped in this frame topology. Ignoring.")
            return
            
        if direction == 'X':
            self.beam_x_sections[(story, j, i)] = section
        elif direction == 'Y':
            self.beam_y_sections[(story, i, j)] = section

    def _initialize_sections(self):
        """Populate the section grids based on defaults and section_map."""
        
        # 1. Fill Everything with Defaults first
        for s in range(1, self.num_stories + 1):
            # Columns
            for i in range(self.num_x_grid):
                for j in range(self.num_y_grid):
                    is_mom = self._is_perimeter(i, j)
                    def_key = 'mom_column' if is_mom else 'grav_column'
                    self.set_column(s, i, j, self.defaults[def_key])
            
            # Beams (Only Valid Ones)
            # X-Beams: j=0 and j=Ny-1
            for i in range(self.num_x_grid - 1):
                if self._is_valid_beam(s, 'X', i, 0):
                    self.set_beam(s, 'X', i, 0, self.defaults['mom_girder']) # Front
                if self._is_valid_beam(s, 'X', i, self.num_y_grid - 1):
                    self.set_beam(s, 'X', i, self.num_y_grid - 1, self.defaults['mom_girder']) # Back
            
            # Y-Beams: i=0 and i=Nx-1
            for j in range(self.num_y_grid - 1):
                if self._is_valid_beam(s, 'Y', 0, j):
                    self.set_beam(s, 'Y', 0, j, self.defaults['mom_girder']) # Left
                if self._is_valid_beam(s, 'Y', self.num_x_grid - 1, j):
                    self.set_beam(s, 'Y', self.num_x_grid - 1, j, self.defaults['mom_girder']) # Right

        # 2. If no section_map provided AND no user defaults, Load SAC 9-Story Defaults
        if self.section_map is None and not self._user_provided_defaults:
            self._load_sac_9_story_defaults()
            return
            
            
        # 3. Apply Granular Tuple Maps (Overwrites)
        if self.section_map:
            # Columns: (story, x, y, section)
            col_tuples = self.section_map.get('columns', [])
            if col_tuples:
                for item in col_tuples:
                    if isinstance(item, tuple) and len(item) == 4:
                        self.set_column(item[0], item[1], item[2], item[3])
        
        # Beams: (story, dir, i, j, section)
        beam_tuples = self.section_map.get('beams', []) if self.section_map else []

        if beam_tuples:
            for item in beam_tuples:
                if isinstance(item, tuple) and len(item) == 5:
                    self.set_beam(item[0], item[1], item[2], item[3], item[4])

    def view_story(self, story: int, mode: str = 'text'):
        """
        Visualize the layout and sections for a specific story.
        
        Args:
            story: 1-based story index.
            mode: 'text' for ASCII output, 'plot' for matplotlib window.
        """
        if not (1 <= story <= self.num_stories):
            print(f"Error: Story {story} is out of bounds (1-{self.num_stories}).")
            return

        print(f"\nStructure Layout - Story {story}")
        print("==============================")
        
        # Grid Data
        Nx = self.num_x_grid
        Ny = self.num_y_grid
        
        # Collect Data for this Story
        cols = {} # (i,j) -> section
        beams_x = {} # (j, i) -> section (Beam at j, starting at i)
        beams_y = {} # (i, j) -> section (Beam at i, starting at j)

        for i in range(Nx):
            for j in range(Ny):
                cols[(i,j)] = self.col_sections.get((story, i, j), "   ")
        
        # Note keys in beam dicts are (story, j, i) or (story, i, j)
        for (s, j, i), sect in self.beam_x_sections.items():
            if s == story: beams_x[(j, i)] = sect
            
        for (s, i, j), sect in self.beam_y_sections.items():
            if s == story: beams_y[(i, j)] = sect

        if mode == 'text':
            # Matrix Mode: Print separate tables for clarity
            
            cell_w = 15
            
            def print_row(label, cells):
                row_str = f"{label:<8} |"
                for c in cells:
                    row_str += f"{c:^{cell_w}} |"
                print(row_str)
            
            def print_sep(n_cols):
                print("-" * (8 + 2 + n_cols * (cell_w + 3)))

            # 1. Columns Matrix
            print("\n[COLUMNS] (Y-Rows x X-Cols)")
            # Header (X-Grid Indices)
            header_cells = [f"X{i}" for i in range(Nx)]
            print_row("Grid", header_cells)
            print_sep(Nx)
            
            # Rows (Y-Grid Indices, Top to Bottom)
            for j in range(Ny - 1, -1, -1):
                row_cells = []
                for i in range(Nx):
                    sect = cols.get((i,j), " ")
                    row_cells.append(sect)
                print_row(f"Y{j}", row_cells)
            
            # 2. X-Beams Matrix
            print("\n[X-BEAMS] (Y-Rows x Bays)")
            # Header (Bays)
            header_cells = [f"Bay{i}" for i in range(Nx - 1)]
            print_row("Grid", header_cells)
            print_sep(Nx - 1)
            
            for j in range(Ny - 1, -1, -1):
                row_cells = []
                for i in range(Nx - 1):
                    # Beam starts at i
                    sect = beams_x.get((j,i), "-")
                    # If None, use "-"
                    if sect is None: sect = "-"
                    row_cells.append(sect)
                print_row(f"Y{j}", row_cells)

            # 3. Y-Beams Matrix
            print("\n[Y-BEAMS] (Bays x X-Cols)")
            # Header (X-Cols)
            header_cells = [f"X{i}" for i in range(Nx)]
            print_row("Grid", header_cells)
            print_sep(Nx)
            
            # Rows (Bays, Top to Bottom)
            for j in range(Ny - 2, -1, -1):
                row_cells = []
                for i in range(Nx):
                    # Beam starts at j
                    sect = beams_y.get((i,j), "-")
                    if sect is None: sect = "-"
                    row_cells.append(sect)
                print_row(f"Bay{j}", row_cells)
            print("")

        elif mode == 'plot':
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                print("Error: matplotlib is required for 'plot' mode.")
                return

            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Setup Grid
            X = [0]
            for b in self.x_bays: X.append(X[-1] + b)
            Y = [0]
            for b in self.y_bays: Y.append(Y[-1] + b)
            
            # Plot Beams first (lines)
            # X-Beams
            for (j, i), section in beams_x.items():
                x_start, x_end = X[i], X[i+1]
                y = Y[j]
                ax.plot([x_start, x_end], [y, y], 'b-', lw=2, label='Beam' if 'Beam' not in ax.get_legend_handles_labels()[1] else "")
                ax.text((x_start+x_end)/2, y, section, ha='center', va='bottom', fontsize=8, color='blue')
                
            # Y-Beams
            for (i, j), section in beams_y.items():
                x = X[i]
                y_start, y_end = Y[j], Y[j+1]
                ax.plot([x, x], [y_start, y_end], 'g-', lw=2, label='Beam' if 'Beam' not in ax.get_legend_handles_labels()[1] else "")
                ax.text(x, (y_start+y_end)/2, section, ha='left', va='center', fontsize=8, color='green', rotation=90)
                
            # Plot Columns (markers)
            for i in range(Nx):
                for j in range(Ny):
                    sect = cols.get((i,j), "N/A")
                    ax.plot(X[i], Y[j], 'rs', markersize=10, zorder=5)
                    ax.text(X[i], Y[j], f"\n{sect}", ha='center', va='top', fontsize=8, fontweight='bold')

            ax.set_title(f"Story {story} Layout")
            ax.set_xlabel("X (in)")
            ax.set_ylabel("Y (in)")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_aspect('equal')
            plt.tight_layout()
            plt.show()

    def _load_sac_9_story_defaults(self):
        """Internal helper to load the specific LA9 benchmark sections."""
        grav_columns = ["W14X145", "W14X132", "W14X120", "W14X109", "W14X99", "W14X90", "W14X82", "W14X74", "W14X68"]
        mom_columns  = ["W24X335", "W24X306", "W24X279", "W24X250", "W24X229", "W24X207", "W24X192", "W24X176", "W24X162"]
        mom_girders  = ["W30X116", "W30X108", "W30X99", "W27X94", "W27X84", "W24X76", "W24X68", "W21X62", "W21X55"]
        
        # Columns
        for k in range(self.num_stories):
            s = k + 1
            idx = min(k, len(grav_columns)-1)
            sect_grav = grav_columns[idx]
            sect_mom = mom_columns[idx]
            
            for i in range(self.num_x_grid):
                for j in range(self.num_y_grid):
                    is_mom = self._is_perimeter(i, j)
                    self.set_column(s, i, j, sect_mom if is_mom else sect_grav)

        # Girders
        for k in range(self.num_stories):
            s = k + 1
            idx = min(k, len(mom_girders)-1)
            sect = mom_girders[idx]
            
            # Apply to all valid beams on this story
            for key in list(self.beam_x_sections.keys()):
                if key[0] == s: self.beam_x_sections[key] = sect
            for key in list(self.beam_y_sections.keys()):
                if key[0] == s: self.beam_y_sections[key] = sect

    def build(self, model, material: Material, material_density: float=0.0) -> CompositeMesh:
        """
        Generate the steel frame geometry and return as a CompositeMesh.
        """
        
        print(f"\n--- Section Data Prepared ({self.num_stories} Stories) ---")
        print(f"Building with {len(self.col_sections)} Columns and {len(self.beam_x_sections) + len(self.beam_y_sections)} Beams configured.")
        print("-" * 60)
        
        # Coordinates
        x_coords = [0.0]
        for b in self.x_bays: x_coords.append(x_coords[-1] + b)
        x_coords = np.cumsum([0] + self.x_bays)
        y_coords = np.cumsum([0] + self.y_bays)
        z_coords = np.cumsum([0] + self.story_heights)
        
        # Apply Origin Offset
        x_coords += self.origin[0]
        y_coords += self.origin[1]
        z_coords += self.origin[2]
        
        # --- Geometry Collection ---
        elements_cache = {}
        all_points = []
        all_cells = [] 
        cell_element_tags = []
        current_point_id = 0
    
        # --- Transformations ---
        transf_col_x = GeometricTransformation3D("Linear", 1, 0, 0, description="Column_Transf_X")
        transf_col_y = GeometricTransformation3D("Linear", 0, 1, 0, description="Column_Transf_Y")
        transf_beam = GeometricTransformation3D("Linear", 0, 0, 1, description="Beam_Transf")
        
        cat_transf_map = {
            "Column_Grav": transf_col_x, 
            "Column_Mom_X": transf_col_x, 
            "Column_Mom_Y": transf_col_y, 
            "Beam": transf_beam
        }
        
        def get_or_create_element(category, section_name):
            key = (category, section_name)
            if key in elements_cache: return elements_cache[key]
            
            try:
                try: fm_section = model.section.get_section(section_name)
                except KeyError: fm_section = aisc.create_section(section_name, model, material, type="Elastic", unit_system=self.section_unit_system)
            except Exception as e:
                print(f"Warning: Issue with section {section_name}: {e}. using W14X90")
                try: fm_section = model.section.get_section('W14X90')
                except KeyError: fm_section = aisc.create_section('W14X90', model, material, type="Elastic", unit_system=self.section_unit_system)
    
            transf = cat_transf_map.get(category, transf_col_x)
            element = ElasticBeamColumnElement(ndof=6, section=fm_section, transformation=transf)
            elements_cache[key] = element
            return element
    
            return element
    
        def add_element_segment(category, section_name, p1, p2):
            nonlocal current_point_id
            element = get_or_create_element(category, section_name)
            all_points.append(p1)
            all_points.append(p2)
            all_cells.extend([2, current_point_id, current_point_id + 1])
            current_point_id += 2
            cell_element_tags.append(element.tag)

        def add_member(category, section_name, p_start, p_end, n_ele):
            p_start = np.array(p_start)
            p_end = np.array(p_end)
            vector = p_end - p_start
            
            for k in range(n_ele):
                # Linear interpolation
                t1 = k / n_ele
                t2 = (k + 1) / n_ele
                
                pt1 = p_start + t1 * vector
                pt2 = p_start + t2 * vector
                
                # Convert back to list for existing logic if needed, or keep numpy
                add_element_segment(category, section_name, pt1.tolist(), pt2.tolist())

        # --- Build Logic using Grids ---
        
        # 1. Beams (Floor 1 to Roof)
        # Valid beams are already in the dictionaries. Just iterate them.
        # But we need coordinates. Keys are (story, i, j) etc.
        
        for (s, j, i), section in self.beam_x_sections.items():
            z = z_coords[s] # Floor s elevation (Story s top)
            # Beam from i to i+1
            p1 = [x_coords[i], y_coords[j], z]
            p2 = [x_coords[i+1], y_coords[j], z]
            add_member("Beam", section, p1, p2, self.n_ele_beam)
            
        for (s, i, j), section in self.beam_y_sections.items():
            z = z_coords[s]
            # Beam from j to j+1
            p1 = [x_coords[i], y_coords[j], z]
            p2 = [x_coords[i], y_coords[j+1], z]
            add_member("Beam", section, p1, p2, self.n_ele_beam)
            
        # 2. Columns (Story 1 to N)
        for (s, i, j), section in self.col_sections.items():
            z_bot = z_coords[s-1]
            z_top = z_coords[s]
            p1 = [x_coords[i], y_coords[j], z_bot]
            p2 = [x_coords[i], y_coords[j], z_top]
            
            # Determine Transformation Category
            # Interior -> Grav. X-Face -> Mom_X. Y-Face -> Mom_Y.
            # Corner? Corners belong to both faces technically.
            # TCL says:
            #   Front/Back cols (j=0, j=Ny-1) use X-Transf.
            #   Left/Right cols (i=0, i=Nx-1) use Y-Transf.
            #   Overlap at corners?
            #   TCL Loop Structure:
            #     X-Cols Loop: hits (i,0) and (i, Ny-1).
            #     Y-Cols Loop: hits (0,j) and (Nx-1, j).
            #     Corner (0,0) is hit by... well, the loops were specific ranges.
            #     X Loop: i=1 to Nx-1 (misses 0). 
            #     Y Loop: j=0 to Ny-2 (hits 0). 
            #     So Corner (0,0) is in Y-Loop -> colTransfTagY.
            
            # Let's derive simpler logic:
            cat = "Column_Grav"
            if self._is_perimeter(i, j):
                # Corners:
                # (0,0) -> Y-Face? (Based on TCL exclusion from X-loop)
                # (Nx-1, 0) -> Y-Face? (TCL Y-loop hits it? X-Loop i goes to Nx-1... wait. range(1, Nx) hits Nx-1.)
                # Let's stick to the TCL loops' implicit assignment logic if possible, or a geometric rule.
                # Geometric rule:
                # X-Face columns (resisting X-moment) need Strong Axis perp to X? No, Strong Axis (Z) usually horizontal.
                # Standard: Web in plane of frame.
                # X-Frame (Z-axis out of page, Y-axis up). Iz is strong axis.
                # Col Transf X (1 0 0) -> VecXZ is X. Local Z aligns with global X?
                # This seems backwards. Usually VecXZ defines local Z.
                # If TransfX is Linear 1 0 0, Local y is perp to x and Z?
                # Actually, let's just use the logic from before, but per-node.
                
                # Logic:
                # if j=0 or j=Ny-1: X-Face (Transf_X).
                # ELSE (so i=0 or i=Nx-1): Y-Face (Transf_Y).
                # But what about corners (0,0)?
                # If (0,0) is X-Face, it resists X-Moment. If Y-Face, Y-Moment.
                # Corner columns participate in BOTH frames often.
                # TCL:
                # (0,0) was NOT in X-Loop (i=1..). It WAS in Y-Loop (j=0..). -> Y-Transf.
                # (Nx-1, 0) was in X-Loop (i=..Nx-1). NOT in Y-Loop (j=1..). -> X-Transf.
                # (0, Ny-1) was in X-Loop (i=0..). NOT in Y-Loop (j=0..Ny-2). -> X-Transf.
                # (Nx-1, Ny-1) was NOT in X-Loop (i..Nx-2). WAS in Y-Loop (j=1..). -> Y-Transf.
                
                if (i==0 and j==0): cat = "Column_Mom_Y"
                elif (i==self.num_x_grid-1 and j==0): cat = "Column_Mom_X"
                elif (i==0 and j==self.num_y_grid-1): cat = "Column_Mom_X"
                elif (i==self.num_x_grid-1 and j==self.num_y_grid-1): cat = "Column_Mom_Y"
                elif j==0 or j==self.num_y_grid-1: cat = "Column_Mom_X"
                else: cat = "Column_Mom_Y"
            

            add_member(cat, section, p1, p2, self.n_ele_col)
            
        # --- Construct Composite Mesh ---
        if not all_points:
            return CompositeMesh(f"{self.name_prefix}_frame", pv.UnstructuredGrid())
    
        points_array = np.array(all_points)
        cells_array = np.array(all_cells)
        num_cells = len(cell_element_tags)
        cell_types = np.array([pv.CellType.LINE] * num_cells)
        
        grid = pv.UnstructuredGrid(cells_array, cell_types, points_array)
        grid.cell_data["ElementTag"] = np.array(cell_element_tags)
        
        # Merge coincident points
        grid = grid.clean(tolerance=1e-5)
        
        # --- Explicit Element Mass Calculation ---
        # Initialize Mass Array (N, 6)
        if "Mass" not in grid.point_data:
            grid.point_data["Mass"] = np.zeros((grid.n_points, FEMORA_MAX_NDF))

    
        
        # Robustly get rho (handle if it's an attribute or in params dict)
        # print(material)
        rho = material_density
        # TODO: The Mass calculation is the bottleneck of this code. nedd to be vectorized.
        for i in range(grid.n_cells):

            start = grid.offset[i]
            end   = grid.offset[i+1]

            if start - end >2:
                continue

            pid1, pid2 = grid.cell_connectivity[start:end]

            # Beam end point coordinates
            p1 = grid.points[pid1]
            p2 = grid.points[pid2]

            ele_tag = grid.cell_data["ElementTag"][i]
            element = model.element.get_element(ele_tag)

            if not element:
                continue

            section = element.get_section()
            
            if not section:
                print("there is no sections for this element")
                raise ValueError

            # Get the section information
            A  = section.get_area()
            Iy = section.get_Iy()
            Iz = section.get_Iz()
            L = np.linalg.norm(p1 - p2) 

            # print(L,A,Iy,Iz)


            # Calculate Mass Terms
            M_trans = rho * A * L
            M_rot_torsion = rho * (Iy + Iz) * L # Polar Moment of Inertia for Torsion
            M_rot_iy = rho * Iy * L             # Weak Axis Bending Mass
            M_rot_iz = rho * Iz * L             # Strong Axis Bending Mass


            transf_name = getattr(element._transformation, 'description', "")
            # Distribute Lumped Mass (M/2) to both nodes
            for pid in [pid1, pid2]:
                # Translational Mass (Scalar, same for X,Y,Z)
                grid.point_data["Mass"][pid, 0] += M_trans / 2.0
                grid.point_data["Mass"][pid, 1] += M_trans / 2.0
                grid.point_data["Mass"][pid, 2] += M_trans / 2.0
                
                # Rotational Mass Mapping
                if "Column" in transf_name:
                    # Column (Parallel to Z)
                    # Local x (Torsion) -> Global Rz
                    # Local y (Weak)    -> Global Ry
                    # Local z (Strong)  -> Global Rx
                    grid.point_data["Mass"][pid, 3] += M_rot_iz / 2.0 # Rx
                    grid.point_data["Mass"][pid, 4] += M_rot_iy / 2.0 # Ry
                    grid.point_data["Mass"][pid, 5] += M_rot_torsion / 2.0 # Rz
                    
                elif "Beam_X" in transf_name:
                    # Beam X (Parallel to X)
                    # Local x (Torsion) -> Global Rx
                    # Local y (Weak)    -> Global Ry
                    # Local z (Strong)  -> Global Rz
                    grid.point_data["Mass"][pid, 3] += M_rot_torsion / 2.0 # Rx
                    grid.point_data["Mass"][pid, 4] += M_rot_iy / 2.0 # Ry
                    grid.point_data["Mass"][pid, 5] += M_rot_iz / 2.0 # Rz
                    
                elif "Beam_Y" in transf_name:
                    # Beam Y (Parallel to Y)
                    # Local x (Torsion) -> Global Ry
                    # Local y (Weak)    -> Global Rx
                    # Local z (Strong)  -> Global Rz
                    grid.point_data["Mass"][pid, 3] += M_rot_iy / 2.0 # Rx
                    grid.point_data["Mass"][pid, 4] += M_rot_torsion / 2.0 # Ry
                    grid.point_data["Mass"][pid, 5] += M_rot_iz / 2.0 # Rz
            




            
            
            







        # for i in range(grid.n_cells):
        #     cell = grid.get_cell(i)
        #     # cell.point_ids is a list of point indices (assuming line elements)
        #     if len(cell.point_ids) != 2:
        #         continue
                
        #     pid1, pid2 = cell.point_ids
        #     p1 = grid.points[pid1]
        #     p2 = grid.points[pid2]
        #     print(p1,p2,pid1,pid2)
            
        #     # Calculate Length
        #     L = np.linalg.norm(p1 - p2)
            
        #     # Get Element
        #     ele_tag = grid.cell_data["ElementTag"][i]
        #     element = Element._elements.get(ele_tag)
            
        #     if not element:
        #         continue 
                
        #     # Get Section Properties
        #     section = element._section
            
        #     # Helper to get property (handle attributes or params)
        #     def get_prop(obj, name, default=0.0):
        #         try:
        #             val = getattr(obj, name, None)
        #             if val is None and hasattr(obj, 'params'):
        #                 p = obj.params
        #                 if isinstance(p, dict):
        #                     val = p.get(name)
        #             return float(val) if val is not None else default
        #         except Exception as e:
        #             print(f"Error in get_prop for {name}: {e}")
        #             return default

        #     A = get_prop(section, 'A')
        #     Iy = get_prop(section, 'Iy')
        #     Iz = get_prop(section, 'Iz') # Strong axis for W-shapes usually
            
        #     # Calculate Mass Terms
        #     M_trans = rho * A * L
        #     M_rot_torsion = rho * (Iy + Iz) * L # Polar Moment of Inertia for Torsion
        #     M_rot_iy = rho * Iy * L             # Weak Axis Bending Mass
        #     M_rot_iz = rho * Iz * L             # Strong Axis Bending Mass
            
        #     # Determine Orientation & Map to Global DOFs
        #     # Global Indices: 0:Mx, 1:My, 2:Mz, 3:Rx, 4:Ry, 5:Rz
        #     transf_name = getattr(element._transformation, 'description', "")
            
        #     # Distribute Lumped Mass (M/2) to both nodes
        #     # for pid in [pid1, pid2]:
        #     #     # Translational Mass (Scalar, same for X,Y,Z)
        #     #     grid.point_data["Mass"][pid, 0] += M_trans / 2.0
        #     #     grid.point_data["Mass"][pid, 1] += M_trans / 2.0
        #     #     grid.point_data["Mass"][pid, 2] += M_trans / 2.0
                
        #         # Rotational Mass Mapping
        #         # if "Column" in transf_name:
        #         #     # Column (Parallel to Z)
        #         #     # Local x (Torsion) -> Global Rz
        #         #     # Local y (Weak)    -> Global Ry
        #         #     # Local z (Strong)  -> Global Rx
        #         #     grid.point_data["Mass"][pid, 3] += M_rot_iz / 2.0 # Rx
        #         #     grid.point_data["Mass"][pid, 4] += M_rot_iy / 2.0 # Ry
        #         #     grid.point_data["Mass"][pid, 5] += M_rot_torsion / 2.0 # Rz
                    
        #         # elif "Beam_X" in transf_name:
        #         #     # Beam X (Parallel to X)
        #         #     # Local x (Torsion) -> Global Rx
        #         #     # Local y (Weak)    -> Global Ry
        #         #     # Local z (Strong)  -> Global Rz
        #         #     grid.point_data["Mass"][pid, 3] += M_rot_torsion / 2.0 # Rx
        #         #     grid.point_data["Mass"][pid, 4] += M_rot_iy / 2.0 # Ry
        #         #     grid.point_data["Mass"][pid, 5] += M_rot_iz / 2.0 # Rz
                    
        #         # elif "Beam_Y" in transf_name:
        #         #     # Beam Y (Parallel to Y)
        #         #     # Local x (Torsion) -> Global Ry
        #         #     # Local y (Weak)    -> Global Rx
        #         #     # Local z (Strong)  -> Global Rz
        #         #     grid.point_data["Mass"][pid, 3] += M_rot_iy / 2.0 # Rx
        #         #     grid.point_data["Mass"][pid, 4] += M_rot_torsion / 2.0 # Ry
        #         #     grid.point_data["Mass"][pid, 5] += M_rot_iz / 2.0 # Rz
        
        # pl = pv.Plotter()
        # pl.add_mesh(grid,scalars="Mass")
        # pl.show()

        # --- Add Center-of-Mass Nodes at Floor Centers (Story 1 to Roof) ---
        # A center-of-mass node is placed at the geometric center of each
        # floor plan.  These nodes are useful for rigid diaphragm control
        # points, mass application, and recorders.  Each uses a unique
        # GhostNodeElement so it will never be merged with structural nodes
        # or other center-of-mass nodes during assembly.
        x_center = (x_coords[0] + x_coords[-1]) / 2.0
        y_center = (y_coords[0] + y_coords[-1]) / 2.0

        com_coords = []
        com_element_tags = []

        for story_idx in range(1, self.num_stories + 1):
            z_floor = z_coords[story_idx]

            # One GhostNodeElement per floor (unique sentinel ndf each)
            com_elem = GhostNodeElement(ndof=6)

            com_coords.append([x_center, y_center, z_floor])
            com_element_tags.append(com_elem.tag)

        if com_coords:
            # pv.PolyData automatically creates one VERTEX cell per point
            com_grid = pv.PolyData(np.array(com_coords))
            com_grid = com_grid.cast_to_unstructured_grid()

            com_grid.cell_data["ElementTag"] = np.array(com_element_tags)

            # --- Fix: Ensure Ghost Nodes have their unique 'ndf' sentinels ---
            # This prevents them from being merged with structural nodes or each other
            # during the Assembler's cleaning step.
            com_ndfs = [Element.get_element_by_tag(tag).get_ndof() for tag in com_element_tags]
            com_grid.point_data["ndf"] = np.array(com_ndfs, dtype=np.uint16)

            # Initialize center-of-mass Mass array
            com_mass = np.zeros((len(com_coords), FEMORA_MAX_NDF))

            # Apply floor_masses if provided
            if self.floor_masses is not None:
                for i in range(min(len(self.floor_masses), self.num_stories)):
                    if self.floor_masses[i] is not None:
                        fm = self.floor_masses[i]
                        com_mass[i, 0] = fm  # Mx
                        com_mass[i, 1] = fm  # My
                        com_mass[i, 2] = fm  # Mz

            com_grid.point_data["Mass"] = com_mass

            # Merge center-of-mass grid into the main grid (no point merging)
            print("grid num points", grid.n_points)
            print("com_grid num points", com_grid.n_points)
            print("grid num cells", grid.n_cells)
            print("com_grid num cells", com_grid.n_cells)
            grid = grid.merge(com_grid, merge_points=False)
            print("grid num points", grid.n_points)
            print("grid num cells", grid.n_cells)

            print(f"Added {len(com_coords)} center-of-mass nodes at floor centers "
                  f"(x={x_center:.1f}, y={y_center:.1f}, "
                  f"z={z_coords[1]:.1f}..{z_coords[-1]:.1f})")

        composite_mesh = CompositeMesh(f"{self.name_prefix}_frame", grid)
        
        return composite_mesh

def create_steel_frame(
    name_prefix: str,
    model, 
    x_bays: List[float],
    y_bays: List[float],
    story_heights: List[float],
    section_map: Dict[str, List[str]],
    material: Material,
    n_ele_col: int = 5,
    n_ele_beam: int = 5,
    section_unit_system: str = 'in',
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> MeshPart:
    """
    Legacy wrapper for schema compatibility.
    Instantiates a FEMA_SAC_SteelFrame with provided geometry and builds it.
    """
    building = FEMA_SAC_SteelFrame(
        name_prefix=name_prefix,
        x_bays=x_bays,
        y_bays=y_bays,
        story_heights=story_heights,
        section_map=section_map,
        n_ele_col=n_ele_col,
        n_ele_beam=n_ele_beam,
        section_unit_system=section_unit_system,
        origin=origin
    )
    return building.build(model, material)
