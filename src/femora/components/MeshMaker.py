class MeshMaker:
    """Manages the creation, assembly, and export of a Femora finite element model.

    This singleton class provides a centralized interface for defining a structural
    model, including materials, elements, constraints, and other components,
    and then assembling and exporting it to formats like OpenSees TCL or VTK.

    Attributes:
        model (femora.Model or None): The internal representation of the structural
            model after assembly.
        model_name (str or None): The name of the model, used for file naming.
        model_path (str or None): The directory path where model files are saved.
        assembler (Assembler): Manages the assembly of mesh parts into a complete model.
        material (MaterialManager): Manages material properties defined in the model.
        element (ElementRegistry): Manages element definitions and their properties.
        damping (DampingManager): Manages damping properties for the model.
        mass (MassManager): Manages mass properties for nodes and elements.
        region (RegionManager): Manages spatial regions within the model.
        constraint (Constraint): Manages boundary conditions and multi-point constraints.
        meshPart (MeshPartManager): Manages individual mesh components before assembly.
        timeSeries (TimeSeriesManager): Manages time series data for dynamic analyses.
        analysis (AnalysisManager): Manages analysis configurations and procedures.
        pattern (PatternManager): Manages load patterns applied to the model.
        recorder (RecorderManager): Manages data recorders for simulation output.
        process (ProcessManager): Manages various processing steps for model setup.
        interface (InterfaceManager): Manages various interfaces and connections.
        transformation (GeometricTransformationManager): Manages geometric
            transformations applied to elements.
        section (SectionManager): Manages section properties for beam and shell elements.
        spatial_transform (SpatialTransformManager): Manages spatial transformations
            for various model components.
        _start_nodetag (int): The starting integer tag for nodes when exporting to TCL.
        _start_ele_tag (int): The starting integer tag for elements when exporting to TCL.
        _start_core_tag (int): The starting integer tag for cores when exporting to TCL.
        drm (DRM): Manages Distributed Response Model (DRM) functionality.

    Example:
        >>> import femora as fm
        >>> mesh_maker = fm.MeshMaker.get_instance(model_name="my_model", model_path=".")
        >>> # Now you can use mesh_maker to define your model
        >>> print(mesh_maker.model_name)
        my_model
    """
    _instance = None
    _results_folder = ""

    def __new__(cls, *args, **kwargs):
        """Creates a new instance of MeshMaker if it doesn't exist.

        This method ensures that only one instance of MeshMaker is ever created,
        implementing the singleton pattern.

        Returns:
            MeshMaker: The singleton instance of the MeshMaker.
        """
        if cls._instance is None:
            cls._instance = super(MeshMaker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, **kwargs):
        """Initializes the MeshMaker instance.

        Args:
            **kwargs: Keyword arguments for initialization, including:
                model_name: The name of the model.
                model_path: The path to save the model files.
        """
        # Only initialize once
        if self._initialized:
            return
            
        self._initialized = True
        self.model = None
        self.model_name = kwargs.get('model_name')
        self.model_path = kwargs.get('model_path')
        self.assembler = Assembler()
        self.material = MaterialManager()
        self.element = ElementRegistry()
        self.damping = DampingManager()
        self.mass = MassManager()
        self.region = RegionManager()
        self.constraint = Constraint()
        self.meshPart = MeshPartManager()
        self.timeSeries = TimeSeriesManager()
        self.analysis = AnalysisManager()
        self.pattern = PatternManager()
        self.recorder = RecorderManager()
        self.process = ProcessManager()
        self.interface = InterfaceManager()
        self.transformation = GeometricTransformationManager()
        self.section = SectionManager()
        self.spatial_transform = SpatialTransformManager()
        
        # Tag start controls for node and element IDs written to TCL
        # These control only exported OpenSees node/element tags (not Material/Element class tags)
        self._start_nodetag: int = 1
        self._start_ele_tag: int = 1
        self._start_core_tag: int = 0
        
        @property
        def mesh_part(self):
            """Provides access to the MeshPartManager instance.

            Returns:
                MeshPartManager: The manager for mesh parts.

            Example:
                >>> import femora as fm
                >>> mesh_maker = fm.MeshMaker.get_instance()
                >>> mesh_part_manager = mesh_maker.mesh_part
                >>> print(isinstance(mesh_part_manager, fm.MeshPartManager))
                True
            """
            return self.meshPart
        
        

        
        # Initialize DRMHelper with a reference to this MeshMaker instance
        self.drm = DRM()
        self.drm.set_meshmaker(self)
        
    # ------------------------------------------------------------------
    # Progress helpers
    # ------------------------------------------------------------------

    def set_nodetag_start(self, start_tag: int) -> None:
        """Sets the starting tag number for nodes in exported TCL files.

        Args:
            start_tag: The first node tag to use. Must be an integer greater than or equal to 1.

        Raises:
            ValueError: If `start_tag` is not an integer or is less than 1.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_nodetag_start(100)
            >>> print(mesh_maker.get_start_node_tag())
            100
        """
        if not isinstance(start_tag, int) or start_tag < 1:
            raise ValueError("Node tag start must be an integer >= 1")
        self._start_nodetag = start_tag

    def set_eletag_start(self, start_tag: int) -> None:
        """Sets the starting tag number for elements in exported TCL files.

        Args:
            start_tag: The first element tag to use. Must be an integer greater than or equal to 1.

        Raises:
            ValueError: If `start_tag` is not an integer or is less than 1.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_eletag_start(200)
            >>> print(mesh_maker.get_start_ele_tag())
            200
        """
        if not isinstance(start_tag, int) or start_tag < 1:
            raise ValueError("Element tag start must be an integer >= 1")
        self._start_ele_tag = start_tag

    def set_start_core_tag(self, start_tag: int) -> None:
        """Sets the starting tag number for cores in exported TCL files.

        Args:
            start_tag: The first core tag to use. Must be an integer greater than or equal to 0.

        Raises:
            ValueError: If `start_tag` is not an integer or is less than 0.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_start_core_tag(0)
            >>> print(mesh_maker._start_core_tag)
            0
        """
        if not isinstance(start_tag, int) or start_tag < 0:
            raise ValueError("Core tag start must be an integer >= 0")
        self._start_core_tag = start_tag

    def _progress_callback(self, value: float, message: str):
        """Reports progress using the shared Progress utility.

        Args:
            value: The current progress value, typically between 0.0 and 1.0.
            message: A descriptive message about the current progress step.
        """
        Progress.callback(value, message, desc="Exporting to TCL")

    def _get_tcl_helper_functions(self) -> str:
        """Returns TCL helper functions as a string.
        
        This method contains all the TCL helper functions needed for the exported model.
        Embedding them directly in the code ensures they're always available and makes
        the package more professional and self-contained.
        
        Returns:
            str: A string containing TCL helper function definitions.
        """
        return '''proc getFemoraMax {type} {
	set local_max -1.e8
	if {$type == "eleTag"} {
		set Tags [getEleTags]
	} elseif {$type == "nodeTag"} {
		set Tags [getNodeTags]
	} else {
		puts "Unknown type $type"
		return -1
	}
	# set Tags [getNodeTags]
	foreach tag $Tags {
		if {$tag > $local_max} {
			set local_max $tag
		}
	}
	# send the max ele tag form each pid to the master
	if {$::pid == 0} {
		for {set i 1 } {$i < $::np} {incr i 1} { 
			recv -pid $i ANY maxTag
			if {$maxTag > $local_max} {
				set local_max $maxTag
			}
		}
	} else {
		send -pid 0 "$local_max"
	}

	# now send the max ele tag to all pids
	if {$::pid == 0} {
		for {set i 1 } {$i < $::np} {incr i 1} { 
			send -pid $i $local_max
		}
		set global_max $local_max
	} else {
		recv -pid 0 ANY global_max
	}
	return $global_max
}

'''

    def _get_tcl_file_header(self, required_np: int) -> str:
        """Generates the header string for an exported TCL file.

        Args:
            required_np: The number of MPI processes required for the model.

        Returns:
            str: The formatted header string for the TCL file.
        """
        header = f"""
#   ╔══════════════════════════════════════════════════════════╗
#   ║                                                          ║
#   ║   ███████╗███████╗███╗   ███╗ ██████╗ ██████╗  █████╗    ║
#   ║   ██╔════╝██╔════╝████╗ ████║██╔═══██╗██╔══██╗██╔══██╗   ║
#   ║   █████╗  █████╗  ██╔████╔██║██║   ██║██████╔╝███████║   ║
#   ║   ██╔══╝  ██╔══╝  ██║╚██╔╝██║██║   ██║██╔══██╗██╔══██║   ║
#   ║   ██║     ███████╗██║ ╚═╝ ██║╚██████╔╝██║  ██║██║  ██║   ║
#   ║   ╚═╝     ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ║
#   ║══════════════════════════════════════════════════════════║
#   ║            Soil-Structure Interaction Analysis           ║
#   ║             Femora Tcl Export                            ║
#   ║             Developers: Amin Pakzad, Pedro Arduino       ║
#   ║             License: MIT                                 ║
#   ║             Required MPI processes: {required_np:<17}    ║
#   ║══════════════════════════════════════════════════════════║
#   ╚══════════════════════════════════════════════════════════╝
"""
        return header

    @classmethod
    def get_instance(cls, **kwargs) -> "MeshMaker":
        """Gets the singleton instance of MeshMaker.
        
        If an instance does not already exist, it is created and initialized
        with the provided keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass to the MeshMaker constructor
                if a new instance needs to be created.

        Returns:
            MeshMaker: The singleton instance of MeshMaker.

        Example:
            >>> import femora as fm
            >>> mesh_maker1 = fm.MeshMaker.get_instance(model_name="project1")
            >>> mesh_maker2 = fm.MeshMaker.get_instance(model_name="project2")
            >>> # mesh_maker1 and mesh_maker2 are the same instance
            >>> print(mesh_maker1 is mesh_maker2)
            True
            >>> print(mesh_maker1.model_name)
            project1
        """
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    

    def gui(self):
        """Launches the Femora GUI application.
        
        This method creates and shows the main GUI window for interacting with
        the MeshMaker instance, providing a visual interface for model definition
        and analysis.

        Returns:
            MainWindow or None: The main window instance if successful,
                otherwise None if GUI components cannot be loaded.

        Raises:
            ImportError: If required GUI dependencies (e.g., qtpy, pyvista)
                are not installed.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> # main_window = mesh_maker.gui() # Uncomment to launch the GUI
            >>> # The GUI will open in a separate window.
        """
        try:
            # Import required modules
            from qtpy.QtWidgets import QApplication
            from femora.gui.main_window import MainWindow
            
            # Ensure a QApplication instance exists
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
                
            # Initialize and show the main window
            main_window = MainWindow()
            
            # Only start event loop if not already running
            if not app.startingUp():
                app.exec_()
                
            return main_window
        except ImportError as e:
            print(f"Error: Unable to load GUI components. {str(e)}")
            print("Please ensure qtpy, pyvista, and other GUI dependencies are installed.")
            return None

    def export_to_tcl(self, filename: str = None, progress_callback=None) -> bool:
        """Exports the assembled Femora model to an OpenSees TCL input file.
        
        This method generates a TCL script that can be executed by OpenSees
        to reconstruct and run the defined structural model. It includes
        materials, elements, nodes, constraints, time series, and other
        model components.

        Args:
            filename: The full path and name of the TCL file to export to.
                If None, uses `model_name` within `model_path`.
            progress_callback: A callable function to report export progress.
                It should accept `(value: float, message: str)`. If None,
                a default `tqdm`-based progress bar is used.

        Returns:
            True: If the export process was successful.

        Raises:
            ValueError: If no `filename` is provided and `model_name` or
                `model_path` are not set in the MeshMaker instance.
            ValueError: If no assembled mesh is found.

        Example:
            >>> import femora as fm
            >>> import os
            >>> # Assuming a model is already defined and assembled
            >>> mesh_maker = fm.MeshMaker.get_instance(model_name="my_tcl_model", model_path=".")
            >>> # Example: Create a dummy mesh for demonstration
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>> success = mesh_maker.export_to_tcl(filename="my_model.tcl")
            >>> print(f"TCL export successful: {success}")
            TCL export successful: True
            >>> os.remove("my_model.tcl") # Clean up
        """
        # Use the default tqdm progress callback if none is provided
        if progress_callback is None:
            progress_callback = self._progress_callback
            
        if True: # This 'if True' is redundant, but leaving logic unchanged as per Rule 1.
            # Determine the full file path
            if filename is None:
                if self.model_name is None or self.model_path is None:
                    raise ValueError("Either provide a filename or set model_name and model_path")
                filename = os.path.join(self.model_path, f"{self.model_name}.tcl")
            
            # chek if the end is not .tcl then add it
            if not filename.endswith('.tcl'):
                filename += '.tcl'
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Get the assembled content
            if self.assembler.AssembeledMesh is None:
                print("No mesh found")
                raise ValueError("No mesh found\n Please assemble the mesh first")
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:

                # Determine required MPI process count for this model export
                required_np = 1
                try:
                    core_ids = np.asarray(self.assembler.AssembeledMesh.cell_data["Core"])
                    if core_ids.size:
                        required_np = int(np.max(np.unique(core_ids))) + 1
                except Exception:
                    required_np = 1

                # Write a banner/header at the very beginning of the file
                f.write(self._get_tcl_file_header(required_np))

                # Inform interfaces that we are about to export
                EventBus.emit(FemoraEvent.PRE_EXPORT, file_handle=f, assembled_mesh=self.assembler.AssembeledMesh)

                f.write("wipe\n")
                f.write("set pid [getPID]\n")
                f.write("set np [getNP]\n")

                # Validate MPI process count early
                f.write(f"set FEMORA_REQUIRED_NP {required_np}\n")
                f.write("if {$np != $FEMORA_REQUIRED_NP} {\n")
                f.write("\tif {$pid == 0} {\n")
                f.write("\t\tputs \"ERROR: This model requires $FEMORA_REQUIRED_NP MPI processes, but OpenSees is running with $np.\"\n")
                f.write("\t\tputs \"Please re-run with: mpiexec/mpirun -np $FEMORA_REQUIRED_NP OpenSeesMP <script.tcl>\"\n")
                f.write("\t}\n")
                f.write("\texit 2\n")
                f.write("}\n")
                f.write("model BasicBuilder -ndm 3\n")

                if self._results_folder != "":
                    f.write("if {$pid == 0} {" + f"file mkdir {self._results_folder}" + "} \n")

                f.write("\n# Helper functions ======================================\n")
                f.write(self._get_tcl_helper_functions())

                # Write the meshBounds
                f.write("\n# Mesh Bounds ======================================\n")
                bounds = self.assembler.AssembeledMesh.bounds
                f.write(f"set X_MIN {bounds[0]}\n")
                f.write(f"set X_MAX {bounds[1]}\n")
                f.write(f"set Y_MIN {bounds[2]}\n")
                f.write(f"set Y_MAX {bounds[3]}\n")
                f.write(f"set Z_MIN {bounds[4]}\n")
                f.write(f"set Z_MAX {bounds[5]}\n")

                if progress_callback:
                    progress_callback(0, "writing materials")
                    

                # Write the materials
                f.write("\n# Materials ======================================\n")
                for tag,mat in self.material.get_all_materials().items():
                    f.write(f"{mat.to_tcl()}\n")

                # write the transformations
                f.write("\n# Transformations ======================================\n")
                for transf in self.transformation.get_all_transformations():
                    f.write(f"{transf.to_tcl()}\n")

                # Write the sections
                f.write("\n# Sections ======================================\n")
                for tag,section in self.section.get_all_sections().items():
                    f.write(f"{section.to_tcl()}\n")

                if progress_callback:
                    progress_callback(5,"writing nodes and elements")

                # Write the nodes
                f.write("\n# Nodes & Elements ======================================\n")
                cores = self.assembler.AssembeledMesh.cell_data["Core"]
                num_cores = unique(cores)
                nodes     = self.assembler.AssembeledMesh.points
                ndfs      = self.assembler.AssembeledMesh.point_data["ndf"]
                mass      = self.assembler.AssembeledMesh.point_data["Mass"]
                num_nodes = self.assembler.AssembeledMesh.n_points
                wroted    = zeros((num_nodes, len(num_cores)), dtype=bool) # to keep track of the nodes that have been written
                nodeTags  = arange(self._start_nodetag,
                                   self._start_nodetag + num_nodes,
                                   dtype=int)
                eleTags   = arange(self._start_ele_tag,
                                   self._start_ele_tag + self.assembler.AssembeledMesh.n_cells,
                                   dtype=int)


                elementClassTag = self.assembler.AssembeledMesh.cell_data["ElementTag"]


                for i in range(self.assembler.AssembeledMesh.n_cells):
                    cell = self.assembler.AssembeledMesh.get_cell(i)
                    pids = cell.point_ids
                    core = cores[i]
                    f.write("if {$pid ==" + str(core) + "} {\n")
                    # writing nodes
                    for pid in pids:
                        if not wroted[pid][core]:
                            f.write(f"\tnode {nodeTags[pid]} {nodes[pid][0]} {nodes[pid][1]} {nodes[pid][2]} -ndf {ndfs[pid]}\n")
                            mass_vec = mass[pid]
                            mass_vec = mass_vec[:ndfs[pid]] 
                            # if any of the mass vector is not zero then write it
                            if abs(mass_vec).sum() > 1e-6:
                                f.write(f"\tmass {nodeTags[pid]} {' '.join(map(str, mass_vec))}\n")
                            # write them mass for that node
                            wroted[pid][core] = True
                    
                    eleclass = Element._elements[elementClassTag[i]]
                    nodeTag = [nodeTags[pid] for pid in pids]
                    eleTag = eleTags[i]
                    f.write("\t"+eleclass.to_tcl(eleTag, nodeTag) + "\n")
                    f.write("}\n")     
                    if progress_callback:
                        progress_callback((i / self.assembler.AssembeledMesh.n_cells) * 45 + 5, "writing nodes and elements")

                # notify EmbbededBeamSolidInterface event
                EventBus.emit(FemoraEvent.INTERFACE_ELEMENTS_TCL, file_handle=f)             
                EventBus.emit(FemoraEvent.EMBEDDED_BEAM_SOLID_TCL, file_handle=f)             
                
                
                if progress_callback:
                    progress_callback(50, "writing dampings")
                # writ the dampings 
                f.write("\n# Dampings ======================================\n")
                if self.damping.get_all_dampings() is not None:
                    for tag,damp in self.damping.get_all_dampings().items():
                        f.write(f"{damp.to_tcl()}\n")
                else:
                    f.write("# No dampings found\n")

                if progress_callback:
                    progress_callback(55, "writing regions")

                # write regions
                f.write("\n# Regions ======================================\n")
                Regions = unique(self.assembler.AssembeledMesh.cell_data["Region"])
                for i,regionTag in enumerate(Regions):
                    region = self.region.get_region(regionTag)
                    if region.get_type().lower() == "noderegion":
                        raise ValueError(f"""Region {regionTag} is of type NodeTRegion which is not supported in yet""")
                    
                    region.setComponent("element", eleTags[self.assembler.AssembeledMesh.cell_data["Region"] == regionTag])
                    f.write(f"{region.to_tcl()} \n")
                    del region
                    if progress_callback:
                        progress_callback((i / Regions.shape[0]) * 10 + 55, "writing regions")

                if progress_callback:
                    progress_callback(65, "writing constraints")


                # Write mp constraints
                f.write("\n# mpConstraints ======================================\n")

                # Precompute mappings
                core_to_idx = {core: idx for idx, core in enumerate(num_cores)}
                master_nodes = zeros(num_nodes, dtype=bool)
                slave_nodes = zeros(num_nodes, dtype=bool)
                
                # Modified data structures to handle multiple constraints per node
                constraint_map = {}  # map master node to list of constraints
                constraint_map_rev = {}  # map slave node to list of (master_id, constraint) tuples
                
                for constraint in self.constraint.mp:
                    master_id = constraint.master_node - 1
                    master_nodes[master_id] = True
                    
                    # Add constraint to master's list
                    if master_id not in constraint_map:
                        constraint_map[master_id] = []
                    constraint_map[master_id].append(constraint)
                    
                    # For each slave, record the master and constraint
                    for slave_id in constraint.slave_nodes:
                        slave_id = slave_id - 1
                        slave_nodes[slave_id] = True
                        
                        if slave_id not in constraint_map_rev:
                            constraint_map_rev[slave_id] = []
                        constraint_map_rev[slave_id].append((master_id, constraint))

                # Get mesh data
                cells = self.assembler.AssembeledMesh.cell_connectivity
                offsets = self.assembler.AssembeledMesh.offset

                for core_idx, core in enumerate(num_cores):
                    # Get elements in current core
                    eleids = where(cores == core)[0]
                    if eleids.size == 0:
                        continue
                    
                    # Get all nodes in this core's elements
                    starts = offsets[eleids]
                    ends = offsets[eleids + 1]
                    core_node_indices = concatenate([cells[s:e] for s, e in zip(starts, ends)])
                    in_core = isin(arange(num_nodes), core_node_indices)
                    
                    # Find active masters and slaves in this core
                    active_masters = where(master_nodes & in_core)[0]
                    active_slaves = where(slave_nodes & in_core)[0]

                    # Add the master nodes that are not in the core but needed for constraints
                    masters_to_add = []
                    for slave_id in active_slaves:
                        if slave_id in constraint_map_rev:
                            for master_id, _ in constraint_map_rev[slave_id]:
                                masters_to_add.append(master_id)
                    
                    # Add unique masters
                    if masters_to_add:
                        active_masters = concatenate([active_masters, array(masters_to_add)])
                        active_masters = unique(active_masters)

                    if not active_masters.size:
                        continue

                    f.write(f"if {{$pid == {core}}} {{\n")
                    
                    # Process all master nodes that are not in the current core
                    valid_mask = ~in_core[active_masters]
                    valid_masters = active_masters[valid_mask]
                    if valid_masters.size > 0:
                        f.write("\t# Master nodes not defined in this core\n")
                        for master_id in valid_masters:
                            node = nodes[master_id]
                            f.write(f"\tnode {master_id+1} {node[0]} {node[1]} {node[2]} -ndf {ndfs[master_id]}\n")

                    # Process all slave nodes that are not in the current core
                    # Collect all unique slave nodes from active master nodes' constraints
                    all_slaves = []
                    for master_id in active_masters:
                        for constraint in constraint_map[master_id]:
                            all_slaves.extend([sid - 1 for sid in constraint.slave_nodes])
                    
                    # Filter out slave nodes that are not in the current core
                    valid_slaves = array([sid for sid in all_slaves if 0 <= sid < num_nodes and not in_core[sid]])
                    
                    if valid_slaves.size > 0:
                        f.write("\t# Slave nodes not defined in this core\n")
                        for slave_id in unique(valid_slaves):
                            node = nodes[slave_id]
                            f.write(f"\tnode {slave_id+1} {node[0]} {node[1]} {node[2]} -ndf {ndfs[slave_id]}\n")

                    # Write constraints after nodes
                    f.write("\t# Constraints\n")
                    
                    # Process constraints where master is in this core
                    for master_id in active_masters:
                        for constraint in constraint_map[master_id]:
                            f.write(f"\t{constraint.to_tcl()}\n")
                    
                    f.write("}\n")

                    if progress_callback:
                        progress = 65 + (core_idx + 1) / len(num_cores) * 15
                        progress_callback(min(progress, 80), "writing constraints")
                
                # write sp constraints
                f.write("\n# spConstraints ======================================\n")
                size = len(self.constraint.sp)
                indx = 1
                for constraint in self.constraint.sp:
                    f.write(f"{constraint.to_tcl()}\n")
                    if progress_callback:
                        progress_callback(80 + indx / size * 5, "writing sp constraints")
                    indx += 1


                # write time series
                f.write("\n# Time Series ======================================\n")
                size = len(self.timeSeries)
                indx = 1
                for timeSeries in self.timeSeries:
                    f.write(f"{timeSeries.to_tcl()}\n")
                    if progress_callback:
                        progress_callback(85 + indx / size * 5, "writing time series")
                    indx += 1

                # write process
                f.write("\n# Process ======================================\n")
                indx = 1
                size = len(self.process)
                f.write(f"{self.process.to_tcl()}\n")
                
                f.write("exit\n")
                # for process in self.process:
                #     print(process["component"])
                #     f.write(f"{process['component'].to_tcl()}\n")
                #     if progress_callback:
                #         progress_callback(90 + indx / size * 10, "writing process")
                #     indx += 1


                
                    

                if progress_callback:
                    progress_callback(100,"finished writing")
                 
        return True



    def export_to_vtk(self, filename: str = None) -> bool:
        """Exports the assembled Femora model to a VTK file.
        
        This method saves the assembled mesh, including nodal coordinates,
        element connectivity, and any associated point/cell data, into a
        binary VTK file format. This file can be opened with visualization
        software like ParaView or PyVista.

        Args:
            filename: The full path and name of the VTK file to export to.
                If None, uses `model_name` within `model_path`.

        Returns:
            True: If the export process was successful.

        Raises:
            ValueError: If no `filename` is provided and `model_name` or
                `model_path` are not set in the MeshMaker instance.
            ValueError: If no assembled mesh is found.
            Exception: Any exception raised by the underlying mesh saving operation.

        Example:
            >>> import femora as fm
            >>> import os
            >>> # Assuming a model is already defined and assembled
            >>> mesh_maker = fm.MeshMaker.get_instance(model_name="my_vtk_model", model_path=".")
            >>> # Example: Create a dummy mesh for demonstration
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>> success = mesh_maker.export_to_vtk(filename="my_model.vtk")
            >>> print(f"VTK export successful: {success}")
            VTK export successful: True
            >>> os.remove("my_model.vtk") # Clean up
        """
        if True: # This 'if True' is redundant, but leaving logic unchanged as per Rule 1.
            # Determine the full file path
            if filename is None:
                if self.model_name is None or self.model_path is None:
                    raise ValueError("Either provide a filename or set model_name and model_path")
                filename = os.path.join(self.model_path, f"{self.model_name}.vtk")
            
            # check if the end is not .vtk then add it
            if not filename.endswith('.vtk'):
                filename += '.vtk'
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

            # Get the assembled content
            if self.assembler.AssembeledMesh is None:
                print("No mesh found")
                raise ValueError("No mesh found\\n Please assemble the mesh first")
            
            # export to vtk
            # self.assembler.AssembeledMesh.save(filename, binary=True)
            try:
                self.assembler.AssembeledMesh.save(filename, binary=True)
            except Exception as e:
                raise e
        return True

    # -------------------------------------------------------------
    # Mask convenience
    # -------------------------------------------------------------
    @property
    def mask(self) -> MaskManager:
        """Accesses a MaskManager bound to the assembled mesh.

        This property provides a convenient way to create and apply masks
        to nodes and elements of the assembled mesh, enabling advanced
        selection and manipulation.

        Returns:
            MaskManager: A MaskManager instance providing typed views
                via `.nodes` and `.elements` attributes.

        Raises:
            RuntimeError: If the model has not been assembled yet.

        Example:
            >>> import femora as fm
            >>> # Assuming a model is already defined and assembled
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> # Example: Create a dummy mesh for demonstration
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>>
            >>> # Access the mask manager
            >>> mask_manager = mesh_maker.mask
            >>> # For illustration, check if nodes property exists
            >>> print(hasattr(mask_manager, 'nodes'))
            True
        """
        return MaskManager.from_assembled()

    def set_model_info(self, model_name: str = None, model_path: str = None) -> None:
        """Updates the model's name and/or path.
        
        This method allows modification of the model's identifying information,
        which is used for default export filenames and paths.

        Args:
            model_name: The new name for the model. If None, the current name is retained.
            model_path: The new directory path where model files will be saved.
                If None, the current path is retained.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance(model_name="old_name", model_path=".")
            >>> mesh_maker.set_model_info(model_name="new_name", model_path="./models")
            >>> print(mesh_maker.model_name)
            new_name
            >>> print(mesh_maker.model_path)
            ./models
        """
        if model_name is not None:
            self.model_name = model_name
        if model_path is not None:
            self.model_path = model_path

    @classmethod
    def set_results_folder(cls, folder_name: str) -> None:
        """Sets the global results folder for the model.

        This class method updates the default directory where simulation results
        will be stored. This setting is shared across all MeshMaker instances.

        Args:
            folder_name: The path to the results folder.

        Example:
            >>> import femora as fm
            >>> fm.MeshMaker.set_results_folder("./output_data")
            >>> print(fm.MeshMaker.get_results_folder())
            ./output_data
        """
        cls._results_folder = folder_name

    @classmethod
    def get_results_folder(cls) -> str:
        """Gets the current global results folder path.
        
        Returns:
            str: The path to the results folder, or an empty string if not set.

        Example:
            >>> import femora as fm
            >>> fm.MeshMaker.set_results_folder("./sim_results")
            >>> folder = fm.MeshMaker.get_results_folder()
            >>> print(folder)
            ./sim_results
        """
        return cls._results_folder if cls._results_folder else ""
    

    def print_info(self) -> None:
        """Prints information about the current assembled model to the console.

        If a mesh has been assembled, this method outputs the number of nodes
        and elements. Otherwise, it indicates that no mesh is found.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.print_info()
            No mesh found
            >>> # Assuming a mesh is assembled
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>> mesh_maker.print_info() # doctest: +SKIP
            Number of nodes: 8
            Number of elements: 1
        """

        if self.assembler.AssembeledMesh is None:
            print("No mesh found")
        else:
            numpoints = self.assembler.AssembeledMesh.n_points
            numcells = self.assembler.AssembeledMesh.n_cells
            print(f"Number of nodes: {numpoints}")
            print(f"Number of elements: {numcells}")    
        
        
    def get_max_ele_tag(self) -> int:
        """Gets the maximum element tag in the assembled mesh.

        This method calculates the highest tag that would be assigned to
        an element, considering the starting element tag offset.

        Returns:
            int: The maximum element tag, or -1 if no mesh is assembled.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_eletag_start(100)
            >>> print(mesh_maker.get_max_ele_tag())
            -1
            >>> # Assuming a mesh is assembled
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>> print(mesh_maker.get_max_ele_tag()) # doctest: +SKIP
            100
        """

        max_ele_tag = self.assembler.get_num_cells()

        if max_ele_tag < 0:
            return -1
        return max_ele_tag + self._start_ele_tag - 1
    
    def get_max_node_tag(self) -> int:
        """Gets the maximum node tag in the assembled mesh.

        This method calculates the highest tag that would be assigned to
        a node, considering the starting node tag offset.

        Returns:
            int: The maximum node tag, or -1 if no mesh is assembled.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_nodetag_start(1)
            >>> print(mesh_maker.get_max_node_tag())
            -1
            >>> # Assuming a mesh is assembled
            >>> mesh_maker.meshPart.create_block_mesh_from_cube(tag=1, x_dim=1, y_dim=1, z_dim=1)
            >>> mesh_maker.assembler.assemble_all_meshes()
            >>> print(mesh_maker.get_max_node_tag()) # doctest: +SKIP
            8
        """

        max_node_tag = self.assembler.get_num_points()

        if max_node_tag < 0:
            return -1
        return max_node_tag + self._start_nodetag - 1

    def get_start_ele_tag(self) -> int:
        """Gets the current starting element tag.

        Returns:
            int: The integer value of the starting element tag.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_eletag_start(500)
            >>> print(mesh_maker.get_start_ele_tag())
            500
        """
        return self._start_ele_tag
    

    def get_start_node_tag(self) -> int:
        """Gets the current starting node tag.

        Returns:
            int: The integer value of the starting node tag.

        Example:
            >>> import femora as fm
            >>> mesh_maker = fm.MeshMaker.get_instance()
            >>> mesh_maker.set_nodetag_start(1000)
            >>> print(mesh_maker.get_start_node_tag())
            1000
        """
        return self._start_nodetag