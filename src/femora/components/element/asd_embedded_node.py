from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class ASDEmbeddedNodeElement3D(Element):
    """
    OpenSees ASDEmbeddedNodeElement for 3D problems.

    This element is used to constrain a node (constrained node) to a domain
    defined by 3 or 4 retained nodes. For 3D Solid domains, 4 retained nodes
    forming a tetrahedron are used.
    """

    def __init__(
        self, 
        ndof: int, 
        rot: bool = False, 
        p: bool = False, 
        K: Optional[float] = None, 
        KP: Optional[float] = None, 
        contact: bool = False, 
        Kn: float = 1.0e8, 
        Kt: float = 1.0e8, 
        mu: float = 0.5, 
        orient: list = None, 
        orient_map: dict = None, 
        int_type: int = 1,
        **kwargs
    ):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3, 4, or 6.
            rot (bool, optional): Optional flag to constrain rotations. 
                Defaults to False.
            p (bool, optional): Optional flag to constrain pressure. 
                Defaults to False.
            K (float, optional): User-defined penalty stiffness. 
                Defaults to 1.0e18.
            KP (float, optional): User-defined penalty stiffness for pressure. 
                Defaults to 1.0e18.
            contact (bool, optional): Optional flag to enable frictional contact. 
                Defaults to False.
            Kn (float, optional): Penalty stiffness for normal contact. 
                Defaults to 1.0e8.
            Kt (float, optional): Penalty stiffness for tangential contact. 
                Defaults to 1.0e8.
            mu (float, optional): Friction coefficient. 
                Defaults to 0.5.
            orient (list, optional): Orientation vector if orient_map is None. 
                Defaults to [1, 0, 0].
            orient_map (dict, optional): Orientation mapping. 
                Defaults to None.
            int_type (int, optional): Integration type (0: Implicit, 1: IMPL-EX). 
                Defaults to 1.

        OpenSees command syntax:
            ``element ASDEmbeddedNodeElement $eleTag $Cnode $Rnode1 $Rnode2 $Rnode3 $Rnode4 [-rot] [-p] [-K $K] [-KP $KP] [ -contact $Kn $Kt $mu [-orient $orient] [-int_type $int_type]]``

        Notes:
            ``1) Using ASDEmbeddedNodeElement3D is solely for 3D problems could be very hard. This element is implemented to use with EmbeddedNodeInterFace element.``

        Example:
            ```python
            element = ASDEmbeddedNodeElement3D(ndof=6, rot=True)
            print(element.rot)
            ```
        """
        if ndof not in [3, 4, 6]:
            raise ValueError(f"ASDEmbeddedNodeElement3D requires 3, 4, or 6 DOFs, but got {ndof}")
        
        # Validate and coerce parameters
        params = {
            "rot": rot, "p": p, "K": K, "KP": KP, "contact": contact,
            "Kn": Kn, "Kt": Kt, "mu": mu, "orient": orient,
            "orient_map": orient_map, "int_type": int_type
        }
        validated = self.validate_element_parameters(**params)
        
        super().__init__('ASDEmbeddedNodeElement', ndof, material=None, **kwargs)
        
        self.rot = validated.get("rot", False)
        self.p = validated.get("p", False)
        self.K = validated.get("K")
        self.KP = validated.get("KP")
        self.contact = validated.get("contact", False)
        self.Kn = validated.get("Kn", 1.0e8)
        self.Kt = validated.get("Kt", 1.0e8)
        self.mu = validated.get("mu", 0.5)
        self.orient = validated.get("orient")
        self.orient_map = validated.get("orient_map")
        self.int_type = validated.get("int_type", 1)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command.
        
        Args:
            tag: Element tag.
            nodes: List of nodes [Cnode, Rnode1, Rnode2, Rnode3, Rnode4].
        
        Returns:
            str: TCL command string.
        """
        if len(nodes) != 5:
            raise ValueError("ASDEmbeddedNodeElement3D requires 5 nodes (1 constrained, 4 retained)")
        
        nodes_str = " ".join(str(node) for node in nodes)
        cmd = f"element ASDEmbeddedNodeElement {tag} {nodes_str}"
        
        if self.rot:
            cmd += " -rot"
        if self.p:
            cmd += " -p"
        if self.K is not None:
            cmd += f" -K {self.K}"
        if self.KP is not None:
            cmd += f" -KP {self.KP}"
        
        if self.contact:
            cmd += f" -contact {self.Kn} {self.Kt} {self.mu}"
            
            # Orientation
            orient = None
            if self.orient_map and nodes[0] in self.orient_map:
                orient = self.orient_map[nodes[0]]
            elif self.orient:
                orient = self.orient
            
            if orient:
                cmd += f" -orient {orient[0]} {orient[1]} {orient[2]}"
                
            cmd += f" -int_type {self.int_type}"
            
        return cmd

    @classmethod
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names."""
        return ["rot", "p", "K", "KP", "contact", "Kn", "Kt", "mu", "orient", "orient_map", "int_type"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element."""
        return [
            "Constrain rotational DOFs",
            "Constrain pressure DOFs",
            "Penalty stiffness",
            "Penalty stiffness for pressure",
            "Enable frictional contact",
            "Penalty stiffness for normal contact",
            "Penalty stiffness for tangential contact",
            "Friction coefficient",
            "Orientation vector [nx, ny, nz]",
            "Orientation mapping {nodeTag: [nx, ny, nz]}",
            "Integration type (0: Implicit, 1: IMPL-EX)"
        ]

    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node."""
        return ["3", "4", "6"]

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters."""
        return {key: getattr(self, key) for key in keys if hasattr(self, key)}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update element parameters."""
        for key, value in values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate and coerce parameters."""
        if "rot" in kwargs:
            kwargs["rot"] = bool(kwargs["rot"])
        if "p" in kwargs:
            kwargs["p"] = bool(kwargs["p"])
        if "K" in kwargs:
            # if K is None skip
            if kwargs["K"] is not None:
                try:
                    kwargs["K"] = float(kwargs["K"])
                except (ValueError, TypeError):
                    raise ValueError("K must be a float number")
            else:
                del kwargs["K"]
        if "KP" in kwargs:
            if kwargs["KP"] is not None:
                try:
                    kwargs["KP"] = float(kwargs["KP"])
                except (ValueError, TypeError):
                    raise ValueError("KP must be a float number")
            else:
                del kwargs["KP"]
        if "contact" in kwargs:
            kwargs["contact"] = bool(kwargs["contact"])
        if "Kn" in kwargs:
            kwargs["Kn"] = float(kwargs["Kn"])
        if "Kt" in kwargs:
            kwargs["Kt"] = float(kwargs["Kt"])
        if "mu" in kwargs:
            kwargs["mu"] = float(kwargs["mu"])
        if "orient" in kwargs and kwargs["orient"] is not None:
            if not isinstance(kwargs["orient"], (list, tuple)) or len(kwargs["orient"]) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            kwargs["orient"] = [float(x) for x in kwargs["orient"]]
        if "orient_map" in kwargs and kwargs["orient_map"] is not None:
            if not isinstance(kwargs["orient_map"], dict):
                raise ValueError("orient_map must be a dictionary")
            # Minimal validation for orient_map
            new_map = {}
            for k, v in kwargs["orient_map"].items():
                if not isinstance(v, (list, tuple)) or len(v) != 3:
                     raise ValueError(f"orient_map value for node {k} must be a list/tuple of 3 floats")
                new_map[k] = [float(x) for x in v]
            kwargs["orient_map"] = new_map
        if "int_type" in kwargs:
            kwargs["int_type"] = int(kwargs["int_type"])
            if kwargs["int_type"] not in [0, 1]:
                raise ValueError("int_type must be 0 or 1")
        elif kwargs.get("contact"):
            kwargs["int_type"] = 1
        return kwargs

ElementRegistry.register_element_type('ASDEmbeddedNodeElement3D', ASDEmbeddedNodeElement3D)
