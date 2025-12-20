Linear
""""""""""""""""""""""

The Linear time series represents a linearly varying function with time, defined by a scale factor.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **factor**
      - Scale factor for the linear function (default: 1.0)
      - float

The linear time series creates a function that increases linearly with time, multiplied by the factor parameter.

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        
        ts_manager = TimeSeriesManager()
        
        # Create a linear time series with factor 2.0
        linear_ts = ts_manager.create_time_series(
            'Linear',
            factor=2.0
        )

        # Via Femora
        import femora as fm
        
         
        linear_ts = fm.timeSeries.create_time_series(
            'Linear',
            factor=1.5
        )

.. admonition:: Mathematical Representation
    :class: info

    The linear time series is defined by the formula:

    f(t) = factor × t

    where t is the time.

