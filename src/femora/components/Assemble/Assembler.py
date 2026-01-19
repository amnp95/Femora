from typing import List, Optional, Dict, Any
import numpy as np
import pyvista as pv
import warnings
import logging
import sys
from scipy.spatial import KDTree

from femora.components.Mesh.meshPartBase import MeshPart
from femora.components.Element.elementBase import Element
from femora.components.Material.materialBase import Material
from femora.components.event.event_bus import EventBus, FemoraEvent
from femora.utils.progress import Progress
from femora.constants import FEMORA_MAX_NDF


class Assembler:
    """
    Singleton Assembler class to manage multiple AssemblySection instances.
    
    This class ensures only one Assembler instance exists in the program 
    and keeps track of all created assembly sections with dynamic tag management.
    It provides methods for creating, managing, and assembling mesh sections
    into a complete structural model.
    
    The Assembler is responsible for:
    - Creating and tracking AssemblySection instances
    - Maintaining unique tags for each section
    - Combining multiple sections into a unified mesh
    - Managing the lifecycle of assembly sections
    """
    _instance = None
    _assembly_sections: Dict[int, 'AssemblySection'] = {}
    AssembeledMesh = None
    AssembeledActor = None
    # AbsorbingMesh = None
    # AbsorbingMeshActor = None
    
    def __new__(cls):
        """
        Implement singleton pattern for the Assembler class.
        
        Ensures only one Assembler instance is created throughout the program's lifecycle.
        If an instance already exists, returns that instance instead of creating a new one.
        
        Returns:
            Assembler: The singleton Assembler instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """
        Class method to get the single Assembler instance.
        
        This method provides an alternative way to access the singleton instance,
        creating it if it doesn't already exist.
        
        Returns:
            Assembler: The singleton Assembler instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_section(
        self, 
        meshparts: List[str], 
        num_partitions: int = 1, 
        partition_algorithm: str = "kd-tree", 
        merging_points: bool = True,
        mass_merging: str = "sum",
        tolerance: float = 1e-5,
        **kwargs: Any
    ) -> 'AssemblySection':
        """
        Create an AssemblySection directly through the Assembler.
        
        This method creates a new AssemblySection from the specified mesh parts and
        automatically registers it with the Assembler. It handles initialization of
        the section, assigns a unique tag, and returns the created section.
        
        Args:
            meshparts (List[str]): List of mesh part names to be assembled. These must be
                                  names of previously created MeshPart instances.
            num_partitions (int, optional): Number of partitions for parallel processing.
                                          For kd-tree, will be rounded to next power of 2.
                                          Defaults to 1 (no partitioning).
            partition_algorithm (str, optional): Algorithm used for partitioning the mesh.
                                               Currently supports "kd-tree".
                                               Defaults to "kd-tree".
            merging_points (bool, optional): Whether to merge points that are within a 
                                           tolerance distance when assembling mesh parts.
                                           Defaults to True.
            mass_merging (str, optional): Method for merging mass properties of mesh parts.
                                           Defaults to "sum". Options are "sum" or "average".
                                           if "sum", the mass is summed across all merged points.
                                           if "average", the mass is averaged across merged points.
            **kwargs: Additional keyword arguments to pass to AssemblySection constructor
        
        Returns:
            AssemblySection: The newly created and registered assembly section
            
        Raises:
            ValueError: If any of the specified mesh parts don't exist or if the
                      partition algorithm is invalid
        """
        
        # Create the AssemblySection 
        assembly_section = AssemblySection(
            meshparts=meshparts,
            num_partitions=num_partitions,
            partition_algorithm=partition_algorithm,
            merging_points=merging_points,
            mass_merging=mass_merging,
            **kwargs
        )
        
        return assembly_section

    def delete_section(self, tag: int) -> None:
        """
        Delete an AssemblySection by its tag.
        
        Removes the specified assembly section from the internal registry and
        updates the tags of remaining sections to maintain sequential numbering.
        
        Args:
            tag (int): Tag of the assembly section to delete
        
        Raises:
            KeyError: If no assembly section with the given tag exists
        """
        # Retrieve the section to ensure it exists
        section = self.get_assembly_section(tag)
        
        # Remove the section from the internal dictionary
        del self._assembly_sections[tag]
        
        # Retag remaining sections
        self._retag_sections()

    def _add_assembly_section(self, assembly_section: 'AssemblySection') -> int:
        """
        Internally add an AssemblySection to the Assembler's tracked sections.
        
        This method is called by the AssemblySection constructor to register 
        itself with the Assembler. It assigns a unique tag to the section and 
        adds it to the internal registry.
        
        Args:
            assembly_section (AssemblySection): The AssemblySection to add
        
        Returns:
            int: Unique tag assigned to the added assembly section
        """
        # Find the first available tag starting from 1
        tag = 1
        while tag in self._assembly_sections:
            tag += 1
        
        # Store the assembly section with its tag
        self._assembly_sections[tag] = assembly_section
        
        return tag

    def _remove_assembly_section(self, tag: int) -> None:
        """
        Remove an assembly section by its tag and retag remaining sections.
        
        Internal method to delete a section from the registry and update
        tags of remaining sections to maintain sequential numbering.
        
        Args:
            tag (int): Tag of the assembly section to remove
        
        Raises:
            KeyError: If no assembly section with the given tag exists
        """
        if tag not in self._assembly_sections:
            raise KeyError(f"No assembly section with tag {tag} exists")
        
        # Remove the specified tag
        del self._assembly_sections[tag]
        
        # Retag all remaining sections to ensure continuous numbering
        self._retag_sections()

    def _retag_sections(self):
        """
        Retag all assembly sections to ensure continuous numbering from 1.
        
        This internal method is called after removing a section to ensure that
        the remaining sections have sequential tags starting from 1. It creates
        a new dictionary with updated tags and updates each section's internal tag.
        """
        # Sort sections by their current tags
        sorted_sections = sorted(self._assembly_sections.items(), key=lambda x: x[0])
        
        # Create a new dictionary with retagged sections
        new_assembly_sections = {}
        for new_tag, (_, section) in enumerate(sorted_sections, 1):
            new_assembly_sections[new_tag] = section
            section._tag = new_tag  # Update the section's tag
        
        # Replace the old dictionary with the new one
        self._assembly_sections = new_assembly_sections
    
    def get_assembly_section(self, tag: int) -> 'AssemblySection':
        """
        Retrieve an AssemblySection by its tag.
        
        Gets a specific assembly section from the internal registry using its unique tag.
        
        Args:
            tag (int): Tag of the assembly section to retrieve
        
        Returns:
            AssemblySection: The requested assembly section
        
        Raises:
            KeyError: If no assembly section with the given tag exists
        """
        return self._assembly_sections[tag]
    
    def list_assembly_sections(self) -> List[int]:
        """
        List all tags of assembly sections.
        
        Returns a list of all tags that can be used to retrieve assembly sections.
        The tags are sorted in ascending order.
        
        Returns:
            List[int]: Tags of all added assembly sections
        """
        return list(self._assembly_sections.keys())
    
    def clear_assembly_sections(self) -> None:
        """
        Clear all tracked assembly sections.
        
        Removes all assembly sections from the internal registry, effectively
        resetting the Assembler's state. This does not affect the assembled mesh
        if one has already been created.
        """
        self._assembly_sections.clear()

    def get_sections(self) -> Dict[int, 'AssemblySection']:
        """
        Get all assembly sections.
        
        Returns a copy of the internal dictionary containing all assembly sections.
        This ensures that modifications to the returned dictionary don't affect
        the Assembler's internal state.
        
        Returns:
            Dict[int, AssemblySection]: Dictionary of all assembly sections, keyed by their tags
        """
        return self._assembly_sections.copy()
    
    def get_section(self, tag: int) -> 'AssemblySection':
        """
        Get an assembly section by its tag.
        
        Alias for get_assembly_section for backward compatibility.
        
        Args:
            tag (int): Tag of the assembly section to retrieve
        
        Returns:
            AssemblySection: The requested assembly section
        
        Raises:
            KeyError: If no assembly section with the given tag exists
        """
        return self._assembly_sections[tag]

    @staticmethod
    def _snap_points(points: np.ndarray, tol: float = 1e-5) -> np.ndarray:
        """
        Snap points within tolerance to the first representative point
        using KDTree.
        """
        tree = KDTree(points)
        groups = tree.query_ball_tree(tree, tol)

        visited = np.zeros(len(points), dtype=bool)
        snapped = points.copy()

        for i in range(len(points)):
            if visited[i]:
                continue
            cluster = groups[i]
            rep = points[i]  # pick the first point
            for j in cluster:
                snapped[j] = rep
                visited[j] = True

        return snapped
    
    def get_num_cells(self) -> int:
        """
        return the total number of cells in the assembled mesh

        Args:
            None
        Returns:
            positive int: total number of cells
            negative int: if assembled mesh is None
        """
        if self.AssembeledMesh is None:
            return -1
        return self.AssembeledMesh.n_cells
    
    def get_num_points(self) -> int:
        """
        return the total number of points in the assembled mesh

        Args:
            None
        Returns:
            positive int: total number of points
            negative int: if assembled mesh is None
        """
        if self.AssembeledMesh is None:
            return -1
        return self.AssembeledMesh.n_points


    
    def Assemble(self, 
                 merge_points: bool = True, 
                 mass_merging: str = "sum",
                 tolerance: float = 1e-5,
                 *, 
                 progress_callback=None) -> None:
        """
        Assemble all registered AssemblySections into a single unified mesh.
        
        This method combines all assembly sections into a single PyVista
        UnstructuredGrid. It preserves important mesh data like element tags,
        material tags, and region information. It also handles partitioning by
        correctly updating the Core cell data to maintain distinct partition ids.
        
        Args:
            merge_points (bool, optional): Whether to merge points during assembly.
                                         If True, points within a small tolerance will
                                         be combined, creating a continuous mesh.
                                         If False, all points are preserved.
                                         Defaults to True.
                                         
        Raises:
            ValueError: If no assembly sections have been created
            Exception: If any error occurs during the assembly process
        """
        
        if self.AssembeledMesh is not None:
            del self.AssembeledMesh
            self.AssembeledMesh = None
        
        if not self._assembly_sections:
            raise ValueError("No assembly sections have been created")
        
        # Progress setup
        if progress_callback is None:
            progress_callback = lambda v, msg="": Progress.callback(v, msg, desc="Assembling")

        progress_callback(0, "initialising")

        # Notify subscribers that assembly is starting
        EventBus.emit(FemoraEvent.PRE_ASSEMBLE)
        
        sorted_sections = sorted(self._assembly_sections.items(), key=lambda x: x[0])
        
        first_mesh = sorted_sections[0][1].mesh
        # assert first_mesh is not None, "AssemblySection mesh is None"
        if first_mesh is None:
            raise ValueError("There is no mesh to assemble. Please create an AssemblySection first.")
        
        self.AssembeledMesh = pv.MultiBlock();
        self.AssembeledMesh.append(first_mesh.copy())
        progress_callback(1 / len(sorted_sections) * 70, f"merged section 1/{len(sorted_sections)}")
        num_partitions = sorted_sections[0][1].num_partitions

        try :
            for idx, (tag, section) in enumerate(sorted_sections[1:], start=2):
                second_mesh = section.mesh.copy()  # type: ignore[attr-defined]
                second_mesh.cell_data["Core"] = second_mesh.cell_data["Core"] + num_partitions
                num_partitions = num_partitions + section.num_partitions
                self.AssembeledMesh.append(second_mesh)
                perc = idx / len(sorted_sections) * 70
                progress_callback(perc, f"merged section {idx}/{len(sorted_sections)}")
            self.AssembeledMesh = self.AssembeledMesh.combine(
                merge_points=False,
                tolerance=1e-5,
            )
            if merge_points:
                number_of_points_before_cleaning = self.AssembeledMesh.n_points

                # snap points within tolerance
                self.AssembeledMesh.points = self._snap_points(self.AssembeledMesh.points, tolerance)

                mass = self.AssembeledMesh.point_data["Mass"]
                self.AssembeledMesh = self.AssembeledMesh.clean(
                    tolerance=1e-5,
                    remove_unused_points=False,
                    produce_merge_map=True,
                    average_point_data=True,
                    merging_array_name="ndf",
                    progress_bar=False,
                )
                # make the ndf array uint16
                self.AssembeledMesh.point_data["ndf"] = self.AssembeledMesh.point_data["ndf"].astype(np.uint16)
                # make the MeshPartTag_pointdata array uint16
                self.AssembeledMesh.point_data["MeshPartTag_pointdata"] = self.AssembeledMesh.point_data["MeshPartTag_pointdata"].astype(np.uint16)
                
                number_of_points_after_cleaning = self.AssembeledMesh.n_points

                if mass_merging == "sum":
                    if number_of_points_before_cleaning != number_of_points_after_cleaning:
                        Mass = np.zeros((number_of_points_after_cleaning, FEMORA_MAX_NDF), dtype=np.float32)
                        for i in range(self.AssembeledMesh.field_data["PointMergeMap"].shape[0]):
                            Mass[self.AssembeledMesh.field_data["PointMergeMap"][i],:] += mass[i,:]
                
                        self.AssembeledMesh.point_data["Mass"] = Mass

                del self.AssembeledMesh.field_data["PointMergeMap"]


        except Exception as e:
            raise e
        
        # Notify any subscribers that the mesh has been assembled and partitioned
        progress_callback(70, "post-assemble")
        EventBus.emit(FemoraEvent.POST_ASSEMBLE, assembled_mesh=self.AssembeledMesh)
        progress_callback(90, "resolving core conflicts")
        EventBus.emit(FemoraEvent.RESOLVE_CORE_CONFLICTS, assembled_mesh=self.AssembeledMesh)

        progress_callback(100, "done")
        # Announce the number of cores used for assembly
        self._announce_required_cores()
        
    def delete_assembled_mesh(self) -> None:
        """
        Delete the assembled mesh.
        
        Releases memory by deleting the assembled mesh, if it exists.
        This is useful when you want to clear resources or prepare for
        a new assembly operation without affecting the assembly sections.
        """
        if self.AssembeledMesh is not None:
            del self.AssembeledMesh
            self.AssembeledMesh = None

    def plot(
        self,
        color=None,
        style=None,
        scalars=None,
        clim=None,
        show_edges=None,
        edge_color=None,
        point_size=None,
        line_width=None,
        opacity=None,
        flip_scalars=False,
        lighting=None,
        n_colors=256,
        interpolate_before_map=None,
        cmap=None,
        label=None,
        reset_camera=None,
        scalar_bar_args=None,
        show_scalar_bar=None,
        multi_colors=False,
        name=None,
        texture=None,
        render_points_as_spheres=None,
        render_lines_as_tubes=None,
        smooth_shading=None,
        split_sharp_edges=None,
        ambient=None,
        diffuse=None,
        specular=None,
        specular_power=None,
        nan_color=None,
        nan_opacity=1.0,
        culling=None,
        rgb=None,
        categories=False,
        silhouette=None,
        use_transparency=False,
        below_color=None,
        above_color=None,
        annotations=None,
        pickable=True,
        preference='point',
        log_scale=False,
        pbr=None,
        metallic=None,
        roughness=None,
        render=True,
        user_matrix=None,
        component=None,
        emissive=None,
        copy_mesh=False,
        backface_params=None,
        show_vertices=None,
        edge_opacity=None,
        add_axes=True,
        add_bounding_box=False,
        show_grid= False,
        explode=False,
        explode_factor=0.1,
        sperate_beams_solid=False,
        opacity_beams=1.,
        opacity_solids=.5,
        tube_radius=0.05,
        show_cells_by_type = False,
        cells_to_show: Optional[List[int]] = None,
        **kwargs
    ) -> None:
        """
        Plot the assembled mesh using PyVista.

        This method visualizes the assembled mesh for the Assembler instance.
        It uses the PyVista plotting capabilities to render the mesh with
        all keyword arguments supported by `pyvista.Plotter.add_mesh` for customization.

        Parameters
        ----------
        color : str, sequence, or ColorLike, optional
            Solid color for the mesh. Accepts string, RGB list, or hex color string.
        style : str, optional
            Visualization style: 'surface', 'wireframe', 'points', or 'points_gaussian'.
        scalars : str or numpy.ndarray, optional
            Scalars used to color the mesh. String name or array.
        clim : sequence of float, optional
            Two-item color bar range for scalars. Example: [-1, 2].
        show_edges : bool, optional
            Show mesh edges. Not for wireframe style.
        edge_color : str, sequence, or ColorLike, optional
            Color for edges when show_edges=True.
        point_size : float, optional
            Size of points. Default is 5.0.
        line_width : float, optional
            Thickness of lines for wireframe/surface.
        opacity : float, str, or array_like, optional
            Opacity of the mesh. Float (0-1), string transfer function, or array.
        flip_scalars : bool, optional
            Flip direction of colormap.
        lighting : bool, optional
            Enable/disable view direction lighting.
        n_colors : int, optional
            Number of colors for scalars. Default is 256.
        interpolate_before_map : bool, optional
            Smoother scalars display. Default True.
        cmap : str, list, or LookupTable, optional
            Colormap for scalars. String name, list of colors, or LookupTable.
        label : str, optional
            Label for legend.
        reset_camera : bool, optional
            Reset camera after adding mesh.
        scalar_bar_args : dict, optional
            Arguments for scalar bar.
        show_scalar_bar : bool, optional
            Show/hide scalar bar.
        multi_colors : bool, str, cycler, or sequence, optional
            Color each block by a solid color for MultiBlock datasets.
        name : str, optional
            Name for the mesh/actor for updating.
        texture : pyvista.Texture or np.ndarray, optional
            Texture to apply if mesh has texture coordinates.
        render_points_as_spheres : bool, optional
            Render points as spheres.
        render_lines_as_tubes : bool, optional
            Show lines as tubes.
        smooth_shading : bool, optional
            Enable smooth shading (Phong algorithm).
        split_sharp_edges : bool, optional
            Split sharp edges >30 degrees for smooth shading.
        ambient : float, optional
            Ambient lighting coefficient (0-1).
        diffuse : float, optional
            Diffuse lighting coefficient. Default 1.0.
        specular : float, optional
            Specular lighting coefficient. Default 0.0.
        specular_power : float, optional
            Specular power (0.0-128.0).
        nan_color : str, sequence, or ColorLike, optional
            Color for NaN values in scalars.
        nan_opacity : float, optional
            Opacity for NaN values (0-1). Default 1.0.
        culling : str, optional
            Face culling: 'front' or 'back'.
        rgb : bool, optional
            Interpret scalars as RGB(A) colors.
        categories : bool, optional
            Use unique values in scalars as n_colors.
        silhouette : dict or bool, optional
            Plot silhouette highlight for mesh. Dict for properties.
        use_transparency : bool, optional
            Invert opacity mapping to transparency.
        below_color : str, sequence, or ColorLike, optional
            Color for values below scalars range.
        above_color : str, sequence, or ColorLike, optional
            Color for values above scalars range.
        annotations : dict, optional
            Annotations for scalar bar.
        pickable : bool, optional
            Set actor pickable.
        preference : str, optional
            Scalar mapping preference: 'point' or 'cell'.
        log_scale : bool, optional
            Use log scale for color mapping.
        pbr : bool, optional
            Enable physics-based rendering (PBR).
        metallic : float, optional
            Metallic value for PBR (0-1).
        roughness : float, optional
            Roughness for PBR (0-1).
        render : bool, optional
            Force render. Default True.
        user_matrix : np.ndarray or vtkMatrix4x4, optional
            Transformation matrix for actor.
        component : int, optional
            Component of vector-valued scalars to plot.
        emissive : bool, optional
            Treat points as emissive light sources (for 'points_gaussian').
        copy_mesh : bool, optional
            Copy mesh before adding. Default False.
        backface_params : dict or pyvista.Property, optional
            Backface rendering parameters.
        show_vertices : bool, optional
            Render external surface vertices. See vertex_* kwargs.
        edge_opacity : float, optional
            Edge opacity (0-1).
        explode : bool, optional
            Whether to explode blocks apart when style="explode".
        explode_factor : float, optional
            Factor to explode blocks apart when style="explode".
        sperate_beams_solid : bool, optional
            Whether to render beams and solids seperately. 
        opacity_beams : float, optional
            Opacity of beams when sperate_beams_solid=True.
        opacity_solids : float, optional
            Opacity of solids when sperate_beams_solid=True.
        **kwargs : dict, optional
            Additional keyword arguments for PyVista add_mesh.

        Raises
        ------
        ValueError
            If no assembled mesh exists to plot.
        """
        if self.AssembeledMesh is None:
            raise ValueError("No assembled mesh exists to plot")
        
        # remove the options that are not part of pyvista
        options = locals().copy()
        del options["self"]
        del options["show_cells_by_type"]
        del options["cells_to_show"]
        del options["tube_radius"]
        del options["kwargs"]
        del options["opacity_solids"]
        del options["opacity_beams"]
        del options["sperate_beams_solid"]
        del options["explode"]
        del options["explode_factor"]
        del options["add_axes"]
        del options["add_bounding_box"]
        del options["show_grid"]

        if show_cells_by_type:
            if cells_to_show is None:
                raise ValueError("cells_to_show must be provided when show_cells_by_type is True")
            mesh = self.AssembeledMesh.copy()
            mesh = pv.UnstructuredGrid(mesh)
            mesh = mesh.extract_cells_by_type(cells_to_show)
            pl = pv.Plotter()
            pl.add_mesh(mesh, **options)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            return
        
        # create a dict from all the inputs
        if sperate_beams_solid:
            mesh = self.AssembeledMesh.copy()
            mesh = pv.UnstructuredGrid(mesh)
            beams = mesh.extract_cells_by_type([pv.CellType.LINE, pv.CellType.POLY_LINE])
            mesh_solids = mesh.extract_cells_by_type([pv.CellType.TETRA, 
                                                      pv.CellType.HEXAHEDRON,
                                                      pv.CellType.QUAD, 
                                                      pv.CellType.WEDGE, 
                                                      pv.CellType.TRIANGLE, 
                                                      pv.CellType.VOXEL, 
                                                      pv.CellType.PIXEL])

            pl = pv.Plotter()
            del options["opacity"]
            if beams.n_cells > 0:
                op = options.copy()
                op["show_edges"] = False
                op["line_width"] = tube_radius
                pl.add_mesh(beams, **op, opacity=opacity_beams, )
                del op
            if mesh_solids.n_cells > 0:
                options["render_lines_as_tubes"] = False
                pl.add_mesh(mesh_solids, **options, opacity=opacity_solids)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            return

        
            
        if scalars=="Core":
            scalars = None
            Mesh = self.AssembeledMesh.copy()

            if explode:
                Mesh = Mesh.explode(factor=explode_factor)

            cores = Mesh.cell_data["Core"]
            mesh = pv.MultiBlock()
            for core in np.unique(cores):
                core_mesh = Mesh.extract_cells(cores==core)
                mesh.append(core_mesh)

            pl = pv.Plotter()
            pl.add_mesh(mesh,
                color=color,
                style=style,
                scalars=scalars,
                clim=clim,
                show_edges=show_edges,
                edge_color=edge_color,
                point_size=point_size,
                line_width=line_width,
                opacity=opacity,
                flip_scalars=flip_scalars,
                lighting=lighting,
                n_colors=n_colors,
                interpolate_before_map=interpolate_before_map,
                cmap=cmap,
                label=label,
                reset_camera=reset_camera,
                scalar_bar_args=scalar_bar_args,
                show_scalar_bar=show_scalar_bar,
                multi_colors=True,
                name=name,
                texture=texture,
                render_points_as_spheres=render_points_as_spheres,
                render_lines_as_tubes=render_lines_as_tubes,
                smooth_shading=smooth_shading,
                split_sharp_edges=split_sharp_edges,
                ambient=ambient,
                diffuse=diffuse,
                specular=specular,
                specular_power=specular_power,
                nan_color=nan_color,
                nan_opacity=nan_opacity,
                culling=culling,
                rgb=rgb,
                categories=categories,
                silhouette=silhouette,
                use_transparency=use_transparency,
                below_color=below_color,
                above_color=above_color,
                annotations=annotations,
                pickable=pickable,
                preference=preference,
                log_scale=log_scale,
                pbr=pbr,
                metallic=metallic,
                roughness=roughness,
                render=render,
                user_matrix=user_matrix,
                component=component,
                emissive=emissive,
                copy_mesh=copy_mesh,
                backface_params=backface_params,
                show_vertices=show_vertices,
                edge_opacity=edge_opacity,
                **kwargs)
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            pl.close()

        else:
            pl = pv.Plotter()
            mesh = self.AssembeledMesh.copy()
            if explode:
                mesh = mesh.explode(factor=explode_factor)

            pl.add_mesh(
                mesh,
                color=color,
                style=style,
                scalars=scalars,
                clim=clim,
                show_edges=show_edges,
                edge_color=edge_color,
                point_size=point_size,
                line_width=line_width,
                opacity=opacity,
                flip_scalars=flip_scalars,
                lighting=lighting,
                n_colors=n_colors,
                interpolate_before_map=interpolate_before_map,
                cmap=cmap,
                label=label,
                reset_camera=reset_camera,
                scalar_bar_args=scalar_bar_args,
                show_scalar_bar=show_scalar_bar,
                multi_colors=multi_colors,
                name=name,
                texture=texture,
                render_points_as_spheres=render_points_as_spheres,
                render_lines_as_tubes=render_lines_as_tubes,
                smooth_shading=smooth_shading,
                split_sharp_edges=split_sharp_edges,
                ambient=ambient,
                diffuse=diffuse,
                specular=specular,
                specular_power=specular_power,
                nan_color=nan_color,
                nan_opacity=nan_opacity,
                culling=culling,
                rgb=rgb,
                categories=categories,
                silhouette=silhouette,
                use_transparency=use_transparency,
                below_color=below_color,
                above_color=above_color,
                annotations=annotations,
                pickable=pickable,
                preference=preference,
                log_scale=log_scale,
                pbr=pbr,
                metallic=metallic,
                roughness=roughness,
                render=render,
                user_matrix=user_matrix,
                component=component,
                emissive=emissive,
                copy_mesh=copy_mesh,
                backface_params=backface_params,
                show_vertices=show_vertices,
                edge_opacity=edge_opacity,
                **kwargs
            )
            if add_axes:
                pl.add_axes()
            if add_bounding_box:
                pl.add_bounding_box()
            if show_grid:
                pl.show_grid()
            pl.show()
            pl.close()
    

    def get_mesh(self) -> Optional[pv.UnstructuredGrid]:
        """
        Get the assembled mesh.
        
        Returns the currently assembled mesh as a PyVista UnstructuredGrid.
        If no mesh has been assembled yet, returns None.
        
        Returns:
            Optional[pv.UnstructuredGrid]: The assembled mesh, or None if not yet created
        """
        return self.AssembeledMesh.copy() 


    # Big announcement box
    def _announce_required_cores(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        # this part should be gou through the Assembled Mesh and see how many cores are used to print
        # the number of cores used in the assembly
        if self.AssembeledMesh is None:
            logging.warning("No assembled mesh found. Cannot announce required cores.")
            return
        cores = self.AssembeledMesh.cell_data["Core"]
        unique_cores = np.unique(cores) 
        cores = len(unique_cores)
        RED = "\033[91m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        BLUE = "\033[94m"
        message = f"{BOLD}{BLUE}!!! IMPORTANT RESOURCE NOTICE !!!{RESET}\n" \
                f"{BOLD}This model requires {RED}{cores}{RESET}{BOLD} CPU cores to run effectively.{RESET}\n" \
                f"Please ensure your environment has sufficient resources.\n"

        border = "=" * 70
        full_message = f"\n{BLUE}{border}\n{message}{BLUE}{border}{RESET}\n"

        

        print(full_message)
        
            

class AssemblySection:
    """
    A class representing a group of mesh parts combined into a single mesh.
    
    The AssemblySection class takes multiple mesh parts, combines them into a single
    mesh, and optionally partitions the mesh for parallel computing. Each assembly 
    section is automatically registered with the Assembler singleton and assigned
    a unique tag for identification.
    
    This class is responsible for:
    - Validating mesh parts before assembly
    - Merging mesh parts with appropriate metadata
    - Managing degrees of freedom consistency
    - Partitioning the mesh for parallel processing
    - Storing references to elements and materials
    
    Attributes:
        meshparts_list (List[MeshPart]): List of MeshPart objects in this section
        num_partitions (int): Number of partitions for parallel processing
        partition_algorithm (str): Algorithm used for partitioning the mesh
        merging_points (bool): Whether points are merged during assembly
        mesh (pyvista.UnstructuredGrid): The assembled mesh
        elements (List[Element]): Elements used in this assembly section
        materials (List[Material]): Materials used in this assembly section
        actor: PyVista actor for visualization
        _tag (int): Unique tag assigned by the Assembler
    """
    def __init__(
        self, 
        meshparts: List[str], 
        num_partitions: int = 1, 
        partition_algorithm: str = "kd-tree", 
        merging_points: bool = True,
        progress_callback=None,
        mass_merging: str = "sum",
        tolerance: float = 1e-5,
    ):
        """
        Initialize an AssemblySection by combining multiple mesh parts.
        
        This constructor takes a list of mesh part names, validates them, combines them
        into a single mesh, and optionally partitions the result. The assembled section
        is automatically registered with the Assembler singleton.
        
        If the partition algorithm is "kd-tree" and num_partitions is not a power of 2,
        it will be automatically rounded up to the next power of 2.

        Args:
            meshparts (List[str]): List of mesh part names to be assembled. These must be
                                  names of previously created MeshPart instances.
            num_partitions (int, optional): Number of partitions for parallel processing.
                                          For kd-tree, will be rounded to next power of 2.
                                          Defaults to 1 (no partitioning).
            partition_algorithm (str, optional): Algorithm used for partitioning the mesh.
                                               Currently supports "kd-tree".
                                               Defaults to "kd-tree".
            mass_merging (str, optional): Method for merging mass properties of mesh parts.
                                          Options are "sum" or "average". Defaults to "sum".
            merging_points (bool, optional): Whether to merge points that are within a
                                           tolerance distance when assembling mesh parts.
                                           Defaults to True.
                                           
        
        Raises:
            ValueError: If no valid mesh parts are provided, if the partition algorithm
                      is invalid, or if mesh assembly fails
        """
        # Validate and collect mesh parts
        self.meshparts_list = self._validate_mesh_parts(meshparts)
        
        # Configuration parameters
        self.num_partitions = num_partitions
        self.partition_algorithm = partition_algorithm
        # check if the partition algorithm is valid
        if self.partition_algorithm not in ["kd-tree"]:
            raise ValueError(f"Invalid partition algorithm: {self.partition_algorithm}")

        if self.partition_algorithm == "kd-tree" :
            # If a non-power of two value is specified for 
            # n_partitions, then the load balancing simply 
            # uses the power-of-two greater than the requested value
            if self.num_partitions & (self.num_partitions - 1) != 0:
                self.num_partitions = 2**self.num_partitions.bit_length()

        # Initialize tag to None
        self._tag = None
        self.merging_points = merging_points
        if mass_merging not in ["sum", "average"]:
            raise ValueError(f"Invalid mass merging method: {mass_merging}. Must be 'sum' or 'average'.")
        self.mass_merging = mass_merging
        
        # Assembled mesh attributes
        self.mesh: Optional[pv.UnstructuredGrid] = None
        self.elements : List[Element] = []
        self.materials : List[Material] = []
        self.tolerance = tolerance

        # Assemble the mesh first
        try:
            self._assemble_mesh(progress_callback=progress_callback)
            # Only add to Assembler if mesh assembly is successful
            self._tag = Assembler.get_instance()._add_assembly_section(self)
        except Exception as e:
            # If mesh assembly fails, raise the original exception
            raise

        self.actor = None

    @property
    def tag(self) -> int:
        """
        Get the unique tag for this AssemblySection.
        
        The tag is a unique identifier assigned by the Assembler when the 
        AssemblySection is successfully created and registered. It can be
        used to retrieve the section from the Assembler later.
        
        Returns:
            int: Unique tag assigned by the Assembler
        
        Raises:
            ValueError: If the section hasn't been successfully added to the Assembler
        """
        if self._tag is None:
            raise ValueError("AssemblySection has not been successfully created")
        return self._tag
    
    def _validate_mesh_parts(self, meshpart_names: List[str]) -> List[MeshPart]:
        """
        Validate and retrieve mesh parts.
        
        This internal method checks that all specified mesh part names exist 
        in the MeshPart registry and retrieves the corresponding MeshPart objects.
        It also verifies that at least one valid mesh part is provided.

        Args:
            meshpart_names (List[str]): List of mesh part names to validate

        Returns:
            List[MeshPart]: List of validated MeshPart objects

        Raises:
            ValueError: If any specified mesh part doesn't exist or if no valid mesh parts are found
        """
        validated_meshparts = []
        for name in meshpart_names:
            meshpart = MeshPart._mesh_parts.get(name)
            if meshpart is None:
                raise ValueError(f"Mesh with name '{name}' does not exist")
            validated_meshparts.append(meshpart)
        
        if not validated_meshparts:
            raise ValueError("No valid mesh parts were provided")
        
        return validated_meshparts
    
    def _validate_degrees_of_freedom(self) -> bool:
        """
        Check if all mesh parts have the same number of degrees of freedom.
        
        This internal method verifies that all mesh parts in the section have
        consistent degrees of freedom, which is important for proper mesh assembly
        when merging points. If merging_points is False, this check is skipped.
        
        If inconsistent degrees of freedom are detected, a warning is issued but
        the method returns False rather than raising an exception.

        Returns:
            bool: True if all mesh parts have the same number of degrees of freedom,
                 or if merging_points is False. False if inconsistencies are detected.
        """
        if not self.merging_points:
            return True
        
        ndof_list = [meshpart.element._ndof for meshpart in self.meshparts_list]
        unique_ndof = set(ndof_list)
        
        if len(unique_ndof) > 1:
            warnings.warn("Mesh parts have different numbers of degrees of freedom", UserWarning)
            return False
        
        return True

    @staticmethod
    def _snap_points(points, tol=1e-6):
        """
        Snap points within tolerance to the first representative point
        using KDTree.
        """
        tree = KDTree(points)
        groups = tree.query_ball_tree(tree, tol)

        visited = np.zeros(len(points), dtype=bool)
        snapped = points.copy()

        for i in range(len(points)):
            if visited[i]:
                continue
            cluster = groups[i]
            rep = points[i]  # pick the first point
            for j in cluster:
                snapped[j] = rep
                visited[j] = True

        return snapped
    
    def _assemble_mesh(self, progress_callback=None):
        """
        Assemble mesh parts into a single mesh.
        
        This internal method performs the actual assembly of mesh parts into a single
        PyVista UnstructuredGrid. It:
        1. Validates degrees of freedom consistency
        2. Starts with the first mesh part as the base
        3. Adds metadata to the mesh (ElementTag, MaterialTag, Region, etc.)
        4. Merges subsequent mesh parts one by one
        5. Optionally partitions the resulting mesh for parallel processing
        
        The assembled mesh is stored in the 'mesh' attribute, with cell data arrays
        for ElementTag, MaterialTag, Region, and Core (partition ID).

        Raises:
            ValueError: If mesh parts have different degrees of freedom and this causes
                      assembly to fail, or if any other error occurs during assembly
        """
        if progress_callback is None:
            def progress_callback(v, msg=""):
                Progress.callback(v, msg, desc=f"Assembly Section: {len(Assembler._assembly_sections) + 1}")

        # Validate degrees of freedom
        self._validate_degrees_of_freedom()
            
        # Start with the first mesh
        first_meshpart = self.meshparts_list[0]
        first_mesh = first_meshpart.mesh.copy()
        
        # Collect elements and materials
        ndf = first_meshpart.element._ndof
        matTag = first_meshpart.element.get_material_tag()
        EleTag = first_meshpart.element.tag
        regionTag = first_meshpart.region.tag
        sectionTag = first_meshpart.element.get_section_tag()
        meshTag  = first_meshpart.tag
        
        # Add initial metadata to the first mesh
        n_cells = first_mesh.n_cells
        n_points = first_mesh.n_points

        # ensure Mass array exists
        if "Mass" not in first_mesh.point_data:
            first_mesh.point_data["Mass"] = np.zeros((n_points, FEMORA_MAX_NDF), dtype=np.float32)

        # add cell and point data
        first_mesh.cell_data["ElementTag"]  = np.full(n_cells, EleTag, dtype=np.uint16)
        first_mesh.cell_data["MaterialTag"] = np.full(n_cells, matTag, dtype=np.uint16)
        first_mesh.cell_data["SectionTag"]  = np.full(n_cells, sectionTag, dtype=np.uint16)
        first_mesh.point_data["ndf"]        = np.full(n_points, ndf, dtype=np.uint16)
        first_mesh.cell_data["Region"]      = np.full(n_cells, regionTag, dtype=np.uint16)
        first_mesh.cell_data["MeshPartTag_celldata"]   = np.full(n_cells, meshTag, dtype=np.uint16)
        first_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points, meshTag, dtype=np.uint16)
        # Merge subsequent meshes
        n_sections = len(self.meshparts_list)
        perc = 1 / n_sections * 100
        progress_callback(perc, f"merged meshpart {1}/{n_sections}")
        self.mesh = pv.MultiBlock([first_mesh])  # Start with the first mesh as a MultiBlock
        for idx, meshpart in enumerate(self.meshparts_list[1:], start=2):
            second_mesh = meshpart.mesh.copy()
            ndf = meshpart.element._ndof
            matTag = meshpart.element.get_material_tag()
            EleTag = meshpart.element.tag
            regionTag = meshpart.region.tag
            sectionTag = meshpart.element.get_section_tag()
            meshTag  = meshpart.tag
            n_cells_second  = second_mesh.n_cells
            n_points_second = second_mesh.n_points
            if "Mass" not in second_mesh.point_data:
                second_mesh.point_data["Mass"] = np.zeros((n_points_second, FEMORA_MAX_NDF), dtype=np.float32)
            # add cell and point data to the second mesh
            second_mesh.cell_data["ElementTag"]  = np.full(n_cells_second, EleTag, dtype=np.uint16)
            second_mesh.cell_data["MaterialTag"] = np.full(n_cells_second, matTag, dtype=np.uint16)
            second_mesh.point_data["ndf"]        = np.full(n_points_second, ndf, dtype=np.uint16)
            second_mesh.cell_data["Region"]      = np.full(n_cells_second, regionTag, dtype=np.uint16)
            second_mesh.cell_data["SectionTag"]  = np.full(n_cells_second, sectionTag, dtype=np.uint16)
            second_mesh.cell_data["MeshPartTag_celldata"]   = np.full(n_cells_second, meshTag, dtype=np.uint16)
            second_mesh.point_data["MeshPartTag_pointdata"] = np.full(n_points_second, meshTag, dtype=np.uint16)
            # Merge with tolerance and optional point merging
            self.mesh.append(second_mesh)
            perc = idx / n_sections * 100
            progress_callback(perc, f"merged meshpart {idx}/{n_sections}")

        
        self.mesh = self.mesh.combine(
            merge_points = False,
            tolerance = 1e-5,
        )
        if self.merging_points:
            mass = self.mesh.point_data["Mass"]
            number_of_points_before_cleaning = self.mesh.number_of_points

            # fist we snap points within tolerance to the first representative point
            points = self._snap_points(self.mesh.points, tol=self.tolerance)
            self.mesh.points = points

            self.mesh = self.mesh.clean(
                tolerance=self.tolerance,
                remove_unused_points=False,
                produce_merge_map=True,
                average_point_data=True,
                merging_array_name="ndf",
                progress_bar=False,
            )

            number_of_points_after_cleaning = self.mesh.number_of_points
            # make the ndf array uint16
            self.mesh.point_data["ndf"] = self.mesh.point_data["ndf"].astype(np.uint16)
            # make the MeshPartTag_pointdata array uint16
            self.mesh.point_data["MeshPartTag_pointdata"] = self.mesh.point_data["MeshPartTag_pointdata"].astype(np.uint16)

            if self.mass_merging == "sum":
                if number_of_points_before_cleaning != number_of_points_after_cleaning:
                    Mass = np.zeros((self.mesh.number_of_points, FEMORA_MAX_NDF), dtype=np.float32)
                    for i in range(self.mesh.field_data["PointMergeMap"].shape[0]):
                        Mass[self.mesh.field_data["PointMergeMap"][i],:] += mass[i,:]
            
                    self.mesh.point_data["Mass"] = Mass

            del self.mesh.field_data["PointMergeMap"]


        # partition the mesh
        self.mesh.cell_data["Core"] = np.zeros(self.mesh.n_cells, dtype=int)
        if self.num_partitions > 1:
            partitiones = self.mesh.partition(self.num_partitions,
                                              generate_global_id=True, 
                                              as_composite=True)
            for i, partition in enumerate(partitiones):
                ids = partition.cell_data["vtkGlobalCellIds"]
                self.mesh.cell_data["Core"][ids] = i
            
            del partitiones

    @property
    def meshparts(self) -> List[str]:
        """
        Get the names of mesh parts in this AssemblySection.
        
        This property returns a list of the user-friendly names of all mesh parts
        included in this assembly section. These are the names that were originally
        provided when creating the mesh parts.
        
        Returns:
            List[str]: Names of mesh parts included in this assembly section
        """
        return [meshpart.user_name for meshpart in self.meshparts_list]
    
    def assign_actor(self, actor) -> None:
        """
        Assign a PyVista actor to the assembly section.
        
        This method associates a visualization actor with the assembly section,
        which can be used for rendering the mesh in a visualization pipeline.
        
        Args:
            actor: PyVista actor to assign to this assembly section for visualization
        """
        self.actor = actor

    def plot(self,**kwargs) -> None:

        """
        Plot the assembled mesh using PyVista.
        
        This method visualizes the assembled mesh for the assembly section.
        It uses the PyVista plotting capabilities to render the mesh with
        optional parameters for customization.

        Args:
            **kwargs: Additional keyword arguments to customize the plot (e.g., color, opacity)
        
        """
        if self.mesh is None:
            raise ValueError("Mesh has not been assembled yet")
        else:
            self.mesh.plot(**kwargs)
        
        













