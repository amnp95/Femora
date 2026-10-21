# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List, Dict, Optional, Union

from femora.core.group import ElementGroup
from femora.core.recorder_base import Recorder
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface


def _resolve_element_group_tag(recorder: Recorder, group_input) -> int:
    if isinstance(group_input, ElementGroup):
        if group_input.tag is None:
            raise ValueError(f"ElementGroup '{group_input.name}' has no OpenSees region tag")
        return group_input.tag
    if isinstance(group_input, str):
        mesh_maker = recorder._mesh_maker()
        if mesh_maker is None:
            raise ValueError(f"Cannot resolve group name '{group_input}' without a manager-owned recorder")
        group = mesh_maker.group.element.get(group_input)
        if group is None:
            raise ValueError(f"Element group '{group_input}' not found")
        if group.tag is None:
            raise ValueError(f"ElementGroup '{group.name}' has no OpenSees region tag")
        return group.tag
    raise TypeError("group must be an ElementGroup instance or an element group name")


def _results_folder(recorder: Recorder) -> str:
    """Resolve the results folder path for the given recorder.

    Args:
        recorder: The recorder instance.

    Returns:
        The results directory path ending with a slash.

    Raises:
        ValueError: If the recorder does not belong to a managed Model.
    """
    mesh_maker = recorder._mesh_maker()
    if mesh_maker is None:
        raise ValueError(
            "Recorder must belong to a Model recorder manager to resolve results paths"
        )
    folder = mesh_maker.get_results_folder()
    if folder == "":
        return "./"
    return folder + "/"


class EmbeddedBeamSolidInterfaceRecorder(Recorder):
    """Recorder for embedded beam-solid interfaces.

    EmbeddedBeamSolidInterfaceRecorder monitors the kinematic and force interaction
    between embedded beams and solid elements. It records displacements, axial forces,
    solid forces, or beam forces directly at the interfaces.

    Tcl form:
        None (renders internally via interface-specific export commands).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create an interface recorder for an interface named 'pile_solid_interface'
        recorder = model.recorder.embedded_beam_solid_interface(
            interface="pile_solid_interface",
            resp_type=["axialForce", "displacement"],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        interface: Union[str, 'EmbeddedBeamSolidInterface', List[Union[str, 'EmbeddedBeamSolidInterface']]],
        resp_type: Union[str, List[str]] = ["displacement", "localDisplacement", "axialDisp", "radialDisp",
                   "tangentialDisp", "globalForce", "localForce", "axialForce",
                   "radialForce", "tangentialForce", "solidForce", "beamForce","beamLocalForce"],
        dt: Union[float, None] = None,
        cores: Optional[Union[int, List[int]]] = None,
    ):
        """Create an embedded beam-solid interface recorder.

        Args:
            interface: The interface(s) to record. Can be an
                EmbeddedBeamSolidInterface instance, a string name, or a list
                of both.
            resp_type: The response type or list of response types to record.
            dt: Optional recording time step interval.
            cores: Optional processor core ID(s) for MPI execution.

        Raises:
            ValueError: If interface validation fails.
            TypeError: If resp_type is invalid.
        """
        super().__init__("EmbeddedBeamSolidInterface", cores=cores)
        if isinstance(interface, list):
            if not interface:
                raise ValueError("interface list must not be empty")
            for iface in interface:
                if not isinstance(iface, (str, EmbeddedBeamSolidInterface)):
                    raise ValueError(
                        "All interfaces must be instances of EmbeddedBeamSolidInterface or valid names"
                    )
            self._interface_input = interface
        elif isinstance(interface, (str, EmbeddedBeamSolidInterface)):
            self._interface_input = interface
        else:
            raise ValueError(
                "interface must be an instance of EmbeddedBeamSolidInterface or a valid interface name"
            )

        if isinstance(resp_type, str):
            resp_type = [resp_type]
        elif not isinstance(resp_type, list):
            raise TypeError("resp_type must be a string or a list of strings")

        self.resp_type = resp_type

        for resp in self.resp_type:
            if resp not in ["displacement", "localDisplacement", "axialDisp", "radialDisp",
                            "tangentialDisp", "globalForce", "localForce", "axialForce",
                            "radialForce", "tangentialForce", "solidForce", "beamForce","beamLocalForce"]:
                raise ValueError(f"Invalid response type: {resp}. ")

        self.dt = dt

    def _resolve_interfaces(self) -> List[EmbeddedBeamSolidInterface]:
        """Resolve interface identifiers to actual EmbeddedBeamSolidInterface instances.

        Returns:
            A list of resolved EmbeddedBeamSolidInterface instances.

        Raises:
            ValueError: If the recorder is not currently managed or if the
                interface name is not found.
            TypeError: If the interface is an invalid type.
        """
        mesh_maker = self._mesh_maker()
        if mesh_maker is None:
            raise ValueError(
                "EmbeddedBeamSolidInterfaceRecorder must belong to a Model recorder manager before export"
            )
        interface_manager = mesh_maker.interface

        def resolve_one(item: Union[str, EmbeddedBeamSolidInterface]) -> EmbeddedBeamSolidInterface:
            if isinstance(item, str):
                resolved = interface_manager.require(item)
                if not isinstance(resolved, EmbeddedBeamSolidInterface):
                    raise ValueError(
                        f"Interface '{item}' is registered but is not an EmbeddedBeamSolidInterface"
                    )
                return resolved
            if isinstance(item, EmbeddedBeamSolidInterface):
                interface_manager.require_registered(item)
                return item
            raise TypeError("interfaces must be EmbeddedBeamSolidInterface instances or valid names")

        if isinstance(self._interface_input, list):
            return [resolve_one(item) for item in self._interface_input]
        return [resolve_one(self._interface_input)]

    def _to_tcl_impl(self) -> str:
        """Convert this recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.
        """
        # This recorder does not generate a TCL command, it writes directly to a file
        cmd = "# recorder EmbeddedBeamSolidInterface\n"
        results_folder = _results_folder(self)

        for interface in self._resolve_interfaces():
           cmd += interface._get_recorder(self.resp_type,
                                          dt=self.dt,
                                          results_folder=results_folder)
           cmd += "\n"
        return cmd


class NodeRecorder(Recorder):
    """Node recorder for recording nodal responses at every converged step.

    NodeRecorder monitors nodal degrees of freedom throughout the analysis,
    exporting results such as displacements, velocities, accelerations, or reaction
    forces to files, XML, binary, or TCP streams.

    Tcl form:
        ``recorder Node -file <fileName> -node <nodeTags...> -dof <dofs...> <respType>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Record displacement at DOFs 1 and 2 for nodes 101 and 102
        recorder = model.recorder.node(
            file_name="displacement.out",
            nodes=[101, 102],
            dofs=[1, 2],
            resp_type="disp",
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, **kwargs):
        """Create a node recorder.

        Args:
            **kwargs: Key-value parameters:
                file_name: Optional file path for plain text output.
                xml_file: Optional file path for XML output.
                binary_file: Optional file path for binary output.
                inet_addr / port: Optional IP and port for TCP output.
                precision: Number of significant digits (default: 6).
                time_series: Optional TimeSeries tag.
                time: If True, includes time in the first column.
                delta_t: Optional time step recording interval.
                close_on_write: If True, opens/closes the output file on each write.
                nodes: Optional list of node tags.
                node_range: Optional start and end tag `[start, end]`.
                region: Optional target region tag or name.
                dofs: List of active degrees of freedom (required).
                resp_type: Response type, e.g. `'disp'`, `'vel'`, `'accel'`, `'reaction'` (required).

        Raises:
            ValueError: If output destination, node selection, DOFs, or response type
                validation fails.
        """
        super().__init__("Node", cores=kwargs.get("cores", None))
        self.file_name = kwargs.get("file_name", None)
        self.xml_file = kwargs.get("xml_file", None)
        self.binary_file = kwargs.get("binary_file", None)
        self.inet_addr = kwargs.get("inet_addr", None)
        self.port = kwargs.get("port", None)
        self.precision = kwargs.get("precision", 6)
        self.time_series = kwargs.get("time_series", None)
        self.time = kwargs.get("time", False)
        self.delta_t = kwargs.get("delta_t", None)
        self.close_on_write = kwargs.get("close_on_write", False)
        self.nodes = kwargs.get("nodes", None)
        self.node_range = kwargs.get("node_range", None)
        self.region = kwargs.get("region", None)
        self.dofs = kwargs.get("dofs", [])
        self.resp_type = kwargs.get("resp_type", "")

        output_options = [
            self.file_name is not None,
            self.xml_file is not None,
            self.binary_file is not None,
            (self.inet_addr is not None and self.port is not None),
        ]
        if sum(output_options) > 1:
            raise ValueError("Only one of -file, -xml, -binary, or -tcp may be used")

        node_options = [
            self.nodes is not None,
            self.node_range is not None,
            self.region is not None,
        ]
        if sum(node_options) > 1:
            raise ValueError("Only one of -node, -nodeRange, or -region may be used")
        if sum(node_options) == 0:
            raise ValueError("One of -node, -nodeRange, or -region must be specified")
        if not self.dofs:
            raise ValueError("DOFs must be specified")
        if not self.resp_type:
            raise ValueError("Response type must be specified")
        valid_resp_types = [
            "disp", "vel", "accel", "incrDisp", "reaction", "rayleighForces",
        ]
        if not (self.resp_type in valid_resp_types or self.resp_type.startswith("eigen ")):
            raise ValueError(
                f"Invalid response type: {self.resp_type}. "
                f"Valid types are: {', '.join(valid_resp_types)}, or 'eigen $mode'"
            )

    def _to_tcl_impl(self) -> str:
        """Convert this node recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.
        """
        cmd = "recorder Node"
        
        # Output destination
        if self.file_name:
            cmd += f" -file {self.file_name}"
        elif self.xml_file:
            cmd += f" -xml {self.xml_file}"
        elif self.binary_file:
            cmd += f" -binary {self.binary_file}"
        elif self.inet_addr and self.port:
            cmd += f" -tcp {self.inet_addr} {self.port}"
        
        # Other options
        if self.precision != 6:
            cmd += f" -precision {self.precision}"
        
        if self.time_series:
            cmd += f" -timeSeries {self.time_series}"
        
        if self.time:
            cmd += " -time"
        
        if self.delta_t:
            cmd += f" -dT {self.delta_t}"
        
        if self.close_on_write:
            cmd += " -closeOnWrite"
        
        # Node selection
        if self.nodes:
            cmd += f" -node {' '.join(map(str, self.nodes))}"
        elif self.node_range:
            cmd += f" -nodeRange {self.node_range[0]} {self.node_range[1]}"
        elif self.region:
            cmd += f" -region {self.region}"
        
        # DOFs and response type
        cmd += f" -dof {' '.join(map(str, self.dofs))} {self.resp_type}"
        
        return cmd


class DriftRecorder(Recorder):
    """Recorder for inter-story drift ratios.

    DriftRecorder captures inter-story drift ratios between pairs of nodes (such
    as story bottoms and tops) to monitor shear deformation and relative structural
    movements.

    Tcl form:
        ``recorder Drift -file <fileName> -iNode <iNodeTags...> -jNode <jNodeTags...> -dof <dof> -perpDirn <perpDirn>``

    Note:
        - In parallel MPI runs, this recorder automatically injects `$pid` into the
          output filename (before the extension) to prevent file conflicts.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Record inter-story drift between node 1 and 101 along DOF 1
        recorder = model.recorder.drift(
            file_name="StoryDrift.out",
            i_nodes=[1],
            j_nodes=[101],
            dof=1,
            perp_dirn=3,
            time=True,
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, **kwargs):
        """Create a drift recorder.

        Args:
            **kwargs: Key-value parameters:
                file_name: Output file name (required).
                i_nodes: List of bottom node tags (required).
                j_nodes: List of top node tags (required).
                dof: Target degree of freedom (1 to 6).
                perp_dirn: Perpendicular direction (1 to 3).
                time: If True, records simulation time.
                delta_t: Optional time step recording interval.
                precision: Optional number of significant digits.
                cores: Optional processor core ID(s) for MPI execution.

        Raises:
            ValueError: If input validation fails.
            TypeError: If cores or node lists are invalid types.
        """
        # Accept both legacy `core` and new `cores` arguments.
        cores = kwargs.get("cores", None)
        core = kwargs.get("core", None)
        if cores is None and core is not None:
            cores = int(core)

        super().__init__("Drift", cores=cores)

        self.file_name: str = str(kwargs.get("file_name", ""))

        i_nodes = kwargs.get("i_nodes", None)
        j_nodes = kwargs.get("j_nodes", None)

        self.i_nodes: List[int] = self._normalize_nodes(i_nodes, "i_nodes")
        self.j_nodes: List[int] = self._normalize_nodes(j_nodes, "j_nodes")

        self.dof: int = int(kwargs.get("dof", 0))
        self.perp_dirn: int = int(kwargs.get("perp_dirn", 3))
        self.time: bool = bool(kwargs.get("time", False))
        self.delta_t: Optional[float] = kwargs.get("delta_t", None)
        self.precision: Optional[int] = kwargs.get("precision", None)

        if not self.file_name:
            raise ValueError("file_name must be specified for DriftRecorder")
        if not self.i_nodes or not self.j_nodes:
            raise ValueError("Both i_nodes and j_nodes must be specified")
        if len(self.i_nodes) != len(self.j_nodes):
            raise ValueError("i_nodes and j_nodes must have the same length")
        for n in self.i_nodes + self.j_nodes:
            if not isinstance(n, int) or n <= 0:
                raise ValueError("All node tags must be positive integers")
        if self.dof not in (1, 2, 3, 4, 5, 6):
            raise ValueError("dof must be an integer in [1..6]")
        if self.perp_dirn not in (1, 2, 3):
            raise ValueError("perp_dirn must be an integer in [1..3]")
        if self.delta_t is not None:
            self.delta_t = float(self.delta_t)
            if self.delta_t <= 0:
                raise ValueError("delta_t must be > 0 when provided")
        if self.precision is not None:
            self.precision = int(self.precision)
            if self.precision <= 0:
                raise ValueError("precision must be > 0 when provided")
        if self.cores is not None:
            if isinstance(self.cores, int):
                if self.cores < 0:
                    raise ValueError("cores must be >= 0 when provided")
            elif isinstance(self.cores, (list, tuple)):
                for c in self.cores:
                    if not isinstance(c, int) or c < 0:
                        raise ValueError("each entry in cores must be a non-negative integer")
            else:
                raise TypeError("cores must be an int or list/tuple of ints")

    @staticmethod
    def _normalize_nodes(value, name: str) -> List[int]:
        """Normalize node tag inputs to a list of integers.

        Args:
            value: Node tags input (integer, list, or array).
            name: The argument field name.

        Returns:
            A list of validated node tags.

        Raises:
            TypeError: If the input is not a supported type.
        """
        if value is None:
            return []
        if isinstance(value, int):
            return [int(value)]
        if isinstance(value, (list, tuple)):
            return [int(v) for v in value]

        # Allow numpy arrays without importing numpy at module import time.
        try:
            import numpy as _np  # local import

            if isinstance(value, _np.ndarray):
                return [int(v) for v in value.tolist()]
        except Exception:
            pass
        raise TypeError(f"{name} must be an int or a list/tuple of ints")

    @staticmethod
    def _inject_pid_in_filename(file_name: str) -> str:
        """Inject MPI process tag `$pid` into the output file name.

        Args:
            file_name: File name to modify.

        Returns:
            The modified file name with `$pid` before the extension.
        """
        parts = file_name.split(".")
        if len(parts) > 1:
            ext = parts[-1]
            return file_name[: -(len(ext) + 1)] + f"$pid.{ext}"
        return file_name + "$pid"

    def _to_tcl_impl(self) -> str:
        """Convert this drift recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.
        """
        results_folder = _results_folder(self)
        file_path = DriftRecorder._inject_pid_in_filename(self.file_name)
        if results_folder != "./":
            file_path = results_folder + file_path

        cmd = f"recorder Drift -file {file_path}"
        if self.precision is not None:
            cmd += f" -precision {int(self.precision)}"

        cmd += " -iNode " + " ".join(str(n) for n in self.i_nodes)
        cmd += " -jNode " + " ".join(str(n) for n in self.j_nodes)
        cmd += f" -dof {int(self.dof)} -perpDirn {int(self.perp_dirn)}"

        if self.time:
            cmd += " -time"
        if self.delta_t is not None:
            cmd += f" -dT {float(self.delta_t)}"

        return cmd


class VTKHDFRecorder(Recorder):
    """Whole-model recorder exporting geometry and results in VTK HDF format.

    VTKHDFRecorder records the entire model mesh geometry, elements, and selected
    response field variables (such as displacement, stress, or strain) into a
    binary `.h5` file format, allowing high-performance 3D visualization in ParaView.

    Tcl form:
        ``recorder vtkhdf <fileBaseName> [options] <respTypes...>``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create a VTKHDF whole-model recorder
        recorder = model.recorder.vtkhdf(
            file_base_name="results.h5",
            resp_types=["disp", "stress3D6"],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, **kwargs):
        """Create a VTK HDF recorder.

        Args:
            **kwargs: Key-value parameters:
                file_base_name: Base name of the file to which output is sent (required).
                resp_types: Requested fields (required). Nodal fields are
                    ``disp``, ``vel``, ``accel``. Element fields are
                    ``force2D``, ``force3D``, ``localForce2D``, ``localForce3D``,
                    ``stress2D3``, ``strain2D3``, ``stress3D6``, ``strain3D6``.
                    Availability depends on the OpenSees recorder build and
                    each element's implemented responses. Inspect the output
                    datasets to confirm availability; some older binaries
                    silently ignore force keywords. Continuum stress/strain
                    fields are not substitutes for beam-fiber recorders.
                delta_t: Optional time interval for recording.
                r_tol_dt: Optional relative tolerance for time step matching.
                region: Optional region tag, name, or RegionBase instance used to restrict VTKHDF output to one region. If not specified, the entire model will be recorded.
                group: Optional ElementGroup or element group name used to restrict VTKHDF output.

        Raises:
            ValueError: If file_base_name or resp_types are not specified, or if
                invalid response types are supplied.
        """
        super().__init__("VTKHDF", cores=kwargs.get("cores", None))
        self.file_base_name = kwargs.get("file_base_name", "")
        self.resp_types = kwargs.get("resp_types", [])
        self.delta_t = kwargs.get("delta_t", None)
        self.r_tol_dt = kwargs.get("r_tol_dt", None)
        if "region" in kwargs and "regions" in kwargs:
            raise ValueError("Use only one of region or regions for VTKHDFRecorder")
        group_keys = [key for key in ("group", "element_group") if key in kwargs]
        if len(group_keys) > 1:
            raise ValueError("Use only one of group or element_group for VTKHDFRecorder")
        if ("region" in kwargs or "regions" in kwargs) and group_keys:
            raise ValueError("Use only one of region, regions, or group for VTKHDFRecorder")
        self.region = kwargs.get("region", kwargs.get("regions", None))
        self.element_group = kwargs.get("group", kwargs.get("element_group", None))
        if self.element_group is not None and not isinstance(self.element_group, (ElementGroup, str)):
            raise TypeError("group must be an ElementGroup instance or an element group name")

        if not self.file_base_name:
            raise ValueError("File base name must be specified")
        if not self.resp_types:
            raise ValueError("At least one response type must be specified")
        valid_resp_types = [
            "disp", "vel", "accel", 
            "stress3D6", "strain3D6", 
            "stress2D3", "strain2D3",
            "force2D", "force3D", 
            "localForce2D", "localForce3D",
        ]
        for resp_type in self.resp_types:
            if resp_type not in valid_resp_types:
                raise ValueError(
                    f"Invalid response type: {resp_type}. "
                    f"Valid types are: {', '.join(valid_resp_types)}"
                )

    def _to_tcl_impl(self) -> str:
        """Convert this VTK HDF recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.
        """
        # separete name and format of the file
        name = self.file_base_name.split(".")
        if len(name) < 2:
            fileformat = "vtkhdf"
        else:
            fileformat = name[-1]
        name = name[0]
        name = name + "$pid"
        results_folder = _results_folder(self)
        if results_folder != "./":
            name = results_folder + name
        file_base_name = name + "." + fileformat

        cmd = f"recorder vtkhdf {file_base_name}"
        
        # Add optional parameters
        if self.delta_t is not None:
            cmd += f" -dT {self.delta_t}"

        if self.r_tol_dt is not None:
            cmd += f" -rTolDt {self.r_tol_dt}"

        # Add response types
        for resp_type in self.resp_types:
            cmd += f" {resp_type}"

        if self.region is not None:
            region_tags = self._resolve_regions(self.region)
            if len(region_tags) != 1:
                raise ValueError("VTKHDFRecorder supports exactly one region")
            cmd += f" -region {region_tags[0]}"
        elif self.element_group is not None:
            cmd += f" -region {_resolve_element_group_tag(self, self.element_group)}"
        
        return cmd


class MPCORecorder(Recorder):
    """MPCO whole-model recorder for STKO.

    MPCORecorder exports complex finite element model databases, mesh topology,
    and nodal/element response variables into an HDF5-based MPCO database (*.mpco)
    readable by STKO.

    Tcl form:
        ``recorder mpco <fileName> [options]``

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create an MPCO recorder
        recorder = model.recorder.mpco(
            file_name="results.mpco",
            node_responses=["displacement", "velocity"],
            element_responses=["force"],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, **kwargs):
        """Create an MPCO recorder.

        Args:
            **kwargs: Key-value parameters:
                file_name: Output database file name (required).
                node_responses: Optional list of node response variables to record.
                element_responses: Optional list of element response variables.
                node_sensitivities: Optional list of node sensitivities.
                regions: Optional list of region tags or names to restrict recording to.
                groups: Optional list of ElementGroups or element group names used to restrict recording.
                delta_t: Optional recording time step interval.
                num_steps: Optional recording step interval.

        Raises:
            ValueError: If file_name is missing or parameters are conflicting.
            TypeError: If input parameter types are incorrect.
        """
        super().__init__("MPCO", cores=kwargs.get("cores", None))
        self.file_name = kwargs.get("file_name", "")
        self.node_responses = kwargs.get("node_responses", [])
        self.element_responses = kwargs.get("element_responses", [])
        self.node_sensitivities = kwargs.get("node_sensitivities", [])
        self.regions = self._resolve_regions(kwargs.get("regions", []))
        if "groups" in kwargs and "element_groups" in kwargs:
            raise ValueError("Use only one of groups or element_groups for MPCORecorder")
        self.element_groups = kwargs.get("groups", kwargs.get("element_groups", []))
        self.delta_t = kwargs.get("delta_t", None)
        self.num_steps = kwargs.get("num_steps", None)

        if not self.file_name:
            raise ValueError("File name must be specified for MPCO recorder")
        if self.node_responses is None:
            self.node_responses = []
        if not isinstance(self.node_responses, list):
            raise TypeError("node_responses must be a list of strings")
        valid_node_responses = [
            "displacement", "rotation",
            "velocity", "angularVelocity",
            "acceleration", "angularAcceleration",
            "reactionForce", "reactionMoment",
            "reactionForceIncludingInertia", "reactionMomentIncludingInertia",
            "rayleighForce", "rayleighMoment",
            "unbalancedForce", "unbalancedForceIncludingInertia",
            "unbalancedMoment", "unbalancedMomentIncludingInertia",
            "pressure",
            "modesOfVibration", "modesOfVibrationRotational",
        ]
        for resp in self.node_responses:
            if not isinstance(resp, str):
                raise TypeError("Each node response must be a string")
            if resp not in valid_node_responses:
                raise ValueError(
                    f"Invalid node response: {resp}. Valid: {', '.join(valid_node_responses)}"
                )
        if self.element_responses is None:
            self.element_responses = []
        if not isinstance(self.element_responses, list):
            raise TypeError("element_responses must be a list of strings")
        for er in self.element_responses:
            if not isinstance(er, str):
                raise TypeError("Each element response must be a string")
        if self.node_sensitivities is None:
            self.node_sensitivities = []
        valid_sensitivity_names = [
            "displacementSensitivity", "rotationSensitivity",
            "velocitySensitivity", "angularVelocitySensitivity",
            "accelerationSensitivity", "angularAccelerationSensitivity",
        ]
        normalized_pairs = []
        if not isinstance(self.node_sensitivities, list):
            raise TypeError("node_sensitivities must be a list of pairs or dicts")
        for item in self.node_sensitivities:
            if isinstance(item, dict):
                name = item.get("name")
                par = item.get("param")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                name, par = item[0], item[1]
            else:
                raise TypeError("node_sensitivities items must be (name, param) or {'name','param'}")
            if name not in valid_sensitivity_names:
                raise ValueError(
                    f"Invalid node sensitivity: {name}. Valid: {', '.join(valid_sensitivity_names)}"
                )
            if not isinstance(par, int):
                raise TypeError("Sensitivity parameter id must be an integer")
            normalized_pairs.append((name, par))
        self.node_sensitivities = normalized_pairs
        if self.regions is None:
            self.regions = []
        if not isinstance(self.regions, list):
            raise TypeError("regions must be a list of integers")
        for r in self.regions:
            if not isinstance(r, int):
                raise TypeError("Each region tag must be an integer")
        if self.element_groups is None:
            self.element_groups = []
        if isinstance(self.element_groups, (ElementGroup, str)):
            self.element_groups = [self.element_groups]
        if not isinstance(self.element_groups, list):
            raise TypeError("groups must be a list of ElementGroup instances or element group names")
        for group in self.element_groups:
            if not isinstance(group, (ElementGroup, str)):
                raise TypeError("Each group must be an ElementGroup instance or an element group name")
        if self.delta_t is not None and self.num_steps is not None:
            raise ValueError("Only one of delta_t or num_steps may be specified")

    def _to_tcl_impl(self) -> str:
        """Convert this MPCO recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.
        """
        results_folder = _results_folder(self)
        file_path = self.file_name

        file_ext = self.file_name.split(".")[-1]
        if len(self.file_name.split(".")) > 1:
            file_path = self.file_name.replace("." + file_ext, "$pid." + file_ext)
        else:
            file_path = self.file_name + "$pid"

        if results_folder != "./":
            file_path = results_folder + file_path

        cmd = f'recorder mpco "{file_path}"'

        if self.node_responses:
            cmd += " -N " + " ".join(self.node_responses)

        if self.element_responses:
            cmd += " -E " + " ".join(self.element_responses)

        if self.node_sensitivities:
            ns_parts = []
            for name, par in self.node_sensitivities:
                ns_parts.append(name)
                ns_parts.append(str(par))
            cmd += " -NS " + " ".join(ns_parts)

        for r in self.regions:
            cmd += f" -R {r}"
        for group in self.element_groups:
            cmd += f" -R {_resolve_element_group_tag(self, group)}"

        if self.delta_t is not None:
            cmd += f" -T dt {self.delta_t}"
        elif self.num_steps is not None:
            cmd += f" -T nsteps {self.num_steps}"

        return cmd


class BeamForceRecorder(Recorder):
    """Specialized Element force recorder for line meshes.

    BeamForceRecorder automatically resolves the element tags associated with
    selected line mesh parts and creates parallel Element force recorders grouped
    by MPI compute core.

    Tcl form:
        Generates parallel ``recorder Element`` commands guarded by ``$pid == <core>``.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Record beam local forces for two line meshparts
        recorder = model.recorder.beam_force(
            meshparts=["Beam1", "Beam2"],
            force_type="localForce",
            file_prefix="BeamForces",
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, **kwargs):
        """Create a beam force recorder.

        Args:
            **kwargs: Key-value parameters:
                meshparts: Optional list of MeshPart identifiers (user_name strings
                    or MeshPart instances). If omitted, all line mesh parts are used.
                force_type: Force system, either `'globalForce'` or `'localForce'`.
                file_prefix: Prefix for output files (default: `'Beam'`).
                delta_t: Optional time step recording interval.
                include_time: If True, includes time in columns (default: True).
                output_format: Output format, either `'file'`, `'xml'`, or `'binary'`.
                precision: Optional significant digits.

        Raises:
            ValueError: If force_type or output_format are invalid.
        """
        super().__init__("BeamForce", cores=kwargs.get("cores", None))
        self.meshparts = kwargs.get("meshparts", [])
        self.force_type = kwargs.get("force_type", "globalForce")
        self.file_prefix = kwargs.get("file_prefix", "Beam")
        self.delta_t = kwargs.get("delta_t", None)
        self.include_time = kwargs.get("include_time", True)
        self.output_format = kwargs.get("output_format", "file")
        self.precision = kwargs.get("precision", None)

        # Validate force type
        if self.force_type not in ("globalForce", "localForce"):
            raise ValueError("force_type must be 'globalForce' or 'localForce'")
        if self.output_format not in ("file", "xml", "binary"):
            raise ValueError("output_format must be one of 'file', 'xml', 'binary'")

    def _resolve_meshparts(self):
        """Resolve meshpart identifiers to actual MeshPart instances.

        Returns:
            A dictionary of resolved MeshPart instances keyed by user_name.

        Raises:
            ValueError: If the recorder is not managed or a meshpart is not found.
            TypeError: If meshpart identifiers are invalid types.
        """
        from femora.core.meshpart_base import MeshPart

        mesh_maker = self._mesh_maker()
        if mesh_maker is None:
            raise ValueError(
                "BeamForceRecorder must belong to a Model recorder manager before resolving meshparts"
            )
        manager = mesh_maker.meshpart
        if not self.meshparts:
            return {
                name: part
                for name, part in manager.get_all().items()
                if part.category.lower() == "line mesh"
            }
        resolved: Dict[str, object] = {}
        for mp in self.meshparts:
            if isinstance(mp, str):
                part = manager.get(mp)
                if part is None:
                    raise ValueError(f"MeshPart '{mp}' not found")
                resolved[mp] = part
            elif isinstance(mp, MeshPart):
                resolved[mp.user_name] = mp
            else:
                raise TypeError("meshparts must be MeshPart instances or user_name strings")
        return resolved

    @staticmethod
    def _compress_to_ranges(sorted_tags: List[int]) -> List[Union[int, tuple]]:
        """Compress a sorted list of element tags into ranges.

        Args:
            sorted_tags: A sorted list of integer tags.

        Returns:
            A list of integers or tuples representing element tag ranges.
        """
        if not sorted_tags:
            return []
        ranges: List[Union[int, tuple]] = []
        start = prev = sorted_tags[0]
        for t in sorted_tags[1:]:
            if t == prev + 1:
                prev = t
                continue
            # close current range
            if start == prev:
                ranges.append(start)
            else:
                ranges.append((start, prev))
            start = prev = t
        # close last range
        if start == prev:
            ranges.append(start)
        else:
            ranges.append((start, prev))
        return ranges

    def _to_tcl_impl(self) -> str:
        """Convert this beam force recorder to an OpenSees TCL command string.

        Returns:
            The TCL command string.

        Raises:
            ValueError: If Model, assembled mesh, or required mesh datasets are missing.
        """
        import numpy as np
        try:
            import pyvista as pv
        except Exception:
            pv = None

        mm = self._mesh_maker()
        if mm is None:
            raise ValueError(
                "BeamForceRecorder must belong to a Model recorder manager before export"
            )
        assembled = mm.assembled_mesh
        if assembled is None:
            raise ValueError("No assembled mesh found. Assemble the model before creating BeamForceRecorder.")

        results_folder = _results_folder(self)

        start_ele_tag = mm._start_ele_tag

        # Resolve meshparts
        parts = self._resolve_meshparts()

        # Determine beam cell types mask, if pyvista is available
        celltypes = getattr(assembled, "celltypes", None)
        beam_mask_all = None
        if pv is not None and celltypes is not None:
            beam_types = set()
            if hasattr(pv, "CellType"):
                # Common line-like cell types
                for name in ("LINE", "POLY_LINE"):
                    if hasattr(pv.CellType, name):
                        beam_types.add(getattr(pv.CellType, name))
            if beam_types:
                beam_mask_all = np.isin(celltypes, list(beam_types))

        cores = assembled.cell_data.get("Core")
        mesh_tags = assembled.cell_data.get("MeshPartTag_celldata")
        if mesh_tags is None or cores is None:
            raise ValueError("Assembled mesh missing required cell_data ('MeshPartTag_celldata' or 'Core')")

        lines: List[str] = []
        # For each meshpart, build recorder(s) grouped by core
        for name, part in parts.items():
            # mask by mesh tag
            mask = (mesh_tags == part.tag)
            if beam_mask_all is not None:
                mask = mask & beam_mask_all

            idxs = np.where(mask)[0]
            if idxs.size == 0:
                lines.append(f"# No beam elements found for meshpart '{name}'")
                continue

            # Map indices to element tags
            ele_tags = (start_ele_tag + idxs).astype(int)

            # group by core
            part_cores = cores[idxs]
            unique_cores = np.unique(part_cores)
            for core in unique_cores:
                core_mask = (part_cores == core)
                core_tags = np.sort(ele_tags[core_mask])
                if core_tags.size == 0:
                    continue

                # File name per meshpart per core with extension by format
                ext = ".out" if self.output_format == "file" else (".xml" if self.output_format == "xml" else ".bin")
                file_name = f"{results_folder}{self.file_prefix}_{name}_Core{int(core)}_{self.force_type}{ext}"

                # Build command
                file_flag = "-file" if self.output_format == "file" else ("-xml" if self.output_format == "xml" else "-binary")
                cmd = f"if {{$pid == {int(core)}}} {{\n\trecorder Element {file_flag} {file_name}"
                if self.precision is not None:
                    cmd += f" -precision {int(self.precision)}"
                if self.include_time:
                    cmd += " -time"
                if self.delta_t is not None:
                    cmd += f" -dT {self.delta_t}"

                # Always use explicit element tags with -ele
                tags_list = core_tags.tolist()
                if self.output_format == "xml":
                    # Avoid multiple XML recorders writing to same file; single line with all tags
                    cmd += " -ele " + " ".join(str(t) for t in tags_list)
                    cmd += f" {self.force_type}\n}}"
                    lines.append(cmd)
                else:
                    # Split into chunks if long (text/binary append-friendly)
                    CHUNK = 1000
                    head, rest = tags_list[:CHUNK], tags_list[CHUNK:]
                    if head:
                        cmd += " -ele " + " ".join(str(t) for t in head)
                        cmd += f" {self.force_type}\n"
                    # For remaining chunks, create additional recorder lines with same file
                    while rest:
                        chunk, rest = rest[:CHUNK], rest[CHUNK:]
                        cmd += f"\trecorder Element {file_flag} {file_name}"
                        if self.precision is not None:
                            cmd += f" -precision {int(self.precision)}"
                        if self.include_time:
                            cmd += " -time"
                        if self.delta_t is not None:
                            cmd += f" -dT {self.delta_t}"
                        cmd += " -ele " + " ".join(str(t) for t in chunk)
                        cmd += f" {self.force_type}\n"
                    cmd += "}"
                    lines.append(cmd)

        return "\n".join(lines)
