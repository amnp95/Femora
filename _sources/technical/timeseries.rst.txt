TimeSeries
----------------

Understanding the TimeSeriesManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `TimeSeriesManager` is a core component of the Femora library that serves as a centralized system for creating, retrieving, tracking, and managing time series objects. It implements the Singleton pattern to ensure a single, consistent point of time series management across the entire application.

Time series defined in Femora are automatically tracked, tagged, and organized by the TimeSeriesManager, simplifying the process of creating dynamic models with time-varying loads, displacements, or boundary conditions.

Accessing the TimeSeriesManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to access the TimeSeriesManager in your code:

1. **Direct Access**: Import and use the TimeSeriesManager class directly

   .. code-block:: python

      from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager

      # Get the singleton instance
      timeseries_manager = TimeSeriesManager()

      # Use the time series manager directly
      timeseries_manager.create_time_series(...)

2. **Through Femora** (Recommended): Access via the Femora class's .timeSeries property

   .. code-block:: python

      import femora as fm

      # Create a Femora instance
       

      # Access the TimeSeriesManager through the .timeSeries property
      fm.timeSeries.create_time_series(...)

The second approach is recommended as it provides a unified interface to all of Femora's components and ensures proper initialization of all dependencies.

How TimeSeriesManager Works
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The TimeSeriesManager provides several key capabilities:

1. **Time Series Creation**: Creates time series objects of various types with appropriate parameters
2. **Time Series Tracking**: Keeps track of all time series by tag and name
3. **Time Series Tagging**: Automatically assigns sequential tags to time series
4. **Time Series Management**: Provides methods to retrieve, update, and delete time series

When a time series is created, the TimeSeriesManager:

- Assigns a unique numeric tag automatically
- Registers it with the user-provided name (if provided)
- Validates that all required parameters are present and valid

TimeSeriesManager API Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: femora.components.TimeSeries.timeSeriesBase.TimeSeriesManager
   :members:
   :undoc-members:
   :show-inheritance:

.. py:class:: TimeSeriesManager

   Singleton class for managing time series objects in the application.

   .. py:method:: clear_all(self)

      :no-index:

      Clears all time series from the registry.

   .. py:method:: create_time_series(self, series_type: str, **kwargs) -> TimeSeries

      :no-index:

      Create a new time series of the specified type.

      :param str series_type: The type of time series to create
      :param kwargs: Parameters specific to the time series type initialization
      :return: A new time series instance
      :rtype: TimeSeries

   .. py:method:: get_time_series(self, tag: int) -> TimeSeries

      :no-index:

      Retrieve a specific time series by its tag.

      :param int tag: The unique identifier tag of the time series
      :return: The time series object with the specified tag
      :rtype: TimeSeries

   .. py:method:: get_all_time_series(self) -> Dict[int, TimeSeries]

      :no-index:

      Retrieve all registered time series objects.

      :return: A dictionary of all time series objects
      :rtype: Dict[int, TimeSeries]

   .. py:method:: get_available_types(self) -> List[str]

      :no-index:

      Get a list of all available time series types.

      :return: A list of available time series types
      :rtype: List[str]

   .. py:method:: remove_time_series(self, tag: int) -> None

      :no-index:

      Remove a time series by its tag.

      :param int tag: The tag of the time series to remove

Time Series Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating time series is one of the primary functions of the TimeSeriesManager. When creating a time series, you need to specify:

1. **series_type**: Specifies the type of time series. Available types include:
   - `Constant`: A constant value across all time
   - `Linear`: Linear interpolation between specified time-value pairs
   - `Path`: Load time series from a path
   - `Path Time`: Load time and value series from separate paths
   - `Trig`: Trigonometric function (sine, cosine)
   - `PulseTrain`: Series of pulse loadings

2. **Time series-specific parameters**: Each time series type requires specific parameters

The TimeSeriesManager handles all the details of creating the appropriate time series object based on these parameters, ensuring type safety and parameter validation.

Usage Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import femora as fm

   # Create a femora instance
    

   # Create a constant time series
   constant_ts = fm.timeSeries.create_time_series(
       'Constant', 
       factor=1.0
   )

   # Create a linear time series
   linear_ts = fm.timeSeries.create_time_series(
       'Linear',
       time_points=[0.0, 0.1, 0.2, 0.5, 1.0],
       factor_points=[0.0, 0.2, 0.5, 0.8, 1.0]
   )

   # Create a path time series from a file
   path_ts = fm.timeSeries.create_time_series(
       'Path',
       file_path='data/acceleration.txt',
       dt=0.01,
       factor=9.81
   )

   # Create a trigonometric time series
   trig_ts = fm.timeSeries.create_time_series(
       'Trig',
       trig_type='Sine',  # 'Sine' or 'Cosine'
       period=1.0,
       phase_shift=0.0,
       factor=1.0
   )

Available Time Series Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   timeseries/constant
   timeseries/linear
   timeseries/path
   timeseries/pathtime
   timeseries/trig
   timeseries/pulsetrain

The time series types available in Femora provide various ways to define time-dependent behavior. Follow the links above to explore the different time series types available.

Each time series type has its own documentation page with detailed parameter descriptions and usage examples.

Applying Time Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Time series can be applied to various aspects of your model:

1. **Pattern Application**: Used with UniformExcitation or other patterns
2. **Load Application**: Applied to nodal loads, surface loads, etc.
3. **Boundary Condition Application**: For time-varying boundary conditions

Example of applying a time series to a uniform excitation pattern:

.. code-block:: python

   # Create a time series for ground motion
   ground_motion_ts = fm.timeSeries.create_time_series(
       'Path',
       file_path='ground_motion.txt',
       dt=0.01,
       factor=1.0
   )

   # Create a pattern using the time series
   fm.pattern.create_pattern(
       'uniformexcitation',
       dof=1,  # X direction
       time_series=ground_motion_ts,
       vel0=0.0
   )