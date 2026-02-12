from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class ZeroLengthContactASDimplex(Element):
    """OpenSees ZeroLengthContactASDimplex Element.

    This element is used to model contact between two nodes. It supports
    normal and tangential stiffness, and friction.
    """

    def __init__(self, ndof: int, Kn: float, Kt: float, mu: float, material: Material = None, orient: List[float] = None, intType: int = 0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node.
            Kn (float): Penalty stiffness for normal contact.
            Kt (float): Penalty stiffness for tangential contact.
            mu (float): Friction coefficient using Mohr-Coulomb friction.
            material (Material, optional): Not used by this element, but required by base class signature.
                Defaults to None.
            orient (List[float], optional): Orientation vector [nx, ny, nz].
            intType (int, optional): Integration type (0: Implicit, 1: IMPL-EX). Defaults to 0.

        Raises:
            ValueError: If parameters are invalid.

        OpenSees command syntax:
             ``element zeroLengthContactASDimplex $tag $n1 $n2 $Kn $Kt $mu [-orient $nx $ny $nz] [-intType $type]``

        Example:
            ```python
            element = ZeroLengthContactASDimplex(ndof=3, Kn=1e8, Kt=1e8, mu=0.5)
            ```
        """
        super().__init__('ZeroLengthContactASDimplex', ndof, material=None, **kwargs)
        
        # Store required params
        self.params = {
            'Kn': float(Kn),
            'Kt': float(Kt),
            'mu': float(mu)
        }
        
        if intType != 0:
            self.params['intType'] = int(intType)
        
        # Store optional path
        if orient is not None:
             # Validate orient
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            try:
                self.params['orient'] = [float(x) for x in orient]
            except (ValueError, TypeError):
                raise ValueError("orient components must be floats")

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this element.

        Args:
            tag: Unique element tag.
            nodes: List of 2 node tags.

        Returns:
            str: TCL command string.
        """
        if len(nodes) != 2:
            raise ValueError("ZeroLengthContactASDimplex element requires 2 nodes")
        
        cmd = f"element zeroLengthContactASDimplex {tag} {nodes[0]} {nodes[1]} {self.params['Kn']} {self.params['Kt']} {self.params['mu']}"
        
        if 'orient' in self.params:
            orient = self.params['orient']
            cmd += f" -orient {orient[0]} {orient[1]} {orient[2]}"
            
        if 'intType' in self.params:
            cmd += f" -intType {self.params['intType']}"
            
        return cmd

    @classmethod
    def get_parameters(cls) -> List[str]:
        return ["Kn", "Kt", "mu", "intType", "orient"]

    @classmethod
    def get_description(cls) -> List[str]:
        return [
            "Penalty stiffness for normal contact",
            "Penalty stiffness for tangential contact",
            "Friction coefficient",
            "Integration type (0: Implicit, 1: IMPL-EX)",
            "Orientation vector [nx, ny, nz] (optional)"
        ]

    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        # Supports 2D (2, 3 DOFs) and 3D (3, 4, 6 DOFs)
        return ['2', '3', '4', '6']

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str, List[float]]]:
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str, List[float]]]) -> None:
        self.params.update(values)

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str, List[float]]]:
        # Validate optional parameters
        if 'intType' in kwargs:
            try:
                kwargs['intType'] = int(kwargs['intType'])
                if kwargs['intType'] not in [0, 1]:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValueError("intType must be 0 or 1")
                
        if 'orient' in kwargs:
            orient = kwargs['orient']
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            try:
                kwargs['orient'] = [float(x) for x in orient]
            except (ValueError, TypeError):
                raise ValueError("orient components must be floats")
                
        return kwargs

ElementRegistry.register_element_type('ZeroLengthContactASDimplex', ZeroLengthContactASDimplex)
