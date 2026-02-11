from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class SSPbrickElement(Element):
    """OpenSees 8-node stabilized single-point integration brick (SSPbrick).

    The SSPbrick element is an eight-node hexahedral 3D continuum element that
    uses a physically stabilized single-point integration scheme ("Stabilized
    Single Point"). The stabilization employs an enhanced assumed strain field
    to eliminate both volumetric and shear locking, improving coarse mesh
    accuracy for bending-dominated and nearly-incompressible problems while
    typically providing faster analysis times than full integration elements.
    """
    def __init__(self, ndof: int, material: Material, b1: float = 0.0, b2: float = 0.0, b3: float = 0.0, **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 3.
            material (Material): Associated OpenSees material. Must have
                material_type == 'nDMaterial' (3D material).
            b1 (float, optional): Constant body force in global x-direction. 
                Defaults to 0.0.
            b2 (float, optional): Constant body force in global y-direction. 
                Defaults to 0.0.
            b3 (float, optional): Constant body force in global z-direction. 
                Defaults to 0.0.

        Raises:
            ValueError: If the material is incompatible, ndof != 3, or any
                provided parameter is invalid.

        OpenSees command syntax:
            ``element SSPbrick $tag $n1 $n2 $n3 $n4 $n5 $n6 $n7 $n8 $matTag [$b1 $b2 $b3]``

        Notes:
            1. Body forces are constant in the global coordinate directions and
               default to 0.0 when omitted.
            2. Recorder queries (e.g. ``stress``, ``strain``) correspond to those of
               the assigned ``nDMaterial`` and are evaluated at the single
               integration point located at the element center.
            3. Designed to duplicate functionality of ``stdBrick``; report any
               discrepancies to developers.
            
            Reference:
                SSPbrick Element documentation – https://opensees.berkeley.edu/wiki/index.php/SSPbrick_Element

        Example:
            ```python
            element = SSPbrickElement(ndof=3, material=my_material, b3=-9.81)
            ```
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} is not compatible with SSPbrickElement"
            )
        if ndof != 3:
            raise ValueError(f"SSPbrickElement requires 3 DOFs, but got {ndof}")
        
        # Validate parameters
        params = {"b1": b1, "b2": b2, "b3": b3}
        validated = self.validate_element_parameters(**params)
        
        super().__init__('SSPbrick', ndof, material, **kwargs)
        
        # specific attributes
        self.b1 = validated.get("b1", 0.0)
        self.b2 = validated.get("b2", 0.0)
        self.b3 = validated.get("b3", 0.0)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this SSPbrick element.

        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.

        Returns:
            str: TCL command of the form:
                ``element SSPbrick <tag> <n1> ... <n8> <matTag> [b1] [b2] [b3]``

        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDs.
        """
        if len(nodes) != 8:
            raise ValueError("SSPbrick element requires 8 nodes")
        
        nodes_str = " ".join(str(node) for node in nodes)
        cmd = f"element SSPbrick {tag} {nodes_str} {self._material.tag}"
        
        if self.b3 != 0.0:
            cmd += f" {self.b1} {self.b2} {self.b3}"
        elif self.b2 != 0.0:
            cmd += f" {self.b1} {self.b2}"
        elif self.b1 != 0.0:
            cmd += f" {self.b1}"
            
        return cmd

    @classmethod
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names for SSPbrick.

        Returns:
            List[str]: ``["b1", "b2", "b3"]``.
        """
        return ["b1", "b2", "b3"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element.

        Returns:
            List[str]: Descriptions aligned with :meth:`get_parameters`.
        """
        return [
            'Constant body force in global x direction',
            'Constant body force in global y direction',
            'Constant body force in global z direction'
        ]

    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node for this element.

        Returns:
            List[str]: ``['3']``.
        """
        return ['3']

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters.

        Args:
            keys: Parameter names to retrieve.

        Returns:
            Dict: standard key-value pairs.
        """
        values = {}
        for key in keys:
            if key == "b1": values[key] = self.b1
            elif key == "b2": values[key] = self.b2
            elif key == "b3": values[key] = self.b3
        return values
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update element parameters."""
        sanitized = self.validate_element_parameters(**values)
        if "b1" in sanitized: self.b1 = sanitized["b1"]
        if "b2" in sanitized: self.b2 = sanitized["b2"]
        if "b3" in sanitized: self.b3 = sanitized["b3"]

    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate and coerce SSPbrick parameters.

        Optional parameters ``b1``, ``b2`` and ``b3`` are converted to ``float``
        if provided.

        Args:
            **kwargs: Raw parameter mapping.

        Returns:
            Dict[str, Union[int, float, str]]: Validated parameter mapping.

        Raises:
            ValueError: If any provided body force cannot be converted to
                ``float``.
        """
        for key in ["b1", "b2", "b3"]:
            if key in kwargs:
                try:
                    kwargs[key] = float(kwargs.get(key, 0.0))
                except (ValueError, TypeError):
                    raise ValueError(f"{key} must be a float number")
        return kwargs

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with SSPbrick.

        Requires an OpenSees 3D ``nDMaterial``.

        Args:
            material: Material instance to check.

        Returns:
            bool: ``True`` if ``material.material_type == 'nDMaterial'``.
        """
        return material.material_type == 'nDMaterial'

ElementRegistry.register_element_type('SSPbrick', SSPbrickElement)
