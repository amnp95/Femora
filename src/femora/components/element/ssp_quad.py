from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class SSPQuadElement(Element):
    """OpenSees 4-node stabilized single-point integration quadrilateral (SSPquad).

    This element represents a 2D continuum element that can operate in
    PlaneStrain or PlaneStress. It requires materials of type ``nDMaterial``
    and exactly 2 DOFs per node.
    """
    def __init__(self, ndof: int, material: Material, Type: str, Thickness: float, b1: float = 0.0, b2: float = 0.0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 2.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial'.
            Type (str): Either 'PlaneStrain' or 'PlaneStress'. Required.
            Thickness (float): Element thickness (out-of-plane). Required.
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.

        Raises:
            ValueError: If the material is incompatible, ndof != 2, or any
                parameter is missing/invalid.

        OpenSees command syntax:
            ``element SSPquad $tag $n1 $n2 $n3 $n4 $matTag $Type $Thickness [$b1 $b2]``

        Example:
            ```python
            element = SSPQuadElement(ndof=2, material=mat, Type='PlaneStrain', Thickness=1.0)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with SSPQuadElement")
        
        # Validate DOF requirement
        if ndof != 2:
            raise ValueError(f"SSPQuadElement requires 2 DOFs, but got {ndof}")
        
        # Validate element parameters
        params = {"Type": Type, "Thickness": Thickness, "b1": b1, "b2": b2}
        validated = self.validate_element_parameters(**params)
            
        super().__init__('SSPQuad', ndof, material, **kwargs)
        
        self.Type = validated["Type"]
        self.Thickness = validated["Thickness"]
        self.b1 = validated.get("b1", 0.0)
        self.b2 = validated.get("b2", 0.0)


    def __str__(self):
        """Return a compact string with material tag and parameters.
        
        Returns:
            str: String representation.
        """
        params_str = f"{self.Type} {self.Thickness}"
        if self.b2 != 0.0:
            params_str += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            params_str += f" {self.b1}"
            
        return f"{self._material.tag} {params_str}"
    
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this SSPquad element.
        
        Args:
            tag: Unique element tag.
            nodes: List of 4 node tags in counter-clockwise order.
        
        Returns:
            str: A TCL command of the form:
                 ``element SSPquad <tag> <n1> <n2> <n3> <n4> <matTag> <Type> <Thickness> [b1] [b2]``
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 4 node IDs.
        """
        if len(nodes) != 4:
            raise ValueError("SSPQuad element requires 4 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        tag = str(tag)
        
        cmd = f"element SSPquad {tag} {nodes_str} {self._material.tag} {self.Type} {self.Thickness}"
        
        if self.b2 != 0.0:
            cmd += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            cmd += f" {self.b1}"
            
        return cmd
    
    @classmethod 
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names for SSPQuad.
        
        Returns:
            List[str]: ``["Type", "Thickness", "b1", "b2"]``.
        """
        return ["Type", "Thickness", "b1", "b2"]

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters.
        
        Args:
            keys: Parameter names to retrieve; see :meth:`get_parameters`.
        
        Returns:
            Dict: standard key-value pairs.
        """
        values = {}
        for key in keys:
            if key == "Type": values[key] = self.Type
            elif key == "Thickness": values[key] = self.Thickness
            elif key == "b1": values[key] = self.b1
            elif key == "b2": values[key] = self.b2
        return values

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping.
        """
        # We need to preserve existing values if not provided
        current_params = {
            "Type": self.Type, 
            "Thickness": self.Thickness, 
            "b1": self.b1, 
            "b2": self.b2
        }
        current_params.update(values)
        
        validated = self.validate_element_parameters(**current_params)
        
        self.Type = validated["Type"]
        self.Thickness = validated["Thickness"]
        if "b1" in validated: self.b1 = validated["b1"]
        if "b2" in validated: self.b2 = validated["b2"]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate and coerce SSPQuad parameters.

        The following rules apply:
        - ``Type`` must be ``'PlaneStrain'`` or ``'PlaneStress'`` (required).
        - ``Thickness`` must be convertible to ``float`` (required).
        - ``b1`` and ``b2`` are optional but, if provided, must be ``float``.

        Args:
            **kwargs: Raw parameter mapping.

        Returns:
            Dict[str, Union[int, float, str]]: Validated and coerced parameters.

        Raises:
            ValueError: If a required parameter is missing or a value cannot be
                coerced/validated.
        """
        if 'Type' not in kwargs:
            raise ValueError("Type of element must be specified")
        elif kwargs['Type'] not in ['PlaneStrain', 'PlaneStress']:
            raise ValueError("Element type must be either 'PlaneStrain' or 'PlaneStress'")
        
        if "Thickness" not in kwargs:
            raise ValueError("Thickness must be specified")
        else:
            try:
                kwargs['Thickness'] = float(kwargs['Thickness'])
            except ValueError:
                raise ValueError("Thickness must be a float number")
        
        if "b1" in kwargs:
            try:
                kwargs['b1'] = float(kwargs['b1'])
            except ValueError:
                raise ValueError("b1 must be a float number")
        
        if "b2" in kwargs:
            try:
                kwargs['b2'] = float(kwargs['b2'])
            except ValueError:
                raise ValueError("b2 must be a float number")
            
        return kwargs


    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with SSPQuad.
        
        SSPQuad requires an OpenSees ``nDMaterial``.
        
        Args:
            material: Material instance to check.
        
        Returns:
            bool: ``True`` if ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == 'nDMaterial'
    
    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node for this element.
        
        Returns:
            List[str]: ``['2']``.
        """
        return ['2']
    
    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element.
        
        Returns:
            List[str]: Human-readable descriptions in the same order as
            :meth:`get_parameters`.
        """
        return ['Type of element can be either "PlaneStrain" or "PlaneStress" ', 
                'Thickness of the element in out-of-plane direction ',
                'Constant body forces in global x direction',
                'Constant body forces in global y direction'] 

ElementRegistry.register_element_type('SSPQuad', SSPQuadElement)
