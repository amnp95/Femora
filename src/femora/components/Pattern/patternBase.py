from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Type
import numpy as np
from femora.components.TimeSeries.timeSeriesBase import TimeSeries
from femora.components.load.load_base import Load, LoadManager
try:
    # For docstring forwarding in _AddLoadProxy
    from femora.components.load.node_load import NodeLoad
    from femora.components.load.element_load import ElementLoad
    from femora.components.load.sp_load import SpLoad
except Exception:
    NodeLoad = None  # type: ignore
    ElementLoad = None  # type: ignore
    SpLoad = None  # type: ignore

class Pattern(ABC):
    """
    Base abstract class for all load patterns
    """
    _patterns = {}  # Class-level dictionary to track all patterns
    _start_tag = 1  # Class variable to track the starting tag

    def __init__(self, pattern_type: str):
        """
        Initialize a new pattern with a sequential tag
        
        Args:
            pattern_type (str): The type of pattern (e.g., 'UniformExcitation', 'H5DRM')
        """
        self.tag = len(Pattern._patterns) + Pattern._start_tag
        
        self.pattern_type = pattern_type
        
        # Register this pattern in the class-level tracking dictionary
        Pattern._patterns[self.tag] = self

    @classmethod
    def get_pattern(cls, tag: int) -> 'Pattern':
        """
        Retrieve a specific pattern by its tag.
        
        Args:
            tag (int): The tag of the pattern
        
        Returns:
            Pattern: The pattern with the specified tag
        
        Raises:
            KeyError: If no pattern with the given tag exists
        """
        if tag not in cls._patterns:
            raise KeyError(f"No pattern found with tag {tag}")
        return cls._patterns[tag]

    @classmethod
    def remove_pattern(cls, tag: int) -> None:
        """
        Delete a pattern by its tag.
        
        Args:
            tag (int): The tag of the pattern to delete
        """
        if tag in cls._patterns:
            del cls._patterns[tag]
            cls._reassign_tags()


    @classmethod
    def get_all_patterns(cls) -> Dict[int, 'Pattern']:
        """
        Retrieve all created patterns.
        
        Returns:
            Dict[int, Pattern]: A dictionary of all patterns, keyed by their unique tags
        """
        return cls._patterns
    
    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all patterns and reset tags.
        """
        cls._patterns.clear()

    @classmethod
    def reset(cls):
        cls._patterns.clear()
        cls._start_tag = 1

    @classmethod
    def set_tag_start(cls, start_tag: int):
        cls._start_tag = start_tag
        cls._reassign_tags()

    @classmethod
    def _reassign_tags(cls) -> None:
        """
        Reassign tags to all patterns sequentially starting from _start_tag.
        """
        new_patterns = {}
        for idx, pattern in enumerate(sorted(cls._patterns.values(), key=lambda p: p.tag), start=cls._start_tag):
            pattern.tag = idx
            new_patterns[idx] = pattern
        cls._patterns = new_patterns

    @abstractmethod
    def to_tcl(self) -> str:
        """
        Convert the pattern to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        pass

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this pattern
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        pass

    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Get the parameters defining this pattern
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary of parameter values
        """
        pass

    @abstractmethod
    def update_values(self, **kwargs) -> None:
        """
        Update the values of the pattern
        
        Args:
            **kwargs: Parameters for pattern update
        """
        pass


class UniformExcitation(Pattern):
    """
    UniformExcitation pattern allows applying a uniform excitation to a model
    acting in a certain direction.
    """
    def __init__(self, **kwargs):
        """
        Initialize a UniformExcitation pattern
        
        Args:
            dof (int): DOF direction the ground motion acts
            time_series (TimeSeries): TimeSeries defining the acceleration history
            vel0 (float, optional): Initial velocity (default=0.0)
            factor (float, optional): Constant factor (default=1.0)
        """
        super().__init__("UniformExcitation")
        validated_params = self.validate(**kwargs)
        self.dof = validated_params["dof"]
        self.time_series = validated_params["time_series"]
        self.vel0 = validated_params.get("vel0", 0.0)
        self.factor = validated_params.get("factor", 1.0)

    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[int, float, TimeSeries]]:
        """
        Validate parameters for UniformExcitation pattern
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            Dict[str, Union[int, float, TimeSeries]]: Validated parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if "dof" not in kwargs:
            raise ValueError("DOF direction must be specified")
        
        try:
            dof = int(kwargs["dof"])
            if dof < 1:
                raise ValueError("DOF must be a positive integer")
        except ValueError:
            raise ValueError("DOF must be an integer")
        
        if "time_series" not in kwargs:
            raise ValueError("TimeSeries must be specified")
        
        time_series = kwargs["time_series"]
        if not isinstance(time_series, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        
        # Optional parameters
        validated = {"dof": dof, "time_series": time_series}
        
        if "vel0" in kwargs:
            try:
                vel0 = float(kwargs["vel0"])
                validated["vel0"] = vel0
            except ValueError:
                raise ValueError("Initial velocity (vel0) must be a number")
        
        if "factor" in kwargs:
            try:
                factor = float(kwargs["factor"])
                validated["factor"] = factor
            except ValueError:
                raise ValueError("Constant factor must be a number")
        
        return validated

    def to_tcl(self) -> str:
        """
        Convert the UniformExcitation pattern to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        cmd = f"pattern UniformExcitation {self.tag} {self.dof} -accel {self.time_series.tag}"
        
        if self.vel0 != 0.0:
            cmd += f" -vel0 {self.vel0}"
        
        if self.factor != 1.0:
            cmd += f" -fact {self.factor}"
            
        return cmd

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this pattern
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("dof", "DOF direction the ground motion acts"),
            ("time_series", "TimeSeries defining the acceleration history"),
            ("vel0", "Initial velocity (optional, default=0.0)"),
            ("factor", "Constant factor (optional, default=1.0)")
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, TimeSeries]]:
        """
        Get the parameters defining this pattern
        
        Returns:
            Dict[str, Union[str, int, float, TimeSeries]]: Dictionary of parameter values
        """
        return {
            "dof": self.dof,
            "time_series": self.time_series,
            "vel0": self.vel0,
            "factor": self.factor
        }

    def update_values(self, **kwargs) -> None:
        """
        Update the values of the pattern
        
        Args:
            **kwargs: Parameters for pattern update
        """
        validated_params = self.validate(**kwargs)
        if "dof" in validated_params:
            self.dof = validated_params["dof"]
        if "time_series" in validated_params:
            self.time_series = validated_params["time_series"]
        if "vel0" in validated_params:
            self.vel0 = validated_params["vel0"]
        if "factor" in validated_params:
            self.factor = validated_params["factor"]


class H5DRMPattern(Pattern):
    """
    H5DRM pattern implements the Domain Reduction Method (DRM) 
    using the H5DRM data format for seismic analysis.
    """
    def __init__(self, **kwargs):
        """
        Initialize a H5DRM pattern
        
        Args:
            filepath (str): Path to the H5DRM dataset
            factor (float): Scale factor for DRM forces and displacements
            crd_scale (float): Scale factor for dataset coordinates
            distance_tolerance (float): Tolerance for DRM point to FE mesh matching
            do_coordinate_transformation (int): Whether to apply coordinate transformation
            transform_matrix (list): 3x3 transformation matrix [T00, T01, T02, T10, T11, T12, T20, T21, T22]
            origin (list): Origin location after transformation [x00, x01, x02]
        """
        super().__init__("H5DRM")
        validated_params = self.validate(**kwargs)
        self.filepath = validated_params["filepath"]
        self.factor = validated_params["factor"]
        self.crd_scale = validated_params["crd_scale"]
        self.distance_tolerance = validated_params["distance_tolerance"]
        self.do_coordinate_transformation = validated_params["do_coordinate_transformation"]
        self.transform_matrix = validated_params["transform_matrix"]
        self.origin = validated_params["origin"]

    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, float, int, list]]:
        """
        Validate parameters for H5DRM pattern
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            Dict[str, Union[str, float, int, list]]: Validated parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        required_params = [
            "filepath", "factor", "crd_scale", "distance_tolerance", 
            "do_coordinate_transformation"
        ]
        
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Required parameter '{param}' is missing")
        
        validated = {}
        
        # Validate filepath
        validated["filepath"] = str(kwargs["filepath"])
        
        # Validate numeric parameters
        numeric_params = ["factor", "crd_scale", "distance_tolerance"]
        for param in numeric_params:
            try:
                validated[param] = float(kwargs[param])
            except ValueError:
                raise ValueError(f"Parameter '{param}' must be a number")
        
        # Validate coordinate transformation flag
        try:
            do_transform = int(kwargs["do_coordinate_transformation"])
            if do_transform not in [0, 1]:
                raise ValueError("do_coordinate_transformation must be 0 or 1")
            validated["do_coordinate_transformation"] = do_transform
        except ValueError:
            raise ValueError("do_coordinate_transformation must be an integer (0 or 1)")
        
        # Validate transformation matrix
        transform_keys = ["T00", "T01", "T02", "T10", "T11", "T12", "T20", "T21", "T22"]
        if "transform_matrix" in kwargs:
            transform_matrix = kwargs["transform_matrix"]
            if len(transform_matrix) != 9:
                raise ValueError("transform_matrix must be a list of 9 values")
            validated["transform_matrix"] = transform_matrix
        else:
            # Check for individual transformation parameters
            transform_matrix = []
            for key in transform_keys:
                if key not in kwargs:
                    raise ValueError(f"Required transformation parameter '{key}' is missing")
                try:
                    transform_matrix.append(float(kwargs[key]))
                except ValueError:
                    raise ValueError(f"Transformation parameter '{key}' must be a number")
            validated["transform_matrix"] = transform_matrix
        
        # Validate origin
        origin_keys = ["x00", "x01", "x02"]
        if "origin" in kwargs:
            origin = kwargs["origin"]
            if len(origin) != 3:
                raise ValueError("origin must be a list of 3 values")
            validated["origin"] = origin
        else:
            # Check for individual origin parameters
            origin = []
            for key in origin_keys:
                if key not in kwargs:
                    raise ValueError(f"Required origin parameter '{key}' is missing")
                try:
                    origin.append(float(kwargs[key]))
                except ValueError:
                    raise ValueError(f"Origin parameter '{key}' must be a number")
            validated["origin"] = origin
        
        return validated

    def to_tcl(self) -> str:
        """
        Convert the H5DRM pattern to a TCL command string for OpenSees
        
        Returns:
            str: The TCL command string
        """
        # Extract transformation matrix and origin values
        T00, T01, T02, T10, T11, T12, T20, T21, T22 = self.transform_matrix
        x00, x01, x02 = self.origin
        
        cmd = f'pattern H5DRM {self.tag} "{self.filepath}" {self.factor} {self.crd_scale} '
        cmd += f'{self.distance_tolerance} {self.do_coordinate_transformation} '
        cmd += f'{T00} {T01} {T02} {T10} {T11} {T12} {T20} {T21} {T22} '
        cmd += f'{x00} {x01} {x02}'
        
        return cmd

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters defining this pattern
        
        Returns:
            List[tuple]: List of (parameter name, description) tuples
        """
        return [
            ("filepath", "Path to the H5DRM dataset"),
            ("factor", "Scale factor for DRM forces and displacements"),
            ("crd_scale", "Scale factor for dataset coordinates"),
            ("distance_tolerance", "Tolerance for DRM point to FE mesh matching"),
            ("do_coordinate_transformation", "Whether to apply coordinate transformation (0/1)"),
            ("transform_matrix", "3x3 transformation matrix [T00, T01, T02, T10, T11, T12, T20, T21, T22]"),
            ("origin", "Origin location after transformation [x00, x01, x02]")
        ]

    def get_values(self) -> Dict[str, Union[str, float, int, list]]:
        """
        Get the parameters defining this pattern
        
        Returns:
            Dict[str, Union[str, float, int, list]]: Dictionary of parameter values
        """
        return {
            "filepath": self.filepath,
            "factor": self.factor,
            "crd_scale": self.crd_scale,
            "distance_tolerance": self.distance_tolerance,
            "do_coordinate_transformation": self.do_coordinate_transformation,
            "transform_matrix": self.transform_matrix,
            "origin": self.origin
        }

    def update_values(self, **kwargs) -> None:
        """
        Update the values of the pattern
        
        Args:
            **kwargs: Parameters for pattern update
        """
        validated_params = self.validate(**kwargs)
        for key, value in validated_params.items():
            setattr(self, key, value)


class PlainPattern(Pattern):
    """
    Plain load pattern with a shared TimeSeries and contained loads.

    The Plain pattern associates a single :class:`TimeSeries` with a collection
    of loads (nodal, elemental, and single-point) and emits a TCL block using
    OpenSees' Plain pattern syntax.

    TCL form:
        pattern Plain <patternTag> <tsTag> <-fact cFactor> {
            <load commands>
        }

    Attributes:
        time_series (TimeSeries): The time series used by this pattern.
        factor (float): Constant factor applied to all loads in this pattern.
        _loads (List[Load]): Internal list of loads attached to this pattern.

    Examples:
        Create a plain pattern and add loads via the factory proxy::

            plain = PatternManager().create_pattern('plain', time_series=ts, factor=1.0)
            plain.add_load.node(node_tag=3, values=[0.0, -50.0, 0.0])
            plain.add_load.sp(node_mask=mm.nodes.along_axis('z', 9.0, 10.0), dof=2, value=-0.01)
            plain.add_load.ele(kind='beamUniform', element_mask=mm.elements.by_material(3), params={'Wy': -200.0})
    """

    def __init__(self, **kwargs):
        super().__init__("Plain")
        validated = self.validate(**kwargs)
        self.time_series: TimeSeries = validated["time_series"]
        self.factor: float = validated.get("factor", 1.0)
        self._loads: List[Load] = []

    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[TimeSeries, float]]:
        """
        Validate constructor or update parameters.

        Args:
            **kwargs: Supported keys are:
                - time_series (TimeSeries): Required time series instance.
                - factor (float, optional): Constant factor (default 1.0).

        Returns:
            Dict[str, Union[TimeSeries, float]]: Normalized values.

        Raises:
            ValueError: If required parameters are missing or invalid.
        """
        if "time_series" not in kwargs:
            raise ValueError("time_series must be specified")
        ts = kwargs["time_series"]
        if not isinstance(ts, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        out: Dict[str, Union[TimeSeries, float]] = {"time_series": ts}
        if "factor" in kwargs:
            try:
                out["factor"] = float(kwargs["factor"])
            except Exception:
                raise ValueError("factor must be numeric")
        return out

    @staticmethod
    def get_parameters() -> List[tuple]:
        """
        Get the parameters that define this pattern (for UI/metadata).

        Returns:
            List[tuple]: Tuples of (name, description).
        """
        return [
            ("time_series", "TimeSeries used by the load pattern"),
            ("factor", "Constant factor (optional, default=1.0)"),
        ]

    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Return a serializable dictionary of the current pattern state.

        Returns:
            Dict[str, Union[str, int, float, list]]
        """
        return {
            "time_series": self.time_series,
            "factor": self.factor,
            "loads": [l.tag for l in self._loads],
        }

    def update_values(self, **kwargs) -> None:
        """
        Update the pattern's values.

        Args:
            **kwargs: Same keys as :meth:`validate`.

        Raises:
            ValueError: If validation fails.
        """
        validated = self.validate(
            time_series=kwargs.get("time_series", self.time_series),
            factor=kwargs.get("factor", self.factor),
        )
        self.time_series = validated["time_series"]  # type: ignore[index]
        self.factor = float(validated.get("factor", self.factor))

    # -------------------------------
    # Load management (direct)
    # -------------------------------
    def add_load_instance(self, load: Load) -> None:
        """
        Attach a load instance to this pattern.

        Args:
            load (Load): The load to attach.

        Notes:
            Sets ``load.pattern_tag`` to this pattern's tag.
        """
        if not isinstance(load, Load):
            raise ValueError("load must be an instance of Load")
        if load in self._loads:
            return
        load.pattern_tag = self.tag
        self._loads.append(load)

    def remove_load(self, load: Load) -> None:
        """
        Remove a previously attached load instance.

        Args:
            load (Load): The load to remove.
        """
        if load in self._loads:
            self._loads.remove(load)
            load.pattern_tag = None

    def clear_loads(self) -> None:
        """
        Remove all loads attached to this pattern.
        """
        for l in self._loads:
            l.pattern_tag = None
        self._loads.clear()

    def get_loads(self) -> List[Load]:
        """
        Get a copy of the attached loads list.

        Returns:
            List[Load]: Loads currently attached to this pattern.
        """
        return list(self._loads)

    def to_tcl(self) -> str:
        """
        Convert the pattern to a TCL Plain pattern block.

        Returns:
            str: TCL block string for OpenSees.
        """
        fact = f" -fact {self.factor}" if self.factor != 1.0 else ""
        lines: List[str] = [f"pattern Plain {self.tag} {self.time_series.tag} {fact} {{"]
        for l in self._loads:
            lines.append(f"\t{l.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    # -------------------------------
    # Load management (factory proxy)
    # -------------------------------
    class _AddLoadProxy:
        """
        Factory proxy to create loads and attach them to the pattern.

        Methods mirror :class:`LoadManager` and return the created load after
        automatically attaching it to the owning pattern.
        """
        def __init__(self, pattern: 'PlainPattern'):
            self._pattern = pattern
            self._manager = LoadManager()

        def node(self, **kwargs) -> Load:
            """
            Add a nodal load to THIS PlainPattern and return the created NodeLoad.

            Purpose:
                Creates a NodeLoad and immediately attaches it to this pattern so
                it is emitted inside this pattern's TCL block.

            OpenSees form:
                ``load <nodeTag> <values...>``

            Parameters (kwargs):
                - node_tag (int, optional): Target node tag when applying to a single node.
                  Mutually exclusive with ``node_mask``.
                - node_mask (NodeMask, optional): Selects multiple nodes. Mutually
                  exclusive with ``node_tag``. When provided, one ``load`` line is
                  emitted per node tag.
                - values (List[float], required): Reference load vector. When using a
                  mask, this vector is padded/truncated to each node's DOF.
                - pids (List[int], optional): Core ids. If omitted and a mask is used,
                  cores are derived per node from the assembled mesh; otherwise defaults
                  to ``[0]``.

            Returns:
                Load: The created NodeLoad instance (already attached to this pattern).
            """
            load = self._manager.node(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def element(self, **kwargs) -> Load:
            """
            Add an element load to THIS PlainPattern and return the created ElementLoad.

            Purpose:
                Creates an ElementLoad and immediately attaches it to this pattern so
                it is emitted inside this pattern's TCL block.

            OpenSees forms:
                - 2D uniform: ``eleLoad -ele/-range ... -type -beamUniform Wy [Wx]``
                - 3D uniform: ``eleLoad -ele/-range ... -type -beamUniform Wy Wz [Wx]``
                - 2D point:   ``eleLoad -ele/-range ... -type -beamPoint   Py xL [Px]``
                - 3D point:   ``eleLoad -ele/-range ... -type -beamPoint   Py Pz xL [Px]``

            Parameters (kwargs):
                - kind (str, required): ``'beamUniform'`` or ``'beamPoint'``.
                - element_mask (ElementMask, optional): Selects elements; preferred.
                  Alternatively specify exactly one of:
                    - ele_tags (List[int]): Explicit element tags list
                    - ele_range (Tuple[int,int]): Inclusive tag range ``(start, end)``
                - params (Dict[str,float], required):
                    For ``beamUniform``: ``Wy`` (required), optional ``Wz``, ``Wx``.
                    For ``beamPoint``: ``Py`` and ``xL`` (required), optional ``Pz``, ``Px``.
                - pid (int, optional): Core id. If omitted and a mask is used, pid is
                  derived from the first selected element's core; otherwise defaults to 0.

            Returns:
                Load: The created ElementLoad instance (already attached to this pattern).
            """
            load = self._manager.element(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def ele(self, **kwargs) -> Load:
            """
            Alias of ``element``: adds an element load to THIS PlainPattern.

            See :meth:`element` for parameters and behavior.

            Returns:
                Load: The created ElementLoad instance (attached to this pattern).
            """
            return self.element(**kwargs)

        def sp(self, **kwargs) -> Load:
            """
            Add a single-point constraint to THIS PlainPattern and return the created SpLoad.

            Purpose:
                Creates an SpLoad and immediately attaches it to this pattern so it is
                emitted inside this pattern's TCL block.

            OpenSees form:
                ``sp <nodeTag> <dof> <value>``

            Parameters (kwargs):
                - node_tag (int, optional): Target node tag when applying to a single node.
                  Mutually exclusive with ``node_mask``.
                - node_mask (NodeMask, optional): Selects multiple nodes. Mutually
                  exclusive with ``node_tag``. When provided, one ``sp`` line is emitted
                  per node tag.
                - dof (int, required): 1-based DOF index.
                - value (float, required): Prescribed value.
                - pids (List[int], optional): Core ids. If omitted and a mask is used,
                  cores are derived per node from the assembled mesh; otherwise defaults
                  to ``[0]``.

            Returns:
                Load: The created SpLoad instance (already attached to this pattern).
            """
            load = self._manager.sp(**kwargs)
            self._pattern.add_load_instance(load)
            return load

    @property
    def add_load(self) -> '_AddLoadProxy':
        """
        Access a proxy that can create and attach loads to this pattern.

        Examples:
            plain.add_load.node(node_tag=3, values=[0.0, -50.0, 0.0])
            plain.add_load.sp(node_tag=4, dof=2, value=-100.0)
            plain.add_load.ele(kind="beamUniform", ele_tags=[3], params={"Wy": -200.0})
        """
        return PlainPattern._AddLoadProxy(self)

class PatternRegistry:
    """
    A registry to manage pattern types and their creation.
    """
    _pattern_types = {
        'uniformexcitation': UniformExcitation,
        'h5drm': H5DRMPattern,
        'plain': PlainPattern,
    }

    @classmethod
    def register_pattern_type(cls, name: str, pattern_class: Type[Pattern]):
        """
        Register a new pattern type for easy creation.
        
        Args:
            name (str): The name of the pattern type
            pattern_class (Type[Pattern]): The class of the pattern
        """
        cls._pattern_types[name.lower()] = pattern_class

    @classmethod
    def get_pattern_types(cls):
        """
        Get available pattern types.
        
        Returns:
            List[str]: Available pattern types
        """
        return list(cls._pattern_types.keys())

    @classmethod
    def create_pattern(cls, pattern_type: str, **kwargs) -> Pattern:
        """
        Create a new pattern of a specific type.
        
        Args:
            pattern_type (str): Type of pattern to create
            **kwargs: Parameters for pattern initialization
        
        Returns:
            Pattern: A new pattern instance
        
        Raises:
            KeyError: If the pattern type is not registered
        """
        if pattern_type.lower() not in cls._pattern_types:
            raise KeyError(f"Pattern type {pattern_type} not registered")
        
        return cls._pattern_types[pattern_type.lower()](**kwargs)


class PatternManager:
    """
    Singleton class for managing load patterns
    """
    _instance = None

    def __init__(self):
        self.uniformexcitation = UniformExcitation
        self.h5drm = H5DRMPattern
        self.plain = PlainPattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PatternManager, cls).__new__(cls)
        return cls._instance

    def create_pattern(self, pattern_type: str, **kwargs) -> Pattern:
        """Create a new pattern"""
        return PatternRegistry.create_pattern(pattern_type, **kwargs)

    def get_pattern(self, tag: int) -> Pattern:
        """Get pattern by tag"""
        return Pattern.get_pattern(tag)

    def remove_pattern(self, tag: int) -> None:
        """Remove pattern by tag"""
        Pattern.remove_pattern(tag)

    def get_all_patterns(self) -> Dict[int, Pattern]:
        """Get all patterns"""
        return Pattern.get_all_patterns()

    def get_available_types(self) -> List[str]:
        """Get list of available pattern types"""
        return PatternRegistry.get_pattern_types()
    
    def clear_all(self):
        """Clear all patterns"""  
        Pattern.clear_all()



