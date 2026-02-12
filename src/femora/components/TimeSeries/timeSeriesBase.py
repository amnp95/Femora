from abc import ABC, abstractmethod
from typing import List, Dict, Type, Tuple, Union

class TimeSeries(ABC):
    """Base abstract class for all time series in OpenSees.

    This class provides a foundation for creating and managing time-dependent
    functions (time series) for load patterns in structural analysis. It handles
    automatic tag assignment and time series registration.

    Attributes:
        tag: The unique sequential identifier for this time series.
        series_type: The type of time series (e.g., 'Constant', 'Linear', 'Path').

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a time series through the manager
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('constant', factor=1.0)
        >>> # print(ts.tag)
    """
    _time_series = {}  # Class-level dictionary to track all time series
    _start_tag = 1

    def __init__(self, series_type: str):
        """Initializes the TimeSeries with a sequential tag.

        Args:
            series_type: The type of time series (e.g., 'Constant', 'Linear').
        """
        self.tag = len(TimeSeries._time_series) + self._start_tag
        self.series_type = series_type
        
        # Register this time series in the class-level tracking dictionary
        self._time_series[self.tag] = self

    @classmethod
    def get_time_series(cls, tag: int) -> 'TimeSeries':
        """Retrieves a specific time series by its tag.

        Args:
            tag: The tag of the time series.

        Returns:
            The time series with the specified tag.

        Raises:
            KeyError: If no time series with the given tag exists.
        """
        if tag not in cls._time_series:
            raise KeyError(f"No time series found with tag {tag}")
        return cls._time_series[tag]

    @classmethod
    def remove_time_series(cls, tag: int) -> None:
        """Deletes a time series by its tag and reassigns remaining tags.

        Args:
            tag: The tag of the time series to delete.
        """
        if tag in cls._time_series:
            del cls._time_series[tag]
            # Re-tag all remaining time series sequentially
            cls._reassign_tags()

    @classmethod
    def _reassign_tags(cls) -> None:
        """Reassigns tags to all time series sequentially starting from 1.

        This method rebuilds the time series tracking dictionary with new sequential tags.
        """
        new_time_series = {}
        for idx, series in enumerate(sorted(cls._time_series.values(), key=lambda ts: ts.tag), start=cls._start_tag):
            series.tag = idx
            new_time_series[idx] = series
        cls._time_series = new_time_series

    @classmethod
    def get_all_time_series(cls) -> Dict[int, 'TimeSeries']:
        """Retrieves all created time series.

        Returns:
            A dictionary of all time series, keyed by their tags.
        """
        return cls._time_series.copy()

    @classmethod
    def reset(cls):
        """Resets all time series and tag counter to initial state.

        This method clears all time series and resets the starting tag to 1.
        """
        cls._time_series.clear()
        cls._start_tag = 1
        cls._reassign_tags()

    @classmethod
    def set_tag_start(cls, start_tag: int):
        """Sets the starting tag number and reassigns all time series tags.

        Args:
            start_tag: The new starting tag number.
        """
        cls._start_tag = start_tag
        cls._reassign_tags()

    @classmethod
    def clear_all(cls):
        """Clears all time series.

        This method removes all registered time series.
        """
        cls._time_series.clear()


    @abstractmethod
    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Subclasses must implement this method to generate the appropriate
        TCL command for use with OpenSees.

        Returns:
            TCL command string representation of the time series.
        """
        pass

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Subclasses should implement this method to return parameter metadata.

        Returns:
            List of (parameter name, description) tuples.
        """
        pass

    @abstractmethod
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the parameters defining this time series.

        Subclasses must implement this method to return current parameter values.

        Returns:
            Dictionary of parameter values.
        """
        pass

    @abstractmethod
    def update_values(self, **kwargs) -> None:
        """Updates the values of the time series.

        Subclasses must implement this method to update time series parameters.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        pass

    @staticmethod
    @abstractmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a TimeSeries.

        Subclasses must implement this method to validate parameters before creation.

        Args:
            **kwargs: Parameters to validate.

        Returns:
            Dictionary of validated parameter values.

        Raises:
            ValueError: If any parameter is invalid.
        """
        pass



class ConstantTimeSeries(TimeSeries):
    """Time series with a constant load factor throughout the analysis.

    This time series applies a constant scaling factor to loads, useful for
    static or constant-amplitude dynamic loads.

    Attributes:
        factor: The constant load factor value.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a constant time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('constant', factor=1.5)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a constant time series with the given factor.

        Args:
            factor: The constant load factor value. Defaults to 1.0 if not provided.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Constant')
        self.factor = kwargs["factor"]


    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the constant time series.
        """
        return f"timeSeries Constant {self.tag} -factor {self.factor}"


    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [("factor", "The constant load factor value (optional , default: 1.0)")]
    
    @staticmethod
    def validate(**kwargs)-> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a constant time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If factor is not a number.
        """
        factor = kwargs.get("factor", 1.0)
        factor = float(factor)
        # check if factor is a number
        if not isinstance(factor, (int, float)):
            raise ValueError("factor must be a number")
        return {"factor": factor}

    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing the factor value.
        """
        return {"factor": self.factor}

    def update_values(self, **kwargs) -> None:
        """Updates the factor value of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.factor = kwargs["factor"]


class LinearTimeSeries(TimeSeries):
    """Time series with a load factor that varies linearly with time.

    This time series applies a scaling factor that increases linearly with
    pseudo-time, useful for proportional loading scenarios.

    Attributes:
        factor: The linear load factor scale multiplier.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a linear time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('linear', factor=2.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a linear time series with the given factor.

        Args:
            factor: The linear load factor scale. Defaults to 1.0 if not provided.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Linear')
        self.factor = kwargs["factor"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the linear time series.
        """
        return f"timeSeries Linear {self.tag} -factor {self.factor}"

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [("factor", "The linear load factor scale (optional, default: 1.0)")]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a linear time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If factor is not a number.
        """
        factor = kwargs.get("factor", 1.0)
        factor = float(factor)
        if not isinstance(factor, (int, float)):
            raise ValueError("factor must be a number")
        return {"factor": factor}

    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing the factor value.
        """
        return {"factor": self.factor}

    def update_values(self, **kwargs) -> None:
        """Updates the factor value of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.factor = kwargs["factor"]


class TrigTimeSeries(TimeSeries):
    """Time series with a sinusoidal load factor.

    This time series applies a sinusoidal (trigonometric) scaling factor,
    useful for harmonic or cyclic loading scenarios.

    Attributes:
        tStart: Start time of the time series.
        tEnd: End time of the time series.
        period: Period of the sine wave.
        factor: Load factor amplitude.
        shift: Phase shift in radians.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a sinusoidal time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('trig', tStart=0.0, tEnd=10.0,
        >>> #                                  period=1.0, factor=1.0, shift=0.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a sinusoidal time series with the given parameters.

        Args:
            tStart: Start time of time series. Defaults to 0.0.
            tEnd: End time of time series. Defaults to 1.0.
            period: Period of sine wave. Defaults to 1.0.
            factor: Load factor amplitude. Defaults to 1.0.
            shift: Phase shift in radians. Defaults to 0.0.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Trig')
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the trigonometric time series.
        """
        return (f"timeSeries Trig {self.tag} "
                f"{self.tStart} {self.tEnd} {self.period} "
                f"-factor {self.factor} -shift {self.shift}")

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("tStart", "Start time of time series (optional, default: 0.0)"),
            ("tEnd", "End time of time series (optional, default: 1.0)"),
            ("period", "Period of sine wave (optional, default: 1.0)"),
            ("factor", "Load factor amplitude (optional, default: 1.0)"),
            ("shift", "Phase shift in radians (optional, default: 0.0)"),
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a trigonometric time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If any parameter is not a number, tStart >= tEnd, or period <= 0.
        """
        tStart = kwargs.get("tStart", 0.0)
        tEnd = kwargs.get("tEnd", 1.0)
        period = kwargs.get("period", 1.0)
        factor = kwargs.get("factor", 1.0)
        shift = kwargs.get("shift", 0.0)

        try:
            tStart = float(tStart)
        except ValueError:
            raise ValueError("tStart must be a number")
        
        try:
            tEnd = float(tEnd)
        except ValueError:
            raise ValueError("tEnd must be a number")
        
        try:
            period = float(period)
        except ValueError:
            raise ValueError("period must be a number")
        
        try:
            factor = float(factor)
        except ValueError:
            raise ValueError("factor must be a number")
        
        try:
            shift = float(shift)
        except ValueError:
            raise ValueError("shift must be a number")
        
        if tStart >= tEnd:
            raise ValueError("tStart must be less than tEnd")
        
        if period <= 0:
            raise ValueError("period must be greater than 0")
        
        return {
            "tStart": tStart,
            "tEnd": tEnd,
            "period": period,
            "factor": factor,
            "shift": shift,
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing tStart, tEnd, period, factor, and shift values.
        """
        return {
            "tStart": self.tStart,
            "tEnd": self.tEnd,
            "period": self.period,
            "factor": self.factor,
            "shift": self.shift,
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]

class RampTimeSeries(TimeSeries):
    """Time series with a ramped load factor from start to end time.

    This time series applies a load that ramps from zero to a target value
    over a specified duration, with optional smoothness and offset parameters.

    Attributes:
        tStart: Start time of the ramp.
        tRamp: Length of time to perform the ramp.
        smoothness: Smoothness parameter (0.0 to 1.0).
        offset: Vertical offset amount.
        cFactor: Load factor scale factor.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a ramp time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('ramp', tStart=0.0, tRamp=5.0,
        >>> #                                  smoothness=0.5, cFactor=1.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a ramp time series with the given parameters.

        Args:
            tStart: Start time of ramp. Defaults to 0.0.
            tRamp: Length of time to perform the ramp. Defaults to 1.0.
            smoothness: Smoothness parameter (0.0 to 1.0). Defaults to 0.0.
            offset: Vertical offset amount. Defaults to 0.0.
            cFactor: Load factor scale factor. Defaults to 1.0.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Ramp')
        self.tStart = kwargs["tStart"]
        self.tRamp = kwargs["tRamp"]
        self.smoothness = kwargs["smoothness"]
        self.offset = kwargs["offset"]
        self.cFactor = kwargs["cFactor"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the ramp time series.
        """
        cmd = f"timeSeries Ramp {self.tag} {self.tStart} {self.tRamp}"
        cmd += f" -smooth {self.smoothness}"
        cmd += f" -offset {self.offset}"
        cmd += f" -factor {self.cFactor}"
        return cmd

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("tStart", "Start time of ramp (optional, default: 0.0)"),
            ("tRamp", "Length of time to perform the ramp (optional, default: 1.0)"),
            ("smoothness", "Smoothness parameter (optional, default: 0.0)"),
            ("offset", "Vertical offset amount (optional, default: 0.0)"),
            ("cFactor", "Load factor scale factor (optional, default: 1.0)")
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a ramp time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If any parameter is not a number or smoothness is not between 0 and 1.
        """
        tStart = kwargs.get("tStart", 0.0)
        tRamp = kwargs.get("tRamp", 1.0)
        smoothness = kwargs.get("smoothness", 0.0)
        offset = kwargs.get("offset", 0.0)
        cFactor = kwargs.get("cFactor", 1.0)

        try :
            tStart = float(tStart)
        except ValueError:
            raise ValueError("tStart must be a number")
        
        try:
            tRamp = float(tRamp)
        except ValueError:
            raise ValueError("tRamp must be a number")
        
        try:
            smoothness = float(smoothness)
        except ValueError:
            raise ValueError("smoothness must be a number")
        
        try:
            offset = float(offset)
        except ValueError:
            raise ValueError("offset must be a number")
        
        try:
            cFactor = float(cFactor)
        except ValueError:
            raise ValueError("cFactor must be a number")
        
        
        if not (0 <= smoothness <= 1):
            raise ValueError("smoothness must be between 0 and 1")
        
        return {
            "tStart": tStart,
            "tRamp": tRamp,
            "smoothness": smoothness,
            "offset": offset,
            "cFactor": cFactor
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing tStart, tRamp, smoothness, offset, and cFactor values.
        """
        return {
            "tStart": self.tStart,
            "tRamp": self.tRamp,
            "smoothness": self.smoothness,
            "offset": self.offset,
            "cFactor": self.cFactor
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.tStart = kwargs["tStart"]
        self.tRamp = kwargs["tRamp"]
        self.smoothness = kwargs["smoothness"]
        self.offset = kwargs["offset"]
        self.cFactor = kwargs["cFactor"]



class TriangularTimeSeries(TimeSeries):
    """Time series with a triangular wave load pattern.

    This time series applies a triangular wave scaling factor, useful for
    cyclic loading with linear ramps.

    Attributes:
        tStart: Start time of the series.
        tEnd: End time of the series.
        period: Period of the triangular wave.
        factor: Load factor amplitude.
        shift: Phase shift.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a triangular time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('triangular', tStart=0.0, tEnd=10.0,
        >>> #                                  period=2.0, factor=1.0, shift=0.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a triangular time series with the given parameters.

        Args:
            tStart: Start time of series. Defaults to 0.0.
            tEnd: End time of series. Defaults to 1.0.
            period: Period of triangular wave. Defaults to 1.0.
            factor: Load factor amplitude. Defaults to 1.0.
            shift: Phase shift. Defaults to 0.0.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Triangular')
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the triangular time series.
        """
        return (f"timeSeries Triangular {self.tag} "
                f"{self.tStart} {self.tEnd} {self.period} "
                f"-factor {self.factor} -shift {self.shift}")

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("tStart", "Start time of series (optional, default: 0.0)"),
            ("tEnd", "End time of series (optional, default: 1.0)"),
            ("period", "Period of triangular wave (optional, default: 1.0)"),
            ("factor", "Load factor amplitude (optional, default: 1.0)"),
            ("shift", "Phase shift (optional, default: 0.0)")
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a triangular time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If any parameter is not a number, tStart >= tEnd, or period <= 0.
        """
        tStart = kwargs.get("tStart", 0.0)
        tEnd = kwargs.get("tEnd", 1.0)
        period = kwargs.get("period", 1.0)
        factor = kwargs.get("factor", 1.0)
        shift = kwargs.get("shift", 0.0)

        count = 0
        try:
            tStart = float(tStart); count += 1
            tEnd = float(tEnd); count += 1
            period = float(period); count += 1
            factor = float(factor); count += 1
            shift = float(shift); count += 1
        except ValueError:
            if count == 0:
                raise ValueError("tStart must be a number")
            elif count == 1:
                raise ValueError("tEnd must be a number")
            elif count == 2:
                raise ValueError("period must be a number")
            elif count == 3:
                raise ValueError("factor must be a number")
            elif count == 4:
                raise ValueError("shift must be a number")
            
        
        if tStart >= tEnd:
            raise ValueError("tStart must be less than tEnd")
        
        if period <= 0:
            raise ValueError("period must be greater than 0")
        
        return {
            "tStart": tStart,
            "tEnd": tEnd,
            "period": period,
            "factor": factor,
            "shift": shift
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing tStart, tEnd, period, factor, and shift values.
        """
        return {
            "tStart": self.tStart,
            "tEnd": self.tEnd,
            "period": self.period,
            "factor": self.factor,
            "shift": self.shift
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]


class RectangularTimeSeries(TimeSeries):
    """Time series with a rectangular (step) wave load pattern.

    This time series applies a rectangular wave scaling factor, creating
    step-function loading patterns.

    Attributes:
        tStart: Start time of the series.
        tEnd: End time of the series.
        factor: Load factor amplitude.
        period: Period of the rectangular wave.
        shift: Phase shift.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a rectangular time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('rectangular', tStart=0.0, tEnd=10.0,
        >>> #                                  period=2.0, factor=1.0, shift=0.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a rectangular time series with the given parameters.

        Args:
            tStart: Start time of series. Defaults to 0.0.
            tEnd: End time of series. Defaults to 1.0.
            factor: Load factor amplitude. Defaults to 1.0.
            period: Period of rectangular wave. Defaults to 0.0.
            shift: Phase shift. Defaults to 0.0.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Rectangular')
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.factor = kwargs["factor"]
        self.period = kwargs["period"]
        self.shift = kwargs["shift"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the rectangular time series.
        """
        return (f"timeSeries Rectangular {self.tag} "
                f"{self.tStart} {self.tEnd}  {self.period} -shift {self.shift} -factor {self.factor}")

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("tStart", "Start time of series (optional, default: 0.0)"),
            ("tEnd", "End time of series (optional, default: 1.0)"),
            ("factor", "Load factor amplitude (optional, default: 1.0)"),
            ("period", "Period of rectangular wave (optional, default: 0.0)"),
            ("shift", "Phase shift (optional, default: 0.0)")
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a rectangular time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If any parameter is not a number, tStart >= tEnd, or period <= 0.
        """
        tStart = kwargs.get("tStart", 0.0)
        tEnd = kwargs.get("tEnd", 1.0)
        factor = kwargs.get("factor", 1.0)
        period = kwargs.get("period", 0.0)
        shift = kwargs.get("shift", 0.0)

        try:
            tStart = float(tStart)
        except ValueError:
            raise ValueError("tStart must be a number")
        
        try:
            tEnd = float(tEnd)
        except ValueError:
            raise ValueError("tEnd must be a number")
        
        try:
            factor = float(factor)
        except ValueError:
            raise ValueError("factor must be a number")
        

        try:
            period = float(period)
        except ValueError:
            raise ValueError("period must be a number")
        
        try:
            shift = float(shift)
        except ValueError:
            raise ValueError("shift must be a number")

        
        if tStart >= tEnd:
            raise ValueError("tStart must be less than tEnd")
        
        if period <= 0:
            raise ValueError("period must be greater than 0")
        

        
        return {
            "tStart": tStart,
            "tEnd": tEnd,
            "factor": factor
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing tStart, tEnd, factor, period, and shift values.
        """
        return {
            "tStart": self.tStart,
            "tEnd": self.tEnd,
            "factor": self.factor,
            "period": self.period,
            "shift": self.shift
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.factor = kwargs["factor"]
        self.period = kwargs["period"]
        self.shift = kwargs["shift"]



class PulseTimeSeries(TimeSeries):
    """Time series with a pulsed load pattern.

    This time series applies a periodic pulse scaling factor, useful for
    intermittent or impulsive loading scenarios.

    Attributes:
        tStart: Start time of the pulse.
        tEnd: End time of the pulse.
        period: Period of the pulse.
        width: Width of pulse as a fraction of period (0 to 1).
        factor: Load factor amplitude.
        shift: Phase shift.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a pulse time series
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('pulse', tStart=0.0, tEnd=10.0,
        >>> #                                  period=1.0, width=0.3, factor=1.0, shift=0.0)
        >>> # print(ts.to_tcl())
    """
    def __init__(self, **kwargs):
        """Initializes a pulse time series with the given parameters.

        Args:
            tStart: Start time of pulse. Defaults to 0.0.
            tEnd: End time of pulse. Defaults to 1.0.
            period: Period of pulse. Defaults to 1.0.
            width: Width of pulse as a fraction of period (0 to 1). Defaults to 0.5.
            factor: Load factor amplitude. Defaults to 1.0.
            shift: Phase shift. Defaults to 0.0.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Pulse')
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.width = kwargs["width"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the pulse time series.
        """
        return (f"timeSeries Pulse {self.tag} "
                f"{self.tStart} {self.tEnd} {self.period} -width {self.width} "
                f"-factor {self.factor} -shift {self.shift}")

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("tStart", "Start time of pulse (optional, default: 0.0)"),
            ("tEnd", "End time of pulse (optional, default: 1.0)"),
            ("period", "Period of pulse (optional, default: 1.0)"),
            ("width", "Width of pulse as a fraction of period (optional, default: 0.5)"),
            ("factor", "Load factor amplitude (optional, default: 1.0)"),
            ("shift", "Phase shift (optional, default: 0.0)"),
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int]]:
        """Validates the input parameters for creating a pulse time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If any parameter is not a number, tStart >= tEnd, period <= 0,
                or width is not between 0 and 1.
        """
        tStart = kwargs.get("tStart", 0.0)
        tEnd = kwargs.get("tEnd", 1.0)
        period = kwargs.get("period", 1.0)
        width = kwargs.get("width", 0.5)
        factor = kwargs.get("factor", 1.0)
        shift = kwargs.get("shift", 0.0)


        count = 0
        try:
            tStart = float(tStart); count += 1
            tEnd = float(tEnd); count += 1
            period = float(period); count += 1
            width = float(width); count += 1
            factor = float(factor); count += 1
            shift = float(shift); count += 1
        except ValueError:
            if count == 0:
                raise ValueError("tStart must be a number")
            elif count == 1:
                raise ValueError("tEnd must be a number")
            elif count == 2:
                raise ValueError("period must be a number")
            elif count == 3:
                raise ValueError("width must be a number")
            elif count == 4:
                raise ValueError("factor must be a number")
            elif count == 5:
                raise ValueError("shift must be a number")
        
        if tStart >= tEnd:
            raise ValueError("tStart must be less than tEnd")
        
        if period <= 0:
            raise ValueError("period must be greater than 0")
        
        if width <= 0 or width >= 1:
            raise ValueError("width must be between 0 and 1")
        
        return {
            "tStart": tStart,
            "tEnd": tEnd,
            "period": period,
            "width": width,
            "factor": factor,
            "shift": shift,
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing tStart, tEnd, period, width, factor, and shift values.
        """
        return {
            "tStart": self.tStart,
            "tEnd": self.tEnd,
            "period": self.period,
            "width": self.width,
            "factor": self.factor,
            "shift": self.shift,
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.tStart = kwargs["tStart"]
        self.tEnd = kwargs["tEnd"]
        self.period = kwargs["period"]
        self.width = kwargs["width"]
        self.factor = kwargs["factor"]
        self.shift = kwargs["shift"]


class PathTimeSeries(TimeSeries):
    """Time series that interpolates between defined time and load factor points.

    This time series loads values from a file or list and interpolates between
    points, useful for earthquake ground motions or custom loading histories.

    Attributes:
        dt: Time increment for path.
        values: List of force values (if not using filePath).
        filePath: Path to file containing force values.
        factor: Scale factor for force values.
        useLast: Whether to use last force value beyond the last time point.
        prependZero: Whether to prepend a zero value at the start.
        startTime: Start time of the time series.
        time: List of time points (if not using dt or fileTime).
        fileTime: Path to file containing time points.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Create a path time series from file
        >>> # manager = TimeSeriesManager()
        >>> # ts = manager.create_time_series('path', dt=0.02,
        >>> #                                  filePath="ground_motion.acc", factor=9.81)
        >>> # Create a path time series from values
        >>> # ts2 = manager.create_time_series('path', dt=0.01,
        >>> #                                   values="0.0,1.0,0.5,0.0", factor=1.0)
    """
    def __init__(self, **kwargs):
        """Initializes a path time series with the given parameters.

        Args:
            dt: Time increment for path. Required if time or fileTime not provided.
            values: List of force values. Required if filePath not provided.
            filePath: Path to file containing force values. Required if values not provided.
            factor: Scale factor for force values. Defaults to 1.0.
            useLast: Use last force value beyond the last time point. Defaults to False.
            prependZero: Prepend a zero value at the start. Defaults to False.
            startTime: Start time of the time series. Defaults to 0.0.
            time: List of time points. Alternative to dt or fileTime.
            fileTime: Path to file containing time points. Alternative to dt or time.
        """
        kwargs = self.validate(**kwargs)
        super().__init__('Path')
        self.dt = kwargs.get("dt")
        self.values = kwargs.get("values")
        self.filePath = kwargs.get("filePath")
        self.factor = kwargs["factor"]
        self.useLast = kwargs["useLast"]
        self.prependZero = kwargs["prependZero"]
        self.startTime = kwargs["startTime"]
        self.time = kwargs.get("time")
        self.fileTime = kwargs.get("fileTime")

    def to_tcl(self) -> str:
        """Converts the time series to a TCL command string for OpenSees.

        Returns:
            TCL command string for the path time series.
        """
        cmd = f"timeSeries Path {self.tag}"
        if self.dt is not None:
            cmd += f" -dt {self.dt}"
        if self.filePath:
            cmd += f" -filePath {self.filePath}"
        elif self.values:
            values_str = " ".join(map(str, self.values))
            cmd += f" -values {{{values_str}}}"
        if self.time:
            time_str = " ".join(map(str, self.time))
            cmd += f" -time {{{time_str}}}"
        if self.fileTime:
            cmd += f" -fileTime {self.fileTime}"
        if self.factor != 1.0:
            cmd += f" -factor {self.factor}"
        if self.useLast:
            cmd += " -useLast"
        if self.prependZero:
            cmd += " -prependZero"
        if self.startTime != 0.0:
            cmd += f" -startTime {self.startTime}"
        return cmd

    @staticmethod
    def get_Parameters() -> List[Tuple[str, str]]:
        """Gets the parameters defining this time series.

        Returns:
            List of parameter names and explanations as tuples.
        """
        return [
            ("dt", "Time increment for path"),
            ("time", "List of time points (optional)"),
            ("fileTime", "Path to file containing time points (optional)"),
            ("values", "List of comma separated force values (optional if using filePath)"),
            ("filePath", "Path to file containing force values (optional)"),
            ("factor", "Scale factor for force values (optional, default: 1.0)"),
            ("useLast", "Use last force value beyond the last time point if true (optional, default: False)"),
            ("prependZero", "Prepend a zero value at the start (optional, default: False)"),
            ("startTime", "Start time of the time series (optional, default: 0.0)"),
        ]
    
    @staticmethod
    def validate(**kwargs) -> Dict[str, Union[str, list, float, int, bool]]:
        """Validates the input parameters for creating a path time series.

        Args:
            **kwargs: Parameters for time series initialization.

        Returns:
            Dictionary of validated parameter names and values.

        Raises:
            ValueError: If required parameters are missing, invalid types provided,
                or conflicting parameters are specified.
        """
        dt = kwargs.get("dt")
        factor = kwargs.get("factor", 1.0)
        useLast = kwargs.get("useLast", False)
        prependZero = kwargs.get("prependZero", False)
        startTime = kwargs.get("startTime", 0.0)
        time = kwargs.get("time")
        fileTime = kwargs.get("fileTime")
        values = kwargs.get("values")
        filePath = kwargs.get("filePath")

        if kwargs.get("values") is not None and kwargs.get("filePath") is None:
            values = kwargs.get("values")
            values = [float(v) for v in values.split(",")]
        elif kwargs.get("filePath") is not None and kwargs.get("values") is None:
            filePath = str(kwargs.get("filePath"))
        elif kwargs.get("values") is None and kwargs.get("filePath") is None:
            raise ValueError("Either values or filePath must be provided")
        else:
            raise ValueError("Only one of values or filePath should be provided")
        

        if time is not None and fileTime is not None and dt is not None:
            raise ValueError("Only one of time, fileTime or dt should be provided")
        elif time is None and fileTime is None and dt is None:
            raise ValueError("One of time, fileTime or dt should be provided")
        elif time is  None and fileTime is None and dt is not None:
            try:
                dt = float(dt)
            except ValueError:
                raise ValueError("dt must be a number")
        elif time is not None and fileTime is None and dt is None:
            try :
                time = [float(t) for t in time.split(",")]
            except ValueError:
                raise ValueError("time must be a list of comma separated numbers")
        elif time is None and fileTime is not None and dt is None:
            fileTime = str(fileTime)
        
        elif time is not None :
            if fileTime is not None or dt is not None:
                raise ValueError("Only one of time, fileTime or dt should be provided")
        elif time is None:
            if fileTime is not None and dt is not None:
                raise ValueError("Only one of time, fileTime or dt should be provided")


        if values and not isinstance(values, list):
            raise ValueError("values must be a list")
        

        try :
            factor = float(factor)
        except ValueError:
            raise ValueError("factor must be a number")
        
        
        if not isinstance(useLast, bool):
            raise ValueError("useLast must be a boolean")
        
        if not isinstance(prependZero, bool):
            raise ValueError("prependZero must be a boolean")
        
        try:
            startTime = float(startTime)
        except ValueError:
            raise ValueError("startTime must be a number")
        
        if time and not isinstance(time, list):
            raise ValueError("time must be a list")
        
        return {
            "dt": dt,
            "values": values,
            "filePath": filePath,
            "factor": factor,
            "useLast": useLast,
            "prependZero": prependZero,
            "startTime": startTime,
            "time": time,
            "fileTime": fileTime
        }
    
    def get_values(self) -> Dict[str, Union[str, int, float, list, bool]]:
        """Gets the current parameter values of this time series.

        Returns:
            Dictionary containing all path time series parameters.
        """
        return {
            "dt": self.dt,
            "values": ",".join(map(str, self.values)) if self.values else None,
            "filePath": self.filePath,
            "factor": self.factor,
            "useLast": self.useLast,
            "prependZero": self.prependZero,
            "startTime": self.startTime,
            "time": ",".join(map(str, self.time)) if self.time else None,
            "fileTime": self.fileTime
        }

    def update_values(self, **kwargs) -> None:
        """Updates the parameter values of the time series.

        Args:
            **kwargs: Parameters for time series initialization.
        """
        kwargs = self.validate(**kwargs)
        self.dt = kwargs["dt"]
        self.values = kwargs["values"]
        self.filePath = kwargs["filePath"]
        self.factor = kwargs["factor"]
        self.useLast = kwargs["useLast"]
        self.prependZero = kwargs["prependZero"]
        self.startTime = kwargs["startTime"]
        self.time = kwargs["time"]
        self.fileTime = kwargs["fileTime"]




class TimeSeriesRegistry:
    """Registry for managing time series types and their creation.

    This class provides a centralized system for registering time series classes
    and creating time series instances dynamically by type name.

    Attributes:
        _time_series_types: Class-level dictionary mapping time series type names
            to their time series classes.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesRegistry
        >>> # Register a custom time series type
        >>> # TimeSeriesRegistry.register_time_series_type('custom', CustomTimeSeries)
        >>> # Create a time series
        >>> # ts = TimeSeriesRegistry.create_time_series('constant', factor=1.0)
        >>> types = TimeSeriesRegistry.get_time_series_types()
        >>> print('constant' in types)
        True
    """
    _time_series_types = {
        'constant': ConstantTimeSeries,
        'linear': LinearTimeSeries,
        'trig': TrigTimeSeries,
        'ramp': RampTimeSeries,
        'triangular': TriangularTimeSeries,
        'rectangular': RectangularTimeSeries,
        'pulse': PulseTimeSeries,
        'path': PathTimeSeries,
    }

    @classmethod
    def register_time_series_type(cls, name: str, series_class: Type[TimeSeries]):
        """Registers a new time series type for easy creation.

        Args:
            name: The name of the time series type (case-insensitive).
            series_class: The class of the time series to register.
        """
        cls._time_series_types[name.lower()] = series_class

    @classmethod
    def get_time_series_types(cls):
        """Gets available time series types.

        Returns:
            List of registered time series type names.
        """
        return list(cls._time_series_types.keys())

    @classmethod
    def create_time_series(cls, series_type: str, **kwargs) -> TimeSeries:
        """Creates a new time series of a specific type.

        Args:
            series_type: Type of time series to create (case-insensitive).
            **kwargs: Parameters for time series initialization.

        Returns:
            A new time series instance.

        Raises:
            KeyError: If the time series type is not registered.
        """
        if series_type.lower() not in cls._time_series_types:
            raise KeyError(f"Time series type {series_type} not registered")
        
        return cls._time_series_types[series_type.lower()](**kwargs)




class TimeSeriesManager:
    """Singleton manager class for creating and managing time series.

    This class provides a unified interface for creating time series with
    convenient access to time series types.

    Attributes:
        path: Reference to PathTimeSeries class.
        constant: Reference to ConstantTimeSeries class.
        linear: Reference to LinearTimeSeries class.
        trig: Reference to TrigTimeSeries class.
        ramp: Reference to RampTimeSeries class.
        triangular: Reference to TriangularTimeSeries class.
        rectangular: Reference to RectangularTimeSeries class.
        pulse: Reference to PulseTimeSeries class.

    Example:
        >>> from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        >>> # Get the singleton instance
        >>> manager = TimeSeriesManager()
        >>> # Create a time series
        >>> # ts = manager.create_time_series('constant', factor=1.0)
        >>> # Get all time series
        >>> all_ts = manager.get_all_time_series()
        >>> types = manager.get_available_types()
        >>> print('constant' in types)
        True
    """
    _instance = None

    def __new__(cls):
        """Creates a new instance if one doesn't exist (singleton pattern).

        Returns:
            The singleton instance of TimeSeriesManager.
        """
        if cls._instance is None:
            cls._instance = super(TimeSeriesManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the TimeSeriesManager singleton instance.

        This method only initializes on first creation. Subsequent calls
        return the existing instance without re-initialization.
        """
        self.path = PathTimeSeries
        self.constant = ConstantTimeSeries
        self.linear = LinearTimeSeries
        self.trig = TrigTimeSeries
        self.ramp = RampTimeSeries
        self.triangular = TriangularTimeSeries
        self.rectangular = RectangularTimeSeries
        self.pulse = PulseTimeSeries
    
    def __len__(self):
        """Gets the number of time series objects.

        Returns:
            The number of time series objects.
        """
        return len(TimeSeries._time_series)

    def __iter__(self):
        """Iterates over the time series objects.

        Returns:
            An iterator over the time series objects.
        """
        return iter(TimeSeries._time_series.values())

    def create_time_series(self, series_type: str, **kwargs) -> TimeSeries:
        """Creates a new time series of the specified type.

        Args:
            series_type: The type of time series to create (e.g., 'constant', 'linear').
            **kwargs: Parameters specific to the time series type initialization.

        Returns:
            A new time series instance.

        Raises:
            KeyError: If the requested time series type is not registered.
            ValueError: If validation of parameters fails.
        """
        return TimeSeriesRegistry.create_time_series(series_type, **kwargs)

    def get_time_series(self, tag: int) -> TimeSeries:
        """Retrieves a specific time series by its tag.

        Args:
            tag: The unique identifier tag of the time series.

        Returns:
            The time series object with the specified tag.

        Raises:
            KeyError: If no time series with the given tag exists.
        """
        return TimeSeries.get_time_series(tag)

    def remove_time_series(self, tag: int) -> None:
        """Removes a time series by its tag.

        This method removes the time series with the given tag and
        reassigns sequential tags to all remaining time series objects.

        Args:
            tag: The tag of the time series to remove.
        """
        TimeSeries.remove_time_series(tag)

    def get_all_time_series(self) -> Dict[int, TimeSeries]:
        """Retrieves all registered time series objects.

        Returns:
            A dictionary of all time series objects, where keys are the tags
                and values are the TimeSeries objects.
        """
        return TimeSeries.get_all_time_series()

    def get_available_types(self) -> List[str]:
        """Gets a list of all available time series types.

        Returns:
            A list of strings representing available time series types.
        """
        return TimeSeriesRegistry.get_time_series_types()

    def clear_all(self):
        """Clears all time series from the registry.

        This method clears all registered time series objects, effectively
        resetting the state of the time series management system.
        """
        TimeSeries._time_series.clear()

