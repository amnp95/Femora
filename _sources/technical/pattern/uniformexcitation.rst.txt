UniformExcitation Pattern
=========================

The UniformExcitation pattern allows applying a uniform excitation to a model acting in a certain direction.

Overview
--------
The UniformExcitation pattern is used to simulate ground motion in a specific degree of freedom (DOF) direction. It is commonly used in seismic analysis to apply acceleration histories to a model.

Parameters
----------
The following table describes the parameters for the UniformExcitation pattern:

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - **dof**
     - int
     - DOF direction the ground motion acts (required).
   * - **time_series**
     - TimeSeries
     - TimeSeries defining the acceleration history (required).
   * - **vel0**
     - float
     - Initial velocity (optional, default=0.0).
   * - **factor**
     - float
     - Constant factor (optional, default=1.0).

Usage Example
-------------

.. code-block:: python

   from femora.components.Pattern.patternBase import PatternManager
   from femora.components.TimeSeries.timeSeriesBase import TimeSeries

   # Create a time series
   time_series = TimeSeries(tag=1, values=[0.0, 0.1, 0.2, 0.3])

   # Get the pattern manager instance
   pattern_manager = PatternManager()

   # Create a UniformExcitation pattern
   uniform_excitation = pattern_manager.create_pattern(
       'uniformexcitation',
       dof=1,
       time_series=time_series,
       vel0=0.0,
       factor=1.0
   )

