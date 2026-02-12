from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class stdBrickElement(Element):
    """OpenSees 8-node standard brick element (3D continuum).

    This element requires a 3D ``nDMaterial`` and exactly 3 DOFs per node.
    Optional body forces ``b1``, ``b2``, and ``b3`` may be supplied. A
    ``-lumped`` mass option can also be enabled via the boolean parameter
    ``lumped``.
    """
    def __init__(self, ndof: int, material: Material, b1: float = 0.0, b2: float = 0.0, b3: float = 0.0, lumped: bool = False, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial'.
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.
            b3 (float, optional): Constant body force in global z-direction. 
                Defaults to 0.0.
            lumped (bool, optional): If True, append the -lumped flag
                to use a lumped mass matrix. Defaults to False.

        Raises:
            ValueError: If the material is incompatible, ndof != 3, or any
                provided parameter is invalid.

        OpenSees command syntax:
            ``element stdBrick $tag $n1 $n2 $n3 $n4 $n5 $n6 $n7 $n8 $matTag [$b1 $b2 $b3] [-lumped]``

        Example:
            ```python
            element = stdBrickElement(ndof=3, material=mat, b3=-9.81, lumped=True)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with stdBrickElement")
        
        # Validate DOF requirement
        if ndof != 3:
            raise ValueError(f"stdBrickElement requires 3 DOFs, but got {ndof}")
        
        # Validate element parameters
        params = {"b1": b1, "b2": b2, "b3": b3, "lumped": lumped}
        validated = self.validate_element_parameters(**params)
            
        super().__init__('stdBrick', ndof, material, **kwargs)
        
        self.b1 = validated.get("b1", 0.0)
        self.b2 = validated.get("b2", 0.0)
        self.b3 = validated.get("b3", 0.0)
        self.lumped = validated.get("lumped", False)
        
    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this stdBrick element.
        
        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.
        
        Returns:
            str: A TCL command of the form:
                 ``element stdBrick <tag> <n1> ... <n8> <matTag> [b1] [b2] [b3]``
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDs.
        """
        if len(nodes) != 8:
            raise ValueError("stdBrick element requires 8 nodes")

        # Build base command
        nodes_str = " ".join(str(node) for node in nodes)
        elestr = f"element stdBrick {tag} {nodes_str} {self._material.tag}"

        # Optional numeric body forces
        if self.b3 != 0.0:
             elestr += f" {self.b1} {self.b2} {self.b3}"
        elif self.b2 != 0.0:
             elestr += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
             elestr += f" {self.b1}"

        # Optional '-lumped' flag
        if self.lumped:
            elestr += " -lumped"

        return elestr

    @classmethod
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names for stdBrick.
        
        Returns:
            List[str]: ``["b1", "b2", "b3", "lumped"]``.
        """
        return ["b1", "b2", "b3", "lumped"]
    
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters.
        
        Args:
            keys: Parameter names to retrieve; see :meth:`get_parameters`.
        
        Returns:
            Dict[str, Union[int, float, str]]: Mapping from key to stored value
            (or ``None`` if not present).
        """
        values = {}
        for key in keys:
            if key == "b1": values[key] = self.b1
            elif key == "b2": values[key] = self.b2
            elif key == "b3": values[key] = self.b3
            elif key == "lumped": values[key] = self.lumped
        return values
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping.
        """
        params = {"b1": self.b1, "b2": self.b2, "b3": self.b3, "lumped": self.lumped}
        params.update(values)
        validated = self.validate_element_parameters(**params)
        
        if "b1" in validated: self.b1 = validated["b1"]
        if "b2" in validated: self.b2 = validated["b2"]
        if "b3" in validated: self.b3 = validated["b3"]
        if "lumped" in validated: self.lumped = validated["lumped"]

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with stdBrick.
        
        stdBrick requires an OpenSees 3D ``nDMaterial``.
        
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
            List[str]: ``['3']``.
        """
        return ['3']
    
    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element.
        
        Returns:
            List[str]: Human-readable descriptions in the same order as
            :meth:`get_parameters`.
        """
        return ['Constant body forces in global x direction',
                'Constant body forces in global y direction',
                'Constant body forces in global z direction',
                'Use lumped mass matrix (optional flag)']
    
    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate and coerce stdBrick parameters.
        
        ``b1``, ``b2`` and ``b3`` are optional but, if provided, must be
        convertible to ``float``. ``lumped`` is an optional boolean flag.

        Args:
            **kwargs: Raw parameter mapping.

        Returns:
            Dict[str, Union[int, float, str]]: Validated and coerced parameters.

        Raises:
            ValueError: If a value cannot be coerced to ``float``.
        """
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
        
        if "b3" in kwargs:
            try:
                kwargs['b3'] = float(kwargs['b3'])
            except ValueError:
                raise ValueError("b3 must be a float number")

        # Optional '-lumped' flag
        if "lumped" in kwargs:
            val = kwargs["lumped"]
            if isinstance(val, bool):
                kwargs["lumped"] = val
            elif isinstance(val, (int, float)):
                kwargs["lumped"] = bool(int(val))
            elif isinstance(val, str):
                sval = val.strip().lower()
                if sval in ["1", "true", "t", "yes", "y", "on"]:
                    kwargs["lumped"] = True
                elif sval in ["0", "false", "f", "no", "n", "off", ""]:
                    kwargs["lumped"] = False
                else:
                    raise ValueError("lumped must be a boolean (true/false)")
            else:
                raise ValueError("lumped must be a boolean (true/false)")
            
        return kwargs

ElementRegistry.register_element_type('stdBrick', stdBrickElement)
