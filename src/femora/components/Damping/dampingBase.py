from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Union, Tuple
import gc

class DampingBase:
    """Base class for all damping models in structural analysis.

    This abstract class provides the foundation for implementing different types of damping
    models in structural dynamics. It manages damping instances through a class-level registry
    and provides common functionality for all derived damping classes.

    Attributes:
        name: Descriptive name of the damping instance, automatically generated.
        tag: Unique identifier for the damping instance.
        _dampings: Class-level registry of all damping instances.

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a damping through the manager
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('rayleigh', alphaM=0.05, betaK=0.001)
        >>> # print(damping.tag)
    """
    _dampings = {}
    _start_tag = 1
    def __init__(self):
        """Initializes a new damping instance.

        Automatically assigns a unique tag and name to the damping instance and
        registers it in the class-level registry.
        """
        tag = self._get_next_tag()
        self.name = f"damping{tag}"
        self.tag = tag
        self._dampings[tag] = self

    @classmethod
    def _get_next_tag(cls):
        """Returns the next available tag for a new damping.

        Tags are assigned sequentially starting from _start_tag.

        Returns:
            The next available tag number.
        """
        return len(cls._dampings) + cls._start_tag
    
    @classmethod
    def remove_damping(cls, tag):
        """Removes a damping from the list of dampings.

        Args:
            tag: The tag of the damping to remove.

        Note:
            After removal, all remaining dampings have their tags updated
            to maintain sequential numbering.
        """
        if tag in cls._dampings:
            del cls._dampings[tag]
            cls._update_tags()


    @staticmethod
    def get_damping(tag):
        """Returns the damping with the given tag.

        Args:
            tag: The tag of the damping to retrieve.

        Returns:
            The damping instance with the specified tag.

        Raises:
            KeyError: If no damping with the given tag exists.
        """
        return DampingBase._dampings[tag]
    

    def remove(self):
        """Removes the damping from the list of dampings.

        This instance method removes the current damping object from the
        registry and updates the tags of all remaining damping instances.
        """
        refrences = gc.get_referrers(self)
        tag = self.tag
        self.__class__.remove_damping(tag)
        
    

    @classmethod
    def _update_tags(cls):
        """Updates the tags of all dampings.

        This method ensures that damping tags remain sequential after
        a damping has been removed. It renumbers all tags and updates
        the corresponding damping names.
        """
        cls._reassign_tags()

    @classmethod
    def _reassign_tags(cls):
        """Reassigns tags to all dampings sequentially starting from _start_tag."""
        new_dampings = {}
        for idx, damping in enumerate(sorted(cls._dampings.values(), key=lambda d: d.tag), start=cls._start_tag):
            damping.tag = idx
            damping.name = f"damping{idx}"
            new_dampings[idx] = damping
        cls._dampings = new_dampings

    @classmethod
    def reset(cls):
        """Resets all dampings and tag counter to initial state."""
        cls._dampings.clear()
        cls._start_tag = 1

    @classmethod
    def set_tag_start(cls, start_tag: int):
        """Sets the starting tag number and reassigns all damping tags.

        Args:
            start_tag: The new starting tag number.
        """
        cls._start_tag = start_tag
        cls._reassign_tags()

    @classmethod
    def clear_all(cls):
        """Clears all dampings and reassigns tags."""
        cls._dampings.clear()
        cls._reassign_tags()

        
    def __str__(self) -> str:
        """Returns a string representation of the damping object.

        Returns:
            A formatted string showing the damping class name, name, and tag.
        """
        res = f"Damping Class:\t{self.__class__.__name__}"
        res += f"\n\tName: {self.name}"
        res += f"\n\tTag: {self.tag}"
        return res
    
    @classmethod
    def print_dampings(cls):
        """Prints all the dampings currently registered.

        Outputs a formatted representation of each damping instance
        to the console, showing their class, name, tag, and parameters.
        """
        print("Printing all dampings:")
        for tag in cls._dampings:
            print(cls._dampings[tag])

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Returns the parameters of the damping.

        Returns:
            List of parameter name-description pairs.
        """
        pass

    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Returns the notes of the damping.

        Returns:
            Dictionary containing notes and references about the damping model.
        """
        pass
    
    @abstractmethod
    def get_values(self)-> Dict[str, Union[str, int, float, list]]:
        """Returns the values of the parameters of the damping.

        Subclasses must implement this method to return current parameter values.

        Returns:
            Dictionary containing the current parameter values of the damping instance.
        """
        pass

    @abstractmethod
    def update_values(self, **kwargs) -> None:
        """Updates the values of the parameters of the damping.

        Subclasses must implement this method to update damping parameters.

        Args:
            **kwargs: Parameter name-value pairs to update.

        Raises:
            ValueError: If parameter validation fails.
        """
        pass

    @abstractmethod
    def to_tcl(self) -> str:
        """Returns the TCL code of the damping.

        Subclasses must implement this method to generate OpenSees TCL commands.

        Returns:
            OpenSees TCL command string for defining this damping.
        """
        pass


class RayleighDamping(DampingBase):
    """Implementation of Rayleigh damping model.

    Rayleigh damping is a classical damping model used in structural dynamics,
    defined as a linear combination of mass and stiffness matrices.

    Attributes:
        alphaM: Factor applied to mass matrix.
        betaK: Factor applied to current stiffness matrix.
        betaKInit: Factor applied to initial stiffness matrix.
        betaKComm: Factor applied to committed stiffness matrix.

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a Rayleigh damping
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('rayleigh', alphaM=0.05, betaK=0.001)
        >>> # print(damping.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a Rayleigh damping instance.

        Args:
            **kwargs: Keyword arguments defining the damping properties.
                alphaM: Factor applied to mass matrix. Defaults to 0.0.
                betaK: Factor applied to current stiffness matrix. Defaults to 0.0.
                betaKInit: Factor applied to initial stiffness matrix. Defaults to 0.0.
                betaKComm: Factor applied to committed stiffness matrix. Defaults to 0.0.

        Raises:
            ValueError: If parameters are invalid or out of range.
        """
        kwargs = self.validate(**kwargs)
        super().__init__()
        self.alphaM = kwargs["alphaM"]
        self.betaK = kwargs["betaK"]
        self.betaKInit = kwargs["betaKInit"]
        self.betaKComm = kwargs["betaKComm"]

    def __str__(self) -> str:
        """Returns a string representation of the Rayleigh damping object.

        Returns:
            A formatted string showing the damping class, name, tag, and parameters.
        """
        res = super().__str__()
        res += f"\n\talphaM: {self.alphaM}"
        res += f"\n\tbetaK: {self.betaK}"
        res += f"\n\tbetaKInit: {self.betaKInit}"
        res += f"\n\tbetaKComm: {self.betaKComm}"
        return res

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Returns the parameters of the Rayleigh damping.

        Returns:
            List of parameter name-description pairs for Rayleigh damping.
        """
        return [
            ("alphaM", "factor applied to elements or nodes mass matrix (optional, default=0.0)"),
            ("betaK", "factor applied to elements or nodes stiffness matrix (optional, default=0.0)"),
            ("betaKInit", "factor applied to elements initial stiffness matrix (optional, default=0.0)"),
            ("betaKComm", "factor applied to elements commited stiffness matrix (optional, default=0.0)")
        ]
    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """Returns the notes of the Rayleigh damping.

        Returns:
            Dictionary containing explanatory notes and references about Rayleigh damping.
        """
        return {
        "Notes": [
            "The damping matrix is calculated as: C = α<sub>M</sub> M + β<sub>K</sub>  K + β<sub>KInit</sub> Kinit + β<sub>KComm</sub>  Kcomm",
            "The usage of Rayleigh damping may provide incorrect result when used with Non-Linear Time History Analysis using Concentrated Plasticity Model."
            ],
        "References": [
            "https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/rayleigh.html",
            "https://opensees.berkeley.edu/wiki/index.php/Rayleigh_Damping_Command"
        ]
        }
    
    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list]]:
        """Validates the Rayleigh damping parameters.

        Args:
            **kwargs: Parameter name-value pairs to validate.

        Returns:
            Validated parameters.

        Raises:
            ValueError: If any parameter is invalid or out of range.
        """
        newkwargs = {
            "alphaM": 0.0,
            "betaK": 0.0,
            "betaKInit": 0.0,
            "betaKComm": 0.0
        }

        #  check if the values are floats and are between 0 and 1
        for key in newkwargs:
            try:
                newkwargs[key] = float(kwargs.get(key, 0.0))
            except ValueError:
                raise ValueError(f"{key} should be a float")

        for key in newkwargs:
            try:
                if newkwargs[key] < 0 or newkwargs[key] > 1:
                    raise ValueError
            except ValueError:
                raise ValueError(f"{key} should be a float between 0 and 1")
        
        eps = 1e-10
        res = newkwargs["alphaM"] + newkwargs["betaK"] 
        res += newkwargs["betaKInit"] + newkwargs["betaKComm"]
        # at least one of the values should be greater than 0
        if res < eps:
            raise ValueError("At least one of the damping factors should be greater than 0")
        
        return newkwargs

    def get_values(self)-> Dict[str, Union[str, int, float, list]]:
        """Returns the current values of the Rayleigh damping parameters.

        Returns:
            Dictionary containing the current parameter values.
        """
        return {
            "alphaM": self.alphaM,
            "betaK": self.betaK,
            "betaKInit": self.betaKInit,
            "betaKComm": self.betaKComm
        }
    
    def update_values(self, **kwargs) -> None:
        """Updates the values of the Rayleigh damping parameters.

        Args:
            **kwargs: Parameter name-value pairs to update.

        Raises:
            ValueError: If parameter validation fails.
        """
        kwargs = self.validate(**kwargs)
        self.alphaM = kwargs["alphaM"]
        self.betaK = kwargs["betaK"]
        self.betaKInit = kwargs["betaKInit"]
        self.betaKComm = kwargs["betaKComm"]

    def to_tcl(self) -> str:
        """Returns the TCL code for the Rayleigh damping.

        Returns:
            OpenSees TCL command string for defining Rayleigh damping.
        """
        res = f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} {self.betaKInit} {self.betaKComm} (normal rayleigh damping)"
        return res
    
    @staticmethod
    def get_Type() -> str:
        """Returns the type identifier for Rayleigh damping.

        Returns:
            The string "Rayleigh" identifying this damping type.
        """
        return "Rayleigh"


class ModalDamping(DampingBase):
    """Implementation of Modal damping model.

    Modal damping allows specifying different damping ratios for different
    vibration modes of a structure.

    Attributes:
        numberofModes: Number of modes to consider for modal damping.
        dampingFactors: List of damping ratios for each mode.

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a modal damping
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('modal', numberofModes=3,
        >>> #                                   dampingFactors="0.02,0.03,0.04")
        >>> # print(damping.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a Modal damping instance.

        Args:
            **kwargs: Keyword arguments defining the modal damping properties.
                numberofModes: Number of modes to consider.
                dampingFactors: Comma-separated string or list of damping ratios.

        Raises:
            ValueError: If parameters are invalid or out of range.
        """
        kwargs = self.validate(**kwargs)
        super().__init__()
        self.numberofModes = kwargs["numberofModes"]
        self.dampingFactors = kwargs["dampingFactors"]
    
    def __str__(self) -> str:
        """
        Returns a string representation of the Modal damping object.
        
        Returns:
            str: A formatted string showing the damping class, name, tag, and parameters
        """
        res = super().__str__()
        res += f"\n\tNumber of Modes: {self.numberofModes}"
        res += f"\n\tDamping Factors: {self.dampingFactors}"
        return res
    
    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """
        Returns the parameters of the Modal damping.
        
        Returns:
            List[Tuple[str, str]]: List of parameter name-description pairs for Modal damping
        """
        return [
            ("numberofModes", "number of modes to consider for modal damping (integer greater than 0)"),
            ("dampingFactors", "damping factors for each mode (list of comma separated floats between 0 and 1)"),
        ]
    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Returns the notes of the Modal damping.
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing explanatory notes and references
                about Modal damping
        """
        return {
        "References": ["https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/modalDamping.html",
                       "https://portwooddigital.com/2019/09/12/be-careful-with-modal-damping/",
                       "https://portwooddigital.com/2023/01/25/modal-and-stiffness-proportional-damping/",
                    ]
        }

    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list]]:
        """
        Validates the Modal damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to validate
            
        Returns:
            Dict[str, Union[str, list]]: Validated parameters
            
        Raises:
            ValueError: If any parameter is invalid or out of range
        """
        numberofModes = 0
        dampingFactors = []

        if "numberofModes" in kwargs:
            numberofModes = kwargs["numberofModes"]
            try :
                numberofModes = int(numberofModes)
            except ValueError:
                raise ValueError("numberofModes should be an integer")
            if numberofModes <= 0:
                raise ValueError("numberofModes should be greater than 0")
        else:
            raise ValueError("numberofModes is required")
        
        if "dampingFactors" in kwargs:
            dampingFactors = kwargs["dampingFactors"]
            try:
                dampingFactors = dampingFactors.split(",")
            except :
                pass
            if not isinstance(dampingFactors, list):
                raise ValueError("dampingFactors should be a list")
            if len(dampingFactors) != numberofModes:
                raise ValueError("dampingFactors should have the same length as numberofModes")
            for i, factor in enumerate(dampingFactors):
                try:
                    dampingFactors[i] = float(factor)
                    if dampingFactors[i] < 0 or dampingFactors[i] > 1:
                        raise ValueError("dampingFactors should be greater than or equal to 0 and less than or equal to 1")
                except ValueError:
                    raise ValueError("dampingFactors should be a list of floats")
        else:
            raise ValueError("dampingFactors is required")
        
        return {
            "numberofModes": numberofModes,
            "dampingFactors": dampingFactors
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Returns the current values of the Modal damping parameters.
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary containing the
                current parameter values
        """
        return {
            "numberofModes": self.numberofModes,
            "dampingFactors": ",".join([str(x) for x in self.dampingFactors])
        }
    
    def update_values(self, **kwargs) -> None:
        """
        Updates the values of the Modal damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to update
            
        Raises:
            ValueError: If parameter validation fails
        """
        kwargs = self.validate(**kwargs)
        self.numberofModes = kwargs["numberofModes"]
        self.dampingFactors = kwargs["dampingFactors"]
    
    def to_tcl(self) -> str:
        """
        Returns the TCL code for the Modal damping.
        
        Returns:
            str: OpenSees TCL command string for defining Modal damping
        """
        res = f"-modalDamping {' '.join([str(x) for x in self.dampingFactors])}"
        return res
    
    @staticmethod
    def get_Type() -> str:
        """
        Returns the type identifier for Modal damping.
        
        Returns:
            str: The string "Modal" identifying this damping type
        """
        return "Modal"
                

class FrequencyRayleighDamping(RayleighDamping):
    """Implementation of Frequency-dependent Rayleigh damping model.

    This class extends RayleighDamping by allowing specification of target
    frequencies and a damping ratio, from which the Rayleigh coefficients
    are automatically calculated.

    Attributes:
        f1: Lower bound target frequency.
        f2: Upper bound target frequency.
        dampingFactor: Target damping ratio.

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a frequency Rayleigh damping
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('frequency rayleigh',
        >>> #                                   f1=0.5, f2=15.0, dampingFactor=0.05)
        >>> # print(damping.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a Frequency Rayleigh damping instance.

        Args:
            **kwargs: Keyword arguments defining the damping properties.
                f1: Lower bound target frequency. Defaults to 0.2 Hz.
                f2: Upper bound target frequency. Defaults to 20 Hz.
                dampingFactor: Target damping ratio (required).

        Raises:
            ValueError: If parameters are invalid or out of range.
        """
        kwargs = self.validate(**kwargs)
        super().__init__(**kwargs)
        self.f1 = kwargs["f1"]
        self.f2 = kwargs["f2"]
        self.dampingFactor = kwargs["dampingFactor"]
        kwargs = {
            "alphaM": 0.0,
            "betaK": 0.0,
            "betaKInit": 0.0,
            "betaKComm": 0.0,
        }

    def __str__(self) -> str:
        """
        Returns a string representation of the Frequency Rayleigh damping object.
        
        Returns:
            str: A formatted string showing the damping class, name, tag, and parameters
        """
        res = super().__str__()
        res += f"\n\tf1: {self.f1}"
        res += f"\n\tf2: {self.f2}"
        res += f"\n\tDamping Factor: {self.dampingFactor}"
        return res
    
    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """
        Returns the parameters of the Frequency Rayleigh damping.
        
        Returns:
            List[Tuple[str, str]]: List of parameter name-description pairs for 
                Frequency Rayleigh damping
        """
        return [
            ("dampingFactor", "damping factor for the frequency range (float between 0 and 1) (required)"),
            ("f1", "lower bound Target Frequency (float greater than 0) (optional, default=0.2)"),
            ("f2", "upper bound Target Frequency (float greater than 0) (optional, default=20)")
        ]
    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Returns the notes of the Frequency Rayleigh damping.
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing explanatory notes and references
                about Frequency Rayleigh damping including mathematical formulation
        """
        return {
        "Notes": [
            '''
                <b>Mathematical Formulation:</b>
                <p style="text-indent: 30px;">ω₁ = 2π f₁,  ω₂ = 2π f₂</p>
                <p style="text-indent: 30px;">α<sub>M</sub> = 2ω₁ω₂ / (ω₁ + ω₂)</p>
                <p style="text-indent: 30px;">β<sub>K</sub> = 2 / (ω₁ + ω₂)</p>
                <p style="text-indent: 30px;">β<sub>KInit</sub> = 0,  β<sub>KComm</sub> = 0</p>
              ''', 
            "The damping matrix is calculated as: C = α<sub>M</sub> M + β<sub>K</sub>  K",
            ],
        "References": []
    }

    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list]]:
        """
        Validates the Frequency Rayleigh damping parameters.
        
        Converts frequency and damping specifications into Rayleigh coefficients.
        
        Args:
            **kwargs: Parameter name-value pairs to validate
            
        Returns:
            Dict[str, Union[str, list]]: Validated parameters with calculated
                Rayleigh coefficients
            
        Raises:
            ValueError: If any parameter is invalid or out of range
        """
        f1 = 0.2 # Hz 
        f2 = 20  # Hz
        dampingFactor = 0

        if "f1" in kwargs:
            f1 = kwargs["f1"]
            try :
                f1 = float(f1)
            except ValueError:
                raise ValueError("f1 should be a float")
            if f1 <= 0:
                raise ValueError("f1 should be greater than 0")
        
        if "f2" in kwargs:
            f2 = kwargs["f2"]
            try :
                f2 = float(f2)
            except ValueError:
                raise ValueError("f2 should be a float")
            if f2 <= 0:
                raise ValueError("f2 should be greater than 0")
        
        if "dampingFactor" in kwargs:
            dampingFactor = kwargs["dampingFactor"]
            try:
                dampingFactor = float(dampingFactor)
            except ValueError:
                raise ValueError("dampingFactor should be a float")
            
            if dampingFactor < 0 or dampingFactor > 1:
                raise ValueError("dampingFactor should be greater than or equal to 0 and less than or equal to 1")
        else:
            raise ValueError("dampingFactor is required")
        
        # calculating the damping factors
        omega1 = 2 * 3.141592653589 * f1
        omega2 = 2 * 3.141592653589 * f2
        alphaM = 2 * dampingFactor * omega1 * omega2 / (omega1 + omega2)
        betaK  = (2 * dampingFactor) / (omega1 + omega2)

        return {
            "f1": f1,
            "f2": f2,
            "dampingFactor": dampingFactor,
            "alphaM": alphaM,
            "betaK": betaK,
            "betaKInit": 0,
            "betaKComm": 0
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Returns the current values of the Frequency Rayleigh damping parameters.
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary containing the
                current parameter values (frequency and damping specifications)
        """
        return {
            "dampingFactor": self.dampingFactor,
            "f1": self.f1,
            "f2": self.f2,
        }
    

    def update_values(self, **kwargs) -> None:
        """
        Updates the values of the Frequency Rayleigh damping parameters.
        
        Recalculates the Rayleigh coefficients based on the new frequency and
        damping specifications.
        
        Args:
            **kwargs: Parameter name-value pairs to update
            
        Raises:
            ValueError: If parameter validation fails
        """
        kwargs = self.validate(**kwargs)
        self.f1 = kwargs["f1"]
        self.f2 = kwargs["f2"]
        self.dampingFactor = kwargs["dampingFactor"]    
        self.alphaM = kwargs["alphaM"]
        self.betaK = kwargs["betaK"]
        self.betaKInit = kwargs["betaKInit"]
        self.betaKComm = kwargs["betaKComm"]

    @staticmethod
    def get_Type() -> str:
        """
        Returns the type identifier for Frequency Rayleigh damping.
        
        Returns:
            str: The string "Frequency Rayleigh" identifying this damping type
        """
        return "Frequency Rayleigh"
    
    def to_tcl(self) -> str:
        """
        Returns the TCL code for the Frequency Rayleigh damping.
        
        Returns:
            str: OpenSees TCL command string for defining Frequency Rayleigh damping
        """
        res = f"# damping rayleigh {self.tag} {self.alphaM} {self.betaK} {self.betaKInit} {self.betaKComm} (frequency rayleigh damping with f1 = {self.f1} and f2 = {self.f2} and damping factor = {self.dampingFactor})"
        return res


class UniformDamping(DampingBase):
    """Implementation of Uniform damping model.

    Uniform damping provides a constant damping ratio across a specified
    frequency range for all elements in a model.

    Attributes:
        dampingRatio: Target equivalent viscous damping ratio.
        freql: Lower bound of the frequency range.
        freq2: Upper bound of the frequency range.
        Ta: Activation time for damping (optional).
        Td: Deactivation time for damping (optional).
        tsTagScaleFactorVsTime: Time series tag for damping scaling (optional).

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a uniform damping
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('uniform', dampingRatio=0.05,
        >>> #                                   freql=0.1, freq2=10.0)
        >>> # print(damping.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a Uniform damping instance.

        Args:
            **kwargs: Keyword arguments defining the uniform damping properties.
                dampingRatio: Target equivalent viscous damping ratio (required).
                freql: Lower bound of the frequency range (required).
                freq2: Upper bound of the frequency range (required).
                Ta: Activation time for damping (optional).
                Td: Deactivation time for damping (optional).
                tsTagScaleFactorVsTime: Time series tag for damping scaling (optional).

        Raises:
            ValueError: If parameters are invalid or out of range.
        """
        kwargs = self.validate(**kwargs)
        super().__init__()
        self.dampingRatio = kwargs["dampingRatio"]
        self.freql = kwargs["freql"]
        self.freq2 = kwargs["freq2"]
        self.Ta    = kwargs.get("Ta", None)
        self.Td    = kwargs.get("Td", None)
        self.tsTagScaleFactorVsTime = kwargs.get("tsTagScaleFactorVsTime", None)

    def __str__(self) -> str:
        """
        Returns a string representation of the Uniform damping object.
        
        Returns:
            str: A formatted string showing the damping class, name, tag, and parameters
        """
        res = super().__str__()
        res += f"\n\tDamping Ratio: {self.dampingRatio}"
        res += f"\n\tLower Frequency: {self.freql}"
        res += f"\n\tUpper Frequency: {self.freq2}"
        res += f"\n\tTa: {self.Ta if self.Ta is not None else 'default'}"
        res += f"\n\tTd: {self.Td if self.Td is not None else 'default'}"
        res += f"\n\ttsTagScaleFactorVsTime: {self.tsTagScaleFactorVsTime if self.tsTagScaleFactorVsTime is not None else 'No time series'}"
        return res
    
    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """
        Returns the parameters of the Uniform damping.
        
        Returns:
            List[Tuple[str, str]]: List of parameter name-description pairs for Uniform damping
        """
        return [
            ("dampingRatio", "target equivalent viscous damping ratio (float between 0 and 1) (required)"),
            ("freql", "lower bound of the frequency range (in units of T^-1) (float greater than 0) (required)"),
            ("freq2", "upper bound of the frequency range (in units of T^-1) (float greater than 0) (required)"),
            ("Ta", "time when the damping is activated (float)"),
            ("Td", "time when the damping is deactivated (float) (optional)"),
            ("tsTagScaleFactorVsTime", "time series tag identifying the scale factor of the damping versus time (int) (optional)")
        ]
    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Returns the notes of the Uniform damping.
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing explanatory notes and references
                about Uniform damping
        """
        return {
            "References": [
                "https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/elementalDamping/UniformDamping.html",
            ]
        }
    
    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list]]:
        """
        Validates the Uniform damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to validate
            
        Returns:
            Dict[str, Union[str, list]]: Validated parameters
            
        Raises:
            ValueError: If any parameter is invalid or out of range
        """

        # make them float
        try :
            for key in ["dampingRatio", "freql", "freq2", "Ta", "Td"]:
                res = kwargs.get(key, None)
                if res is not None and res != "":
                    kwargs[key] = float(kwargs[key])
        except ValueError:
            raise ValueError(f"{key} should be a float")
        
        # check if the values are between 0 and 1
        for key in ["dampingRatio", "freql", "freq2"]:
            if key not in kwargs:
                raise ValueError(f"{key} is required")
            
        if kwargs["dampingRatio"] < 0 or kwargs["dampingRatio"] > 1:
            raise ValueError("dampingRatio should be greater than or equal to 0 and less than or equal to 1")
        
        if kwargs["freql"] <= 0:
            raise ValueError("freql should be greater than 0")
        
        if kwargs["freq2"] <= 0 or kwargs["freq2"] <= kwargs["freql"]:
            raise ValueError("freq2 should be greater than 0 and greater than freql")
        
        if "tsTagScaleFactorVsTime" in kwargs and kwargs["tsTagScaleFactorVsTime"] != "":
            try:
                kwargs["tsTagScaleFactorVsTime"] = int(kwargs["tsTagScaleFactorVsTime"])
            except ValueError:
                raise ValueError("tsTagScaleFactorVsTime should be an integer")

        
        return kwargs
        
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Returns the current values of the Uniform damping parameters.
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary containing the
                current parameter values
        """
        return {
            "dampingRatio": self.dampingRatio,
            "freql": self.freql,
            "freq2": self.freq2,
            **{k: v for k, v in {
            "Ta": self.Ta,
            "Td": self.Td,
            "tsTagScaleFactorVsTime": self.tsTagScaleFactorVsTime
            }.items() if v is not None}
        }
    
    def update_values(self, **kwargs) -> None:
        """
        Updates the values of the Uniform damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to update
            
        Raises:
            ValueError: If parameter validation fails
        """
        kwargs = self.validate(**kwargs)
        self.dampingRatio = kwargs["dampingRatio"]
        self.freql = kwargs["freql"]
        self.freq2 = kwargs["freq2"]
        
        # Handle optional parameters if they are present
        self.Ta = kwargs.get("Ta", None) # Ta is optional so we use get
        self.Td = kwargs.get("Td", None) # Td is optional so we use get
        self.tsTagScaleFactorVsTime = kwargs.get("tsTagScaleFactorVsTime", None) # tsTagScaleFactorVsTime is optional so we use get

    def to_tcl(self) -> str:
        """
        Returns the TCL code for the Uniform damping.
        
        Returns:
            str: OpenSees TCL command string for defining Uniform damping
        """
        res = f"damping Uniform {self.tag} {self.dampingRatio} {self.freql} {self.freq2}"
        if self.Ta is not None:
            res += f" -activateTime  {self.Ta}"
        if self.Td is not None:
            res += f" -deactivateTime {self.Td}"
        if self.tsTagScaleFactorVsTime is not None:
            res += f" -fact {self.tsTagScaleFactorVsTime}"

        return res
    
    @staticmethod
    def get_Type() -> str:
        """
        Returns the type identifier for Uniform damping.
        
        Returns:
            str: The string "Uniform" identifying this damping type
        """
        return "Uniform"


class SecantStiffnessProportional (DampingBase):
    """Implementation of Secant Stiffness Proportional damping model.

    This damping model applies damping proportional to the secant stiffness
    of elements, which is useful for nonlinear analysis.

    Attributes:
        dampingFactor: Coefficient used in the secant stiffness-proportional damping.
        Ta: Activation time for damping (optional).
        Td: Deactivation time for damping (optional).
        tsTagScaleFactorVsTime: Time series tag for damping scaling (optional).

    Example:
        >>> from femora.components.Damping.dampingBase import DampingManager
        >>> # Create a secant stiffness proportional damping
        >>> # manager = DampingManager()
        >>> # damping = manager.create_damping('secant stiffness proportional',
        >>> #                                   dampingFactor=0.02)
        >>> # print(damping.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a Secant Stiffness Proportional damping instance.

        Args:
            **kwargs: Keyword arguments defining the damping properties.
                dampingFactor: Coefficient used in damping (required).
                Ta: Activation time for damping (optional).
                Td: Deactivation time for damping (optional).
                tsTagScaleFactorVsTime: Time series tag for damping scaling (optional).

        Raises:
            ValueError: If parameters are invalid or out of range.
        """
        kwargs = self.validate(**kwargs)
        super().__init__()
        self.dampingFactor = kwargs["dampingFactor"]
        self.Ta = kwargs.get("Ta", None)
        self.Td = kwargs.get("Td", None)
        self.tsTagScaleFactorVsTime = kwargs.get("tsTagScaleFactorVsTime", None)
    
    def __str__(self) -> str:
        """
        Returns a string representation of the Secant Stiffness Proportional damping object.
        
        Returns:
            str: A formatted string showing the damping class, name, tag, and parameters
        """
        res = super().__str__()
        res += f"\n\tDamping Factor: {self.dampingFactor}"
        res += f"\n\tTa: {self.Ta if self.Ta is not None else 'default'}"
        res += f"\n\tTd: {self.Td if self.Td is not None else 'default'}"
        res += f"\n\ttsTagScaleFactorVsTime: {self.tsTagScaleFactorVsTime if self.tsTagScaleFactorVsTime is not None else 'No time series'}"
        return res
    
    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """
        Returns the parameters of the Secant Stiffness Proportional damping.
        
        Returns:
            List[Tuple[str, str]]: List of parameter name-description pairs for
                Secant Stiffness Proportional damping
        """
        return [
            ("dampingFactor", "coefficient used in the secant stiffness-proportional damping (float between 0 and 1) (required)"),
            ("Ta", "time when the damping is activated (float) (optional)"),
            ("Td", "time when the damping is deactivated (float) (optional)"),
            ("tsTagScaleFactorVsTime", "time series tag identifying the scale factor of the damping versus time (int) (optional)")
        ]
    
    @staticmethod
    def get_Notes() -> Dict[str, Union[str, list]]:
        """
        Returns the notes of the Secant Stiffness Proportional damping.
        
        Returns:
            Dict[str, Union[str, list]]: Dictionary containing explanatory notes and references
                about Secant Stiffness Proportional damping
        """
        return {
            "Notes": [
                """The formulation of the damping matrix is:
                <p style="text-indent: 30px;"> f <sub> damping </sub> = dampingFactor * K<sub> secant </sub> * u&#775; </p>
                """,
            ],

            "References": [
                "https://opensees.github.io/OpenSeesDocumentation/user/manual/model/damping/elementalDamping/SecStifDamping.html"
                ]
        }
    
    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list]]:
        """
        Validates the Secant Stiffness Proportional damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to validate
            
        Returns:
            Dict[str, Union[str, list]]: Validated parameters
            
        Raises:
            ValueError: If any parameter is invalid or out of range
        """
        # make them float
        try :
            for key in ["dampingFactor", "Ta", "Td"]:
                res = kwargs.get(key, None)
                if res is not None and res != "":
                    kwargs[key] = float(kwargs[key])
        except ValueError:
            raise ValueError(f"{key} should be a float")
        
        # check if the values are between 0 and 1
        if "dampingFactor" not in kwargs:
            raise ValueError("dampingFactor is required")
        
        if kwargs["dampingFactor"] < 0 or kwargs["dampingFactor"] > 1:
            raise ValueError("dampingFactor should be greater than or equal to 0 and less than or equal to 1")
        
        if "tsTagScaleFactorVsTime" in kwargs and kwargs["tsTagScaleFactorVsTime"] != "":
            try:
                kwargs["tsTagScaleFactorVsTime"] = int(kwargs["tsTagScaleFactorVsTime"])
            except ValueError:
                raise ValueError("tsTagScaleFactorVsTime should be an integer")

        return kwargs
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """
        Returns the current values of the Secant Stiffness Proportional damping parameters.
        
        Returns:
            Dict[str, Union[str, int, float, list]]: Dictionary containing the
                current parameter values
        """
        return {
            "dampingFactor": self.dampingFactor,
            **{k: v for k, v in {
            "Ta": self.Ta,
            "Td": self.Td,
            "tsTagScaleFactorVsTime": self.tsTagScaleFactorVsTime
            }.items() if v is not None}
        }
    
    def update_values(self, **kwargs) -> None:
        """
        Updates the values of the Secant Stiffness Proportional damping parameters.
        
        Args:
            **kwargs: Parameter name-value pairs to update
            
        Raises:
            ValueError: If parameter validation fails
        """
        kwargs = self.validate(**kwargs)
        self.dampingFactor = kwargs["dampingFactor"]

        # Handle optional parameters if they are present
        self.Ta = kwargs.get("Ta", None)
        self.Td = kwargs.get("Td", None)
        self.tsTagScaleFactorVsTime = kwargs.get("tsTagScaleFactorVsTime", None)
    
    def to_tcl(self) -> str:
        """
        Returns the TCL code for the Secant Stiffness Proportional damping.
        
        Returns:
            str: OpenSees TCL command string for defining Secant Stiffness Proportional damping
        """
        res = f"damping SecStiff {self.tag} {self.dampingFactor}"
        if self.Ta is not None:
            res += f" -activateTime  {self.Ta}"
        if self.Td is not None:
            res += f" -deactivateTime {self.Td}"
        if self.tsTagScaleFactorVsTime is not None:
            res += f" -fact {self.tsTagScaleFactorVsTime}"

        return res
    
    @staticmethod
    def get_Type() -> str:
        """
        Returns the type identifier for Secant Stiffness Proportional damping.
        
        Returns:
            str: The string "Secant Stiffness Proportional" identifying this damping type
        """
        return "Secant Stiffness Proportional"


class DampingManager:
    """
    A centralized manager for all damping instances in MeshMaker.
    
    The DampingManager implements the Singleton pattern to ensure a single, consistent
    point of damping management across the entire application. It provides methods for
    creating, retrieving, and managing damping objects used in dynamic structural analysis.
    
    All damping objects created through this manager are automatically tracked and tagged,
    simplifying the process of creating models with appropriate energy dissipation mechanisms.
    
    Usage:
        # Direct access
        from femora.components.Damping import DampingManager
        damping_manager = DampingManager()
        
        # Through MeshMaker (recommended)
        from femora.components.MeshMaker import MeshMaker
        mk = MeshMaker()
        damping_manager = mk.damping
        
        # Creating a damping instance
        rayleigh_damping = damping_manager.create_damping('rayleigh', alphaM=0.05, betaK=0.001)
    """
    _instance = None
    
    def __new__(cls):
        """
        Create a new DampingManager instance or return the existing one if already created.
        
        Returns:
            DampingManager: The singleton instance of the DampingManager
        """
        if cls._instance is None:
            cls._instance = super(DampingManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize the DampingManager.
        
        This method is called only once when the first instance of DampingManager is created.
        It sets up the necessary attributes and prepares the manager for use.
        """
        # Initialize any required attributes here
        self.rayleigh = RayleighDamping
        self.modal = ModalDamping
        self.frequencyRayleigh = FrequencyRayleighDamping
        self.uniform = UniformDamping
        self.secantStiffnessProportional = SecantStiffnessProportional

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of the DampingManager.
        
        This method ensures that only one instance of DampingManager exists throughout
        the application, following the Singleton design pattern.
        
        Returns:
            DampingManager: The singleton instance of the DampingManager
        """
        return cls._instance

    def create_damping(self, damping_type: str, **kwargs) -> DampingBase:
        """
        Create a new damping instance of the specified type.
        
        This method delegates the damping creation to the DampingRegistry, which
        maintains a dictionary of available damping types and their corresponding classes.
        
        Args:
            damping_type (str): The type of damping to create. Available types include:
                - 'rayleigh': Classical Rayleigh damping
                - 'modal': Modal damping for specific modes
                - 'frequency rayleigh': Rayleigh damping specified by target frequencies
                - 'uniform': Uniform damping across a frequency range
                - 'secant stiffness proportional': Damping proportional to secant stiffness
            **kwargs: Specific parameters for the damping type being created
                      (see documentation for each damping type for details)
        
        Returns:
            DampingBase: A new instance of the requested damping type
            
        Raises:
            ValueError: If the damping type is unknown or if required parameters are missing or invalid
        """
        return DampingRegistry.create_damping(damping_type, **kwargs)

    def get_damping(self, tag: int) -> DampingBase:
        """
        Get a damping instance by its tag.
        
        Args:
            tag (int): The unique identifier of the damping instance
            
        Returns:
            DampingBase: The damping instance with the specified tag
            
        Raises:
            KeyError: If no damping with the given tag exists
        """
        return DampingBase.get_damping(tag)

    def remove_damping(self, tag: int) -> None:
        """
        Remove a damping instance by its tag.
        
        This method removes the specified damping instance and automatically
        updates the tags of the remaining damping instances to maintain sequential numbering.
        
        Args:
            tag (int): The unique identifier of the damping instance to remove
        """
        DampingBase.remove_damping(tag)

    def get_all_dampings(self) -> Dict[int, DampingBase]:
        """
        Get all damping instances currently managed by this DampingManager.
        
        Returns:
            Dict[int, DampingBase]: A dictionary mapping tags to damping instances
        """
        return DampingBase._dampings

    def clear_all_dampings(self) -> None:
        """
        Remove all damping instances managed by this DampingManager.
        
        This method clears all damping instances from the manager, effectively
        resetting the damping system.
        """
        DampingBase._dampings.clear()

    def get_available_types(self) -> List[str]:
        """
        Get a list of available damping types that can be created.
        
        Returns:
            List[str]: A list of damping type names that can be used with create_damping()
        """
        return DampingRegistry.get_available_types()
    
    def set_start_tag(self, start_tag: int) -> None:
        """
        Set the starting tag number for new damping instances.
        
        This method allows customization of the initial tag number assigned to
        newly created damping instances. By default, tags start from 1 and
        increment sequentially with each new instance.
        
        Args:
            start_tag (int): The starting tag number for new damping instances
            
        Raises:
            ValueError: If start_tag is not a positive integer
        """
        if not isinstance(start_tag, int) or start_tag < 1:
            raise ValueError("start_tag must be a positive integer")
        DampingBase.set_tag_start(start_tag)


class DampingRegistry:
    """
    Registry of available damping types for dynamic structural analysis.
    
    The DampingRegistry maintains a dictionary of damping types and their corresponding
    classes, allowing for dynamic registration and creation of damping objects.
    
    This class uses class methods exclusively and is not intended to be instantiated.
    It serves as a factory for creating damping instances of various types.
    """
    _damping_types = {
        'frequency rayleigh': FrequencyRayleighDamping,
        'rayleigh': RayleighDamping,
        'modal': ModalDamping,
        'uniform': UniformDamping,
        'secant stiffness proportional': SecantStiffnessProportional
    }

    @classmethod
    def create_damping(cls, damping_type: str, **kwargs) -> DampingBase:
        """
        Create a new damping instance of the specified type.
        
        Args:
            damping_type (str): The type of damping to create (case insensitive)
            **kwargs: Parameter name-value pairs for the damping type
            
        Returns:
            DampingBase: A new instance of the requested damping type
            
        Raises:
            ValueError: If the damping type is unknown
        """
        if damping_type.lower() not in cls._damping_types:
            raise ValueError(f"Unknown damping type: {damping_type}")
        return cls._damping_types[damping_type.lower()](**kwargs)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """
        Get a list of available damping types that can be created.
        
        Returns:
            List[str]: A list of damping type names that can be used with create_damping()
        """
        return list(cls._damping_types.keys())

    @classmethod
    def register_damping_type(cls, name: str, damping_class: Type[DampingBase]):
        """
        Register a new damping type.
        
        Args:
            name (str): The name to use for this damping type (will be converted to lowercase)
            damping_class (Type[DampingBase]): The class to instantiate for this damping type
        """
        cls._damping_types[name.lower()] = damping_class

    @classmethod
    def remove_damping_type(cls, name: str):
        """
        Remove a registered damping type.
        
        Args:
            name (str): The name of the damping type to remove
        """
        if name.lower() in cls._damping_types:
            del cls._damping_types[name.lower()]


if __name__ == "__main__":
    # test the DampingBase class
    damping1 = DampingBase()
    damping2 = DampingBase()
    damping3 = DampingBase()

    RayleighDamping1 = RayleighDamping(alphaM=0.1, betaK=0.2, betaKInit=0.3, betaKComm=0.4)
    RayleighDamping2 = RayleighDamping(alphaM=0.5, betaK=0.6, betaKInit=0.7, betaKComm=0.8)
    ModalDamping1 = ModalDamping(numberofModes=2, dampingFactors="0.1,0.2")
    ModalDamping2 = ModalDamping(numberofModes=3, dampingFactors="0.3,0.4,0.5")

    DampingBase.print_dampings()

    print(10*"*"+"\nRemoving damping 2\n"+10*"*")

    DampingBase.remove_damping(2)
    DampingBase.print_dampings()

