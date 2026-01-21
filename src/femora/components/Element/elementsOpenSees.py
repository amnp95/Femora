from typing import Dict, List, Union
from ..Material.materialBase import Material
from .elementBase import Element, ElementRegistry


class SSPbrickElement(Element):
    """OpenSees 8-node stabilized single-point integration brick (SSPbrick).

    The SSPbrick element is an eight-node hexahedral 3D continuum element that
    uses a physically stabilized single-point integration scheme ("Stabilized
    Single Point"). The stabilization employs an enhanced assumed strain field
    to eliminate both volumetric and shear locking, improving coarse mesh
    accuracy for bending-dominated and nearly-incompressible problems while
    typically providing faster analysis times than full integration elements.

    OpenSees command syntax:
        ``element SSPbrick <tag> <n1> <n2> <n3> <n4> <n5> <n6> <n7> <n8> <matTag> [b1] [b2] [b3]``

    Where the 8 node tags are provided in counter-clockwise order using the
    same numbering scheme as the standard brick (``stdBrick``) element.

    Parameters can be supplied at construction time via ``**kwargs`` and are
    validated by :meth:`validate_element_parameters`.

    Attributes:
        params (Dict[str, Union[int, float, str]]): Validated element parameters
            (optional body forces ``b1``, ``b2``, ``b3``).

    Notes:
        - Body forces are constant in the global coordinate directions and
          default to 0.0 when omitted.
        - Recorder queries (e.g. ``stress``, ``strain``) correspond to those of
          the assigned ``nDMaterial`` and are evaluated at the single
          integration point located at the element center.
        - Designed to duplicate functionality of ``stdBrick``; report any
          discrepancies to developers.

    Reference:
        SSPbrick Element documentation – https://opensees.berkeley.edu/wiki/index.php/SSPbrick_Element
    """
    def __init__(self, ndof: int, material: Material, **kwargs):
        """Initialize an SSPbrick element.

        Args:
            ndof: Number of degrees of freedom per node. Must be ``3``.
            material: Associated OpenSees material. Must have
                ``material_type == 'nDMaterial'`` (3D material).
            **kwargs: Optional parameters:
                - ``b1`` (float): Constant body force in global x-direction.
                - ``b2`` (float): Constant body force in global y-direction.
                - ``b3`` (float): Constant body force in global z-direction.

        Raises:
            ValueError: If the material is incompatible, ``ndof`` != 3, or any
                provided parameter is invalid.
        """
        if not self._is_material_compatible(material):
            raise ValueError(
                f"Material {material.user_name} with type {material.material_type} is not compatible with SSPbrickElement"
            )
        if ndof != 3:
            raise ValueError(f"SSPbrickElement requires 3 DOFs, but got {ndof}")
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
        super().__init__('SSPbrick', ndof, material)
        self.params = kwargs if kwargs else {}

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
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        nodes_str = " ".join(str(node) for node in nodes)
        return f"element SSPbrick {tag} {nodes_str} {self._material.tag} {params_str}".rstrip()

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
            keys: Parameter names to retrieve; see :meth:`get_parameters`.

        Returns:
            Dict[str, Union[int, float, str]]: Mapping from key to stored value
            (or ``None`` if not present).
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.

        Args:
            values: New parameter mapping. Any previously stored parameter not
                present in this mapping will be removed.
        """
        self.params.clear()
        self.params.update(values)

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
                    kwargs[key] = float(kwargs.get(key,0.0))
                except (ValueError, TypeError):
                    raise ValueError(f"{key} must be a float number")
        return kwargs
    
    
class SSPQuadElement(Element):
    """OpenSees 4-node stabilized single-point integration quadrilateral (SSPquad).

    This element represents a 2D continuum element that can operate in
    PlaneStrain or PlaneStress. It requires materials of type ``nDMaterial``
    and exactly 2 DOFs per node.

    Parameters can be supplied at construction time via ``**kwargs`` and are
    validated by :meth:`validate_element_parameters`.

    Attributes:
        params (Dict[str, Union[int, float, str]]): Validated element parameters
            such as ``Type``, ``Thickness``, ``b1`` and ``b2``.
    """
    def __init__(self, ndof: int, material: Material, **kwargs):
        """Initialize an SSPQuad element.

        Args:
            ndof: Number of degrees of freedom per node. Must be ``2``.
            material: Associated OpenSees material. Must have
                ``material_type == 'nDMaterial'``.
            **kwargs: Element parameters. Supported keys are:
                - ``Type`` (str): Either ``'PlaneStrain'`` or ``'PlaneStress'``. Required.
                - ``Thickness`` (float): Element thickness (out-of-plane). Required.
                - ``b1`` (float): Constant body force in global x-direction. Optional.
                - ``b2`` (float): Constant body force in global y-direction. Optional.

        Raises:
            ValueError: If the material is incompatible, ``ndof`` != 2, or any
                parameter is missing/invalid.
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with SSPQuadElement")
        
        # Validate DOF requirement
        if ndof != 2:
            raise ValueError(f"SSPQuadElement requires 2 DOFs, but got {ndof}")
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        super().__init__('SSPQuad', ndof, material)
        self.params = kwargs if kwargs else {}


    def __str__(self):
        """Return a compact string with material tag and parameters.

        This is not a full TCL command. Use :meth:`to_tcl` to generate an
        executable OpenSees command string.

        ElementRegistry.register_element_type('SSPbrick', SSPbrickElement)
        Returns:
            str: ``"<matTag> <paramValues>"`` where parameters are ordered as
            in :meth:`get_parameters` and included only if present.

        Example:
            ``"10 PlaneStrain 0.2 0.0 0.0"``
        """
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)

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
        
        Example:
            ``element SSPquad 1 1 2 3 4 10 PlaneStress 0.2 0.0 0.0``
        """
        if len(nodes) != 4:
            raise ValueError("SSPQuad element requires 4 nodes")
        keys = self.get_parameters()
        params_str = " ".join(str(self.params[key]) for key in keys if key in self.params)
        nodes_str = " ".join(str(node) for node in nodes)
        tag = str(tag)
        return f"element SSPquad {tag} {nodes_str} {self._material.tag} {params_str}"
    
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
            Dict[str, Union[int, float, str]]: Mapping from key to stored value
            (or ``None`` if not present).
        """
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping. Any previously stored parameter not
                present in this mapping will be removed.
        """
        self.params.clear()
        self.params.update(values)
        # print(f"Updated parameters: {self.params} \nmaterial:{self._material} \nndof:{self._ndof}")

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


class stdBrickElement(Element):
    """OpenSees 8-node standard brick element (3D continuum).

    This element requires a 3D ``nDMaterial`` and exactly 3 DOFs per node.
    Optional body forces ``b1``, ``b2``, and ``b3`` may be supplied. A
    ``-lumped`` mass option can also be enabled via the boolean parameter
    ``lumped``.

    Attributes:
        params (Dict[str, Union[int, float, str]]): Validated parameters such as
            ``b1``, ``b2``, ``b3``.
    """
    def __init__(self, ndof: int, material: Material, **kwargs):
        """Initialize a stdBrick element.

        Args:
            ndof: Number of degrees of freedom per node. Must be ``3``.
            material: Associated OpenSees material. Must have
                ``material_type == 'nDMaterial'``.
            **kwargs: Optional parameters:
                - ``b1`` (float): Constant body force in global x-direction.
                - ``b2`` (float): Constant body force in global y-direction.
                                - ``b3`` (float): Constant body force in global z-direction.
                                - ``lumped`` (bool): If ``True``, append the ``-lumped`` flag
                                    to use a lumped mass matrix (optional, default ``False``).

        Raises:
            ValueError: If the material is incompatible, ``ndof`` != 3, or any
                provided parameter is invalid.
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with stdBrickElement")
        
        # Validate DOF requirement
        if ndof != 3:
            raise ValueError(f"stdBrickElement requires 3 DOFs, but got {ndof}")
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        super().__init__('stdBrick', ndof, material)
        self.params = kwargs if kwargs else {}
        
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
        bparts: List[str] = []
        if 'b1' in self.params:
            bparts.append(str(self.params['b1']))
        if 'b2' in self.params:
            bparts.append(str(self.params['b2']))
        if 'b3' in self.params:
            bparts.append(str(self.params['b3']))
        if bparts:
            elestr += " " + " ".join(bparts)

        # Optional '-lumped' flag
        if bool(self.params.get('lumped', False)):
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
        return {key: self.params.get(key) for key in keys}
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping. Any previously stored parameter not
                present in this mapping will be removed.
        """
        self.params.clear()
        self.params.update(values)

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


class PML3DElement(Element):
    """OpenSees 8-node Perfectly Matched Layer (PML) 3D element.

    This element augments the standard brick element with PML degrees of
    freedom (9 DOFs per node). It requires an isotropic elastic 3D
    ``nDMaterial`` (class name ``ElasticIsotropicMaterial``) and supports two
    mesh types (``box`` and ``general``) with associated parameters.

    Attributes:
        params (Dict[str, Union[int, float, str]]): Validated parameters such as
            ``PML_Thickness``, ``meshType``, ``meshTypeParameters``, and Newmark
            and PML control parameters.
    """
    def __init__(self, ndof: int, material: Material, **kwargs):
        """Initialize a PML3D element.

        Args:
            ndof: Number of degrees of freedom per node. Must be ``9``.
            material: Associated OpenSees material. Must be a 3D
                ``nDMaterial`` with class name ``ElasticIsotropicMaterial``.
            **kwargs: Element parameters. Required/optional keys include:
                - ``PML_Thickness`` (float): Thickness of the PML layer. Required.
                - ``meshType`` (str): ``'box'`` or ``'general'`` (case-insensitive). Required.
                - ``meshTypeParameters`` (list[str|float] | str): 6 values required.
                - Newmark: ``gamma`` (float, default=1/2), ``beta`` (float, default=1/4),
                  ``eta`` (float, default=1/12), ``ksi`` (float, default=1/48).
                - PML: either ``alpha0`` and ``beta0`` (both float, together) or
                  ``m`` (float, default=2.0), ``R`` (float, default=1e-8), and optional ``Cp`` (float).

        Raises:
            ValueError: If the material is incompatible, ``ndof`` != 9, or any
                parameter is missing/invalid.
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with PML3DElement")
        
        # Validate DOF requirement
        if ndof != 9:
            raise ValueError(f"PML3DElement requires 9 DOFs, but got {ndof}")
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        super().__init__('PML3D', ndof, material)
        self.params = kwargs if kwargs else {}

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Generate the OpenSees TCL command for this PML element.

        The command follows OpenSees' ``element PML`` syntax with the Newmark
        parameters and either ``-alphabeta`` or ``-m -R [-Cp]`` depending on
        the provided parameters.
        
        Args:
            tag: Unique element tag.
            nodes: List of 8 node tags.
        
        Returns:
            str: A TCL command string for creating the PML element.
        
        Raises:
            ValueError: If ``nodes`` does not contain exactly 8 node IDs.
        """
        if len(nodes) != 8:
            raise ValueError("PML3D element requires 8 nodes")
        elestr = f"element PML {tag} "
        elestr += " ".join(str(node) for node in nodes)
        elestr += f" {self._material.tag} {self.params.get('PML_Thickness')} \"{self.params.get('meshType')}\" "
        elestr += " ".join(str(val) for val in self.params.get('meshTypeParameters', []))
        elestr += f" \"-Newmark\" {self.params.get('gamma')} {self.params.get('beta')} {self.params.get('eta')} {self.params.get('ksi')}"
        
        alpha0 = self.params.get("alpha0", None)
        beta0 = self.params.get("beta0", None)
        if alpha0 is not None and beta0 is not None:
            elestr += f" -alphabeta {alpha0} {beta0}"
        else:
            elestr += f" -m {self.params['m']} -R {self.params['R']}"
            if self.params.get('Cp', None) is not None:
                elestr += f" -Cp {self.params['Cp']}"
        return elestr

    @classmethod
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names for PML3D.
        
        Returns:
            List[str]: Names including thickness, mesh, Newmark, and PML controls.
        """
        return ["PML_Thickness", 
                "meshType", "meshTypeParameters",
                "gamma", "beta", "eta", "ksi", 
                "m", "R", "Cp", 
                "alpha0", "beta0"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element.
        
        Returns:
            List[str]: Human-readable descriptions in a UI-friendly format.
        """
        return ['Thickness of the PML layer',
            'Type of mesh for the PML layer (put 1:"General", 2:"Box")',
            'Parameters for the mesh type (comma separated)',
            "<html>&gamma; parameter for Newmark integration (optional, default=1./2.)",
            "<html>&beta; parameter for Newmark integration (optional, default=1./4.)",
            "<html>&eta; parameter for Newmark integration (optional, default=1./12.)",
            "<html>&xi; parameter for Newmark integration (optional, default=1./48.)",
            'm parameter for Newmark integration (optional, default=2.0)',
            'R parameter for Newmark integration (optional, default=1e-8)',
            'Cp parameter for Newmark integration (optional, calculated from material properties)',
            "&alpha;<sub>0</sub> PML parameter (optional, default=Calculated from m, R, Cp)",
            "&beta;<sub>0</sub> PML parameter (optional, default=Calculated from m, R, Cp)"]
    
    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node for this element.
        
        Returns:
            List[str]: ``['9']``.
        """
        return ['9']
    
    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters.
        
        For convenience, ``meshTypeParameters`` is returned as a comma-separated
        string if present.
        
        Args:
            keys: Parameter names to retrieve; see :meth:`get_parameters`.
        
        Returns:
            Dict[str, Union[int, float, str]]: Mapping from key to stored value
            (or ``None`` if not present). If ``meshTypeParameters`` is in
            ``keys``, it is formatted as ``"v1, v2, ... v6"``.
        """
        vals = {key: self.params.get(key) for key in keys}
        vals['meshTypeParameters'] = ", ".join(str(val) for val in vals['meshTypeParameters'])
        return vals
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping. Any previously stored parameter not
                present in this mapping will be removed.
        """
        self.params.clear()
        self.params.update(values)

    @classmethod
    def _is_material_compatible(cls, material: Material) -> bool:
        """Check whether the provided material can be used with PML3D.
        
        Requires a 3D ``nDMaterial`` whose class name is
        ``ElasticIsotropicMaterial``.
        
        Args:
            material: Material instance to check.
        
        Returns:
            bool: ``True`` if the material satisfies the requirements.
        """
        check = (material.material_type == 'nDMaterial') and (material.__class__.__name__ == 'ElasticIsotropicMaterial')
        return check
    
    @classmethod
    def validate_element_parameters(cls, **kwargs) -> Dict[str, Union[int, float, str]]:
        """Validate and coerce PML3D parameters.

        Validation rules include (non-exhaustive):
        - ``PML_Thickness``: required, float.
        - ``meshType``: required, one of ``box`` or ``general`` (case-insensitive).
        - ``meshTypeParameters``: required, list/string of 6 numeric values.
        - Newmark params ``gamma``, ``beta``, ``eta``, ``ksi``: optional, float with defaults.
        - Either provide both ``alpha0`` and ``beta0`` (floats) or provide
          ``m`` (float, default 2.0), ``R`` (float, default 1e-8) and optional ``Cp`` (float).

        Args:
            **kwargs: Raw parameter mapping.

        Returns:
            Dict[str, Union[int, float, str]]: Validated and coerced parameters.

        Raises:
            ValueError: If a required parameter is missing, or a value cannot be
                coerced/validated, or PML control parameters are inconsistent.
        """
        if 'PML_Thickness' not in kwargs:
            raise ValueError("PML_Thickness must be specified")
        try:
            kwargs['PML_Thickness'] = float(kwargs['PML_Thickness'])
        except (ValueError, TypeError):
            raise ValueError("PML_Thickness must be a float number")
        
        kwargs['meshType'] = kwargs.get('meshType', None)   
        if kwargs['meshType'] is None:
            raise ValueError("meshType must be specified")
        if kwargs['meshType'].lower() not in ["box", "general"]:    
            raise ValueError("meshType must be either 'box' or 'general'")
                   
        try:
            kwargs['meshTypeParameters'] = kwargs.get('meshTypeParameters', None)
            if kwargs['meshTypeParameters'] is None:
                raise ValueError("meshTypeParameters must be specified")
            else:
                if isinstance(kwargs['meshTypeParameters'], str):
                    # Split the string by commas
                    values = kwargs['meshTypeParameters'].split(",")
                elif isinstance(kwargs['meshTypeParameters'], list):
                    values = kwargs['meshTypeParameters']
                else:
                    raise ValueError("meshTypeParameters must be a string or a list of comma separated float numbers")
                # Remove whitespace from beginning and end of each string
                values = [value.strip() if isinstance(value, str) else value for value in values]
                
                if kwargs['meshType'].lower() in ["box", "general"]:
                    if len(values) < 6:
                        raise ValueError("meshTypeParameters must be a list of 6 comma separated float numbers")
                    values = values[:6]
                    for i in range(6):
                        values[i] = float(values[i])
                
                kwargs['meshTypeParameters'] = values
        except ValueError:
            raise ValueError("meshTypeParameters must be a list of 6 comma separated float numbers")
        
        try:
            kwargs['gamma'] = float(kwargs.get('gamma', 1./2.))
        except ValueError:
            raise ValueError("gamma must be a float number")
        
        try:
            kwargs['beta'] = float(kwargs.get('beta', 1./4.))
        except ValueError:
            raise ValueError("beta must be a float number")
        
        try:
            kwargs['eta'] = float(kwargs.get('eta', 1./12.))
        except ValueError:
            raise ValueError("eta must be a float number")
        
        try:
            kwargs['ksi'] = float(kwargs.get('ksi', 1./48.))
        except ValueError:
            raise ValueError("ksi must be a float number")
        
        try:
            kwargs['m'] = float(kwargs.get('m', 2.0))
        except ValueError:
            raise ValueError("m must be a float number")
        
        try:
            kwargs['R'] = float(kwargs.get('R', 1e-8))
        except ValueError:
            raise ValueError("R must be a float number")
        
        if "Cp" in kwargs:
            try:
                kwargs['Cp'] = float(kwargs['Cp'])
            except ValueError:
                raise ValueError("Cp must be a float number")
        
        if "alpha0" in kwargs or "beta0" in kwargs:
            if "alpha0" not in kwargs or "beta0" not in kwargs:
                raise ValueError("Both alpha0 and beta0 must be specified together")
            try:
                kwargs["alpha0"] = float(kwargs["alpha0"])
                kwargs["beta0"] = float(kwargs["beta0"])
            except ValueError:
                raise ValueError("alpha0 and beta0 must be float numbers")
        
        return kwargs



class ASDEmbeddedNodeElement3D(Element):
    """OpenSees ASDEmbeddedNodeElement for 3D problems.

    This element is used to constrain a node (constrained node) to a domain
    defined by 3 or 4 retained nodes. For 3D Solid domains, 4 retained nodes
    forming a tetrahedron are used.

    OpenSees command syntax:
        ``element ASDEmbeddedNodeElement $eleTag $Cnode $Rnode1 $Rnode2 $Rnode3 $Rnode4 [-rot] [-p] [-K $K] [-KP $KP]``

    Parameters:
        - ``rot`` (bool): Optional flag to constrain rotations (default: False).
        - ``p`` (bool): Optional flag to constrain pressure (default: False).
        - ``K`` (float): User-defined penalty stiffness (default: 1.0e18).
        - ``KP`` (float): User-defined penalty stiffness for pressure (default: 1.0e18).
    """
    def __init__(self, ndof: int, **kwargs):
        """Initialize an ASDEmbeddedNodeElement3D.

        Args:
            ndof: Number of degrees of freedom per node. Must be 3, 4, or 6.
            **kwargs: Element parameters:
                - ``rot`` (bool): Constrain rotations.
                - ``p`` (bool): Constrain pressure.
                - ``K`` (float): Penalty stiffness.
                - ``KP`` (float): Penalty stiffness for pressure.
        """
        if ndof not in [3, 4, 6]:
            raise ValueError(f"ASDEmbeddedNodeElement3D requires 3, 4, or 6 DOFs, but got {ndof}")
        
        # Validate element parameters if provided
        if kwargs:
            kwargs = self.validate_element_parameters(**kwargs)
            
        super().__init__('ASDEmbeddedNodeElement', ndof, material=None)
        self.params = kwargs if kwargs else {}

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
        
        if self.params.get('rot'):
            cmd += " -rot"
        if self.params.get('p'):
            cmd += " -p"
        if 'K' in self.params:
            cmd += f" -K {self.params['K']}"
        if 'KP' in self.params:
            cmd += f" -KP {self.params['KP']}"
            
        return cmd

    @classmethod
    def get_parameters(cls) -> List[str]:
        """List the supported parameter names."""
        return ["rot", "p", "K", "KP"]

    @classmethod
    def get_description(cls) -> List[str]:
        """Describe each parameter expected by this element."""
        return [
            "Constrain rotational DOFs",
            "Constrain pressure DOFs",
            "Penalty stiffness",
            "Penalty stiffness for pressure"
        ]

    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node."""
        return ["3", "4", "6"]

    def get_values(self, keys: List[str]) -> Dict[str, Union[int, float, str]]:
        """Retrieve current values for the given parameters."""
        return {key: self.params.get(key) for key in keys}

    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Update element parameters."""
        self.params.clear()
        self.params.update(values)

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
        return kwargs

class ZeroLengthContactASDimplex(Element):
    """OpenSees ZeroLengthContactASDimplex Element.

    This element is used to model contact between two nodes. It supports
    normal and tangential stiffness, and friction.

    Attributes:
        params (Dict[str, Union[int, float, str]]): Validated element parameters.
    """

    def __init__(self, ndof: int, Kn: float, Kt: float, mu: float, material: Material = None, orient: List[float] = None, intType: int = 0):
        """Initialize a ZeroLengthContactASDimplex element.

        Args:
            ndof: Number of degrees of freedom per node.
            Kn: Penalty stiffness for normal contact.
            Kt: Penalty stiffness for tangential contact.
            mu: Friction coefficient using Mohr-Coulomb friction.
            material: Not used by this element, but required by base class signature.
                      Defaults to None.
            orient: Orientation vector [nx, ny, nz] (optional).
            intType: Integration type (0: Implicit, 1: IMPL-EX). Defaults to 0.
        """
        super().__init__('ZeroLengthContactASDimplex', ndof, material=None)
        
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
        
        cmd = f"element ZeroLengthContactASDimplex {tag} {nodes[0]} {nodes[1]} {self.params['Kn']} {self.params['Kt']} {self.params['mu']}"
        
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



# =================================================================================================
# Register element types
# =================================================================================================
ElementRegistry.register_element_type('SSPQuad', SSPQuadElement)
ElementRegistry.register_element_type('stdBrick', stdBrickElement)
ElementRegistry.register_element_type('PML3D', PML3DElement)
ElementRegistry.register_element_type('SSPbrick', SSPbrickElement)
ElementRegistry.register_element_type('ASDEmbeddedNodeElement3D', ASDEmbeddedNodeElement3D)
ElementRegistry.register_element_type('ZeroLengthContactASDimplex', ZeroLengthContactASDimplex)