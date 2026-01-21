from __future__ import annotations

from typing import List
from collections import defaultdict
# import time

import numpy as np
import pyvista as pv
from pykdtree.kdtree import KDTree

from femora.components.interface.interface_base import InterfaceBase
from femora.components.event.mixins import GeneratesMeshMixin
from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.event.event_bus import EventBus, FemoraEvent
from femora.components.Assemble.Assembler import Assembler
from femora.constants import FEMORA_MAX_NDF

class EmbeddedNodeInterface(InterfaceBase, GeneratesMeshMixin):
    """Create an *embedded node* contact interface. The EmbeddedNodeElement is a constraint between one constrained node and many retained nodes. Since in OpenSees a Multi-Point constraint can have only one retained node, this constraint was implemented as an Element, thus imposing the constraint using the Penalty approach.

    It constrains the displacements of the constrained node (NC) to be the weighted average of the displacements of the surrounding retained nodes (NRi). The same is done with the infinitesimal rotation, if the constrained node has rotational DOFs.

    The constrained node should be inside (or on the boundary of) the domain defined by the retained nodes.


    Using this interface in Femora all the complexities of the EmbeddedNodeElement are hidden from the user. The user only needs to provide two mesh parts: one for the constrained node and one for the retained nodes. The interface will handle the rest.
    """
    def __init__(
        self,
        name: str,
        constrained_node: 'MeshPart | str | int',
        retained_nodes: 'List[MeshPart | str | int] | None' = None,
        rot: bool = False, 
        p: bool = False, 
        K: float | None = None,
        KP: float | None = None,
        offset: float = None,
        use_mesh_part_points = False,
        normal_filter: list[float] | None = None,
        filter_tolerance: float = 0.98,
        friction_interface: bool = True,
        friction_interface_kn: float = 1e10,
        friction_interface_kt: float = 1e10,
        friction_interface_mu: float = 0.5,
        friction_interface_int_type: int = 0

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

        # Resolve MeshParts
        self.constrained_node = resolve_meshpart(constrained_node)
        if retained_nodes:
            self.retained_nodes = [resolve_meshpart(mp) for mp in retained_nodes]
        else:
            self.retained_nodes = list(MeshPart.get_mesh_parts().values())
            # remove the constrained node from the list
            self.retained_nodes.remove(self.constrained_node)


        if offset is None:
            offset = 0.0
        if offset < 0:
            raise ValueError("Offset must be a positive number")
        self.offset = offset

        if offset > 1e-2 and use_mesh_part_points:
            print("Warning: Using offset greater than 1e-2 with use_mesh_part_points=True may lead to unexpected results.")
        self._use_mesh_part_points = use_mesh_part_points

        self._rot = rot
        self._p = p
        self._K = K
        self._KP = KP
        if normal_filter is not None:
            normal_filter = np.array(normal_filter) / np.linalg.norm(normal_filter)
        self._normal_filter = normal_filter
        self._filter_tolerance = filter_tolerance
        self._friction_interface = friction_interface
        self._friction_interface_kn = friction_interface_kn
        self._friction_interface_kt = friction_interface_kt
        self._friction_interface_mu = friction_interface_mu
        self._friction_interface_int_type = friction_interface_int_type

        if self._use_mesh_part_points:
            self._friction_interface = False
            print("Warning: Using use_mesh_part_points=True will disable friction interface.")

        super().__init__(name, owners=[self.constrained_node.user_name])
        



    




    def _create_offset_mesh(self, asembelled_mesh: pv.UnstructuredGrid) -> pv.PolyData:
        if self.offset is None:
            #check if the mesh is a pv.PolyData or pv.UnstructuredGrid
            if isinstance(self.constrained_node.mesh, pv.PolyData):
                return self.constrained_node.mesh
            elif isinstance(self.constrained_node.mesh, pv.UnstructuredGrid):
                return self.constrained_node.mesh.extract_surface()
            else:
                raise ValueError("Mesh must be a pv.PolyData or pv.UnstructuredGrid")
        else:

            # offset the mesh
            asembelled_mesh.point_data['NodeIndex'] = np.arange(asembelled_mesh.n_points)
            constrained_mesh = asembelled_mesh.extract_cells(
                asembelled_mesh.cell_data['MeshPartTag_celldata'] == self.constrained_node.tag
            )
            original_mesh = constrained_mesh.extract_surface()
            # clean_original_mesh = original_mesh.clean(point_merging=True, tolerance=1e-6)

            # mesh with normals
            normal_filter = self._normal_filter
            filter_tolerance = self._filter_tolerance
            if normal_filter is None:
                mesh_with_normals = original_mesh.compute_normals(
                                                cell_normals=False, 
                                                point_normals=True, 
                                                inplace=False,
                                                split_vertices= False,
                                            )
                mask = np.ones(original_mesh.n_points, dtype=bool)
                original_mesh.point_data['Normals'] = mesh_with_normals.point_data['Normals']
            else:
                mesh_with_normals = original_mesh.compute_normals(
                                                cell_normals=False, 
                                                point_normals=True, 
                                                inplace=False,
                                                split_vertices= True
                                            )
                mask = np.zeros(original_mesh.n_points, dtype=bool)
                pyvistaOriginalPointIds = mesh_with_normals.point_data['pyvistaOriginalPointIds']
                normals = np.zeros((original_mesh.n_points, 3))
                for i in range(mesh_with_normals.n_points):
                    normal = mesh_with_normals.point_data['Normals'][i]
                    # dot product
                    dot_product = np.dot(normal, normal_filter)
                    if dot_product > filter_tolerance:
                        mask[pyvistaOriginalPointIds[i]] = True

                ids = np.where(mask)[0]
                normals[ids] = np.array(normal_filter)
                original_mesh.point_data['Normals'] = normals
                    
                    
                
            # pyvistaOriginalPointIds




            points = original_mesh.points
            normals = original_mesh.point_data['Normals']
            offset_dist = self.offset
            new_points = points + (normals * offset_dist)
            

            offset_mesh = original_mesh.copy()
            offset_mesh.points = new_points

            pl = pv.Plotter()
            pl.add_mesh(original_mesh, opacity=0.5, show_edges=True, color='gray')
            pl.add_mesh(offset_mesh, opacity=0.5, show_edges=True, color='orange')
            pl.show()
            

            # find the points in the constrained mesh 
            tree = KDTree(constrained_mesh.points)
            distances, indices = tree.query(points, k=1, distance_upper_bound=1e-6)
            
            # check that all the point are found
            if np.any(distances > 1e-6):
                raise ValueError("Some points in the offset mesh can not be related to the constrained mesh")
            
            # create a new mesh with the offset points
            point_ids = constrained_mesh.point_data['NodeIndex'][indices]

            # filter the points that are aligned with the normal vector
            # if normal_filter is not None:
            #     offset_mesh = offset_mesh.compute_normals(
            #                                     cell_normals=False, 
            #                                     point_normals=True, 
            #                                     inplace=False,
            #                                 )
            #     normals = offset_mesh.point_data['Normals']
            #     # Normalize the filter vector just in case
            #     filter_vec = np.array(normal_filter) / np.linalg.norm(normal_filter)
                
            #     # Calculate dot product: (N_points, 3) dot (3,) -> (N_points,)
            #     alignment = np.dot(normals, filter_vec)
                
            #     # Create a mask: True only for normals aligned with filter_vec
            #     # alignment > 0.9 means roughly within 25 degrees of the vector
            #     mask = alignment > filter_tolerance
            # else:
            #     # If no filter, apply offset to all points
            #     mask = np.ones(len(points), dtype=bool)

            # apply the mask to the points
            offset_mesh = offset_mesh.extract_points(mask, include_cells=False)
            point_ids = point_ids[mask]
            offset_points = offset_mesh.points
            normals = offset_mesh.point_data["Normals"]


            # now we need to filter out the point_ids that are in the retained mesh
            mask = np.zeros(asembelled_mesh.n_cells, dtype=bool)
            for part in self.retained_nodes:
                mask |= asembelled_mesh.cell_data['MeshPartTag_celldata'] == part.tag
            
            retained_mesh = asembelled_mesh.extract_cells(mask)
            reained_point_ids = retained_mesh.point_data['NodeIndex']

            mask = np.ones(len(point_ids), dtype=bool)
            for i, point_id in enumerate(point_ids):
                if point_id in reained_point_ids:
                    mask[i] = False
            
            offset_points = offset_points[mask]
            point_ids = point_ids[mask]


            pl = pv.Plotter()
            pl.add_mesh(constrained_mesh, opacity=0.5, show_edges=True, color='gray')
            pl.add_mesh(pv.PolyData(offset_points), opacity=0.5, show_edges=True, color='blue')
            pl.show()
            return offset_points, point_ids, normals
        



    def _on_post_assemble(self, assembled_mesh: pv.UnstructuredGrid) -> None:
        """Detect the nodes from the offset mesh that are inside tetrahedra elements of the retained nodes."""

        # 1) get the asembelled mesh
        # asembelled_mesh = Assembler().get_mesh()
        asembelled_mesh = assembled_mesh.copy()

        if asembelled_mesh is None:
            raise ValueError("Assembled mesh not found; please run Assembler first.")
        
        # 2) tetrahedralize the asembelled mesh
        tetrahedra_mesh = self._tetrahedralize(asembelled_mesh)

        # 3) offset the constrained node
        offset_points, point_ids, normals = self._create_offset_mesh(asembelled_mesh)


        # 4) filter out only the tetrahedrons that are from the retained nodes
        mask1 = tetrahedra_mesh.celltypes == pv.CellType.TETRA
        mask2 = np.zeros(tetrahedra_mesh.n_cells, dtype=bool)
        for part in self.retained_nodes:
            mask2 |= tetrahedra_mesh.cell_data['MeshPartTag_celldata'] == part.tag

        mask = mask1 & mask2
        
        # 5) create a node index array for points
        # node_index = np.arange(0, tetrahedra_mesh.n_points, dtype=int)
        cell_index = np.arange(0, tetrahedra_mesh.n_cells, dtype=int)
        # tetrahedra_mesh.point_data['NodeIndex'] = node_index 
        tetrahedra_mesh.cell_data['CellIndex'] = cell_index
        print(mask.shape)

        # 6) extract cells that are from the retained nodes
        tetrahedra_mesh_filtered = tetrahedra_mesh.extract_cells(mask)

        # 7) find the nodes that are inside the tetrahedra elements
        cell_ids = tetrahedra_mesh_filtered.find_containing_cell(offset_points)
        # delete the -1 values
        mask = cell_ids != -1
        



        selected_cells = cell_ids[mask]
        selected_points = offset_points[mask]
        selected_normals = normals[mask]
        point_ids = point_ids[mask]
        print(f"filtered tetrahedra has {tetrahedra_mesh_filtered.n_cells} cells")
        print(f"filtered tetrahedra has {tetrahedra_mesh_filtered.n_points} points")
        print(f"selected points has {selected_points.shape[0]} points")
        original_cells = tetrahedra_mesh_filtered.cell_data['CellIndex'][selected_cells]

        # 8) mask
    
        pl = pv.Plotter()
        pl.add_mesh(asembelled_mesh, opacity=0.5, show_edges=True, color='gray')
        pl.add_mesh(asembelled_mesh.extract_points(point_ids,include_cells = False), opacity=0.5, show_edges=True, color='blue')
        pl.show()



        



        # creating tet elements
        tet_elements = np.zeros((selected_points.shape[0], 4), dtype=int)
        start = tetrahedra_mesh.offset[original_cells]
        indices = start[:, None] + np.arange(4)
        tet_elements = tetrahedra_mesh.cell_connectivity[indices]





        # now we need to create cores
        # each selected point is related to a tetrahedron element so the point should be in the core
        # each point id is related to selected_point but the point can be exist in a different core
        tet_cores = tetrahedra_mesh_filtered.cell_data['Core'][selected_cells]
        point_id_cores = []
        for point_id in point_ids:
            tmp_mesh = asembelled_mesh.extract_points(point_id,include_cells = True)
            point_id_cores.append(np.unique(tmp_mesh.cell_data['Core']))
            # pl = pv.Plotter()
            # pl.add_mesh(tmp_mesh, opacity=0.5, show_edges=True, scalars = "Core", cmap = "viridis")
            # pl.add_mesh(asembelled_mesh, opacity=0.5, show_edges=True, color='gray')
            # pl.show()
        print(point_id_cores)

        

        

        # 8) mask
        pl = pv.Plotter()
        mask = asembelled_mesh.cell_data['MeshPartTag_celldata'] == self.constrained_node.tag
        mask = ~mask
        pl.add_mesh(asembelled_mesh.extract_cells(mask), opacity=0.5, show_edges=True, color='gray')
        # pl.add_mesh(offset_mesh, opacity=1.0, show_edges=True, color='blue')
        pl.add_mesh(tetrahedra_mesh.extract_cells(original_cells), opacity=0.5, show_edges=True, color='red')
        pl.add_mesh(pv.PolyData(selected_points), opacity=1.0, show_edges=True, color='blue')
        # pl.add_mesh(self.constrained_node.mesh, opacity=1.0, show_edges=True, color='royalblue')
        pl.add_mesh(asembelled_mesh.extract_points(point_ids,include_cells = False), opacity=1.0, show_edges=True, color='green')
        pl.show()
            
    

        # create a embedded node element
        from femora import MeshMaker
        ndf = 3
        embededd_ele = MeshMaker().element.create_element("ASDEmbeddedNodeElement3D",
                                           ndof = ndf, 
                                           rot = self._rot,
                                           p = self._p, 
                                           K = self._K,
                                           KP = self._KP,
                                           )

        # Assembler().AssembeledMesh.merge(embedded_mesh, merge_points=True, inplace=True)
        # 1. Get references to the existing assembled mesh data
        base_mesh = Assembler().AssembeledMesh
        old_points = base_mesh.points
        old_cells = base_mesh.cells
        old_celltypes = base_mesh.celltypes

        # 2. Offset the indices in the new mesh
        # We must shift the point IDs in the new cells so they point to the 
        # correct positions in the new combined points array.
        offset = old_points.shape[0]

        # Extract the cells array. Remember VTK format: [n, p1, p2, ..., n, p1, p2...]
        new_cells_raw = []
        new_celltypes = []
        new_ndf = base_mesh.point_data['ndf'][point_ids]
        num_new_cells = tet_elements.shape[0]
        num_new_points = selected_points.shape[0] if not self._use_mesh_part_points else 0
        tet_cores = np.array(tet_cores, dtype=int)
        for i in range(0, selected_points.shape[0]):
            new_cells_raw.append(5)
            if self._use_mesh_part_points:
                new_cells_raw.append(point_ids[i])  # Constrained node from original mesh
            else:
                new_cells_raw.append(i + offset)  # Constrained node
            for j in tet_elements[i]:
                new_cells_raw.append(j)
            new_celltypes.append(pv.CellType.POLY_VERTEX)

        # 3. Concatenate Point and Cell arrays
        if self._use_mesh_part_points:
            combined_points = old_points
        else:
            combined_points = np.vstack((old_points, selected_points))
            
        combined_cells = np.concatenate((old_cells, new_cells_raw))
        combined_celltypes = np.concatenate((old_celltypes, new_celltypes))

        # 4. Create the final Mesh
        final_mesh = pv.UnstructuredGrid(combined_cells, combined_celltypes, combined_points)

        # 5. Copy over existing data arrays
        # cell data
        final_mesh.cell_data['Core'] = np.concatenate((base_mesh.cell_data['Core'], tet_cores))
        final_mesh.cell_data['ElementTag'] = np.concatenate((base_mesh.cell_data['ElementTag'], np.full(num_new_cells, embededd_ele.tag, dtype=np.uint16)))
        final_mesh.cell_data['MaterialTag'] = np.concatenate((base_mesh.cell_data['MaterialTag'], np.full(num_new_cells, 0, dtype=np.uint16)))
        final_mesh.cell_data['Region'] = np.concatenate((base_mesh.cell_data['Region'], np.full(num_new_cells, 0, dtype=np.uint16)))
        final_mesh.cell_data['MeshPartTag_celldata'] = np.concatenate((base_mesh.cell_data['MeshPartTag_celldata'], np.full(num_new_cells, 0, dtype=np.uint16)))

        # point_data 
        if num_new_points > 0:
            final_mesh.point_data['MeshPartTag_pointdata'] = np.concatenate((base_mesh.point_data['MeshPartTag_pointdata'], np.full(num_new_points, 0, dtype=np.uint16)))
            final_mesh.point_data['Mass'] = np.vstack((base_mesh.point_data['Mass'], np.full(shape=(num_new_points, FEMORA_MAX_NDF), fill_value=0.0, dtype=np.float32)))
            final_mesh.point_data['ndf'] = np.concatenate((base_mesh.point_data['ndf'], new_ndf))
        else:
            final_mesh.point_data['MeshPartTag_pointdata'] = base_mesh.point_data['MeshPartTag_pointdata']
            final_mesh.point_data['Mass'] = base_mesh.point_data['Mass']
            final_mesh.point_data['ndf'] = base_mesh.point_data['ndf']
                                                 

        # 6. Update your Assembler
        Assembler().AssembeledMesh = final_mesh
        Assembler().plot(color="blue", opacity=0.5, show_edges=False, )


        # now if not use_mesh_part_points, we need to make mpconstraint for the new points to the original point
        if not self._use_mesh_part_points:
            mk = MeshMaker()
            start_node = mk.get_start_node_tag()
            for i in range(selected_points.shape[0]):
                original_point_id = point_ids[i] + start_node
                new_point_id = i + offset + start_node
                ndf = base_mesh.point_data['ndf'][original_point_id]
                mk.constraint.mp.create_equal_dof(
                    master_node = new_point_id,
                    slave_nodes = [original_point_id],
                    dofs = list(range(1, ndf+1))
                )
                    
        
        if self._friction_interface:
            friction_ele = MeshMaker().element.create_element("ASDFrictionInterfaceElement3D",
                                           ndof = ndf, 
                                           rot = self._rot,
                                           p = self._p, 
                                           K = self._K,
                                           KP = self._KP,
                                           )
            
            # 1. Get the base mesh
            base_mesh = Assembler().AssembeledMesh
            old_points = base_mesh.points
            old_cells = base_mesh.cells
            old_celltypes = base_mesh.celltypes

            # 2. Create the new cells
            new_cells = []
            new_celltypes = []
            
            # 3. Create the new cells for friction interface
            # offset remains from the previous mesh before adding embedded nodes
            for i in range(selected_points.shape[0]):
                new_cells.append(2)
                new_cells.append(i + offset)
                new_cells.append(point_ids[i])
                new_celltypes.append(pv.CellType.LINE)

            # 4. Concatenate Point and Cell arrays
            combined_points = old_points
            combined_cells = np.concatenate((old_cells, new_cells))
            combined_celltypes = np.concatenate((old_celltypes, new_celltypes))

            # 5. Create the final Mesh
            final_mesh = pv.UnstructuredGrid(combined_cells, combined_celltypes, combined_points)

            # 6. Copy over existing data arrays
            # cell data
            final_mesh.cell_data['Core'] = np.concatenate((base_mesh.cell_data['Core'], tet_cores))
            final_mesh.cell_data['ElementTag'] = np.concatenate((base_mesh.cell_data['ElementTag'], np.full(num_new_cells, friction_ele.tag, dtype=np.uint16)))
            final_mesh.cell_data['MaterialTag'] = np.concatenate((base_mesh.cell_data['MaterialTag'], np.full(num_new_cells, 0, dtype=np.uint16)))
            final_mesh.cell_data['Region'] = np.concatenate((base_mesh.cell_data['Region'], np.full(num_new_cells, 0, dtype=np.uint16)))
            final_mesh.cell_data['MeshPartTag_celldata'] = np.concatenate((base_mesh.cell_data['MeshPartTag_celldata'], np.full(num_new_cells, 0, dtype=np.uint16)))
            
            # point data
            final_mesh.point_data['MeshPartTag_pointdata'] = base_mesh.point_data['MeshPartTag_pointdata']
            final_mesh.point_data['Mass'] = base_mesh.point_data['Mass']
            final_mesh.point_data['ndf'] = base_mesh.point_data['ndf']

            # 7. Update Assembler
            Assembler().AssembeledMesh = final_mesh
            



        


            
    def _tetrahedralize(self, mesh: pv.UnstructuredGrid) -> pv.UnstructuredGrid:
        new_cells = []
        new_cell_types = []
        parent_indices = [] # Track which original cell each new cell came from
        
        cells = mesh.cells
        cell_types = mesh.celltypes
        offset = 0


        # print(mesh.cell_data.keys())
        # print(mesh.point_data.keys())

        # only tetrahedralize the cells that are from the retained nodes
        mask = np.zeros(mesh.n_cells, dtype=bool)
        for meshpart in self.retained_nodes:
            mask |= mesh.cell_data["MeshPartTag_celldata"] == meshpart.tag
         
        for i in range(mesh.n_cells):
            n_points = cells[offset]
            cell_nodes = cells[offset + 1 : offset + 1 + n_points]
            c_type = cell_types[i]
            
            # 1. Handle Hexahedrons (Decompose)
            if c_type == pv.CellType.HEXAHEDRON and n_points == 8 and mask[i]:
                # Standard 5-tetra decomposition
                tets = [
                    [cell_nodes[0], cell_nodes[1], cell_nodes[3], cell_nodes[4]],
                    [cell_nodes[1], cell_nodes[2], cell_nodes[3], cell_nodes[6]],
                    [cell_nodes[4], cell_nodes[5], cell_nodes[6], cell_nodes[1]],
                    [cell_nodes[4], cell_nodes[7], cell_nodes[6], cell_nodes[3]],
                    [cell_nodes[1], cell_nodes[3], cell_nodes[4], cell_nodes[6]]
                ]
                for t in tets:
                    new_cells.extend([4] + t)
                    new_cell_types.append(pv.CellType.TETRA)
                    parent_indices.append(i) # All 5 tets point to the original Hex index
            
            # 2. Handle everything else (Preserve)
            else:
                new_cells.extend([n_points] + list(cell_nodes))
                new_cell_types.append(c_type)
                parent_indices.append(i) # 1-to-1 mapping
                
            offset += n_points + 1

        # Create the new mesh structure
        new_mesh = pv.UnstructuredGrid(np.array(new_cells), np.array(new_cell_types), mesh.points)
        
        # --- Data Preservation ---
        
        # 1. Point Data: Node numbering is identical, so we just copy
        new_mesh.point_data.update(mesh.point_data)
        
        # 2. Cell Data: Use parent_indices to map original data to new cells
        parent_indices = np.array(parent_indices)
        for key, data in mesh.cell_data.items():
            # This handles both scalars and vectors (e.g., stress tensors)
            new_mesh.cell_data[key] = data[parent_indices]
            
        # return new_mesh

        print(f"New mesh has {new_mesh.n_cells} cells")
        print(f"New mesh has {new_mesh.n_points} points")
        
        # print cell types
        print(f"original mesh has {mesh.n_cells} cells")
        print(f"original mesh has {mesh.n_points} points")


        # check the number of points are equal
        assert new_mesh.n_points == mesh.n_points, "Number of points are not equal in the new and original mesh"
    
        # check the number of cells are equal
        num_hex = mesh.celltypes == pv.CellType.HEXAHEDRON
        num_hex = num_hex & mask
        assert new_mesh.n_cells == mesh.n_cells + 4*sum(num_hex), "Number of cells are not equal in the new and original mesh"        


        pl = pv.Plotter()
        pl.add_mesh(new_mesh, color='red', opacity=1.0, style='wireframe')
        pl.add_mesh(mesh, color='blue', opacity=0.5)
        pl.show()

        return new_mesh

    

        
    # def _on_interface_tcl_export(self, **payload):
    #     file_handle = payload['file_handle']
    #     file_handle.write(f"# {self.name} interface elements\n")
        
    #     # check if the point_ids, selected_points, tet_elements are not None
    #     if self._point_ids is None or self._selected_points is None or self._tet_elements is None:
    #         raise ValueError("Assemble the model first.")
        
    #     # mesh maker is the mother class 
    #     from femora import MeshMaker
    #     mesh_maker = MeshMaker()
    #     max_ele_tag = mesh_maker.get_max_ele_tag() + 1
    #     max_node_tag = mesh_maker.get_max_node_tag() + 1
    #     ndfs = mesh_maker.assembler.get_mesh().point_data['ndf']
    #     ndfs = ndfs[self._point_ids]
    #     point_id_coords = mesh_maker.assembler.get_mesh().points[self._point_ids]
    #     point_id_tags = mesh_maker.get_start_node_tag() + self._point_ids
 

        

    #     for i in range(len(self._tet_elements)):
    #         node_tag = i + max_node_tag
    #         ele_tag = i + max_ele_tag
    #         file_handle.write("if {$pid == %d} {\n" % self._tet_cores[i])
    #         file_handle.write("\tnode %d %f %f %f -ndf %d\n" % (node_tag, self._selected_points[i][0], self._selected_points[i][1], self._selected_points[i][2], ndfs[i]))
    #         if self._tet_cores[i] not in self._point_id_cores:
    #             file_handle.write("\tnode %d %f %f %f -ndf %d\n" % (point_id_tags[i], point_id_coords[i][0], point_id_coords[i][1], point_id_coords[i][2], ndfs[i]))
    #             file_handle.write("\tequalDOF %d %d 1 2 3 4\n" % (node_tag, self._tet_cores[i]))

    #         # file_handle.write("\t element tetra %d %d %d %d %d\n
    #         #  element ASDEmbeddedNodeElement $eleTag $Cnode $Rnode1 $Rnode2 $Rnode3 <$Rnode4> <-rot> <-p> <-K $K> <-KP $KP>")
    #         # print(self._tet_elements[i])
    #         file_handle.write("\telement ASDEmbeddedNodeElement %d %d %d %d %d %d\n" % (ele_tag, node_tag, self._tet_elements[i][0], self._tet_elements[i][1], self._tet_elements[i][2], self._tet_elements[i][3]))
    #         file_handle.write("}\n")


        

    


            
            


            
            

        

    



    