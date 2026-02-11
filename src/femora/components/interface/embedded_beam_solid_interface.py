from __future__ import annotations

from typing import List
from collections import defaultdict
# import time

import numpy as np
import pyvista as pv

from femora.components.interface.interface_base import InterfaceBase
from femora.components.event.mixins import HandlesDecompositionMixin
from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Mesh.meshPartInstance import SingleLineMesh, StructuredLineMesh
from femora.components.event.event_bus import EventBus, FemoraEvent
from femora.components.interface.embedded_info import EmbeddedInfo
from femora.components.Region.regionBase import RegionBase




class EmbeddedBeamSolidInterface(InterfaceBase, HandlesDecompositionMixin):
    """Create an *embedded beam–solid* contact interface.

    Parameters
    ----------
    name : str
        Unique interface name.
    beam_part : str
        *user_name* of the **line** `MeshPart` containing beam elements.
    solid_parts : str
        *user_name* of the **volume** `MeshPart` containing hexahedral elements.
        Not implemented yet, please do not use this parameter for now.
    radius : float
        Cylinder radius used to pick surrounding solid cells.
    n_peri, n_long : int
        Discretisation for `generateInterfacePoints` TCL command.
    penalty_param : float | None
        Overrides default 1.0e12.
    g_penalty : bool
        Whether to add the "-gPenalty" flag.
    region : RegionBase | None
        Optional region to confine the interface to a specific region.
        Not implemented yet, please do not use this parameter for now.
    write_connectivity : bool
        Whether to write connectivity information to the output file.
    write_interface : bool
        Whether to write interface information to the output file.
    """

    _embeddedinfo_list: List[EmbeddedInfo] = []  # Class-level list to store all instances
    # Guard to ensure we register the class-level callback only once
    _class_subscribed: bool = False

    def __init__(
        self,
        name: str,
        beam_part: 'MeshPart | str | int',
        solid_parts: 'List[MeshPart | str | int] | None' = None,
        shape: str = "circle",
        radius: float = 0.5,
        n_peri: int = 8,
        n_long: int = 10,
        penalty_param: float = 1.0e12,
        g_penalty: bool = True,
        region: 'RegionBase | None' = None,
        write_connectivity: bool = False,
        write_interface: bool = False,
    ) -> None:
        # Helper to resolve MeshPart from str, int, or instance
        def resolve_meshpart(mp):
            if isinstance(mp, MeshPart):
                return mp
            elif isinstance(mp, str):
                return MeshPart.get_mesh_parts().get(mp)
            elif isinstance(mp, int):
                for part in MeshPart.get_mesh_parts().values():
                    if getattr(part, 'tag', None) == mp:
                        return part
            return None

        resolved_beam = resolve_meshpart(beam_part)
        if resolved_beam is None:
            raise ValueError(f"Could not retrieve beam_part '{beam_part}' to a MeshPart.")
        # Enforce beam_part is SingleLineMesh
        if not isinstance(resolved_beam, (SingleLineMesh, StructuredLineMesh)):
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")
        
        resolved_soild_parts = []
        if solid_parts is not None:
            if not isinstance(solid_parts, list):
                raise TypeError("soild_parts must be a list of MeshPart instances or their user_names.")
            for part in solid_parts:
                resolved_part = resolve_meshpart(part)
                if resolved_part is None:
                    raise ValueError(f"Could not retrieve solid_part '{part}' to a MeshPart.")
                resolved_soild_parts.append(resolved_part)

        super().__init__(name=name, owners=[resolved_beam.user_name])

        # store references
        self.beam_part = resolved_beam
        self.solid_parts = resolved_soild_parts if len(resolved_soild_parts) > 0 else None
        self.radius = radius
        self.n_peri = n_peri
        self.n_long = n_long
        self.penalty_param = penalty_param
        self.g_penalty = g_penalty
        self._instance_embeddedinfo_list: List[EmbeddedInfo] = [] # Instance-level list to store per-instance EmbeddedInfo
        if shape.lower() not in ["circle"]:
            raise ValueError(f"Unsupported shape '{shape}'. Supported shapes: 'circle'.")
        self.shape = shape
        if region is not None and not isinstance(region, RegionBase):
            raise TypeError("region must be an instance of RegionBase or None.")
        elif region is None:
            self.region = region
        else:
            raise NotImplementedError("Region handling is not implemented yet. Please do not use region parameter for now.")
        self.write_connectivity = write_connectivity
        self.write_interface = write_interface



    def _fork_solid_for_single_beam(self, assembled_mesh: pv.UnstructuredGrid, beam_cells_idx: np.ndarray):
        """
        Fork solid mesh for a single beam element.

        This method is forking the solid mesh around single beam element
        to ensure that the solid mesh is consistent with the beam element's core.
        It will extract the solid cells that are within the radius of the beam element
        and edit the _core_elements dictionary to include the solid elements
        that are within the radius of the beam element.
        """
        # t_start_total = time.time()
        assembled_mesh = assembled_mesh.copy()
        beam_core_array = assembled_mesh.cell_data["Core"][beam_cells_idx]
        unique_cores = np.unique(beam_core_array)
        # sort the unique cores from smallest to largest
        unique_cores = np.sort(unique_cores)
        if unique_cores.size > 1:
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] Multiple cores found for beam cells: {unique_cores}.")
            # print("Moving all beam cells to the first core for consistency.")
            # print("all beam cells are going to be moved to core", unique_cores[0])
            # Move all beam cells to same core (pick first) for safety
            target_core = int(unique_cores[0])
            for c in unique_cores[1:]:
                assembled_mesh.cell_data["Core"][beam_cells_idx[beam_core_array == c]] = target_core
        else:
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] Single core found for beam cells: {unique_cores[0]}.")
            # print("all beam cells are in the same core, core:", unique_cores[0])
            target_core = int(unique_cores[0])


        # Beam cell centers
        # t_start_section = time.time()
        beam_points = assembled_mesh.copy().extract_cells(beam_cells_idx).points
        # print(f"--- Time for beam_points extraction: {time.time() - t_start_section:.4f}s")


        # TODO: need to modify the height since the the tail and head 
        # are not necessarily are the first and last points
        # FIXME: this is a hacky way to get the height of the beam

        # t_start_section = time.time()
        beam_tail = beam_points[0]  # Take the first point as tail
        beam_head = beam_points[-1]  # Take the last point as head
        beam_vector = beam_head - beam_tail
        height = np.linalg.norm(beam_vector)
        center = (beam_tail + beam_head) / 2
        beam_vector = beam_vector / height  # Normalize the vector
        clinder = pv.Cylinder(center=center, 
                              direction=beam_vector, 
                              radius=self.radius,
                              height=height,
                              resolution=8,
                              capping=True)  

        # clinder.plot(show_edges=True, opacity=1.0, line_width=2)
        clinder = clinder.clean(inplace=False)  # Clean the cylinder mesh
        # print(f"--- Time for cylinder creation: {time.time() - t_start_section:.4f}s")

        # t_start_section = time.time()
        inner_ind = assembled_mesh.compute_implicit_distance(
            surface=clinder, 
            inplace=False
        ).point_data["implicit_distance"] <= 0
        # print(f"--- Time for initial implicit_distance: {time.time() - t_start_section:.4f}s")

        # find the cells that intersects with the beam line
        intersect_ind = assembled_mesh.find_cells_intersecting_line(beam_tail,
                                                                     beam_head, 
                                                                     tolerance=self.radius)
        if len(intersect_ind) > 0:
            intersect_ind_point_ids = []
            for ind in intersect_ind:
                intersect_ind_point_ids.extend(assembled_mesh.get_cell(ind).point_ids)
        
            intersect_ind_point_ids = np.array(intersect_ind_point_ids)
            # make it 1D array and unique
            # intersect_ind_point_ids = intersect_ind_point_ids.flatten()  # Already 1D
            intersect_ind_point_ids = np.unique(intersect_ind_point_ids)


            inner_ind[intersect_ind_point_ids] = True

                

        # t_start_section = time.time()
        inner = assembled_mesh.extract_points(
            ind=inner_ind,
            include_cells=True,
            adjacent_cells=True,
            progress_bar=False
        )
        # print(f"--- Time for inner mesh extraction: {time.time() - t_start_section:.4f}s")



        beam_elements = inner.celltypes == pv.CellType.LINE
        solid_elements = inner.celltypes == pv.CellType.HEXAHEDRON
        beam_ind = inner.cell_data["vtkOriginalCellIds"][beam_elements]
        solid_ind = inner.cell_data["vtkOriginalCellIds"][solid_elements]

        # TODO: Implement solid parts handling which will confine the interface to use only solid parts
        # given in the solid_parts parameter and not all solid elements
        if self.solid_parts is not None:
            raise NotImplementedError(
                "Solid parts handling is not implemented yet. Please do not use solid_parts parameter for now."
            )


        # save the assembeled mesh indexes to the inner mesh
        inner.cell_data["mesh_ind"] = np.zeros(inner.n_cells, dtype=np.int32)
        inner.cell_data["mesh_ind"][solid_elements] = solid_ind
        inner.cell_data["mesh_ind"][beam_elements] = beam_ind


        # Do a for loop and in every iteration pop up the largest solid mesh from the inner mesh
        solid_mesh = inner.extract_cells(solid_elements, progress_bar=False)
        beam_mesh  = inner.extract_cells(beam_elements, progress_bar=False)
        beams_solids = []
        # t_start_loop = time.time()
        while solid_mesh.n_cells > 0:
            solid_mesh_largest = solid_mesh.extract_largest()
            surf = solid_mesh_largest.extract_surface()
            beam_mesh.compute_implicit_distance(surf,inplace=True)
            beams = beam_mesh.point_data["implicit_distance"] <= 0
            beams = beam_mesh.extract_points(beams, include_cells=True, adjacent_cells=True, progress_bar=False)

            if beams.n_cells < 1:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No beams and solids found in the solid mesh.")
                else:
                    # # plot for debugging
                    # pl = pv.Plotter()
                    # pl.add_mesh(solid_mesh_largest, color="blue", opacity=0.5, show_edges=True)
                    # pl.add_mesh(beam_mesh, color="red", opacity=1.0, line_width=5)
                    # # beam tail and head as points
                    # pl.add_mesh(pv.PolyData(beam_tail), color="green", point_size=20, render_points_as_spheres=True)
                    # pl.add_mesh(pv.PolyData(beam_head), color="yellow", point_size=20, render_points_as_spheres=True)
                    # pl.show()
                    # check if the beam is even going through the solid mesh
                    ind = solid_mesh_largest.find_cells_intersecting_line(beam_tail, beam_head, tolerance=0)
                    if len(ind) < 1:
                        pass
                    else:
                        raise ValueError(f"[EmbeddedBeamSolidInterface:{self.name}]: No beams found in the solid mesh, but solids are present. This is unexpected. \
                        probably the beam mesh size is too small. \
                        please increase the number of points in the beam mesh.")
            else:
                if solid_mesh_largest.n_cells < 1:
                    raise ValueError("No solids found in the solid mesh, but beams are present. This is unexpected. contact the developers.")
                

            if beams.n_cells > 0 and solid_mesh_largest.n_cells > 0:
                beams = beams.cell_data["mesh_ind"]
                solids = solid_mesh_largest.cell_data["mesh_ind"]

                if len(beams) > 0 and len(solids) > 0:
                    beams_solids.append((beams, solids))

            # now remove the largset solid mesh from the solid_mesh
            solid_mesh = solid_mesh.extract_values(solid_mesh_largest.cell_data["mesh_ind"] , invert=True, scalars="mesh_ind")
        # print(f"--- Time for while loop: {time.time() - t_start_loop:.4f}s")
      
        
        
        # print("num cells:", assembled_mesh.n_cells)
        # print("num points:", assembled_mesh.n_points)


        if len(beams_solids) == 0:
            return
        

        ef = EmbeddedInfo(beams=beam_ind,
                     core_number= target_core,
                     beams_solids=beams_solids)
        # add the embedded info to the class-level list
        self._embeddedinfo_list.append(ef)
        self._instance_embeddedinfo_list.append(ef)


        assembled_mesh.cell_data["Core"][inner.cell_data["mesh_ind"]] = target_core

        # print(f"--- Total time for _fork_solid_for_single_beam: {time.time() - t_start_total:.4f}s")




    def _on_post_assemble(self, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Locate beam & solid element tags; enforce same core."""

        # shout  out that this is a post-assemble hook is called
        # print(f"[EmbeddedBeamSolidInterface:{self.name}] Post-assemble hook called.")

        # Collect beam cells indices & compute their mean location
        beam_cells_idx = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
        if beam_cells_idx.size == 0:
            raise ValueError("No beam elements found in assembled mesh for provided MeshPart")
        
        # if beam_part is SingleLineMesh or StructuredLineMesh do different handling
        if isinstance(self.beam_part, SingleLineMesh):
            # print(f"[EmbeddedBeamSolidInterface:{self.name}] SingleLineMesh detected, forking solid mesh around beam.")
            self._fork_solid_for_single_beam(assembled_mesh, beam_cells_idx)
        elif isinstance(self.beam_part, StructuredLineMesh):
            # Type hint for IDE auto-complete
            beam_mesh: pv.UnstructuredGrid = self.beam_part.mesh.copy()
            params = self.beam_part.params
            norm_x = params.get("normal_x", None)
            norm_y = params.get("normal_y", None)
            norm_z = params.get("normal_z", None)
            offset_1 = params.get("offset_1", 0.0)
            offset_2 = params.get("offset_2", 0.0)
            base_point_x = params.get("base_point_x", 0.0)
            base_point_y = params.get("base_point_y", 0.0)
            base_point_z = params.get("base_point_z", 0.0)
            base_vector_1_x = params.get("base_vector_1_x", None)
            base_vector_1_y = params.get("base_vector_1_y", None)
            base_vector_1_z = params.get("base_vector_1_z", None)
            base_vector_2_x = params.get("base_vector_2_x", None)
            base_vector_2_y = params.get("base_vector_2_y", None)
            base_vector_2_z = params.get("base_vector_2_z", None)
            grid_size_1 = params.get("grid_size_1", None)
            grid_size_2 = params.get("grid_size_2", None)
            spacing_1 = params.get("spacing_1", None)
            spacing_2 = params.get("spacing_2", None)
            length = params.get("length", None)

            if length is None:
                raise ValueError("StructuredLineMesh must have length defined in params.")

            

            if grid_size_1 is None or grid_size_2 is None:
                raise ValueError("StructuredLineMesh must have grid_size_1 and grid_size_2 defined in params.")
            
            if spacing_1 is None or spacing_2 is None:
                raise ValueError("StructuredLineMesh must have spacing_1 and spacing_2 defined in params.")

            if base_vector_1_x is None or base_vector_1_y is None or base_vector_1_z is None:
                raise ValueError("StructuredLineMesh must have base_vector_1_x, base_vector_1_y, and base_vector_1_z defined in params.")
            
            if base_vector_2_x is None or base_vector_2_y is None or base_vector_2_z is None:
                raise ValueError("StructuredLineMesh must have base_vector_2_x, base_vector_2_y, and base_vector_2_z defined in params.")

            if base_point_x is None or base_point_y is None or base_point_z is None:
                raise ValueError("StructuredLineMesh must have base_point_x, base_point_y, and base_point_z defined in params.")
            
            if offset_1 is None or offset_2 is None:
                raise ValueError("StructuredLineMesh must have offset_1 and offset_2 defined in params.")

            if norm_x is None or norm_y is None or norm_z is None:
                raise ValueError("StructuredLineMesh must have normal_x, normal_y, and normal_z defined in params.")

            i_size = int(grid_size_1 * spacing_1 + 2*offset_1) * 1.2 # 1.2 to make sure the plane is larger than the mesh
            j_size = int(grid_size_2 * spacing_2 + 2*offset_2) * 1.2 # 1.2 to make sure the plane is larger than the mesh


            project_beam = pv.PolyData(beam_mesh.points).project_points_to_plane(origin=beam_mesh.center_of_mass(),
                                                                                 normal=(norm_x, norm_y, norm_z))
            project_beam.merge_points(tolerance=1e-3, inplace=True)
            normal = np.array([norm_x, norm_y, norm_z])
            normal = normal / np.linalg.norm(normal)  # Normalize the normal vector
            beamindxes = np.where(assembled_mesh.cell_data["MeshPartTag_celldata"] == self.beam_part.tag)[0]
            for projected_point in project_beam.points:
                point_a = projected_point - 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                point_b = projected_point + 1.1 * normal * length / 2 # 1.1 to make sure the line is longer than the mesh
                indxes = assembled_mesh.find_cells_along_line(point_a, point_b, tolerance=1e-3)
                indxes = np.intersect1d(indxes, beamindxes, assume_unique=True)  # Only keep beam indices
                if indxes.shape[0] == 0:
                    raise ValueError(
                        f"No beam elements found in assembled mesh for projected point {projected_point}."
                    )
                else:
                    # add interface
                    self._fork_solid_for_single_beam(assembled_mesh, indxes)
                # pl = pv.Plotter()
                # pl.add_mesh(assembled_mesh, color="blue", show_edges=True, opacity=0.5)
                # pl.add_mesh(assembled_mesh.extract_cells(indxes), color="red", show_edges=True, opacity=1.0,
                #             line_width=5)
                # pl.show()
            
        else:
            raise TypeError("beam_part must be a SingleLineMesh or StructuredLineMesh instance.")



        

    # ------------------------------------------------------------------
    # Event subscription
    # ------------------------------------------------------------------
    def _subscribe_events(self):  # type: ignore[override]
        """Override default subscription so RESOLVE_CORE_CONFLICTS is handled once per class."""
        # Per-instance hooks we still want
        EventBus.subscribe(FemoraEvent.PRE_ASSEMBLE, self._on_pre_assemble)
        EventBus.subscribe(FemoraEvent.POST_ASSEMBLE, self._on_post_assemble)
        EventBus.subscribe(FemoraEvent.POST_EXPORT, self._on_post_export)
        EventBus.subscribe(FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, self._on_embedded_beam_solid_tcl_export)

        # Register the collective callback only the first time a pile is created
        if not self.__class__._class_subscribed:
            EventBus.subscribe(
                FemoraEvent.RESOLVE_CORE_CONFLICTS,
                self.__class__._cls_resolve_core_conflicts,
            )
            self.__class__._class_subscribed = True


    @classmethod
    def _cls_resolve_core_conflicts(cls, assembled_mesh: pv.UnstructuredGrid, **kwargs):
        """Resolve core conflicts across *all* EmbeddedInfo objects collected during assembly.

        Steps:
        1. Remove exact duplicates (equal EmbeddedInfo) – keep one.
        2. Detect conflicts → raise error immediately.
        3. Treat "similar" pairs as friends and build transitive groups.
        4. For each group, set every solid cell’s Core to the **minimum** core_number
           found in that group.
        """

        if not cls._embeddedinfo_list:
            return  # nothing to do
        # print("resolving core conflicts")
        # ----------------------------------------------------------
        # 1. Deduplicate identical EmbeddedInfo objects
        # ----------------------------------------------------------
        unique_infos: list[EmbeddedInfo] = []
        for info in cls._embeddedinfo_list:
            if all(info != u for u in unique_infos):
                unique_infos.append(info)

        infos = unique_infos
        n = len(infos)

        # ----------------------------------------------------------
        # 2–3. Build similarity graph & detect conflicts
        # ----------------------------------------------------------
        parent = list(range(n))  # union-find structure

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int):
            pi, pj = find(i), find(j)
            if pi != pj:
                parent[pj] = pi

        for i in range(n):
            for j in range(i + 1, n):
                relation = infos[i].compare(infos[j])
                if relation == "conflict":
                    raise ValueError(
                        f"EmbeddedInfo conflict detected between {infos[i]} and {infos[j]}"
                    )
                elif relation == "similar":
                    union(i, j)
                # "equal" already handled via deduplication

        # ----------------------------------------------------------
        # 4. Apply lowest core number per connected component
        # ----------------------------------------------------------
        groups = defaultdict(list)  # root index → list[info index]
        for idx in range(n):
            groups[find(idx)].append(idx)

        for idx_list in groups.values():
            min_core = min(infos[i].core_number for i in idx_list)
            for i in idx_list:
                info = infos[i]
                # Create a new EmbeddedInfo with updated core_number
                new_info = EmbeddedInfo(
                    beams=info.beams,
                    core_number=min_core,
                    beams_solids=info.beams_solids
                )
                infos[i] = new_info
                # Also update the class-level list if present
                for idx, orig in enumerate(cls._embeddedinfo_list):
                    if orig == info:
                        cls._embeddedinfo_list[idx] = new_info
                # Update all instance-level lists in all instances
                for obj in cls.__subclasses__() + [cls]:
                    for inst in getattr(obj, "__dict__", {}).values():
                        if hasattr(inst, "_instance_embeddedinfo_list"):
                            inst_list = inst._instance_embeddedinfo_list
                            for idx2, orig2 in enumerate(inst_list):
                                if orig2 == info:
                                    inst_list[idx2] = new_info
                for _beams, solids in new_info.beams_solids:
                    try:
                        assembled_mesh.cell_data["Core"][solids] = min_core
                    except Exception as exc:
                        print(
                            f"[EmbeddedBeamSolidInterface] Failed to set core for solids {solids}: {exc}"
                        )
                try:
                    assembled_mesh.cell_data["Core"][list(new_info.beams)] = min_core
                except Exception as exc:
                    print(f"[EmbeddedBeamSolidInterface] Failed to set core for beams {new_info.beams}: {exc}")


        # print("end of resolve core conflicts")
        # pl = pv.Plotter()
        # pl.add_mesh(assembled_mesh, color='blue', scalars="Core", opacity=1.0, show_edges=True)
        # pl.show()



    def _on_embedded_beam_solid_tcl_export(self, file_handle, **kwargs):
        """Export TCL commands for the EmbeddedBeamSolidInterface.

        This method is called when the FEMora event `EMBEDDED_BEAM_SOLID_TCL` is emitted.
        It writes the necessary TCL commands to the provided file handle.
        """
        # print(f"[EmbeddedBeamSolidInterface:{self.name}] Exporting TCL commands.")
        from femora import MeshMaker
        crd_transf_tag = self.beam_part.element.get_transformation().tag
        file_handle.write("set Femora_embeddedBeamSolidStartTag [getFemoraMax eleTag]\n")
        file_handle.write("set Femora_embeddedBeamSolidStartTag [expr $Femora_embeddedBeamSolidStartTag + 1]\n")
        ele_start_tag = MeshMaker()._start_ele_tag
        core_start_tag = MeshMaker()._start_core_tag
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            file_handle.write("if {$pid == %d} {\n" % core)
            # for beams, solids in info.beams_solids:
            for jj, (beams, solids) in enumerate(info.beams_solids):
                # handle if elements tags are not starting from 1
                beams_str = " -beamEle ".join(str(b + ele_start_tag) for b in beams)
                solids_str = " -solidEle ".join(str(s + ele_start_tag) for s in solids)
                connect_file = f"EmbeddedBeamSolidConnect_{self.name}_beam{ii}_part{jj}.dat"
                interface_file = f"EmbeddedBeamSolidInterface_{self.name}_beam{ii}_part{jj}.dat"
                connect_file = MeshMaker.get_results_folder() + "/" + connect_file
                interface_file = MeshMaker.get_results_folder() + "/" + interface_file
                if self.write_connectivity:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (connect_file, connect_file))
                if self.write_interface:
                    file_handle.write("\tif {[file exists %s] == 1} {file delete %s}\n" % (interface_file, interface_file))
                file_handle.write(
                    f"\tset maxEleTag [generateInterfacePoints -beamEle {beams_str} -solidEle {solids_str} {'-gPenalty' if self.g_penalty else ''} " +
                    f"-shape {self.shape}  -nP {self.n_peri} -nL {self.n_long} -crdTransf {crd_transf_tag} -radius {self.radius} " +
                    f"-penaltyParam {self.penalty_param} -startTag $Femora_embeddedBeamSolidStartTag" +
                    f"{f' -connectivity {connect_file}' if self.write_connectivity else ''}" +
                    f"{f' -file {interface_file}' if self.write_interface else ''}]\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag $Femora_embeddedBeamSolidStartTag\n"
                    f"\tset EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag $maxEleTag\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj} startTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag\"\n"
                    # f"\tputs \"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag: $EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag\"\n"
                    f"\tset Femora_embeddedBeamSolidStartTag [expr $maxEleTag + 1]\n"
                    # f"\tputs $Femora_embeddedBeamSolidStartTag\n"
                )
            file_handle.write("}\n")
            file_handle.write("barrier\n")


    def _get_recorder(self, 
                      res_type: list[str],
                      dt: 'float | None' = None,
                      results_folder: str = "",
                      ) -> str:
        """
        This method is helper to get the recorder for the interface.
        It returns the recorder name based on the res_type.

        This method is caling by the EmbeddedBeamSolidInterfaceRecorder class to get the recorder command.

        Parameters
        ----------
        res_type : list[str]
            The type of the result to be recorded. It can be :
                - "displacement"
                - "localDisplacement"
                - "axialDisp"
                - "radialDisp"  
                - "tangentialDisp"
                - "globalForce"
                - "localForce"
                - "axialForce"
                - "radialForce"
                - "tangentialForce"
                - "solidForce"
                - "beamForce"
                - "beamLocalForce"
        Returns
        -------
        str
            The recorder command for the interface.

        Raises
        ------
        ValueError
            If the res_type is not supported.
        """
        from femora import MeshMaker    
        core_start_tag = MeshMaker()._start_core_tag

        cmd = ""
        for ii, info in enumerate(self._instance_embeddedinfo_list):
            core = info.core_number + core_start_tag
            cmd += "if {$pid == %d} {\n" % core
            for jj, (beams, solids) in enumerate(info.beams_solids):
                startEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_startTag"
                endEle = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_endTag"
                for res in res_type:
                    fileName = f"EmbeddedBeamSolid_{self.name}_beam{ii}_part{jj}_{res}.out"
                    fileName = results_folder + fileName
                    deltaT = "-dT %f" % dt if dt is not None else ""
                    cmd += f"\trecorder Element -file {fileName} -time {deltaT} -eleRange ${startEle} ${endEle} {res}\n"
            cmd += "}\n"
        return cmd


    # Keep an instance-level no-op to avoid accidental per-instance registration elsewhere
    def _on_resolve_core_conflicts(self, **payload):
        pass

    def _on_pre_assemble(self, **payload):
        # clear the class-level list
        self._embeddedinfo_list.clear()
        self._instance_embeddedinfo_list.clear()  # Clear instance-level list for this instance




if __name__ == "__main__":
    """Quick demo – builds a cube soil mesh and a central pile, then creates
    the EmbeddedBeamSolidInterface and exports a TCL file named
    `embedded_demo.tcl`.  Run with `python concrete_embedded_beam_solid.py`.
    """
    import femora as fm
    from femora.components.transformation.transformation import GeometricTransformation3D
    from femora.components.section.section_base import SectionManager
    # Ensure section types (e.g., 'Elastic') are registered
    import femora.components.section.section_opensees

    # Clear previous global state (helpful when running repeatedly)
    # fm.material.clear_all_materials()
    # fm.element.clear_all_elements()
    # fm.meshPart.clear_all_mesh_parts()
    # fm.section.clear_all_sections()
    # fm.region.clear()
    # fm.assembler.clear_assembly_sections()

    # ------------------------------------------------------------------
    # 1. Create materials and elements
    # ------------------------------------------------------------------
    soil_mat = fm.material.create_material("nDMaterial", "ElasticIsotropic", user_name="Soil", E=30e6, nu=0.3, rho=2000)
    brick_ele = fm.element.create_element("stdBrick", ndof=3, material=soil_mat)

    # Beam – needs section + transformation
    sec_mgr = SectionManager()   
    beam_sec = sec_mgr.create_section("Elastic", user_name="PileSection", E=2e11, A=0.05, Iz=1e-4, Iy=1e-4)
    transf = GeometricTransformation3D("Linear", 0, 1, 0)  # Local y-axis as vecXZ
    beam_ele = fm.element.create_element("DispBeamColumn", ndof=6, section=beam_sec, transformation=transf)

    # ------------------------------------------------------------------
    # 2. Create mesh parts
    # ------------------------------------------------------------------
    dx = 0.5
    Nx = int((10 - (-10)) / dx)
    Ny = Nx
    Nz = int((0 - (-20)) / dx)

    fm.mesh_part.volume.uniform_rectangular_grid(
        user_name="soil",
        element=brick_ele,
        region=None,
        **{ 'X Min': -10, 'X Max': 10, 'Y Min': -10, 'Y Max': 10, 'Z Min': -20, 'Z Max': 0,
           'Nx Cells': Nx, 'Ny Cells': Ny, 'Nz Cells': Nz }
    )

    fm.mesh_part.volume.uniform_rectangular_grid(
        user_name="cap",
        element=brick_ele,
        region=None,
        **{ 'X Min': -5, 'X Max': 5, 'Y Min': -5, 'Y Max': 5, 'Z Min': 1, 'Z Max': 2,
           'Nx Cells': 10//0.25, 'Ny Cells': 10//0.25, 'Nz Cells': 1//0.25 }
    )
    
        

    # pile1 = fm.mesh_part.line.single_line(
    #     user_name="beam1",
    #     element=beam_ele,
    #     region=None,
    #     **{ 'x0': 0, 'y0': 0, 'z0': -10, 'x1': 0, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    # )
    # pile2 = fm.mesh_part.line.single_line(
    #     user_name="beam2",
    #     element=beam_ele,
    #     region=None,
    #     **{ 'x0': 1, 'y0': 0, 'z0': -10, 'x1': 1, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    # )
    # pile3 = fm.mesh_part.line.single_line(
    #     user_name="beam3",
    #     element=beam_ele,
    #     region=None,
    #     **{ 'x0': -1, 'y0': 0, 'z0': -10, 'x1': -1, 'y1': 0, 'z1': 3, "number_of_lines":30, }
    # )
    # pile4 = fm.mesh_part.line.single_line(
    #     user_name="beam4",
    #     element=beam_ele,
    #     region=None,
    #     **{ 'x0': 0, 'y0': 1, 'z0': -10, 'x1': 0, 'y1': 1, 'z1': 3, "number_of_lines":30, }
    # )
    # pile5 = fm.mesh_part.line.single_line(
    #     user_name="beam5",
    #     element=beam_ele,
    #     region=None,
    #     **{ 'x0': 0, 'y0': -1, 'z0': -10, 'x1': 0, 'y1': -1, 'z1': 3, "number_of_lines":30, }
    # )

    piles = fm.mesh_part.line.structured_lines(
        user_name="piles",
        element=beam_ele,
        base_point_x = -4,
        base_point_y = -4,
        base_point_z = -8,
        base_vector_1_x = 1,
        base_vector_1_y = 0,
        base_vector_1_z = 0,
        base_vector_2_x = 0,
        base_vector_2_y = 1,
        base_vector_2_z = 0,
        normal_x = 0,
        normal_y = 0,
        normal_z = 1,
        grid_size_1 = 8,
        grid_size_2 = 8,
        spacing_1 = 1.0,
        spacing_2 = 1.0,
        number_of_lines = 10,
        length = 10, 
        offset_1 = 0,
        offset_2 = 0,
    )

    # ------------------------------------------------------------------
    # 3. Make assembly & interface
    # ------------------------------------------------------------------
    fm.assembler.create_section(["soil"], num_partitions=8, merging_points=False)
    # "cap", "beam1", "beam2", "beam3", "beam4", "beam5"
    fm.assembler.create_section(["cap", "piles"], num_partitions=4, merging_points=False)
    # fm.assembler.create_section(["piles"], num_partitions=1, merging_points=False)
    # fm.assembler.create_section(["beam1", "beam2"], num_partitions=4, merging_points=False)
    # fm.assembler.create_section(["beam3", "beam4", "beam5"], num_partitions=4, merging_points=False)
    # fm.assembler.create_section(["beam1", "beam2", "beam3", "beam4", "beam5"], num_partitions=8, merging_points=False)
    interface_radius = 0.25  # Radius for the embedded beam-solid interface
    EmbeddedBeamSolidInterface(
        name="EmbedTest",
        beam_part="piles",
        radius=interface_radius,
        n_peri=8,
        n_long=5,
        penalty_param=1.0e12,
        g_penalty=True,
    )
    
    # EmbeddedBeamSolidInterface(
    #     name="EmbedTest", beam_part="beam1", radius=interface_radius,
    #     n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    # )
    # EmbeddedBeamSolidInterface(
    #     name="EmbedTest2", beam_part="beam2", radius=interface_radius,
    #     n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    # )
    # EmbeddedBeamSolidInterface(
    #     name="EmbedTest3", beam_part="beam3", radius=interface_radius,
    #     n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    # )
    # EmbeddedBeamSolidInterface(
    #     name="EmbedTest4", beam_part="beam4", radius=interface_radius,
    #     n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    # )
    # EmbeddedBeamSolidInterface(
    #     name="EmbedTest5", beam_part="beam5", radius=interface_radius,
    #     n_peri=8, n_long=10, crd_transf_tag=transf.transf_tag,
    # )
    # open the gui to visualize the mesh
    fm.gui()
    exit(0)
    fm.assembler.Assemble()
    # fm.export_to_tcl("embedded_demo.tcl")
    # # fm.gui()

    

    # fm.export_to_tcl("embedded_demo.tcl")

    # pl = pv.Plotter()
    # pl.add_mesh(fm.assembler.AssembeledMesh, color='blue', scalars="Core", opacity=1.0, show_edges=True)
    # pl.show()
    # exit(0)


    # Assemble again to allow interface to move solids if needed
    # exit(0)  # Exit here to avoid exporting TCL if running interactively

 # Exit here to avoid exporting TCL if running interactively
    import os 
    # change the directory to the current directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Export TCL (interface will inject its command)
    fm.export_to_tcl("embedded_demo.tcl")
    fm.assembler.plot(show_edges=True, 
                      scalars="Core",
                      show_grid=True,
                      )

    # print("Demo finished → embedded_demo.tcl generated.")