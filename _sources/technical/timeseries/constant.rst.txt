Constant
"""""""""""""""""""""

The Constant time series represents a fixed value that remains constant throughout time.

Parameters:

.. list-table:: 
    :header-rows: 1

    * - Parameter
      - Description
      - Type
    * - **factor**
      - The constant load factor value (default: 1.0)
      - float

.. admonition:: Example
    :class: note

    .. code-block:: python

        # Direct creation
        from femora.components.TimeSeries.timeSeriesBase import TimeSeriesManager
        
        ts_manager = TimeSeriesManager()
        
        # Create a constant time series with factor 2.0
        constant_ts = ts_manager.create_time_series(
            'Constant',
            factor=2.0
        )

        # Via Femora
        import femora as fm
        
         
        constant_ts = fm.timeSeries.create_time_series(
            'Constant',
            factor=1.5
        )

.. admonition:: Mathematical Representation
    :class: info

    The constant time series is defined by the formula:

    f(t) = factor

    where t is the time.