from typing import Dict, List, Union, Optional
from femora.components.Material.materialBase import Material
from femora.core.element_base import Element, ElementRegistry

class PML3DElement(Element):
    """OpenSees 8-node Perfectly Matched Layer (PML) 3D element.

    This element augments the standard brick element with PML degrees of
    freedom (9 DOFs per node). It requires an isotropic elastic 3D
    ``nDMaterial`` (class name ``ElasticIsotropicMaterial``) and supports two
    mesh types (``box`` and ``general``) with associated parameters.
    """
    def __init__(self, ndof: int, material: Material, 
                 PML_Thickness: float, 
                 meshType: str, 
                 meshTypeParameters: Union[List[float], str],
                 gamma: float = 0.5, 
                 beta: float = 0.25, 
                 eta: float = 1.0/12.0, 
                 ksi: float = 1.0/48.0,
                 m: float = 2.0, 
                 R: float = 1.0e-8, 
                 Cp: Optional[float] = None,
                 alpha0: Optional[float] = None, 
                 beta0: Optional[float] = None,
                 **kwargs):
        """
        Args:
            ndof (int): Number of degrees of freedom per node. Must be 9.
            material (Material): Associated OpenSees material. Must be a 3D
                nDMaterial with class name ElasticIsotropicMaterial.
            PML_Thickness (float): Thickness of the PML layer. Required.
            meshType (str): 'box' or 'general' (case-insensitive). Required.
            meshTypeParameters (Union[List[float], str]): 6 values required.
            gamma (float, optional): Newmark gamma. Defaults to 0.5.
            beta (float, optional): Newmark beta. Defaults to 0.25.
            eta (float, optional): Newmark eta. Defaults to 1/12.
            ksi (float, optional): Newmark ksi. Defaults to 1/48.
            m (float, optional): PML m. Defaults to 2.0.
            R (float, optional): PML R. Defaults to 1e-8.
            Cp (float, optional): PML Cp.
            alpha0 (float, optional): PML alpha0.
            beta0 (float, optional): PML beta0.

        Raises:
            ValueError: If the material is incompatible, ndof != 9, or any
                parameter is missing/invalid.

        OpenSees command syntax:
            ``element PML $tag $n1 ... $n8 $matTag $thick "$meshType" $params "-Newmark" $g $b $e $x ...``

        Example:
            ```python
            element = PML3DElement(ndof=9, material=mat, PML_Thickness=1.0, meshType='box', meshTypeParameters=[1.0]*6)
            ```
        """
        # Validate material compatibility
        if not self._is_material_compatible(material):
            raise ValueError(f"Material {material.user_name} with type {material.material_type} is not compatible with PML3DElement")
        
        # Validate DOF requirement
        if ndof != 9:
            raise ValueError(f"PML3DElement requires 9 DOFs, but got {ndof}")
        
        # Validate element parameters
        params = {
            "PML_Thickness": PML_Thickness,
            "meshType": meshType,
            "meshTypeParameters": meshTypeParameters,
            "gamma": gamma,
            "beta": beta,
            "eta": eta,
            "ksi": ksi,
            "m": m,
            "R": R
        }
        if Cp is not None: params["Cp"] = Cp
        if alpha0 is not None: params["alpha0"] = alpha0
        if beta0 is not None: params["beta0"] = beta0

        validated = self.validate_element_parameters(**params)
            
        super().__init__('PML3D', ndof, material, **kwargs)
        
        self.PML_Thickness = validated["PML_Thickness"]
        self.meshType = validated["meshType"]
        self.meshTypeParameters = validated["meshTypeParameters"]
        self.gamma = validated["gamma"]
        self.beta = validated["beta"]
        self.eta = validated["eta"]
        self.ksi = validated["ksi"]
        self.m = validated["m"]
        self.R = validated["R"]
        self.Cp = validated.get("Cp")
        self.alpha0 = validated.get("alpha0")
        self.beta0 = validated.get("beta0")

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
            ValueError: If ``nodes`` does not contain exactly 8 node IDn.
        """
        if len(nodes) != 8:
            raise ValueError("PML3D element requires 8 nodes")
        elestr = f"element PML {tag} "
        elestr += " ".join(str(node) for node in nodes)
        elestr += f" {self._material.tag} {self.PML_Thickness} \"{self.meshType}\" "
        elestr += " ".join(str(val) for val in self.meshTypeParameters)
        elestr += f" \"-Newmark\" {self.gamma} {self.beta} {self.eta} {self.ksi}"
        
        if self.alpha0 is not None and self.beta0 is not None:
            elestr += f" -alphabeta {self.alpha0} {self.beta0}"
        else:
            elestr += f" -m {self.m} -R {self.R}"
            if self.Cp is not None:
                elestr += f" -Cp {self.Cp}"
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
        vals = {key: getattr(self, key) for key in keys if hasattr(self, key)}
        if 'meshTypeParameters' in vals and isinstance(vals['meshTypeParameters'], list):
            vals['meshTypeParameters'] = ", ".join(str(val) for val in vals['meshTypeParameters'])
        return vals
    
    def update_values(self, values: Dict[str, Union[int, float, str]]) -> None:
        """Replace all stored parameters with the provided mapping.
        
        Args:
            values: New parameter mapping. Any previously stored parameter not
                present in this mapping will be removed.
        """
        # Get current values to preserve defaults not explicitly updated
        current_params = self.get_values(self.get_parameters())
        
        # Convert meshTypeParameters back to list if it's a string for validation
        if 'meshTypeParameters' in values and isinstance(values['meshTypeParameters'], str):
            current_params['meshTypeParameters'] = [float(x.strip()) for x in values['meshTypeParameters'].split(',')]
        elif 'meshTypeParameters' in current_params and isinstance(current_params['meshTypeParameters'], str):
             current_params['meshTypeParameters'] = [float(x.strip()) for x in current_params['meshTypeParameters'].split(',')]

        # Update with new values
        current_params.update(values)
        
        # Validate the combined parameters
        validated = self.validate_element_parameters(**current_params)
        
        # Update instance attributes
        for key, val in validated.items():
            setattr(self, key, val)
        
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
            "m parameter for PML (optional, default=2.0)",
            "R parameter for PML (optional, default=1e-8)",
            "Cp parameter for PML (optional)",
            "alpha0 parameter for PML (optional)",
            "beta0 parameter for PML (optional)"]
    
    @classmethod
    def get_possible_dofs(cls) -> List[str]:
        """Get the allowed number of DOFs per node for this element.
        
        Returns:
            List[str]: ``['9']``.
        """
        return ['9']

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

ElementRegistry.register_element_type('PML3D', PML3DElement)
