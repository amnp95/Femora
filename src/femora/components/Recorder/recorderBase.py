from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Type
from femora.components.Region.regionBase import RegionBase
from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
from femora.components.interface.interface_base import InterfaceManager

class Recorder(ABC):
    """
    Base abstract class for all recorder types in OpenSees.
    
    Recorders are used to monitor what is happening during the analysis 
    and generate output for the user. The output may go to the screen, 
    files, databases, or to remote processes through TCP/IP options.
    """
    _recorders = {}  # Class-level dictionary to track all recorders
    _next_tag = 1   # Class variable to track the next tag to assign

    def __init__(self, recorder_type: str):
        """
        Initialize a new recorder with a sequential tag
        
        Args:
            recorder_type (str): The type of recorder (e.g., 'Node', 'Element', 'VTKHDF')
        """
        self.tag = Recorder._next_tag
        Recorder._next_tag += 1
        
        self.recorder_type = recorder_type
        
        # Register this recorder in the class-level tracking dictionary
        Recorder._recorders[self.tag] = self

    @classmethod
    def get_recorder(cls, tag: int) -> 'Recorder':
        """
        Retrieve a specific recorder by its tag.
        
        Args:
            tag (int): The tag of the recorder
        
        Returns:
            Recorder: The recorder with the specified tag
        
        Raises:
            KeyError: If no recorder with the given tag exists
        """
        if tag not in cls._recorders:
            raise KeyError(f"No recorder found with tag {tag}")
        return cls._recorders[tag]

    @classmethod
    def remove_recorder(cls, tag: int) -> None:
        """
        Delete a recorder by its tag.
        
        Args:
            tag (int): The tag of the recorder to delete
        """
        if tag in cls._recorders:
            del cls._recorders[tag]
            # Recalculate _next_tag if needed
            if cls._recorders:
                cls._next_tag = max(cls._recorders.keys()) + 1
            else:
                cls._next_tag = 1

    @classmethod
    def get_all_recorders(cls) -> Dict[int, 'Recorder']:
        """
        Retrieve all created recorders.
        
        Returns:
            Dict[int, Recorder]: A dictionary of all recorders, keyed by their unique tags
        """
        return cls._recorders
    
    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all recorders and reset tags.
        """
        cls._recorders.clear()
        cls._next_tag = 1

    @abstractmethod
    def to_tcl(self) -> str:
        """
        Convert the recorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        pass

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this recorder
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        pass

    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Get the parameters defining this recorder
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary of parameter values
        """
        pass




class EmbeddedBeamSolidInterfaceRecorder(Recorder):
    """
    Recorder for embedded beam-solid interfaces.
    
    This recorder is used to monitor the interaction between embedded beams and solid elements.
    It generates output files containing the interface points and connectivity information.

    Args:
        interface (EmbeddedBeamSolidInterface | str): The interface to record. (required)
        resp_type (str | List[str] | None): The type of responses to record. (required)
        If None, only displacement is recorded.
        Valid response types include:
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
    Raises:
        ValueError: If the interface is not an instance of EmbeddedBeamSolidInterface or a valid interface name.
        TypeError: If resp_type is not a string or a list of strings.
        ValueError: If resp_type contains invalid response types.

    Returns:
        EmbeddedBeamSolidInterfaceRecorder: An instance of the recorder.
        
    """
    def __init__(self, 
                 interface: Union[str, 'EmbeddedBeamSolidInterface', list['EmbeddedBeamSolidInterface']],
                 resp_type: Union[str, List[str]] = ["displacement", "localDisplacement", "axialDisp", "radialDisp",
                            "tangentialDisp", "globalForce", "localForce", "axialForce",
                            "radialForce", "tangentialForce", "solidForce", "beamForce","beamLocalForce"],
                 dt : Union[float, None] = None,
                 ):
        """
        Initialize an EmbeddedBeamSolidInterfaceRecorder
        
        Args:
            - interface (EmbeddedBeamSolidInterface | str): The interface to record.
            - resp_type (str | List[str]): The type of responses to record.

    
        """
        super().__init__("EmbeddedBeamSolidInterface")
        interfaces = []
        interface_manager = InterfaceManager()
        if isinstance(interface, list):
            for iface in interface:
                if isinstance(iface, str):
                    resolved = interface_manager.get(iface)
                    if resolved is None or not isinstance(resolved, EmbeddedBeamSolidInterface):
                        raise ValueError(f"Interface '{iface}' is not a valid EmbeddedBeamSolidInterface name")
                    interfaces.append(resolved)
                elif isinstance(iface, EmbeddedBeamSolidInterface):
                    interfaces.append(iface)
                else:
                    raise ValueError("All interfaces must be instances of EmbeddedBeamSolidInterface or valid names")
        else:
            if isinstance(interface, str):
                resolved = interface_manager.get(interface)
                if resolved is None or not isinstance(resolved, EmbeddedBeamSolidInterface):
                    raise ValueError(f"Interface '{interface}' is not a valid EmbeddedBeamSolidInterface name")
                interfaces.append(resolved)
            elif isinstance(interface, EmbeddedBeamSolidInterface):
                interfaces.append(interface)
            else:
                raise ValueError("interface must be an instance of EmbeddedBeamSolidInterface or a valid interface name")
        self.interfaces = interfaces


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

    
    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this recorder
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("interface", "The interface to record (EmbeddedBeamSolidInterface instance or name)"),
            ("resp_type", "Type of responses to record (string or list of strings)"),
            ("dt", "Time interval for recording (optional)")
        ]
    

    def get_values(self) -> Dict[str, Union[str, List[str], float]]:
        """
        Get the parameters defining this recorder
        Returns:
            Dict[str, Union[str, List[str], float]]: Dictionary of parameter values
        """
        return {
            "interface": self.interfaces[0].name if self.interfaces else None,
            "resp_type": self.resp_type,
            "dt": self.dt
        }
    
    
    def to_tcl(self) -> str:
        """
        Convert the EmbeddedBeamSolidInterfaceRecorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        # This recorder does not generate a TCL command, it writes directly to a file
        cmd = "# recorder EmbeddedBeamSolidInterface\n"
        from femora import MeshMaker
        results_folder = MeshMaker.get_results_folder()
        if results_folder == "":
            results_folder = "./"
        else:
            results_folder += "/"

        for interface in self.interfaces:
           cmd += interface._get_recorder(self.resp_type,
                                          dt=self.dt,
                                          results_folder=results_folder)
           cmd += "\n"
        return cmd
    

    

class NodeRecorder(Recorder):
    """
    Node recorder class records the response of a number of nodes 
    at every converged step.
    """
    def __init__(self, **kwargs):
        """
        Initialize a Node Recorder
        
        Args:
            file_name (str, optional): Name of file to which output is sent
            xml_file (str, optional): Name of XML file to which output is sent
            binary_file (str, optional): Name of binary file to which output is sent
            inet_addr (str, optional): IP address of remote machine
            port (int, optional): Port on remote machine awaiting TCP
            precision (int, optional): Number of significant digits (default: 6)
            time_series (int, optional): Tag of previously constructed TimeSeries
            time (bool, optional): Places domain time in first output column
            delta_t (float, optional): Time interval for recording
            close_on_write (bool, optional): Opens and closes file on each write
            nodes (List[int], optional): Tags of nodes whose response is being recorded
            node_range (List[int], optional): Start and end node tags
            region (int, optional): Tag of previously defined region
            dofs (List[int]): List of DOF at nodes whose response is requested
            resp_type (str): String indicating response required
        """
        super().__init__("Node")
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
        
        # Validate the recorder parameters
        self.validate()

    def validate(self):
        """
        Validate recorder parameters
        
        Raises:
            ValueError: If the parameters are invalid
        """
        # Check that only one output destination is specified
        output_options = [
            self.file_name is not None,
            self.xml_file is not None,
            self.binary_file is not None,
            (self.inet_addr is not None and self.port is not None)
        ]
        if sum(output_options) > 1:
            raise ValueError("Only one of -file, -xml, -binary, or -tcp may be used")
        
        # Check that only one node selection method is specified
        node_options = [
            self.nodes is not None,
            self.node_range is not None,
            self.region is not None
        ]
        if sum(node_options) > 1:
            raise ValueError("Only one of -node, -nodeRange, or -region may be used")
        
        # Check that at least one node selection method is specified
        if sum(node_options) == 0:
            raise ValueError("One of -node, -nodeRange, or -region must be specified")
        
        # Check that dofs and resp_type are specified
        if not self.dofs:
            raise ValueError("DOFs must be specified")
        
        if not self.resp_type:
            raise ValueError("Response type must be specified")
        
        # Check that resp_type is valid
        valid_resp_types = [
            "disp", "vel", "accel", "incrDisp", "reaction", "rayleighForces"
        ]
        # Allow "eigen $mode" format
        if not (self.resp_type in valid_resp_types or self.resp_type.startswith("eigen ")):
            raise ValueError(f"Invalid response type: {self.resp_type}. " 
                           f"Valid types are: {', '.join(valid_resp_types)}, or 'eigen $mode'")

    def to_tcl(self) -> str:
        """
        Convert the Node recorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
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

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this recorder
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("file_name", "Name of file to which output is sent"),
            ("xml_file", "Name of XML file to which output is sent"),
            ("binary_file", "Name of binary file to which output is sent"),
            ("inet_addr", "IP address of remote machine"),
            ("port", "Port on remote machine awaiting TCP"),
            ("precision", "Number of significant digits (default: 6)"),
            ("time_series", "Tag of previously constructed TimeSeries"),
            ("time", "Places domain time in first output column"),
            ("delta_t", "Time interval for recording"),
            ("close_on_write", "Opens and closes file on each write"),
            ("nodes", "Tags of nodes whose response is being recorded"),
            ("node_range", "Start and end node tags"),
            ("region", "Tag of previously defined region"),
            ("dofs", "List of DOF at nodes whose response is requested"),
            ("resp_type", "String indicating response required")
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, list, bool]]:
        """
        Get the parameters defining this recorder
        
        Returns:
            Dict[str, Union[str, int, float, list, bool]]: Dictionary of parameter values
        """
        return {
            "file_name": self.file_name,
            "xml_file": self.xml_file,
            "binary_file": self.binary_file,
            "inet_addr": self.inet_addr,
            "port": self.port,
            "precision": self.precision,
            "time_series": self.time_series,
            "time": self.time,
            "delta_t": self.delta_t,
            "close_on_write": self.close_on_write,
            "nodes": self.nodes,
            "node_range": self.node_range,
            "region": self.region,
            "dofs": self.dofs,
            "resp_type": self.resp_type
        }


class VTKHDFRecorder(Recorder):
    """
    The VTKHDF recorder type is a whole model recorder designed to record 
    the model geometry and metadata, along with selected response quantities.
    The output of this recorder is in the .h5 file format, which can be 
    visualized using visualization tools like ParaView.

    Args:
        file_base_name (str): Base name of the file to which output is sent
        resp_types (List[str]): List of strings indicating response types to record
        delta_t (float, optional): Time interval for recording
        r_tol_dt (float, optional): Relative tolerance for time step matching

    Raises:
        ValueError: If file_base_name is not specified
        ValueError: If resp_types is not specified or contains invalid types    
    Returns:
        VTKHDFRecorder: An instance of the recorder.
    """
    def __init__(self, **kwargs):
        """
        Initialize a VTKHDF Recorder
        
        Args:
            file_base_name (str): Base name of the file to which output is sent
            resp_types (List[str]): List of strings indicating response types to record
            delta_t (float, optional): Time interval for recording
            r_tol_dt (float, optional): Relative tolerance for time step matching
        """
        super().__init__("VTKHDF")
        self.file_base_name = kwargs.get("file_base_name", "")
        self.resp_types = kwargs.get("resp_types", [])
        self.delta_t = kwargs.get("delta_t", None)
        self.r_tol_dt = kwargs.get("r_tol_dt", None)
        
        # Validate the recorder parameters
        self.validate()

    def validate(self):
        """
        Validate recorder parameters
        
        Raises:
            ValueError: If the parameters are invalid
        """
        # Check that file_base_name is specified
        if not self.file_base_name:
            raise ValueError("File base name must be specified")
        
        # Check that at least one response type is specified
        if not self.resp_types:
            raise ValueError("At least one response type must be specified")
        
        # Check that resp_types are valid
        valid_resp_types = [
            "disp", "vel", "accel", "stress3D6", "strain3D6", "stress2D3", "strain2D3"
        ]
        for resp_type in self.resp_types:
            if resp_type not in valid_resp_types:
                raise ValueError(f"Invalid response type: {resp_type}. "
                               f"Valid types are: {', '.join(valid_resp_types)}")

    def to_tcl(self) -> str:
        """
        Convert the VTKHDF recorder to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """

        # separete name and format of the file
        name = self.file_base_name.split(".")
        if len(name) <2:
            fileformat = "vtkhdf"
        else:
            fileformat = name[-1]
        name = name[0]
        name = name + "$pid"
        from femora import MeshMaker
        results_folder = MeshMaker.get_results_folder()
        if results_folder != "":
            name = results_folder + "/" + name
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
        
        
        
        return cmd

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this recorder
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("file_base_name", "Base name of the file to which output is sent"),
            ("resp_types", "List of strings indicating response types to record"),
            ("delta_t", "Time interval for recording"),
            ("r_tol_dt", "Relative tolerance for time step matching")
        ]

    def get_values(self) -> Dict[str, Union[str, list, float]]:
        """
        Get the parameters defining this recorder
        
        Returns:
            Dict[str, Union[str, list, float]]: Dictionary of parameter values
        """
        return {
            "file_base_name": self.file_base_name,
            "resp_types": self.resp_types,
            "delta_t": self.delta_t,
            "r_tol_dt": self.r_tol_dt
        }


class MPCORecorder(Recorder):
    """
    MPCO recorder writes model responses into an HDF5 database readable by STKO (\*.mpco).

    Command form (see official docs):
        recorder mpco $fileName \
            <-N nodeResponses...> \
            <-E elementResponses...> \
            <-NS name1 par1 name2 par2 ...> \
            <-R regionTag> ... \
            <-T dt $deltaTime | -T nsteps $numSteps>

    Reference: OpenSees MPCO Recorder documentation.
    """
    def __init__(self, **kwargs):
        """
        Initialize an MPCO Recorder

        Args:
            file_name (str): Output file name (e.g., "results.mpco")
            node_responses (List[str], optional): Node response names per docs
            element_responses (List[str], optional): Element/section/material response names
            node_sensitivities (List[tuple[str,int]] | List[dict], optional): Pairs of (name, parameterId)
            regions (List[int], optional): Region tags to record (can repeat)
            delta_t (float, optional): Recording time interval (mutually exclusive with num_steps)
            num_steps (int, optional): Recording step interval (mutually exclusive with delta_t)
        """
        super().__init__("MPCO")
        self.file_name = kwargs.get("file_name", "")
        self.node_responses = kwargs.get("node_responses", [])
        self.element_responses = kwargs.get("element_responses", [])
        self.node_sensitivities = kwargs.get("node_sensitivities", [])
        self.regions = self._resolve_regions(kwargs.get("regions", []))
        self.delta_t = kwargs.get("delta_t", None)
        self.num_steps = kwargs.get("num_steps", None)

        self.validate()

    def validate(self):
        """
        Validate MPCO recorder parameters
        """
        if not self.file_name:
            raise ValueError("File name must be specified for MPCO recorder")

        # Validate node responses against documented options
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

        # element_responses are model-dependent; accept strings if given
        if self.element_responses is None:
            self.element_responses = []
        if not isinstance(self.element_responses, list):
            raise TypeError("element_responses must be a list of strings")
        for er in self.element_responses:
            if not isinstance(er, str):
                raise TypeError("Each element response must be a string")

        # Validate node sensitivities: list of (name, param) pairs
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

        # Regions must be list of ints
        if self.regions is None:
            self.regions = []
        if not isinstance(self.regions, list):
            raise TypeError("regions must be a list of integers")
        for r in self.regions:
            if not isinstance(r, int):
                raise TypeError("Each region tag must be an integer")

        # Mutually exclusive time options
        if self.delta_t is not None and self.num_steps is not None:
            raise ValueError("Only one of delta_t or num_steps may be specified")

    def to_tcl(self) -> str:
        """
        Convert the MPCO recorder to a TCL command string for OpenSees

        Returns:
            str: The TCL command string
        """
        from femora import MeshMaker
        results_folder = MeshMaker.get_results_folder()
        file_path = self.file_name
        
        file_ext = self.file_name.split(".")[-1]
        # add $pid before the extension
        if len(self.file_name.split(".")) >1:
            file_path = self.file_name.replace("." + file_ext, "$pid." + file_ext)
        else:
            file_path = self.file_name + "$pid"

        if results_folder:
            file_path = results_folder + "/" + file_path

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

        if self.delta_t is not None:
            cmd += f" -T dt {self.delta_t}"
        elif self.num_steps is not None:
            cmd += f" -T nsteps {self.num_steps}"

        return cmd

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this recorder

        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("file_name", "Output file name (e.g., results.mpco)"),
            ("node_responses", "List of node responses to record (-N)"),
            ("element_responses", "List of element responses to record (-E)"),
            ("node_sensitivities", "List of (name,param) sensitivity pairs (-NS)"),
            ("regions", "Regions to record: tags, names, or RegionBase instances (-R)"),
            ("delta_t", "Recording time interval: -T dt <deltaTime> (mutually exclusive)"),
            ("num_steps", "Recording step interval: -T nsteps <numSteps> (mutually exclusive)"),
        ]

    def get_values(self) -> Dict[str, Union[str, list, float, int]]:
        """
        Get the parameters defining this recorder

        Returns:
            Dict[str, Union[str, list, float, int]]: Dictionary of parameter values
        """
        return {
            "file_name": self.file_name,
            "node_responses": self.node_responses,
            "element_responses": self.element_responses,
            "node_sensitivities": self.node_sensitivities,
            "regions": self.regions,
            "delta_t": self.delta_t,
            "num_steps": self.num_steps,
        }

class BeamForceRecorder(Recorder):
    """
    Specialized Element recorder for beam meshes to record forces.

    This recorder inspects the assembled mesh, resolves the element tags that
    correspond to selected beam mesh parts (line meshes), and emits one or more
    recorder Element commands per compute core.

    Args:

        meshparts (List[Union[str, int, object]]):
            MeshPart identifiers (user_name strings or MeshPart instances).
            If omitted or empty, all line mesh parts will be used.

        force_type (str): 'globalForce' or 'localForce'. Default: 'globalForce'.

        file_prefix (str): Prefix for output files. Default: 'Beam'.

        delta_t (float | None): Optional -dT value. Default: None.

        include_time (bool): Include -time flag. Default: True.

        output_format (str): 'file', 'xml', or 'binary' (-file/-xml/-binary). Default: 'file'.

        precision (int | None): Number of significant digits (-precision). Default: None.

    Raises:
        ValueError: If force_type is invalid or if specified meshparts are not found.
    
    Returns:
        BeamForceRecorder: An instance of the recorder.

    Example:
    '''
        import femora as fm
        fm.recorder = fm.BeamForceRecorder(
            meshparts=["BeamMeshPart1", "BeamMeshPart2"],
            force_type="localForce",
            file_prefix="MyBeamForces",
            delta_t=0.1,
            include_time=True
        )
    '''
    """
    def __init__(self, **kwargs):
        super().__init__("BeamForce")
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

    @staticmethod
    def get_parameters() -> List[tuple]:
        return [
            ("meshparts", "List of MeshPart names/instances to record (line meshes)"),
            ("force_type", "'globalForce' or 'localForce'"),
            ("file_prefix", "Output file prefix (default: 'Beam')"),
            ("delta_t", "Time interval: -dT <deltaTime> (optional)"),
            ("include_time", "Include -time flag (default: True)"),
            ("output_format", "'file', 'xml', or 'binary' (-file/-xml/-binary)"),
            ("precision", "Number of significant digits (-precision), optional"),
        ]

    def get_values(self) -> Dict[str, Union[str, list, float, bool]]:
        return {
            "meshparts": [mp if isinstance(mp, str) else getattr(mp, "user_name", str(mp)) for mp in (self.meshparts or [])],
            "force_type": self.force_type,
            "file_prefix": self.file_prefix,
            "delta_t": self.delta_t,
            "include_time": self.include_time,
            "output_format": self.output_format,
            "precision": self.precision,
        }

    def _resolve_meshparts(self):
        from femora.components.Mesh.meshPartBase import MeshPart
        if not self.meshparts:
            # Default to all line mesh parts
            return {name: part for name, part in MeshPart.get_mesh_parts().items() if part.category.lower() == "line mesh"}
        resolved: Dict[str, object] = {}
        for mp in self.meshparts:
            if isinstance(mp, str):
                part = MeshPart.get_mesh_parts().get(mp)
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

    def to_tcl(self) -> str:
        from femora import MeshMaker
        import numpy as np
        try:
            import pyvista as pv
        except Exception:
            pv = None

        mm = MeshMaker()
        assembled = mm.assembler.AssembeledMesh
        if assembled is None:
            raise ValueError("No assembled mesh found. Assemble the model before creating BeamForceRecorder.")

        results_folder = MeshMaker.get_results_folder()
        if results_folder != "":
            results_folder = results_folder + "/"

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
        mesh_tags = assembled.cell_data.get("MeshTag_cell")
        if mesh_tags is None or cores is None:
            raise ValueError("Assembled mesh missing required cell_data ('MeshTag_cell' or 'Core')")

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

    def _resolve_regions(self, regions_input: Union[int, str, RegionBase, List[Union[int, str, RegionBase]]]) -> List[int]:
        """
        Normalize provided regions to a list of integer tags.

        Accepts:
            - int tag
            - str name (matched against existing RegionBase.name)
            - RegionBase instance
            - list/tuple of the above
        """
        if regions_input is None:
            return []

        def resolve_one(item) -> int:
            if isinstance(item, int):
                return item
            if isinstance(item, RegionBase):
                return item.tag
            if isinstance(item, str):
                # Find by name
                for tag, region in RegionBase.get_all_regions().items():
                    if getattr(region, "name", None) == item:
                        return tag
                raise ValueError(f"Region with name '{item}' not found")
            raise TypeError("regions must contain ints, names, or RegionBase instances")

        tags: List[int] = []
        if isinstance(regions_input, (list, tuple)):
            for it in regions_input:
                tag = resolve_one(it)
                if tag not in tags:
                    tags.append(tag)
        else:
            tags = [resolve_one(regions_input)]
        return tags

class RecorderRegistry:
    """
    A registry to manage recorder types and their creation.
    """
    _recorder_types = {
        'node': NodeRecorder,
        'vtkhdf': VTKHDFRecorder,
        'mpco': MPCORecorder,
        'beam_force': BeamForceRecorder,
    }

    @classmethod
    def register_recorder_type(cls, name: str, recorder_class: Type[Recorder]):
        """
        Register a new recorder type for easy creation.
        
        Args:
            name (str): The name of the recorder type
            recorder_class (Type[Recorder]): The class of the recorder
        """
        cls._recorder_types[name.lower()] = recorder_class

    @classmethod
    def get_recorder_types(cls):
        """
        Get available recorder types.
        
        Returns:
            List[str]: Available recorder types
        """
        return list(cls._recorder_types.keys())

    @classmethod
    def create_recorder(cls, recorder_type: str, **kwargs) -> Recorder:
        """
        Create a new recorder of a specific type.
        
        Args:
            recorder_type (str): Type of recorder to create
            **kwargs: Parameters for recorder initialization
        
        Returns:
            Recorder: A new recorder instance
        
        Raises:
            KeyError: If the recorder type is not registered
        """
        if recorder_type.lower() not in cls._recorder_types:
            raise KeyError(f"Recorder type {recorder_type} not registered")
        
        return cls._recorder_types[recorder_type.lower()](**kwargs)


class RecorderManager:
    """
    Singleton class for managing recorders
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecorderManager, cls).__new__(cls)
        return cls._instance
        
        
    def __init__(self):
        """
        Initialize the RecorderManager and register recorder types.
        """
        # Register recorder types
        self.node = NodeRecorder    
        self.vtkhdf = VTKHDFRecorder
        self.mpco = MPCORecorder
        self.beam_force = BeamForceRecorder
        self.embedded_beam_solid_interface = EmbeddedBeamSolidInterfaceRecorder



    def create_recorder(self, recorder_type: str, **kwargs) -> Recorder:
        """Create a new recorder"""
        return RecorderRegistry.create_recorder(recorder_type, **kwargs)

    def get_recorder(self, tag: int) -> Recorder:
        """Get recorder by tag"""
        return Recorder.get_recorder(tag)

    def remove_recorder(self, tag: int) -> None:
        """Remove recorder by tag"""
        Recorder.remove_recorder(tag)

    def get_all_recorders(self) -> Dict[int, Recorder]:
        """Get all recorders"""
        return Recorder.get_all_recorders()

    def get_available_types(self) -> List[str]:
        """Get list of available recorder types"""
        return RecorderRegistry.get_recorder_types()
    
    def clear_all(self):
        """Clear all recorders"""  
        Recorder.clear_all()


# Example usage
if __name__ == "__main__":
    # Create a RecorderManager instance
    recorder_manager = RecorderManager()
    
    # Create a Node recorder
    node_recorder = recorder_manager.create_recorder(
        "node",
        file_name="nodesD.out",
        time=True,
        nodes=[1, 2, 3, 4],
        dofs=[1, 2],
        resp_type="disp"
    )
    
    # Output the TCL command
    print(node_recorder.to_tcl())
    
    # Create a VTKHDF recorder
    vtkhdf_recorder = recorder_manager.create_recorder(
        "vtkhdf",
        file_base_name="results",
        resp_types=["disp", "vel", "accel", "stress3D6", "strain3D6"],
        delta_t=0.1,
        r_tol_dt=0.00001
    )
    
    # Output the TCL command
    print(vtkhdf_recorder.to_tcl())