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
      timeseries_manager.path(...)

2. **Through Femora** (Recommended): Access via the Femora class's .timeSeries property

   .. code-block:: python

      import femora as fm

      # Create a Femora instance
       

      # Access the TimeSeriesManager through the .timeSeries property
      fm.time_series.path(...)

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

   .. py:method:: get(self, tag: int) -> TimeSeries

      :no-index:

      Retrieve a specific time series by its tag.

   .. py:method:: get_all(self) -> Dict[int, TimeSeries]

      :no-index:

      Retrieve all managed time series keyed by tag.

   .. py:method:: remove(self, tag: int) -> None

      :no-index:

      Remove a managed time series by tag.

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
   constant_ts = fm.time_series.constant( 
       factor=1.0
   )

   # Create a linear time series
   linear_ts = fm.time_series.linear(
       factor=1.0
   )

   # Create a path time series from a file
   path_ts = fm.time_series.path(
       filePath='data/acceleration.txt',
       dt=0.01,
       factor=9.81
   )

   # Create a trigonometric time series
   trig_ts = fm.time_series.trig(
       period=1.0,
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
   ground_motion_ts = fm.time_series.path(
       filePath='ground_motion.txt',
       dt=0.01,
       factor=1.0
   )

   # Create a pattern using the time series
   fm.pattern.uniform_excitation(
       dof=1,  # X direction
       time_series=ground_motion_ts,
       vel0=0.0
   )